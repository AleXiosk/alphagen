import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from alphagen.data.expression import *
from alphagen.models.linear_alpha_pool import MseAlphaPool
from alphagen.utils.random import reseed_everything
from alphagen_generic.features import *
from alphagen_generic.operators import funcs as generic_funcs
from alphagen_qlib.calculator import QLibStockDataCalculator
from alphagen_qlib.stock_data import StockData, initialize_qlib
from gplearn.fitness import make_fitness
from gplearn.functions import make_function
from gplearn.genetic import SymbolicRegressor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GP baseline for AlphaGen on a selected universe.")
    parser.add_argument("--instruments", default="csi300", help="Instrument universe name, e.g. csi300 or csi500.")
    parser.add_argument("--seed", type=int, default=2, help="Random seed.")
    parser.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data", help="Qlib data directory.")
    parser.add_argument("--device", default="cuda:0", help="Torch device.")
    parser.add_argument("--out-root", default="./out/gp", help="Output root directory.")
    parser.add_argument("--pool-capacity", type=int, default=20, help="Alpha pool capacity.")
    parser.add_argument("--mutual-ic-thres", type=float, default=0.7, help="Mutual IC filter threshold for pool export.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    funcs = [make_function(**func._asdict()) for func in generic_funcs]

    reseed_everything(args.seed)
    initialize_qlib(os.path.expanduser(args.qlib_dir))

    cache: dict[str, float] = {}
    generation = 0
    device = torch.device(args.device)
    output_dir = Path(args.out_root).expanduser().resolve() / args.instruments / str(args.seed)

    data_train = StockData(args.instruments, "2012-01-01", "2021-12-31", device=device)
    data_test = StockData(args.instruments, "2022-01-01", "2023-06-30", device=device)
    calculator_train = QLibStockDataCalculator(data_train, target)
    calculator_test = QLibStockDataCalculator(data_test, target)

    pool = MseAlphaPool(
        capacity=args.pool_capacity,
        calculator=calculator_train,
        ic_lower_bound=None,
        l1_alpha=5e-3,
        device=device,
    )

    def metric_fn(x, y, w):
        del x, w
        key = y[0]
        if key in cache:
            return cache[key]
        token_len = key.count("(") + key.count(")")
        if token_len > 20:
            return -1.0

        expr = eval(key)
        try:
            ic = calculator_train.calc_single_IC_ret(expr)
        except OutOfDataRangeError:
            ic = -1.0
        if np.isnan(ic):
            ic = -1.0
        cache[key] = ic
        return ic

    metric = make_fitness(function=metric_fn, greater_is_better=True)

    def try_pool(capacity: int, mutual_ic_thres: Optional[float] = None):
        eval_pool = MseAlphaPool(
            capacity=capacity,
            calculator=calculator_train,
            ic_lower_bound=None,
        )
        exprs = []

        def acceptable(expr: str) -> bool:
            if mutual_ic_thres is None:
                return True
            return all(
                abs(eval_pool.calculator.calc_mutual_IC(existing, eval(expr))) <= mutual_ic_thres
                for existing in exprs
            )

        most_common = dict(Counter(cache).most_common(capacity if mutual_ic_thres is None else None))
        for key in most_common:
            if acceptable(key):
                exprs.append(eval(key))
                if len(exprs) >= capacity:
                    break
        eval_pool.force_load_exprs(exprs)

        ic_train, ric_train = eval_pool.test_ensemble(calculator_train)
        ic_test, ric_test = eval_pool.test_ensemble(calculator_test)
        return {
            "ic_train": ic_train,
            "ric_train": ric_train,
            "ic_test": ic_test,
            "ric_test": ric_test,
            "pool_state": eval_pool.to_json_dict(),
        }

    def on_generation() -> None:
        nonlocal generation
        generation += 1
        output_dir.mkdir(parents=True, exist_ok=True)
        if generation % 4 != 0:
            return
        res = {
            "instrument": args.instruments,
            "pool": args.pool_capacity,
            "res": try_pool(args.pool_capacity, mutual_ic_thres=args.mutual_ic_thres),
        }
        with (output_dir / f"{generation}.json").open("w", encoding="utf-8") as handle:
            json.dump({"res": res, "cache": cache}, handle, indent=4)

    features = ["open_", "close", "high", "low", "volume", "vwap"]
    constants = [
        f"Constant({v})"
        for v in [-30.0, -10.0, -5.0, -2.0, -1.0, -0.5, -0.01, 0.01, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
    ]
    terminals = features + constants

    est_gp = SymbolicRegressor(
        population_size=1000,
        generations=40,
        init_depth=(2, 6),
        tournament_size=600,
        stopping_criteria=1.0,
        p_crossover=0.3,
        p_subtree_mutation=0.1,
        p_hoist_mutation=0.01,
        p_point_mutation=0.1,
        p_point_replace=0.6,
        max_samples=0.9,
        verbose=1,
        parsimony_coefficient=0.0,
        random_state=args.seed,
        function_set=funcs,
        metric=metric,  # type: ignore[arg-type]
        const_range=None,
        n_jobs=1,
    )
    est_gp.fit(np.array([terminals]), np.array([[1]]), callback=on_generation)
    print(est_gp._program.execute(np.array([terminals])))


if __name__ == "__main__":
    main()
