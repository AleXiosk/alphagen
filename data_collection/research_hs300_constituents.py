"""
本脚本不是直接读取指数历次调样表，而是基于 XtQuant 的
`get_stock_list_in_sector(sector_name, real_timetag)` 按交易日获取历史成分快照，
再通过比较相邻交易日的成员集合识别成分变化点，并压缩为阶段性成分区间。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent
for _path in (str(_THIS_DIR), str(_REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from alphagen_qlib.universe import default_constituents_output_dir, get_universe_spec, resolve_universe_name


RETRY_ATTEMPTS = 3
RETRY_SLEEP_SECONDS = 1.0
LOG_FILE_NAME = "run.log"


@dataclass(slots=True)
class DailySnapshot:
    trade_date: str
    members: tuple[str, ...]
    members_hash: str
    fetch_ok: bool
    note: str | None = None
    n_members: int = field(init=False)
    is_empty: bool = field(init=False)

    def __post_init__(self) -> None:
        self.n_members = len(self.members)
        self.is_empty = self.n_members == 0


@dataclass(slots=True)
class ChangeRecord:
    effective_date: str
    added: tuple[str, ...]
    removed: tuple[str, ...]
    added_count: int = field(init=False)
    removed_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.added_count = len(self.added)
        self.removed_count = len(self.removed)


@dataclass(slots=True)
class PeriodRecord:
    period_id: int
    start_date: str
    end_date: str
    members: tuple[str, ...]
    members_hash: str
    n_members: int = field(init=False)

    def __post_init__(self) -> None:
        self.n_members = len(self.members)


def today_yyyymmdd() -> str:
    return date.today().strftime("%Y%m%d")


def resolve_sector_and_universe(
    sector_name: str | None,
    universe_name: str | None,
) -> tuple[str, str]:
    resolved_universe = resolve_universe_name(universe_name, sector_name, default="csi300")
    spec = get_universe_spec(resolved_universe)
    resolved_sector = sector_name if sector_name is not None else (spec.sector_name if spec is not None else "沪深300")
    return resolved_sector, resolved_universe


def resolve_output_dir(output_dir: str | None, universe_name: str) -> Path:
    if output_dir is not None:
        return Path(output_dir).expanduser().resolve()
    return default_constituents_output_dir(universe_name).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="追溯指数历史成分股，并压缩为每一期成分区间。"
    )
    parser.add_argument(
        "--sector-name",
        default=None,
        help="目标板块名称。若省略，优先按 --universe-name 推断。",
    )
    parser.add_argument(
        "--universe-name",
        default=None,
        help="Universe 名称，例如 csi300、csi500。",
    )
    parser.add_argument(
        "--start-date",
        default="20110101",
        help="起始日期，格式 YYYYMMDD 或 YYYY-MM-DD",
    )
    parser.add_argument(
        "--end-date",
        default=today_yyyymmdd(),
        help="结束日期，格式 YYYYMMDD 或 YYYY-MM-DD",
    )
    parser.add_argument("--market", default="SH", help="交易日历市场代码")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="输出目录。默认生成到 ./outputs/<universe>_constituents",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="CSV/JSON 输出编码",
    )
    return parser.parse_args()


def normalize_input_date(value: str) -> str:
    candidate = value.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(candidate, fmt).strftime("%Y%m%d")
        except ValueError:
            continue
    raise ValueError(f"无法解析日期: {value!r}，请使用 YYYYMMDD 或 YYYY-MM-DD。")


def configure_logging(output_dir: Path, encoding: str) -> logging.Logger:
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("index_constituents")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        output_dir / LOG_FILE_NAME,
        encoding=encoding,
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger


def import_xtdata():
    try:
        from xtquant import xtdata  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "无法导入 xtquant.xtdata。请确认已安装 XtQuant，并在可连接 QMT/MiniQMT 的环境中运行。"
        ) from exc
    if hasattr(xtdata, "enable_hello"):
        xtdata.enable_hello = False
    return xtdata


def compute_members_hash(members: Sequence[str]) -> str:
    joined = "|".join(members)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def normalize_security_codes(values: Iterable[Any] | None) -> tuple[str, ...]:
    if values is None:
        return tuple()
    normalized = {
        str(value).strip()
        for value in values
        if value is not None and str(value).strip()
    }
    return tuple(sorted(normalized))


def normalize_calendar_entry(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    if isinstance(value, int):
        text = str(value)
        if len(text) == 8:
            return text
        if len(text) >= 13:
            return datetime.fromtimestamp(value / 1000.0).strftime("%Y%m%d")
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError("交易日历返回了空字符串。")
        digits = "".join(ch for ch in stripped if ch.isdigit())
        if len(digits) == 8:
            return digits
    raise ValueError(f"无法识别的交易日历日期格式: {value!r}")


def resolve_sector_name(
    xtdata: Any,
    target_name: str,
    logger: logging.Logger,
) -> str:
    logger.info("下载板块分类数据: xtdata.download_sector_data()")
    xtdata.download_sector_data()

    raw_sector_list = xtdata.get_sector_list()
    if not raw_sector_list:
        raise RuntimeError("xtdata.get_sector_list() 返回空结果，无法解析目标板块。")

    sectors = sorted(
        {
            str(item).strip()
            for item in raw_sector_list
            if item is not None and str(item).strip()
        }
    )
    if not sectors:
        raise RuntimeError("板块列表为空，无法解析目标板块。")

    target = target_name.strip()
    if target in sectors:
        logger.info("板块名称精确匹配成功: %s", target)
        return target

    target_compact = target.replace(" ", "")
    exact_compact = [item for item in sectors if item.replace(" ", "") == target_compact]
    if len(exact_compact) == 1:
        logger.info("板块名称压缩空格后匹配成功: %s", exact_compact[0])
        return exact_compact[0]

    preferred_candidates = [
        item
        for item in sectors
        if target_compact in item.replace(" ", "") or item.replace(" ", "") in target_compact
    ]
    preferred_candidates = sorted(set(preferred_candidates))
    if len(preferred_candidates) == 1:
        logger.info("板块名称模糊匹配成功: %s", preferred_candidates[0])
        return preferred_candidates[0]

    sector_300_candidates = [item for item in sectors if "300" in item]
    if len(sector_300_candidates) == 1:
        logger.info("仅找到一个包含 300 的候选板块: %s", sector_300_candidates[0])
        return sector_300_candidates[0]

    candidate_preview = preferred_candidates or sector_300_candidates
    candidate_preview = candidate_preview[:50]
    raise RuntimeError(
        "未能自动确认目标板块名称。"
        f" 请求值: {target_name!r}。"
        f" 包含 '300' 的候选板块示例: {candidate_preview}"
    )


def get_trade_dates(
    xtdata: Any,
    market: str,
    start_date: str,
    end_date: str,
) -> list[str]:
    calendar = xtdata.get_trading_calendar(market, start_time=start_date, end_time=end_date)
    if not calendar:
        raise RuntimeError(
            f"xtdata.get_trading_calendar({market!r}, {start_date!r}, {end_date!r}) 返回空结果。"
        )

    dates = sorted({normalize_calendar_entry(item) for item in calendar})
    filtered = [item for item in dates if start_date <= item <= end_date]
    if not filtered:
        raise RuntimeError("交易日历经过标准化和过滤后为空。")
    return filtered


def fetch_members_with_retry(
    xtdata: Any,
    sector_name: str,
    trade_date: str,
    logger: logging.Logger,
    attempts: int = RETRY_ATTEMPTS,
    sleep_seconds: float = RETRY_SLEEP_SECONDS,
) -> tuple[tuple[str, ...], bool, str | None]:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            raw_members = xtdata.get_stock_list_in_sector(sector_name, real_timetag=trade_date)
            members = normalize_security_codes(raw_members)
            note = None
            if not members:
                note = "empty_snapshot"
                logger.warning("交易日 %s 返回空成分列表。", trade_date)
            return members, True, note
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < attempts:
                logger.warning(
                    "交易日 %s 获取成分失败，第 %s/%s 次重试。错误: %s",
                    trade_date,
                    attempt,
                    attempts,
                    exc,
                )
                time.sleep(sleep_seconds)
            else:
                logger.error(
                    "交易日 %s 在 %s 次重试后仍失败，将该日记为空快照。错误: %s",
                    trade_date,
                    attempts,
                    exc,
                )

    failure_note = f"fetch_failed_after_retries: {last_error}" if last_error else "fetch_failed"
    return tuple(), False, failure_note


def fetch_daily_snapshots(
    xtdata: Any,
    sector_name: str,
    trade_dates: Sequence[str],
    logger: logging.Logger,
) -> tuple[list[DailySnapshot], list[str]]:
    snapshots: list[DailySnapshot] = []
    failed_dates: list[str] = []

    total_days = len(trade_dates)
    for index, trade_date in enumerate(trade_dates, start=1):
        members, fetch_ok, note = fetch_members_with_retry(
            xtdata=xtdata,
            sector_name=sector_name,
            trade_date=trade_date,
            logger=logger,
        )
        if not fetch_ok:
            failed_dates.append(trade_date)
        snapshot = DailySnapshot(
            trade_date=trade_date,
            members=members,
            members_hash=compute_members_hash(members),
            fetch_ok=fetch_ok,
            note=note,
        )
        snapshots.append(snapshot)

        if index == 1 or index == total_days or index % 100 == 0:
            logger.info(
                "快照进度 %s/%s: %s, n_members=%s, hash=%s",
                index,
                total_days,
                trade_date,
                snapshot.n_members,
                snapshot.members_hash[:12],
            )

    return snapshots, failed_dates


def detect_changes_and_periods(
    snapshots: Sequence[DailySnapshot],
) -> tuple[list[PeriodRecord], list[ChangeRecord]]:
    if not snapshots:
        return [], []

    periods: list[PeriodRecord] = []
    changes: list[ChangeRecord] = []

    current_start = snapshots[0].trade_date
    current_members = snapshots[0].members
    previous_snapshot = snapshots[0]
    period_id = 1

    for snapshot in snapshots[1:]:
        if snapshot.members != previous_snapshot.members:
            added = tuple(sorted(set(snapshot.members) - set(previous_snapshot.members)))
            removed = tuple(sorted(set(previous_snapshot.members) - set(snapshot.members)))
            changes.append(
                ChangeRecord(
                    effective_date=snapshot.trade_date,
                    added=added,
                    removed=removed,
                )
            )
            periods.append(
                PeriodRecord(
                    period_id=period_id,
                    start_date=current_start,
                    end_date=previous_snapshot.trade_date,
                    members=current_members,
                    members_hash=compute_members_hash(current_members),
                )
            )
            period_id += 1
            current_start = snapshot.trade_date
            current_members = snapshot.members
        previous_snapshot = snapshot

    periods.append(
        PeriodRecord(
            period_id=period_id,
            start_date=current_start,
            end_date=previous_snapshot.trade_date,
            members=current_members,
            members_hash=compute_members_hash(current_members),
        )
    )
    return periods, changes


def calculate_empty_streaks(snapshots: Sequence[DailySnapshot]) -> tuple[int, int]:
    empty_days = 0
    max_consecutive = 0
    current_streak = 0

    for snapshot in snapshots:
        if snapshot.is_empty:
            empty_days += 1
            current_streak += 1
            max_consecutive = max(max_consecutive, current_streak)
        else:
            current_streak = 0

    return empty_days, max_consecutive


def validate_periods(periods: Sequence[PeriodRecord]) -> list[str]:
    issues: list[str] = []
    for record in periods:
        if record.n_members != len(record.members):
            issues.append(
                f"period_id={record.period_id} 的 n_members={record.n_members} "
                f"与实际 members 数量={len(record.members)} 不一致。"
            )
        if record.n_members < 1:
            issues.append(f"period_id={record.period_id} 没有任何成分股。")
        if record.start_date > record.end_date:
            issues.append(
                f"period_id={record.period_id} 的 start_date={record.start_date} "
                f"晚于 end_date={record.end_date}。"
            )
    return issues


def write_periods_csv(
    periods: Sequence[PeriodRecord],
    output_path: Path,
    encoding: str,
) -> None:
    with output_path.open("w", newline="", encoding=encoding) as file:
        writer = csv.writer(file)
        writer.writerow(["period_id", "start_date", "end_date", "n_members", "members_hash"])
        for record in periods:
            writer.writerow(
                [
                    record.period_id,
                    record.start_date,
                    record.end_date,
                    record.n_members,
                    record.members_hash,
                ]
            )


def write_period_members_csv(
    periods: Sequence[PeriodRecord],
    output_path: Path,
    encoding: str,
) -> None:
    with output_path.open("w", newline="", encoding=encoding) as file:
        writer = csv.writer(file)
        writer.writerow(["period_id", "stock_code"])
        for record in periods:
            for stock_code in record.members:
                writer.writerow([record.period_id, stock_code])


def write_changes_csv(
    changes: Sequence[ChangeRecord],
    output_path: Path,
    encoding: str,
) -> None:
    with output_path.open("w", newline="", encoding=encoding) as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "effective_date",
                "added_count",
                "removed_count",
                "added_codes",
                "removed_codes",
            ]
        )
        for record in changes:
            writer.writerow(
                [
                    record.effective_date,
                    record.added_count,
                    record.removed_count,
                    "|".join(record.added),
                    "|".join(record.removed),
                ]
            )


def write_daily_snapshot_summary_csv(
    snapshots: Sequence[DailySnapshot],
    output_path: Path,
    encoding: str,
) -> None:
    with output_path.open("w", newline="", encoding=encoding) as file:
        writer = csv.writer(file)
        writer.writerow(["trade_date", "n_members", "members_hash"])
        for snapshot in snapshots:
            writer.writerow(
                [
                    snapshot.trade_date,
                    snapshot.n_members,
                    snapshot.members_hash,
                ]
            )


def write_run_summary_json(
    summary: dict[str, Any],
    output_path: Path,
    encoding: str,
) -> None:
    with output_path.open("w", encoding=encoding) as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)


def log_preview(
    logger: logging.Logger,
    periods: Sequence[PeriodRecord],
    changes: Sequence[ChangeRecord],
) -> None:
    logger.info("前 10 个变化点预览:")
    if not changes:
        logger.info("  无变化点。")
    else:
        for record in changes[:10]:
            logger.info(
                "  %s | added=%s | removed=%s",
                record.effective_date,
                "|".join(record.added) if record.added else "-",
                "|".join(record.removed) if record.removed else "-",
            )

    logger.info("前 5 个 period 摘要:")
    if not periods:
        logger.info("  无 period。")
    else:
        for record in periods[:5]:
            logger.info(
                "  period_id=%s | %s ~ %s | n_members=%s | hash=%s",
                record.period_id,
                record.start_date,
                record.end_date,
                record.n_members,
                record.members_hash[:12],
            )


def build_run_summary(
    resolved_sector_name: str,
    universe_name: str,
    start_date: str,
    end_date: str,
    trade_dates: Sequence[str],
    periods: Sequence[PeriodRecord],
    changes: Sequence[ChangeRecord],
    snapshots: Sequence[DailySnapshot],
    failed_dates: Sequence[str],
    consistency_issues: Sequence[str],
) -> dict[str, Any]:
    empty_days, max_consecutive_empty_days = calculate_empty_streaks(snapshots)
    empty_dates = [snapshot.trade_date for snapshot in snapshots if snapshot.is_empty]

    return {
        "resolved_sector_name": resolved_sector_name,
        "universe_name": universe_name,
        "start_date": start_date,
        "end_date": end_date,
        "total_trade_days": len(trade_dates),
        "total_periods": len(periods),
        "total_change_points": len(changes),
        "empty_snapshot_days": empty_days,
        "max_consecutive_empty_days": max_consecutive_empty_days,
        "failed_days_after_retries": list(failed_dates),
        "empty_snapshot_dates_preview": empty_dates[:50],
        "consistency_issue_count": len(consistency_issues),
        "consistency_issues": list(consistency_issues),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "coverage_notice": (
            "XtQuant 文档未保证历史覆盖起点。若开始日期早于数据实际可用范围，"
            "脚本会尽量跑完整个区间，但历史覆盖完整性需自行验证。"
        ),
    }


def write_outputs(
    output_dir: Path,
    encoding: str,
    periods: Sequence[PeriodRecord],
    changes: Sequence[ChangeRecord],
    snapshots: Sequence[DailySnapshot],
    summary: dict[str, Any],
) -> None:
    write_periods_csv(periods, output_dir / "periods.csv", encoding)
    write_period_members_csv(periods, output_dir / "period_members.csv", encoding)
    write_changes_csv(changes, output_dir / "changes.csv", encoding)
    write_daily_snapshot_summary_csv(
        snapshots,
        output_dir / "daily_snapshot_summary.csv",
        encoding,
    )
    write_run_summary_json(summary, output_dir / "run_summary.json", encoding)


def main() -> int:
    args = parse_args()
    start_date = normalize_input_date(args.start_date)
    end_date = normalize_input_date(args.end_date)
    if start_date > end_date:
        raise SystemExit(f"开始日期 {start_date} 晚于结束日期 {end_date}。")

    sector_name, universe_name = resolve_sector_and_universe(args.sector_name, args.universe_name)
    output_dir = resolve_output_dir(args.output_dir, universe_name)
    logger = configure_logging(output_dir, args.encoding)

    logger.info("研究任务启动。")
    logger.info(
        "参数: sector_name=%s, universe_name=%s, start_date=%s, end_date=%s, market=%s",
        sector_name,
        universe_name,
        start_date,
        end_date,
        args.market,
    )
    logger.info("输出目录: %s", output_dir)

    xtdata = import_xtdata()
    resolved_sector_name = resolve_sector_name(xtdata, sector_name, logger)
    trade_dates = get_trade_dates(xtdata, args.market, start_date, end_date)
    logger.info("交易日数量: %s", len(trade_dates))

    snapshots, failed_dates = fetch_daily_snapshots(
        xtdata=xtdata,
        sector_name=resolved_sector_name,
        trade_dates=trade_dates,
        logger=logger,
    )
    periods, changes = detect_changes_and_periods(snapshots)
    consistency_issues = validate_periods(periods)

    if consistency_issues:
        logger.warning("一致性检查发现 %s 个问题。", len(consistency_issues))
        for issue in consistency_issues[:20]:
            logger.warning("  %s", issue)
    else:
        logger.info("一致性检查通过。")

    log_preview(logger, periods, changes)

    summary = build_run_summary(
        resolved_sector_name=resolved_sector_name,
        universe_name=universe_name,
        start_date=start_date,
        end_date=end_date,
        trade_dates=trade_dates,
        periods=periods,
        changes=changes,
        snapshots=snapshots,
        failed_dates=failed_dates,
        consistency_issues=consistency_issues,
    )
    write_outputs(
        output_dir=output_dir,
        encoding=args.encoding,
        periods=periods,
        changes=changes,
        snapshots=snapshots,
        summary=summary,
    )

    logger.info("输出完成: %s", output_dir)
    logger.info(
        "总计: trade_days=%s, periods=%s, change_points=%s, empty_days=%s",
        summary["total_trade_days"],
        summary["total_periods"],
        summary["total_change_points"],
        summary["empty_snapshot_days"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
