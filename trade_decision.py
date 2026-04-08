import argparse
from math import isnan

import pandas as pd
from alphagen.trade.base import StockPosition, StockStatus
from alphagen_qlib.calculator import QLibStockDataCalculator

from alphagen_qlib.strategy import TopKSwapNStrategy
from alphagen_qlib.utils import load_alpha_pool_by_path, load_recent_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate trading decisions from an AlphaGen pool.")
    parser.add_argument("--pool-path", required=True, help="Path to *_pool.json.")
    parser.add_argument("--instrument", default="csi300", help="Instrument universe name, e.g. csi300 or csi500.")
    parser.add_argument("--window-size", type=int, default=365, help="Recent history window size in calendar days.")
    parser.add_argument("--offset", type=int, default=1, help="Offset in calendar days from today.")
    parser.add_argument("--top-k", type=int, default=20, help="Top-K holdings.")
    parser.add_argument("--n-swap", type=int, default=10, help="Number of swaps.")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    data, latest_date = load_recent_data(
        instrument=args.instrument,
        window_size=args.window_size,
        offset=args.offset,
    )
    calculator = QLibStockDataCalculator(data=data, target=None)
    exprs, weights = load_alpha_pool_by_path(args.pool_path)

    ensemble_alpha = calculator.make_ensemble_alpha(exprs, weights)
    df = data.make_dataframe(ensemble_alpha)

    strategy = TopKSwapNStrategy(K=args.top_k,
                                 n_swap=args.n_swap,
                                 signal=df, # placeholder
                                 min_hold_days=1)

    signal = df.xs(latest_date).to_dict()['0']
    status = StockStatus(pd.DataFrame.from_records([
        (k, not isnan(v), not isnan(v), v) for k, v in signal.items()
    ], columns=['code', 'buyable', 'sellable', 'signal']))
    position = pd.DataFrame(columns=StockPosition.dtypes.keys()).astype(
        {col: str(dtype) for col, dtype in StockPosition.dtypes.items()}
    )

    to_buy, to_sell = strategy.step_decision(status_df=status,
                                             position_df=position)

    for i, code in enumerate(to_buy):
        if (i + 1) % 4 == 0:
            print(code)
        else:
            print(code, end=' ')
