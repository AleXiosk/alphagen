import json
import importlib.util
import os
import sys
from typing import Optional, Tuple, List, Union
from datetime import datetime
from pathlib import Path
from openai import OpenAI
import fire

class _FilteredStderr:
    def __init__(self, wrapped):
        self._wrapped = wrapped

    def write(self, data):
        if isinstance(data, str) and "Gym has been unmaintained since 2022" in data:
            return len(data)
        return self._wrapped.write(data)

    def flush(self):
        return self._wrapped.flush()

    def __getattr__(self, name):
        return getattr(self._wrapped, name)


if os.environ.get("ALPHAGEN_HIDE_GYM_NOTICE", "1") == "1":
    sys.stderr = _FilteredStderr(sys.stderr)


import numpy as np
import torch
from sb3_contrib.ppo_mask import MaskablePPO
from stable_baselines3.common.callbacks import BaseCallback

from alphagen.data.expression import *
from alphagen.data.parser import ExpressionParser
from alphagen.models.linear_alpha_pool import LinearAlphaPool, MseAlphaPool
from alphagen.rl.env.wrapper import AlphaEnv
from alphagen.rl.policy import LSTMSharedNet
from alphagen.utils import reseed_everything, get_logger
from alphagen.rl.env.core import AlphaEnvCore
from alphagen_qlib.calculator import QLibStockDataCalculator
from alphagen_qlib.stock_data import initialize_qlib, StockData
from alphagen_llm.client import ChatClient, OpenAIClient, ChatConfig
from alphagen_llm.prompts.system_prompt import EXPLAIN_WITH_TEXT_DESC
from alphagen_llm.prompts.interaction import InterativeSession, DefaultInteraction


def _resolve_tensorboard_log_dir(path: str) -> Optional[str]:
    if importlib.util.find_spec("tensorboard") is None:
        print("[Main] tensorboard is not installed, disabling TensorBoard logging.")
        return None
    return path


def read_alphagpt_init_pool(seed: int) -> List[Expression]:
    DIR = "./out/llm-tests/interaction"
    parser = build_parser()
    for path in Path(DIR).glob(f"v0_{seed}*"):
        with open(path / "report.json") as f:
            data = json.load(f)
            pool_state = data[-1]["pool_state"]
            return [parser.parse(expr) for expr, _ in pool_state]
    return []


def build_parser() -> ExpressionParser:
    return ExpressionParser(
        Operators,
        ignore_case=True,
        non_positive_time_deltas_allowed=False,
        additional_operator_mapping={
            "Max": [Greater],
            "Min": [Less],
            "Delta": [Sub]
        }
    )


def build_chat_client(log_dir: str) -> ChatClient:
    logger = get_logger("llm", os.path.join(log_dir, "llm.log"))
    return OpenAIClient(
        client=OpenAI(base_url="https://api.ai.cs.ac.cn/v1"),
        config=ChatConfig(
            system_prompt=EXPLAIN_WITH_TEXT_DESC,
            logger=logger
        )
    )


class CustomCallback(BaseCallback):
    def __init__(
        self,
        save_path: str,
        test_calculators: List[QLibStockDataCalculator],
        verbose: int = 0,
        chat_session: Optional[InterativeSession] = None,
        llm_every_n_steps: int = 25_000,
        drop_rl_n: int = 5
    ):
        super().__init__(verbose)
        self.save_path = save_path
        self.test_calculators = test_calculators
        os.makedirs(self.save_path, exist_ok=True)

        self.llm_use_count = 0
        self.last_llm_use = 0
        self.obj_history: List[Tuple[int, float]] = []
        self.llm_every_n_steps = llm_every_n_steps
        self.chat_session = chat_session
        self._drop_rl_n = drop_rl_n

    def _on_step(self) -> bool:
        return True

    def _on_rollout_end(self) -> None:
        if self.chat_session is not None:
            self._try_use_llm()

        self.logger.record('pool/size', self.pool.size)
        self.logger.record('pool/significant', (np.abs(self.pool.weights[:self.pool.size]) > 1e-4).sum())
        self.logger.record('pool/best_ic_ret', self.pool.best_ic_ret)
        self.logger.record('pool/eval_cnt', self.pool.eval_cnt)
        n_days = sum(calculator.data.n_days for calculator in self.test_calculators)
        ic_test_mean, rank_ic_test_mean = 0., 0.
        for i, test_calculator in enumerate(self.test_calculators, start=1):
            ic_test, rank_ic_test = self.pool.test_ensemble(test_calculator)
            ic_test_mean += ic_test * test_calculator.data.n_days / n_days
            rank_ic_test_mean += rank_ic_test * test_calculator.data.n_days / n_days
            self.logger.record(f'test/ic_{i}', ic_test)
            self.logger.record(f'test/rank_ic_{i}', rank_ic_test)
        self.logger.record(f'test/ic_mean', ic_test_mean)
        self.logger.record(f'test/rank_ic_mean', rank_ic_test_mean)
        self.save_checkpoint()

    def save_checkpoint(self):
        path = os.path.join(self.save_path, f'{self.num_timesteps}_steps')
        self.model.save(path)   # type: ignore
        if self.verbose > 1:
            print(f'Saving model checkpoint to {path}')
        with open(f'{path}_pool.json', 'w') as f:
            json.dump(self.pool.to_json_dict(), f)

    def show_pool_state(self):
        state = self.pool.state
        print('---------------------------------------------')
        for i in range(self.pool.size):
            weight = state['weights'][i]
            expr_str = str(state['exprs'][i])
            ic_ret = state['ics_ret'][i]
            print(f'> Alpha #{i}: {weight}, {expr_str}, {ic_ret}')
        print(f'>> Ensemble ic_ret: {state["best_ic_ret"]}')
        print('---------------------------------------------')

    def _try_use_llm(self) -> None:
        n_steps = self.num_timesteps
        if n_steps - self.last_llm_use < self.llm_every_n_steps:
            return
        self.last_llm_use = n_steps
        self.llm_use_count += 1
        
        assert self.chat_session is not None
        self.chat_session.client.reset()
        logger = self.chat_session.logger
        logger.debug(
            f"[Step: {n_steps}] Trying to invoke LLM (#{self.llm_use_count}): "
            f"IC={self.pool.best_ic_ret:.4f}, obj={self.pool.best_ic_ret:.4f}")

        try:
            remain_n = max(0, self.pool.size - self._drop_rl_n)
            remain = self.pool.most_significant_indices(remain_n)
            self.pool.leave_only(remain)
            self.chat_session.update_pool(self.pool)
        except Exception as e:
            logger.warning(f"LLM invocation failed due to {type(e)}: {str(e)}")

    @property
    def pool(self) -> LinearAlphaPool:
        assert(isinstance(self.env_core.pool, LinearAlphaPool))
        return self.env_core.pool

    @property
    def env_core(self) -> AlphaEnvCore:
        return self.training_env.envs[0].unwrapped  # type: ignore


def run_single_experiment(
    seed: int = 0,
    qlib_dir: str = "~/.qlib/qlib_data/cn_data",
    qlib_kernels: Optional[int] = None,
    device: str = "cuda:0",
    instruments: str = "csi300",
    pool_capacity: int = 50,
    steps: int = 500_000,
    alphagpt_init: bool = False,
    use_llm: bool = False,
    llm_every_n_steps: int = 25_000,
    drop_rl_n: int = 5,
    llm_replace_n: int = 3,
    ppo_n_steps: int = 8192,
    ppo_batch_size: int = 1024,
    ppo_n_epochs: int = 10,
    learning_rate: float = 3e-4,
    lstm_layers: int = 3,
    d_model: int = 256,
    dropout: float = 0.1,
    progress_bar: bool = True,
    print_expr: bool = False,
):
    reseed_everything(seed)
    qlib_dir = os.path.expanduser(qlib_dir)
    if qlib_kernels is None:
        qlib_kernels = 1 if os.name == "nt" else 8
    initialize_qlib(qlib_dir, kernels=qlib_kernels)

    if ppo_n_steps <= 0:
        raise ValueError("ppo_n_steps must be greater than 0.")
    if ppo_batch_size <= 0:
        raise ValueError("ppo_batch_size must be greater than 0.")
    if ppo_n_epochs <= 0:
        raise ValueError("ppo_n_epochs must be greater than 0.")
    if ppo_n_steps % ppo_batch_size != 0:
        raise ValueError("ppo_batch_size must divide ppo_n_steps when using a single environment.")

    device_obj = torch.device(device)
    if device_obj.type == "cuda":
        torch.backends.cudnn.benchmark = True

    llm_replace_n = 0 if not use_llm else llm_replace_n
    tensorboard_log_dir = _resolve_tensorboard_log_dir("./out/tensorboard")
    print(f"""[Main] Starting training process
    Seed: {seed}
    Qlib dir: {qlib_dir}
    Qlib kernels: {qlib_kernels}
    Device: {device_obj}
    Instruments: {instruments}
    Pool capacity: {pool_capacity}
    Total Iteration Steps: {steps}
    AlphaGPT-Like Init-Only LLM Usage: {alphagpt_init}
    Use LLM: {use_llm}
    Invoke LLM every N steps: {llm_every_n_steps}
    Replace N alphas with LLM: {llm_replace_n}
    Drop N alphas before LLM: {drop_rl_n}
    PPO n_steps: {ppo_n_steps}
    PPO batch size: {ppo_batch_size}
    PPO n_epochs: {ppo_n_epochs}
    Learning rate: {learning_rate}
    LSTM layers: {lstm_layers}
    D model: {d_model}
    Dropout: {dropout}
    Progress bar: {progress_bar}
    TensorBoard log dir: {tensorboard_log_dir}""")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # tag = "rlv2" if llm_add_subexpr == 0 else f"afs{llm_add_subexpr}aar1-5"
    tag = (
        "agpt" if alphagpt_init else
        "rl" if not use_llm else
        f"llm_d{drop_rl_n}")
    name_prefix = f"{instruments}_{pool_capacity}_{seed}_{timestamp}_{tag}"
    save_path = os.path.join("./out/results", name_prefix)
    os.makedirs(save_path, exist_ok=True)

    close = Feature(FeatureType.CLOSE)
    target = Ref(close, -20) / close - 1

    def get_dataset(start: str, end: str) -> StockData:
        return StockData(
            instrument=instruments,
            start_time=start,
            end_time=end,
            device=device_obj
        )

    segments = [
        ("2012-01-01", "2021-12-31"),
        ("2022-01-01", "2022-06-30"),
        ("2022-07-01", "2022-12-31"),
        ("2023-01-01", "2023-06-30")
    ]
    datasets: List[StockData] = []
    for idx, segment in enumerate(segments, start=1):
        start, end = segment
        print(f"[Main] Building dataset {idx}/{len(segments)}: {start} -> {end}")
        dataset = get_dataset(start, end)
        datasets.append(dataset)
        print(
            f"[Main] Dataset {idx}/{len(segments)} ready: "
            f"n_days={dataset.n_days}, n_stocks={dataset.n_stocks}"
        )

    calculators: List[QLibStockDataCalculator] = []
    for idx, dataset in enumerate(datasets, start=1):
        print(f"[Main] Building calculator {idx}/{len(datasets)}")
        calculators.append(QLibStockDataCalculator(dataset, target))

    def build_pool(exprs: List[Expression]) -> LinearAlphaPool:
        pool = MseAlphaPool(
            capacity=pool_capacity,
            calculator=calculators[0],
            ic_lower_bound=None,
            l1_alpha=5e-3,
            device=device_obj
        )
        if len(exprs) != 0:
            pool.force_load_exprs(exprs)
        return pool

    chat, inter, pool = None, None, build_pool([])
    if alphagpt_init:
        pool = build_pool(read_alphagpt_init_pool(seed))
    elif use_llm:
        chat = build_chat_client(save_path)
        inter = DefaultInteraction(
            build_parser(), chat, build_pool,
            calculator_train=calculators[0], calculators_test=calculators[1:],
            replace_k=llm_replace_n, forgetful=True
        )
        pool = inter.run()

    env = AlphaEnv(
        pool=pool,
        device=device_obj,
        print_expr=print_expr
    )
    print("[Main] Environment ready")
    checkpoint_callback = CustomCallback(
        save_path=save_path,
        test_calculators=calculators[1:],
        verbose=1,
        chat_session=inter,
        llm_every_n_steps=llm_every_n_steps,
        drop_rl_n=drop_rl_n
    )
    model = MaskablePPO(
        "MlpPolicy",
        env,
        policy_kwargs=dict(
            features_extractor_class=LSTMSharedNet,
            features_extractor_kwargs=dict(
                n_layers=lstm_layers,
                d_model=d_model,
                dropout=dropout,
                device=device_obj,
            ),
        ),
        n_steps=ppo_n_steps,
        gamma=1.,
        ent_coef=0.01,
        n_epochs=ppo_n_epochs,
        learning_rate=learning_rate,
        batch_size=ppo_batch_size,
        tensorboard_log=tensorboard_log_dir,
        device=device_obj,
        seed=seed,
        verbose=1,
    )
    print("[Main] PPO model ready, starting learn()")
    model.learn(
        total_timesteps=steps,
        callback=checkpoint_callback,
        tb_log_name=name_prefix,
        progress_bar=progress_bar,
    )


def main(
    random_seeds: Union[int, Tuple[int]] = 0,
    qlib_dir: str = "~/.qlib/qlib_data/cn_data",
    qlib_kernels: Optional[int] = None,
    device: str = "cuda:0",
    pool_capacity: int = 50,
    instruments: str = "csi300",
    alphagpt_init: bool = False,
    use_llm: bool = False,
    drop_rl_n: int = 10,
    steps: int = 500_000,
    llm_every_n_steps: int = 25000,
    ppo_n_steps: int = 8192,
    ppo_batch_size: int = 1024,
    ppo_n_epochs: int = 10,
    learning_rate: float = 3e-4,
    lstm_layers: int = 3,
    d_model: int = 256,
    dropout: float = 0.1,
    progress_bar: bool = True,
    print_expr: bool = False,
):
    """
    :param random_seeds: Random seeds
    :param qlib_dir: Qlib data directory
    :param qlib_kernels: Qlib feature-loading worker processes; defaults to 1 on Windows
    :param device: Torch device string
    :param pool_capacity: Maximum size of the alpha pool
    :param instruments: Stock subset name
    :param alphagpt_init: Use an alpha set pre-generated by LLM as the initial pool
    :param use_llm: Enable LLM usage
    :param drop_rl_n: Drop n worst alphas before invoke the LLM
    :param steps: Total iteration steps
    :param llm_every_n_steps: Invoke LLM every n steps
    :param progress_bar: Show SB3 progress bar in terminal
    """
    if isinstance(random_seeds, int):
        random_seeds = (random_seeds, )
    for s in random_seeds:
        run_single_experiment(
            seed=s,
            qlib_dir=qlib_dir,
            qlib_kernels=qlib_kernels,
            device=device,
            instruments=instruments,
            pool_capacity=pool_capacity,
            steps=int(steps),
            alphagpt_init=alphagpt_init,
            drop_rl_n=drop_rl_n,
            use_llm=use_llm,
            llm_every_n_steps=llm_every_n_steps,
            ppo_n_steps=ppo_n_steps,
            ppo_batch_size=ppo_batch_size,
            ppo_n_epochs=ppo_n_epochs,
            learning_rate=learning_rate,
            lstm_layers=lstm_layers,
            d_model=d_model,
            dropout=dropout,
            progress_bar=progress_bar,
            print_expr=print_expr,
        )


if __name__ == '__main__':
    fire.Fire(main)
