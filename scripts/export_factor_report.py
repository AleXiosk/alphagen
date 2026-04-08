from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import torch

from alphagen.data.expression import Feature, FeatureType, Operators, Ref
from alphagen.data.parser import ExpressionParser
from alphagen.utils.correlation import batch_pearsonr, batch_spearmanr
from alphagen_qlib.calculator import QLibStockDataCalculator
from alphagen_qlib.stock_data import StockData, initialize_qlib


SEGMENTS: List[Tuple[str, str, str]] = [
    ("train", "2012-01-01", "2021-12-31"),
    ("oos_2022h1", "2022-01-01", "2022-06-30"),
    ("oos_2022h2", "2022-07-01", "2022-12-31"),
    ("oos_2023h1", "2023-01-01", "2023-06-30"),
]

FEATURE_CN = {
    "open": "开盘价",
    "close": "收盘价",
    "high": "最高价",
    "low": "最低价",
    "volume": "成交量",
    "vwap": "成交均价",
}

FEATURE_RE = re.compile(r"\$(open|close|high|low|volume|vwap)")
WINDOW_RE = re.compile(r"(\d+)d")
OP_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\(")

OP_FAMILY_MAP = {
    "Delta": "变化率",
    "Ref": "滞后",
    "Std": "波动率",
    "Var": "波动率",
    "Mad": "离散度",
    "EMA": "平滑趋势",
    "WMA": "平滑趋势",
    "Mean": "均值平滑",
    "Sum": "累积强度",
    "Med": "稳健中枢",
    "Corr": "相关性",
    "Log": "尺度压缩",
    "Abs": "绝对偏离",
    "Div": "比值归一",
    "Mul": "交互放大",
    "Greater": "上界裁剪",
    "Less": "下界裁剪",
    "Min": "极值下沿",
    "Max": "极值上沿",
    "Sub": "差值偏离",
    "Add": "线性叠加",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export latest AlphaGen factor report to CSV.")
    parser.add_argument("--results-root", default="./out/results", help="Directory that contains AlphaGen run folders.")
    parser.add_argument("--run-dir", default=None, help="Specific run directory. Defaults to the latest run.")
    parser.add_argument("--pool-json", default=None, help="Specific *_pool.json file. Defaults to the latest in the run dir.")
    parser.add_argument("--output-csv", default=None, help="Output CSV path. Defaults next to the pool json.")
    parser.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data", help="Qlib data directory.")
    parser.add_argument("--qlib-kernels", type=int, default=1, help="Qlib worker count. Use 1 on Windows for stability.")
    parser.add_argument("--device", default="cuda:0", help="Torch device used for factor evaluation.")
    parser.add_argument("--instruments", default="csi300", help="Instrument universe name.")
    return parser.parse_args()


def resolve_run_dir(results_root: Path, run_dir: str | None) -> Path:
    if run_dir is not None:
        path = Path(run_dir).expanduser().resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"Run directory does not exist: {path}")
        return path

    candidates = [p for p in results_root.iterdir() if p.is_dir()]
    if not candidates:
        raise FileNotFoundError(f"No run directories found under {results_root}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _pool_sort_key(path: Path) -> Tuple[int, float]:
    match = re.match(r"(\d+)_steps_pool\.json$", path.name)
    step = int(match.group(1)) if match else -1
    return step, path.stat().st_mtime


def resolve_pool_json(run_dir: Path, pool_json: str | None) -> Path:
    if pool_json is not None:
        path = Path(pool_json).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Pool json does not exist: {path}")
        return path

    candidates = sorted(run_dir.glob("*_steps_pool.json"), key=_pool_sort_key)
    if not candidates:
        raise FileNotFoundError(f"No *_steps_pool.json files found under {run_dir}")
    return candidates[-1]


def build_target_expr():
    close = Feature(FeatureType.CLOSE)
    return Ref(close, -20) / close - 1


def load_pool(path: Path) -> Tuple[List[str], List[float]]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    exprs = payload.get("exprs")
    weights = payload.get("weights")
    if not isinstance(exprs, list) or not isinstance(weights, list):
        raise ValueError(f"Unexpected pool format in {path}")
    if len(exprs) != len(weights):
        raise ValueError(f"Expr/weight length mismatch in {path}")
    return exprs, [float(w) for w in weights]


def summarize_batch(batch: torch.Tensor) -> Dict[str, float]:
    values = batch.detach().float().cpu().flatten()
    mask = torch.isfinite(values)
    values = values[mask]
    if values.numel() == 0:
        return {"mean": math.nan, "std": math.nan, "ir": math.nan, "pos_ratio": math.nan, "count": 0.0}

    mean = float(values.mean().item())
    std = float(values.std(unbiased=False).item())
    ir = math.nan if std < 1e-12 else mean / std
    pos_ratio = float((values > 0).float().mean().item())
    return {
        "mean": mean,
        "std": std,
        "ir": ir,
        "pos_ratio": pos_ratio,
        "count": float(values.numel()),
    }


def extract_features(expr_text: str) -> List[str]:
    seen: List[str] = []
    for feature in FEATURE_RE.findall(expr_text):
        if feature not in seen:
            seen.append(feature)
    return seen


def extract_windows(expr_text: str) -> List[int]:
    windows = sorted({int(x) for x in WINDOW_RE.findall(expr_text)})
    return windows


def extract_ops(expr_text: str) -> List[str]:
    ops: List[str] = []
    for op in OP_RE.findall(expr_text):
        if op == "Constant":
            continue
        if op not in ops:
            ops.append(op)
    return ops


def classify_themes(features: Sequence[str], ops: Sequence[str]) -> List[str]:
    themes: List[str] = []
    price_features = {"open", "close", "high", "low"}
    has_price = any(f in price_features for f in features)
    has_volume = "volume" in features
    has_vwap = "vwap" in features
    has_volatility = any(op in ops for op in ("Std", "Var", "Mad"))
    has_trend = any(op in ops for op in ("Delta", "Ref", "EMA", "WMA", "Mean", "Sum"))
    has_corr = "Corr" in ops

    if has_price and (has_volume or has_vwap):
        themes.append("量价关系")
    if has_vwap:
        themes.append("成交重心偏离")
    if has_trend and has_price:
        themes.append("动量/反转")
    if has_volatility:
        themes.append("波动率/离散度")
    if has_corr:
        themes.append("相关性结构")
    if "high" in features and "low" in features:
        themes.append("振幅结构")
    if not themes:
        themes.append("价格相对强弱")
    return themes


def horizon_desc(max_window: int) -> str:
    if max_window <= 1:
        return "当日横截面"
    if max_window <= 5:
        return "短期"
    if max_window <= 20:
        return "短中期"
    if max_window <= 40:
        return "中期"
    return "中长期"


def story_desc(themes: Sequence[str]) -> str:
    if "量价关系" in themes and "相关性结构" in themes:
        return "成交变化与价格位置共振或背离带来的横截面定价偏差"
    if "成交重心偏离" in themes:
        return "价格相对成交重心偏离后的回归或延续"
    if "波动率/离散度" in themes:
        return "波动扩张或压缩后的风险补偿与均值回归"
    if "动量/反转" in themes:
        return "过去走势延续或超调后的回归"
    if "振幅结构" in themes:
        return "高低点分布和振幅变化对应的情绪与风险偏好"
    return "价格与流动性联合变化中的相对强弱"


def build_explanation(expr_text: str, weight: float) -> Tuple[str, str, str, str]:
    features = extract_features(expr_text)
    windows = extract_windows(expr_text)
    ops = extract_ops(expr_text)
    themes = classify_themes(features, ops)
    feature_desc = "、".join(FEATURE_CN[f] for f in features) if features else "价格派生量"
    family_desc = "、".join(dict.fromkeys(OP_FAMILY_MAP[op] for op in ops if op in OP_FAMILY_MAP)) or "非线性组合"
    window_desc = horizon_desc(max(windows) if windows else 1)
    story = story_desc(themes)
    direction = "正向使用" if weight >= 0 else "反向使用"
    explanation = (
        f"该因子主要刻画{'/'.join(themes)}，核心输入是{feature_desc}，"
        f"以{window_desc}窗口为主，通过{family_desc}构造非线性信号，"
        f"尝试捕捉{story}。当前在组合中以{direction}方式参与。"
    )
    return (
        "|".join(features),
        "|".join(str(w) for w in windows) if windows else "",
        "|".join(themes),
        explanation,
    )


def make_calculators(
    qlib_dir: str,
    kernels: int,
    device: torch.device,
    instruments: str,
) -> List[Tuple[str, QLibStockDataCalculator]]:
    initialize_qlib(os.path.expanduser(qlib_dir), kernels=kernels)
    target = build_target_expr()
    calculators: List[Tuple[str, QLibStockDataCalculator]] = []
    for name, start, end in SEGMENTS:
        data = StockData(instrument=instruments, start_time=start, end_time=end, device=device)
        calculators.append((name, QLibStockDataCalculator(data, target)))
    return calculators


def calc_expr_metrics(expr, calculator: QLibStockDataCalculator) -> Dict[str, object]:
    with torch.no_grad():
        alpha = calculator.evaluate_alpha(expr)
        target = calculator.target
        ic_daily = batch_pearsonr(alpha, target)
        ric_daily = batch_spearmanr(alpha, target)
    ic_stats = summarize_batch(ic_daily)
    ric_stats = summarize_batch(ric_daily)
    return {
        "ic_daily": ic_daily.detach().cpu(),
        "ric_daily": ric_daily.detach().cpu(),
        "ic_mean": ic_stats["mean"],
        "ic_std": ic_stats["std"],
        "ic_ir": ic_stats["ir"],
        "ic_pos_ratio": ic_stats["pos_ratio"],
        "rankic_mean": ric_stats["mean"],
        "rankic_std": ric_stats["std"],
        "rankic_ir": ric_stats["ir"],
        "rankic_pos_ratio": ric_stats["pos_ratio"],
    }


def concat_metric_batches(metric_blocks: Iterable[torch.Tensor]) -> Dict[str, float]:
    tensors = [block for block in metric_blocks if block.numel() > 0]
    if not tensors:
        return {"mean": math.nan, "std": math.nan, "ir": math.nan, "pos_ratio": math.nan}
    return summarize_batch(torch.cat(tensors))


def build_rows(
    expr_texts: Sequence[str],
    weights: Sequence[float],
    calculators: Sequence[Tuple[str, QLibStockDataCalculator]],
) -> List[Dict[str, object]]:
    parser = ExpressionParser(Operators)
    exprs = [parser.parse(expr_text) for expr_text in expr_texts]

    rows: List[Dict[str, object]] = []
    abs_weight_order = sorted(
        range(len(weights)),
        key=lambda idx: abs(weights[idx]),
        reverse=True,
    )
    abs_weight_rank = {idx: rank + 1 for rank, idx in enumerate(abs_weight_order)}

    for idx, (expr_text, expr, weight) in enumerate(zip(expr_texts, exprs, weights), start=1):
        row: Dict[str, object] = {
            "factor_id": idx,
            "abs_weight_rank": abs_weight_rank[idx - 1],
            "weight": weight,
            "abs_weight": abs(weight),
            "ensemble_direction": "long" if weight >= 0 else "short",
            "expr": expr_text,
            "expr_length": len(expr_text),
        }

        features, windows, themes, explanation = build_explanation(expr_text, weight)
        row["used_features"] = features
        row["lookback_windows"] = windows
        row["max_lookback_days"] = max((int(x) for x in windows.split("|") if x), default=1)
        row["theme_tags"] = themes
        row["financial_explanation"] = explanation

        segment_metrics: Dict[str, Dict[str, object]] = {}
        for segment_name, calculator in calculators:
            metrics = calc_expr_metrics(expr, calculator)
            segment_metrics[segment_name] = metrics
            row[f"{segment_name}_ic_mean"] = metrics["ic_mean"]
            row[f"{segment_name}_ic_ir"] = metrics["ic_ir"]
            row[f"{segment_name}_rankic_mean"] = metrics["rankic_mean"]
            row[f"{segment_name}_rankic_ir"] = metrics["rankic_ir"]
            row[f"{segment_name}_ic_pos_ratio"] = metrics["ic_pos_ratio"]
            row[f"{segment_name}_rankic_pos_ratio"] = metrics["rankic_pos_ratio"]

        oos_names = [name for name, _, _ in SEGMENTS[1:]]
        oos_ic = concat_metric_batches(segment_metrics[name]["ic_daily"] for name in oos_names)
        oos_ric = concat_metric_batches(segment_metrics[name]["ric_daily"] for name in oos_names)
        row["oos_ic_mean"] = oos_ic["mean"]
        row["oos_ic_ir"] = oos_ic["ir"]
        row["oos_rankic_mean"] = oos_ric["mean"]
        row["oos_rankic_ir"] = oos_ric["ir"]
        row["oos_ic_pos_ratio"] = oos_ic["pos_ratio"]
        row["oos_rankic_pos_ratio"] = oos_ric["pos_ratio"]
        row["oos_ic_signed_by_weight"] = math.copysign(1.0, weight) * oos_ic["mean"] if not math.isnan(oos_ic["mean"]) else math.nan
        row["oos_rankic_signed_by_weight"] = math.copysign(1.0, weight) * oos_ric["mean"] if not math.isnan(oos_ric["mean"]) else math.nan
        row["train_oos_ic_gap"] = (
            row["oos_ic_mean"] - row["train_ic_mean"]
            if not math.isnan(row["oos_ic_mean"]) and not math.isnan(row["train_ic_mean"])
            else math.nan
        )
        row["train_oos_rankic_gap"] = (
            row["oos_rankic_mean"] - row["train_rankic_mean"]
            if not math.isnan(row["oos_rankic_mean"]) and not math.isnan(row["train_rankic_mean"])
            else math.nan
        )
        rows.append(row)
    return rows


def write_csv(rows: Sequence[Dict[str, object]], output_csv: Path) -> None:
    if not rows:
        raise ValueError("No rows to export.")
    fieldnames = list(rows[0].keys())
    with output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    results_root = Path(args.results_root).expanduser().resolve()
    run_dir = resolve_run_dir(results_root, args.run_dir)
    pool_json = resolve_pool_json(run_dir, args.pool_json)
    output_csv = (
        Path(args.output_csv).expanduser().resolve()
        if args.output_csv is not None
        else pool_json.with_name(f"{pool_json.stem}_factor_report.csv")
    )

    expr_texts, weights = load_pool(pool_json)
    device = torch.device(args.device)
    calculators = make_calculators(args.qlib_dir, args.qlib_kernels, device, args.instruments)
    rows = build_rows(expr_texts, weights, calculators)
    write_csv(rows, output_csv)

    print(f"run_dir={run_dir}")
    print(f"pool_json={pool_json}")
    print(f"output_csv={output_csv}")
    print(f"factor_count={len(rows)}")


if __name__ == "__main__":
    main()
