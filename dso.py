import argparse
import json
import os
from pathlib import Path

import numpy as np
import torch

from alphagen.data.expression import *
from alphagen.models.linear_alpha_pool import MseAlphaPool
from alphagen.utils import reseed_everything
from alphagen_generic.features import *
from alphagen_generic.operators import funcs as generic_funcs
from alphagen_qlib.calculator import QLibStockDataCalculator
from alphagen_qlib.stock_data import StockData, initialize_qlib
from dso import DeepSymbolicRegressor
from dso import functions
from dso.library import HardCodedConstant, Token


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DSO baseline for AlphaGen on a selected universe.")
    parser.add_argument("seed", nargs="?", type=int, default=0, help="Random seed.")
    parser.add_argument("--instruments", default="csi300", help="Instrument universe name, e.g. csi300 or csi500.")
    parser.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data", help="Qlib data directory.")
    parser.add_argument("--device", default="cuda:0", help="Torch device.")
    parser.add_argument("--out-root", default="./out/dso", help="Output root directory.")
    parser.add_argument("--pool-capacity", type=int, default=10, help="Alpha pool capacity.")
    parser.add_argument("--n-samples", type=int, default=20000, help="DSO training sample count.")
    parser.add_argument("--batch-size", type=int, default=128, help="DSO batch size.")
    parser.add_argument("--epsilon", type=float, default=0.05, help="DSO epsilon.")
    return parser.parse_args()


def build_function_map() -> dict[str, Token]:
    func_map = {func.name: Token(complexity=1, **func._asdict()) for func in generic_funcs}
    for i, feature in enumerate(["open", "close", "high", "low", "volume", "vwap"]):
        func_map[f"x{i + 1}"] = Token(name=feature, arity=0, complexity=1, function=None, input_var=i)
    for value in [-30.0, -10.0, -5.0, -2.0, -1.0, -0.5, -0.01, 0.01, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]:
        func_map[f"Constant({value})"] = HardCodedConstant(name=f"Constant({value})", value=value)
    return func_map


def main() -> None:
    args = parse_args()
    reseed_everything(args.seed)
    initialize_qlib(os.path.expanduser(args.qlib_dir))

    device = torch.device(args.device)
    output_dir = Path(args.out_root).expanduser().resolve() / args.instruments / str(args.seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    data_train = StockData(args.instruments, "2009-01-01", "2018-12-31", device=device)
    data_valid = StockData(args.instruments, "2019-01-01", "2019-12-31", device=device)
    data_test = StockData(args.instruments, "2020-01-01", "2021-12-31", device=device)
    calculator_train = QLibStockDataCalculator(data_train, target)
    calculator_valid = QLibStockDataCalculator(data_valid, target)
    calculator_test = QLibStockDataCalculator(data_test, target)

    functions.function_map = build_function_map()
    pool = MseAlphaPool(
        capacity=args.pool_capacity,
        calculator=calculator_train,
        ic_lower_bound=None,
    )

    class Evaluator:
        def __init__(self, pool_: MseAlphaPool):
            self.cnt = 0
            self.pool = pool_
            self.results: dict[int, float] = {}

        def alpha_ev_fn(self, key: str) -> float:
            expr = eval(key)
            try:
                ret = self.pool.try_new_expr(expr)
            except OutOfDataRangeError:
                ret = -1.0
            self.cnt += 1
            if self.cnt % 100 == 0:
                test_ic = self.pool.test_ensemble(calculator_test)[0]
                self.results[self.cnt] = test_ic
                print(self.cnt, test_ic)
            return ret

    evaluator = Evaluator(pool)
    config = {
        "task": {
            "task_type": "regression",
            "function_set": list(functions.function_map.keys()),
            "metric": "alphagen",
            "metric_params": [lambda key: evaluator.alpha_ev_fn(key)],
        },
        "training": {
            "n_samples": args.n_samples,
            "batch_size": args.batch_size,
            "epsilon": args.epsilon,
        },
        "prior": {"length": {"min_": 2, "max_": 20, "on": True}},
    }

    model = DeepSymbolicRegressor(config=config)
    model.fit(np.array([["open_", "close", "high", "low", "volume", "vwap"]]), np.array([[1]]))

    payload = {
        "instrument": args.instruments,
        "seed": args.seed,
        "valid_ic": pool.test_ensemble(calculator_valid)[0],
        "test_ic": pool.test_ensemble(calculator_test)[0],
        "pool_state": pool.to_json_dict(),
        "progress": evaluator.results,
    }
    with (output_dir / "result.json").open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(evaluator.results)


if __name__ == "__main__":
    main()
