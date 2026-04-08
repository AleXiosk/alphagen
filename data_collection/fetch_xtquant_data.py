import argparse
import json
import os
import sys
import time
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent
for _path in (str(_THIS_DIR), str(_REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import baostock as bs
import numpy as np
import pandas as pd
from baostock.data.resultset import ResultData
from xtquant import xtdata
from qlib_dump_bin import DumpDataAll

from alphagen_qlib.universe import default_xtquant_out_root, get_universe_spec, resolve_universe_name


DEFAULT_UNIVERSE_NAME = "csi300"
DEFAULT_SECTOR_NAME = "\u6caa\u6df1300"
DEFAULT_START_DATE = "2011-01-01"
DEFAULT_PERIOD = "1d"
DEFAULT_DIVIDEND_TYPE = "none"
DEFAULT_CONSTITUENT_SOURCE = "baostock"
DEFAULT_QLIB_DIR = "~/.qlib/qlib_data/cn_data"
SCRIPT_VERSION = "0.4.0"
CSV_COLUMNS = [
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "vwap",
    "factor",
    "code",
]
MARKET_FIELDS = ["open", "high", "low", "close", "volume", "amount"]
BAOSTOCK_QUERY_BY_SECTOR_NAME: Dict[str, Callable[[str], ResultData]] = {
    "\u6caa\u6df1300": bs.query_hs300_stocks,
    "\u4e0a\u8bc150": bs.query_sz50_stocks,
    "\u4e2d\u8bc1500": bs.query_zz500_stocks,
}


@dataclass(frozen=True)
class Paths:
    out_root: Path
    stocks_dir: Path
    meta_dir: Path
    calendar_path: Path
    instruments_path: Path
    symbols_path: Path
    manifest_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch index constituents from baostock and market data from xtquant."
    )
    parser.add_argument(
        "--sector-name",
        default=None,
        help="Index sector name. Defaults inferred from --universe-name when possible.",
    )
    parser.add_argument(
        "--universe-name",
        default=None,
        help="Qlib instrument universe name, e.g. csi300 or csi500.",
    )
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=date.today().strftime("%Y-%m-%d"))
    parser.add_argument("--period", default=DEFAULT_PERIOD)
    parser.add_argument("--dividend-type", default=DEFAULT_DIVIDEND_TYPE)
    parser.add_argument("--constituent-source", choices=["baostock", "xtquant"], default=DEFAULT_CONSTITUENT_SOURCE)
    parser.add_argument(
        "--out-root",
        default=None,
        help="Output root. Defaults to ./data/xtquant_<universe-name>.",
    )
    parser.add_argument("--mode", choices=["auto", "full", "incremental"], default="auto")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--baostock-retries", type=int, default=5)
    parser.add_argument("--baostock-retry-wait", type=float, default=3.0)
    parser.add_argument("--dump-qlib", action="store_true")
    parser.add_argument("--qlib-dir", default=DEFAULT_QLIB_DIR)
    parser.add_argument("--qlib-max-workers", type=int, default=32)
    return parser.parse_args()


def resolve_sector_and_universe(
    sector_name: str | None,
    universe_name: str | None,
) -> Tuple[str, str]:
    resolved_universe = resolve_universe_name(universe_name, sector_name, default=DEFAULT_UNIVERSE_NAME)
    spec = get_universe_spec(resolved_universe)
    resolved_sector = sector_name if sector_name is not None else (spec.sector_name if spec is not None else DEFAULT_SECTOR_NAME)
    return resolved_sector, resolved_universe


def resolve_paths(out_root: str | None, universe_name: str) -> Paths:
    root = Path(out_root).expanduser().resolve() if out_root is not None else default_xtquant_out_root(universe_name).resolve()
    return Paths(
        out_root=root,
        stocks_dir=root / "stocks",
        meta_dir=root / "meta",
        calendar_path=root / "meta" / "calendar_day.txt",
        instruments_path=root / "meta" / f"instruments_{universe_name}.csv",
        symbols_path=root / "meta" / "symbols.txt",
        manifest_path=root / "meta" / "manifest.json",
    )


def resolve_qlib_dir(qlib_dir: str) -> Path:
    return Path(qlib_dir).expanduser().resolve()


def normalize_date_text(value: str) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def compact_date_text(value: str) -> str:
    return pd.Timestamp(value).strftime("%Y%m%d")


def baostock_date_text(value: str) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def ensure_supported_config(period: str, dividend_type: str) -> None:
    if period != DEFAULT_PERIOD:
        raise ValueError(f"Only period='{DEFAULT_PERIOD}' is supported.")
    if dividend_type != DEFAULT_DIVIDEND_TYPE:
        raise ValueError(f"Only dividend_type='{DEFAULT_DIVIDEND_TYPE}' is supported.")


def determine_mode(requested_mode: str, paths: Paths) -> str:
    if requested_mode != "auto":
        return requested_mode
    if paths.stocks_dir.exists() and any(paths.stocks_dir.glob("*.csv")):
        return "incremental"
    return "full"


def ensure_dirs(paths: Paths) -> None:
    paths.stocks_dir.mkdir(parents=True, exist_ok=True)
    paths.meta_dir.mkdir(parents=True, exist_ok=True)


def xt_code_to_qlib_code(stock_code: str) -> str:
    symbol, market = stock_code.split(".")
    return f"{market.upper()}{symbol}"


def qlib_code_to_xt_code(stock_code: str) -> str:
    return f"{stock_code[2:]}.{stock_code[:2]}"


def baostock_code_to_qlib_code(stock_code: str) -> str:
    market, symbol = stock_code.split(".")
    return f"{market.upper()}{symbol}"


def timetag_to_datestr(timetag: object) -> str:
    if isinstance(timetag, str):
        stripped = timetag.strip()
        if not stripped:
            raise ValueError("Empty timetag is not supported.")
        if stripped.isdigit() and len(stripped) == 8:
            return datetime.strptime(stripped, "%Y%m%d").strftime("%Y-%m-%d")
        return pd.Timestamp(stripped).strftime("%Y-%m-%d")
    if isinstance(timetag, (int, np.integer)):
        return pd.to_datetime(int(timetag), unit="ms").strftime("%Y-%m-%d")
    if isinstance(timetag, (float, np.floating)):
        return pd.to_datetime(int(timetag), unit="ms").strftime("%Y-%m-%d")
    if isinstance(timetag, pd.Timestamp):
        return timetag.strftime("%Y-%m-%d")
    raise TypeError(f"Unsupported timetag type: {type(timetag)!r}")


def get_trading_calendar(start_date: str, end_date: str) -> List[str]:
    raw_dates = xtdata.get_trading_calendar(
        "SH",
        start_time=compact_date_text(start_date),
        end_time=compact_date_text(end_date),
    )
    calendar = [timetag_to_datestr(item) for item in raw_dates]
    if not calendar:
        raise RuntimeError("xtdata.get_trading_calendar returned an empty trading calendar.")
    return calendar


def validate_constituent_source(sector_name: str, constituent_source: str) -> None:
    if constituent_source == "baostock":
        if sector_name not in BAOSTOCK_QUERY_BY_SECTOR_NAME:
            supported = ", ".join(sorted(BAOSTOCK_QUERY_BY_SECTOR_NAME))
            raise RuntimeError(
                "baostock constituent source only supports: "
                f"{supported}. Received: {sector_name!r}."
            )
        return

    print(f"Downloading xtquant sector metadata for '{sector_name}'...")
    xtdata.download_sector_data()
    sectors = xtdata.get_sector_list()
    if sector_name not in sectors:
        raise RuntimeError(f"Sector '{sector_name}' is not available from xtquant.")


def read_existing_calendar(path: Path) -> List[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_existing_intervals(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    frame = pd.read_csv(path, dtype=str)
    expected = {"code", "start_datetime", "end_datetime"}
    if set(frame.columns) != expected:
        raise RuntimeError(f"Unexpected columns in existing instruments file: {frame.columns.tolist()}")
    return frame


def initial_anchor_date(mode: str, existing_calendar: Sequence[str]) -> Optional[str]:
    if mode != "incremental" or not existing_calendar:
        return None
    return existing_calendar[-1]


def merge_incremental_intervals(
    old_intervals: Optional[pd.DataFrame],
    new_intervals: pd.DataFrame,
    anchor_date: Optional[str],
) -> pd.DataFrame:
    if old_intervals is None or old_intervals.empty or anchor_date is None:
        return new_intervals

    keep_old = old_intervals[old_intervals["end_datetime"] < anchor_date].copy()
    merged = pd.concat([keep_old, new_intervals], ignore_index=True)
    merged.sort_values(["code", "start_datetime", "end_datetime"], inplace=True)
    merged.reset_index(drop=True, inplace=True)
    return merged


def read_last_csv_date(csv_path: Path) -> Optional[str]:
    if not csv_path.exists():
        return None
    with csv_path.open("rb") as handle:
        handle.seek(0, 2)
        position = handle.tell()
        buffer = bytearray()
        while position > 0:
            position -= 1
            handle.seek(position)
            char = handle.read(1)
            if char == b"\n" and buffer:
                break
            if char != b"\n":
                buffer.extend(char)
        last_line = bytes(reversed(buffer)).decode("utf-8").strip()
    if not last_line:
        return None
    first_field = last_line.split(",", 1)[0]
    if first_field == "date":
        return None
    return normalize_date_text(first_field)


def next_trading_date(trading_dates: Sequence[str], current_date: str) -> Optional[str]:
    for trade_date in trading_dates:
        if trade_date > current_date:
            return trade_date
    return None


def plan_stock_fetches(
    qlib_codes: Iterable[str],
    paths: Paths,
    trading_dates: Sequence[str],
    global_start_date: str,
    mode: str,
) -> Dict[str, str]:
    fetch_plan: Dict[str, str] = {}
    for qlib_code in sorted(set(qlib_codes)):
        csv_path = paths.stocks_dir / f"{qlib_code}.csv"
        if mode == "full" or not csv_path.exists():
            fetch_plan[qlib_code] = global_start_date
            continue
        last_date = read_last_csv_date(csv_path)
        if last_date is None:
            fetch_plan[qlib_code] = global_start_date
            continue
        start_date = next_trading_date(trading_dates, last_date)
        if start_date is not None:
            fetch_plan[qlib_code] = start_date
    return fetch_plan


def chunked(items: Sequence[str], size: int) -> Iterable[List[str]]:
    for index in range(0, len(items), size):
        yield list(items[index:index + size])


def group_fetch_plan(fetch_plan: Dict[str, str]) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = {}
    for qlib_code, start_date in fetch_plan.items():
        grouped.setdefault(start_date, []).append(qlib_code)
    return grouped


def prepare_factor_series(stock_code: str, start_date: str, end_date: str) -> pd.Series:
    raw = xtdata.get_divid_factors(stock_code, compact_date_text(start_date), compact_date_text(end_date))
    if raw is None or raw.empty:
        return pd.Series(dtype=float)

    frame = raw.copy()
    frame.index = [timetag_to_datestr(idx) for idx in frame.index]
    if "dr" not in frame.columns:
        raise RuntimeError(f"xtdata.get_divid_factors returned no 'dr' column for {stock_code}.")

    series = pd.to_numeric(frame["dr"], errors="coerce")
    series.index = pd.Index(frame.index, name="date")
    series = series[~series.index.duplicated(keep="last")].sort_index()
    return series


def build_output_frame(
    xt_code: str,
    qlib_code: str,
    market_data: pd.DataFrame,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    if market_data.empty:
        raise RuntimeError(f"xtdata.get_market_data_ex returned empty data for {xt_code}.")

    frame = market_data.copy()
    frame.index = pd.Index([timetag_to_datestr(idx) for idx in frame.index], name="date")
    missing = [field for field in MARKET_FIELDS if field not in frame.columns]
    if missing:
        raise RuntimeError(f"{xt_code} missing required fields from xtdata: {missing}")

    frame = frame.loc[:, MARKET_FIELDS].copy()
    for field in MARKET_FIELDS:
        frame[field] = pd.to_numeric(frame[field], errors="coerce")

    frame = frame[(frame.index >= start_date) & (frame.index <= end_date)]
    frame = frame[~frame.index.duplicated(keep="last")]
    frame.sort_index(inplace=True)
    if frame.empty:
        raise RuntimeError(f"{xt_code} has no rows within [{start_date}, {end_date}].")

    factor_series = prepare_factor_series(xt_code, start_date, end_date)
    frame["factor"] = factor_series.reindex(frame.index).ffill().fillna(1.0)
    volume = frame["volume"].replace(0, np.nan)
    frame["vwap"] = frame["amount"] / volume
    frame["code"] = qlib_code
    frame = frame.reset_index()
    return frame.loc[:, CSV_COLUMNS]


def merge_with_existing_csv(csv_path: Path, new_frame: pd.DataFrame) -> pd.DataFrame:
    if not csv_path.exists():
        return new_frame
    old_frame = pd.read_csv(csv_path, dtype={"code": str})
    combined = pd.concat([old_frame, new_frame], ignore_index=True)
    combined.drop_duplicates(subset=["date"], keep="last", inplace=True)
    combined.sort_values("date", inplace=True)
    combined.reset_index(drop=True, inplace=True)
    return combined.loc[:, CSV_COLUMNS]


def download_history_batches(grouped_plan: Dict[str, List[str]], end_date: str) -> None:
    for start_date, qlib_codes in sorted(grouped_plan.items()):
        xt_codes = [qlib_code_to_xt_code(code) for code in qlib_codes]
        print(f"Downloading local xtquant history for {len(xt_codes)} stocks: {start_date} -> {end_date}")
        xtdata.download_history_data2(
            xt_codes,
            DEFAULT_PERIOD,
            compact_date_text(start_date),
            compact_date_text(end_date),
        )


def fetch_market_batches(
    grouped_plan: Dict[str, List[str]],
    end_date: str,
    batch_size: int,
) -> Dict[str, pd.DataFrame]:
    results: Dict[str, pd.DataFrame] = {}
    for start_date, qlib_codes in sorted(grouped_plan.items()):
        xt_codes = [qlib_code_to_xt_code(code) for code in qlib_codes]
        for xt_batch in chunked(xt_codes, batch_size):
            print(f"Reading xtquant market data for {len(xt_batch)} stocks: {start_date} -> {end_date}")
            batch_data = xtdata.get_market_data_ex(
                field_list=MARKET_FIELDS,
                stock_list=xt_batch,
                period=DEFAULT_PERIOD,
                start_time=compact_date_text(start_date),
                end_time=compact_date_text(end_date),
                dividend_type=DEFAULT_DIVIDEND_TYPE,
                fill_data=False,
            )
            results.update(batch_data)
    return results


def write_calendar(path: Path, trading_dates: Sequence[str]) -> None:
    path.write_text("\n".join(trading_dates) + "\n", encoding="utf-8")


def write_intervals(path: Path, intervals: pd.DataFrame) -> None:
    intervals.to_csv(path, index=False)


def write_symbols(path: Path, qlib_codes: Sequence[str]) -> None:
    path.write_text("\n".join(sorted(set(qlib_codes))) + "\n", encoding="utf-8")


def write_manifest(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def dump_qlib_data(csv_dir: Path, qlib_dir: Path, max_workers: int) -> None:
    qlib_dir.mkdir(parents=True, exist_ok=True)
    DumpDataAll(
        csv_path=csv_dir,
        qlib_dir=str(qlib_dir),
        max_workers=max_workers,
        exclude_fields="date,code",
        symbol_field_name="code",
    ).dump()


def write_qlib_instrument_file(
    qlib_dir: Path,
    instrument_name: str,
    intervals: pd.DataFrame,
) -> Path:
    instrument_dir = qlib_dir / "instruments"
    instrument_dir.mkdir(parents=True, exist_ok=True)
    instrument_path = instrument_dir / f"{instrument_name}.txt"
    frame = intervals.loc[:, ["code", "start_datetime", "end_datetime"]].copy()
    frame.sort_values(["code", "start_datetime", "end_datetime"], inplace=True)
    with instrument_path.open("w", encoding="utf-8") as handle:
        for row in frame.itertuples(index=False):
            handle.write(f"{row.code}\t{row.start_datetime}\t{row.end_datetime}\n")
    return instrument_path


@contextmanager
def baostock_login_context() -> Iterable[None]:
    with open(os.devnull, "w") as devnull:
        with redirect_stdout(devnull):
            login_result = bs.login()
    if login_result.error_code != "0":
        raise RuntimeError(
            f"baostock login failed: error_code={login_result.error_code}, "
            f"error_msg={login_result.error_msg}"
        )
    try:
        yield None
    finally:
        with open(os.devnull, "w") as devnull:
            with redirect_stdout(devnull):
                bs.logout()


def baostock_relogin() -> None:
    with open(os.devnull, "w") as devnull:
        with redirect_stdout(devnull):
            bs.logout()
            login_result = bs.login()
    if login_result.error_code != "0":
        raise RuntimeError(
            f"baostock relogin failed: error_code={login_result.error_code}, "
            f"error_msg={login_result.error_msg}"
        )


def get_baostock_constituent_query(sector_name: str) -> Callable[[str], ResultData]:
    try:
        return BAOSTOCK_QUERY_BY_SECTOR_NAME[sector_name]
    except KeyError as exc:
        supported = ", ".join(sorted(BAOSTOCK_QUERY_BY_SECTOR_NAME))
        raise RuntimeError(
            f"Unsupported baostock sector {sector_name!r}. Supported sectors: {supported}."
        ) from exc


def collect_baostock_rows(
    query: Callable[[], ResultData],
    max_retries: int,
    retry_wait: float,
) -> Tuple[List[List[str]], List[str]]:
    attempt = 0
    while True:
        rows: List[List[str]] = []
        result = query()
        while result.error_code == "0":
            if not result.next():
                return rows, result.fields
            rows.append(result.get_row_data())

        attempt += 1
        if attempt > max_retries:
            raise RuntimeError(
                "baostock query failed after retries: "
                f"error_code={result.error_code}, error_msg={result.error_msg}"
            )
        time.sleep(retry_wait)
        baostock_relogin()


def build_constituent_snapshots_from_baostock(
    sector_name: str,
    trading_dates: Sequence[str],
    max_retries: int,
    retry_wait: float,
) -> List[Tuple[str, Set[str]]]:
    query_fn = get_baostock_constituent_query(sector_name)
    snapshots: List[Tuple[str, Set[str]]] = []
    total_days = len(trading_dates)

    with baostock_login_context():
        for index, trade_date in enumerate(trading_dates, start=1):
            query_date = baostock_date_text(trade_date)
            rows, _ = collect_baostock_rows(
                query=lambda current_date=query_date: query_fn(current_date),
                max_retries=max_retries,
                retry_wait=retry_wait,
            )
            if not rows:
                raise RuntimeError(f"baostock returned no constituent rows for {sector_name} at {trade_date}.")

            snapshot = {row[1] for row in rows if len(row) >= 2 and row[1]}
            if not snapshot:
                raise RuntimeError(
                    f"baostock returned constituent rows but no stock codes for {sector_name} at {trade_date}."
                )

            snapshots.append((trade_date, snapshot))
            if index == 1 or index == total_days or index % 100 == 0:
                print(
                    f"Loaded baostock constituents {index}/{total_days}: "
                    f"{trade_date}, n_members={len(snapshot)}"
                )

    return snapshots


def build_constituent_snapshots_from_xtquant(
    sector_name: str,
    trading_dates: Sequence[str],
) -> List[Tuple[str, Set[str]]]:
    snapshots: List[Tuple[str, Set[str]]] = []
    total_days = len(trading_dates)
    for index, trade_date in enumerate(trading_dates, start=1):
        snapshot = set(xtdata.get_stock_list_in_sector(sector_name, compact_date_text(trade_date)))
        if not snapshot:
            raise RuntimeError(
                f"xtquant returned an empty constituent snapshot for {sector_name} at {trade_date}."
            )
        snapshots.append((trade_date, snapshot))
        if index == 1 or index == total_days or index % 100 == 0:
            print(
                f"Loaded xtquant constituents {index}/{total_days}: "
                f"{trade_date}, n_members={len(snapshot)}"
            )
    return snapshots


def build_constituent_snapshots(
    sector_name: str,
    trading_dates: Sequence[str],
    constituent_source: str,
    baostock_retries: int,
    baostock_retry_wait: float,
) -> List[Tuple[str, Set[str]]]:
    if constituent_source == "baostock":
        return build_constituent_snapshots_from_baostock(
            sector_name,
            trading_dates,
            max_retries=baostock_retries,
            retry_wait=baostock_retry_wait,
        )
    return build_constituent_snapshots_from_xtquant(sector_name, trading_dates)


def normalize_constituent_code(stock_code: str, constituent_source: str) -> str:
    if constituent_source == "baostock":
        return baostock_code_to_qlib_code(stock_code)
    return xt_code_to_qlib_code(stock_code)


def compress_snapshots_to_intervals(
    snapshots: Sequence[Tuple[str, Set[str]]],
    constituent_source: str,
) -> pd.DataFrame:
    active: Dict[str, str] = {}
    rows: List[Tuple[str, str, str]] = []
    prev_snapshot: Set[str] = set()
    prev_date: Optional[str] = None

    for trade_date, current_snapshot in snapshots:
        added = current_snapshot - prev_snapshot
        removed = prev_snapshot - current_snapshot

        for stock_code in sorted(added):
            active[stock_code] = trade_date
        for stock_code in sorted(removed):
            start_date = active.pop(stock_code, None)
            if start_date is None or prev_date is None:
                raise RuntimeError(f"Failed to close constituent interval for {stock_code}.")
            rows.append((normalize_constituent_code(stock_code, constituent_source), start_date, prev_date))

        prev_snapshot = current_snapshot
        prev_date = trade_date

    if prev_date is None:
        raise RuntimeError("Cannot compress empty constituent snapshots.")

    for stock_code, start_date in active.items():
        rows.append((normalize_constituent_code(stock_code, constituent_source), start_date, prev_date))

    intervals = pd.DataFrame(rows, columns=["code", "start_datetime", "end_datetime"])
    intervals.sort_values(["code", "start_datetime", "end_datetime"], inplace=True)
    intervals.reset_index(drop=True, inplace=True)
    return intervals


def run(args: argparse.Namespace) -> None:
    ensure_supported_config(args.period, args.dividend_type)
    if args.batch_size <= 0:
        raise ValueError("batch_size must be greater than 0.")
    if args.qlib_max_workers <= 0:
        raise ValueError("qlib_max_workers must be greater than 0.")
    if args.baostock_retries < 0:
        raise ValueError("baostock_retries must be greater than or equal to 0.")
    if args.baostock_retry_wait < 0:
        raise ValueError("baostock_retry_wait must be greater than or equal to 0.")

    start_date = normalize_date_text(args.start_date)
    end_date = normalize_date_text(args.end_date)
    if start_date > end_date:
        raise ValueError("start_date must be earlier than or equal to end_date.")

    if hasattr(xtdata, "enable_hello"):
        xtdata.enable_hello = False

    sector_name, universe_name = resolve_sector_and_universe(args.sector_name, args.universe_name)
    paths = resolve_paths(args.out_root, universe_name)
    qlib_dir = resolve_qlib_dir(args.qlib_dir)
    mode = determine_mode(args.mode, paths)
    ensure_dirs(paths)

    print(f"Running xtquant fetcher in '{mode}' mode.")
    print(f"Universe: {universe_name}")
    print(f"Sector: {sector_name}")
    print(f"Constituent source: {args.constituent_source}")
    validate_constituent_source(sector_name, args.constituent_source)

    existing_calendar = read_existing_calendar(paths.calendar_path)
    anchor_date = initial_anchor_date(mode, existing_calendar)
    constituent_start_date = anchor_date if anchor_date is not None else start_date
    constituent_calendar = get_trading_calendar(constituent_start_date, end_date)
    snapshots = build_constituent_snapshots(
        sector_name,
        constituent_calendar,
        args.constituent_source,
        args.baostock_retries,
        args.baostock_retry_wait,
    )
    new_intervals = compress_snapshots_to_intervals(snapshots, args.constituent_source)
    merged_intervals = merge_incremental_intervals(
        read_existing_intervals(paths.instruments_path),
        new_intervals,
        anchor_date,
    )

    full_calendar = get_trading_calendar(start_date, end_date)
    qlib_codes = merged_intervals["code"].tolist()
    fetch_plan = plan_stock_fetches(qlib_codes, paths, full_calendar, start_date, mode)
    grouped_plan = group_fetch_plan(fetch_plan)

    if grouped_plan:
        download_history_batches(grouped_plan, end_date)
        market_batches = fetch_market_batches(grouped_plan, end_date, args.batch_size)
    else:
        market_batches = {}

    success_codes: List[str] = []
    failed: Dict[str, str] = {}

    for qlib_code in sorted(fetch_plan):
        xt_code = qlib_code_to_xt_code(qlib_code)
        csv_path = paths.stocks_dir / f"{qlib_code}.csv"
        try:
            market_data = market_batches.get(xt_code)
            if market_data is None:
                raise RuntimeError(f"No market data returned for {xt_code}.")
            new_frame = build_output_frame(xt_code, qlib_code, market_data, fetch_plan[qlib_code], end_date)
            merged_frame = merge_with_existing_csv(csv_path, new_frame)
            merged_frame.to_csv(csv_path, index=False)
            success_codes.append(qlib_code)
        except Exception as exc:
            failed[qlib_code] = str(exc)

    qlib_instrument_path: Optional[Path] = None
    if args.dump_qlib:
        print(f"Dumping Qlib data into {qlib_dir}")
        dump_qlib_data(paths.stocks_dir, qlib_dir, args.qlib_max_workers)
        qlib_instrument_path = write_qlib_instrument_file(
            qlib_dir=qlib_dir,
            instrument_name=universe_name,
            intervals=merged_intervals,
        )

    write_calendar(paths.calendar_path, full_calendar)
    write_intervals(paths.instruments_path, merged_intervals)
    write_symbols(paths.symbols_path, qlib_codes)
    write_manifest(
        paths.manifest_path,
        {
            "sources": {
                "constituents": args.constituent_source,
                "market_data": "xtquant",
                "factor_data": "xtquant",
            },
            "script_version": SCRIPT_VERSION,
            "sector_name": sector_name,
            "universe_name": universe_name,
            "mode": mode,
            "period": args.period,
            "dividend_type": args.dividend_type,
            "dump_qlib": args.dump_qlib,
            "start_date": start_date,
            "end_date": end_date,
            "run_at": datetime.now().isoformat(timespec="seconds"),
            "paths": {
                "out_root": str(paths.out_root),
                "stocks_dir": str(paths.stocks_dir),
                "calendar_day": str(paths.calendar_path),
                "instruments": str(paths.instruments_path),
                "symbols": str(paths.symbols_path),
                "qlib_dir": str(qlib_dir),
                "qlib_instrument": None if qlib_instrument_path is None else str(qlib_instrument_path),
            },
            "counts": {
                "calendar_days": len(full_calendar),
                "constituent_intervals": int(len(merged_intervals)),
                "tracked_symbols": int(len(set(qlib_codes))),
                "requested_stock_updates": int(len(fetch_plan)),
                "successful_stock_updates": int(len(success_codes)),
                "failed_stock_updates": int(len(failed)),
            },
            "failed_stocks": failed,
            "baostock": {
                "retries": args.baostock_retries,
                "retry_wait_seconds": args.baostock_retry_wait,
            },
        },
    )

    print(
        "Finished mixed fetch: "
        f"{len(success_codes)} stocks updated, {len(failed)} failures, "
        f"{len(set(qlib_codes))} symbols tracked."
    )
    if qlib_instrument_path is not None:
        print(f"Qlib instrument file written to: {qlib_instrument_path}")


def main() -> None:
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()
