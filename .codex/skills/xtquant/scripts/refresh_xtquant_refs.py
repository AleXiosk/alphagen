#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import re
import sys
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen


USER_AGENT = "Mozilla/5.0 (compatible; xtquant-skill-refresher/1.0)"
FOOTER_MARKERS = ("上次更新", "邀请注册送VIP优惠券", "分享下方的内容给好友", "登录后获取")


@dataclasses.dataclass(frozen=True)
class PageSpec:
    slug: str
    title: str
    url: str
    tags: tuple[str, ...]
    normalized_reference: str
    conflict_priority: int
    start_markers: tuple[str, ...] = ()


BASE_SPECS: tuple[PageSpec, ...] = (
    PageSpec(
        slug="native-start-now",
        title="快速开始",
        url="https://dict.thinktrader.net/nativeApi/start_now.html",
        tags=("native", "overview", "setup"),
        normalized_reference="references/native/overview.md",
        conflict_priority=2,
        start_markers=("XtQuant 能提供哪些服务",),
    ),
    PageSpec(
        slug="native-xtdata",
        title="XtQuant.XtData 行情模块",
        url="https://dict.thinktrader.net/nativeApi/xtdata.html",
        tags=("native", "xtdata", "market-data"),
        normalized_reference="references/native/xtdata.md",
        conflict_priority=2,
        start_markers=("XtQuant.XtData 行情模块", "接口概述"),
    ),
    PageSpec(
        slug="native-xttrader",
        title="XtQuant.Xttrade 交易模块",
        url="https://dict.thinktrader.net/nativeApi/xttrader.html",
        tags=("native", "xttrader", "trading"),
        normalized_reference="references/native/xttrader.md",
        conflict_priority=2,
        start_markers=("XtQuant.Xttrade 交易模块", "版本信息"),
    ),
    PageSpec(
        slug="native-code-examples",
        title="完整实例",
        url="https://dict.thinktrader.net/nativeApi/code_examples.html",
        tags=("native", "examples"),
        normalized_reference="references/native/examples-faq-version.md",
        conflict_priority=3,
        start_markers=("行情示例", "获取行情示例"),
    ),
    PageSpec(
        slug="native-question-function",
        title="原生 FAQ",
        url="https://dict.thinktrader.net/nativeApi/question_function.html",
        tags=("native", "faq"),
        normalized_reference="references/native/examples-faq-version.md",
        conflict_priority=4,
        start_markers=("导入xtquant库时提示", "连接 xtquant 时失败"),
    ),
    PageSpec(
        slug="native-download-xtquant",
        title="xtquant版本下载",
        url="https://dict.thinktrader.net/nativeApi/download_xtquant.html",
        tags=("native", "version", "compatibility"),
        normalized_reference="references/native/examples-faq-version.md",
        conflict_priority=1,
        start_markers=("更新日期", "xtquant_250516"),
    ),
    PageSpec(
        slug="native-linux-guide",
        title="Linux版xtquant快速开始指南",
        url="https://dict.thinktrader.net/nativeApi/Linux%E7%89%88xtquant%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B%E6%8C%87%E5%8D%97.html",
        tags=("native", "linux", "xtdata-only"),
        normalized_reference="references/native/linux.md",
        conflict_priority=2,
        start_markers=("所需环境", "Linux版xtquant快速开始指南"),
    ),
    PageSpec(
        slug="dictionary-home",
        title="数据字典首页",
        url="https://dict.thinktrader.net/dictionary/",
        tags=("dictionary", "overview"),
        normalized_reference="references/dictionary/overview.md",
        conflict_priority=3,
        start_markers=("基础用法 - 获取数据",),
    ),
    PageSpec(
        slug="dictionary-stock",
        title="股票数据",
        url="https://dict.thinktrader.net/dictionary/stock.html",
        tags=("dictionary", "stock"),
        normalized_reference="references/dictionary/stock.md",
        conflict_priority=3,
        start_markers=("获取股票概况", "获取合约基础信息数据"),
    ),
    PageSpec(
        slug="dictionary-industry",
        title="行业概念数据",
        url="https://dict.thinktrader.net/dictionary/industry.html",
        tags=("dictionary", "industry"),
        normalized_reference="references/dictionary/industry-index.md",
        conflict_priority=3,
        start_markers=(
            "获取行业/板块信息前，需要先通过download_sector_data下载板块分类信息",
            "xtdata.get_sector_list()",
            "xtdata.get_stock_list_in_sector(sector_name)",
        ),
    ),
    PageSpec(
        slug="dictionary-indexes",
        title="指数数据",
        url="https://dict.thinktrader.net/dictionary/indexes.html",
        tags=("dictionary", "index"),
        normalized_reference="references/dictionary/industry-index.md",
        conflict_priority=3,
        start_markers=(
            "为了获取指数合约列表",
            "xtdata.get_index_weight(index_code)",
            "xt_sector_index_list = xtdata.get_stock_list_in_sector",
        ),
    ),
    PageSpec(
        slug="dictionary-future",
        title="期货数据",
        url="https://dict.thinktrader.net/dictionary/future.html",
        tags=("dictionary", "future"),
        normalized_reference="references/dictionary/futures-options.md",
        conflict_priority=3,
        start_markers=("获取期货合约信息", "市场简称代码"),
    ),
    PageSpec(
        slug="dictionary-option",
        title="期权数据",
        url="https://dict.thinktrader.net/dictionary/option.html",
        tags=("dictionary", "option"),
        normalized_reference="references/dictionary/futures-options.md",
        conflict_priority=3,
        start_markers=("获取期权数据",),
    ),
    PageSpec(
        slug="dictionary-floorfunds",
        title="场内基金",
        url="https://dict.thinktrader.net/dictionary/floorfunds.html",
        tags=("dictionary", "fund"),
        normalized_reference="references/dictionary/fund-bond.md",
        conflict_priority=3,
        start_markers=("获取基金数据",),
    ),
    PageSpec(
        slug="dictionary-bond",
        title="债券数据",
        url="https://dict.thinktrader.net/dictionary/bond.html",
        tags=("dictionary", "bond"),
        normalized_reference="references/dictionary/fund-bond.md",
        conflict_priority=3,
        start_markers=("可转债数据",),
    ),
    PageSpec(
        slug="dictionary-question-answer",
        title="字典 FAQ",
        url="https://dict.thinktrader.net/dictionary/question_answer.html",
        tags=("dictionary", "faq"),
        normalized_reference="references/dictionary/faq-scenarios.md",
        conflict_priority=4,
        start_markers=("Token 使用相关", "获取行情相关"),
    ),
    PageSpec(
        slug="dictionary-scenario-based-example",
        title="场景化示例",
        url="https://dict.thinktrader.net/dictionary/scenario_based_example.html",
        tags=("dictionary", "scenario"),
        normalized_reference="references/dictionary/faq-scenarios.md",
        conflict_priority=3,
        start_markers=("场景化示例", "判断市场状态"),
    ),
    PageSpec(
        slug="dictionary-xuntou-factor",
        title="迅投因子",
        url="https://dict.thinktrader.net/dictionary/xuntou_factor.html",
        tags=("dictionary", "factor"),
        normalized_reference="references/dictionary/factors-data-browser.md",
        conflict_priority=3,
        start_markers=("因子数据下载", "成长因子"),
    ),
    PageSpec(
        slug="dictionary-data-browser",
        title="数据浏览器",
        url="https://dict.thinktrader.net/dictionary/data_browser_barra_factor.html",
        tags=("dictionary", "data-browser"),
        normalized_reference="references/dictionary/factors-data-browser.md",
        conflict_priority=3,
        start_markers=("数据浏览器使用教程", "纵览"),
    ),
)


INNER_CORE_SPECS: tuple[PageSpec, ...] = (
    PageSpec(
        slug="inner-user-attention",
        title="使用须知",
        url="https://dict.thinktrader.net/innerApi/user_attention.html",
        tags=("inner-python", "usage-notes"),
        normalized_reference="references/inner-python/usage-notes.md",
        conflict_priority=3,
        start_markers=("使用须知",),
    ),
    PageSpec(
        slug="inner-variable-convention",
        title="变量约定",
        url="https://dict.thinktrader.net/innerApi/variable_convention.html",
        tags=("inner-python", "variables"),
        normalized_reference="references/inner-python/variable-conventions.md",
        conflict_priority=3,
        start_markers=("变量约定", "市场分类"),
    ),
    PageSpec(
        slug="inner-data-function",
        title="行情函数",
        url="https://dict.thinktrader.net/innerApi/data_function.html",
        tags=("inner-python", "data-functions"),
        normalized_reference="references/inner-python/data-functions.md",
        conflict_priority=3,
        start_markers=("行情函数", "download_history_data"),
    ),
    PageSpec(
        slug="inner-system-function",
        title="系统函数",
        url="https://dict.thinktrader.net/innerApi/system_function.html",
        tags=("inner-python", "system-functions"),
        normalized_reference="references/inner-python/usage-notes.md",
        conflict_priority=3,
        start_markers=("ContextInfo 对象", "init - 初始化函数"),
    ),
    PageSpec(
        slug="inner-trading-function",
        title="交易函数",
        url="https://dict.thinktrader.net/innerApi/trading_function.html",
        tags=("inner-python", "trading-functions"),
        normalized_reference="references/inner-python/trading-functions.md",
        conflict_priority=3,
        start_markers=("交易函数", "passorder"),
    ),
    PageSpec(
        slug="inner-question-answer",
        title="内置 FAQ",
        url="https://dict.thinktrader.net/innerApi/question_answer.html",
        tags=("inner-python", "faq"),
        normalized_reference="references/inner-python/faq.md",
        conflict_priority=4,
        start_markers=("系统对象 ContextInfo", "快速交易参数 quickTrade"),
    ),
)


def collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@dataclasses.dataclass
class Block:
    kind: str
    text: str
    level: int = 0

    def render(self) -> str:
        if self.kind == "heading":
            level = max(1, min(self.level, 6))
            return f"{'#' * level} {self.text.strip()}"
        if self.kind == "code":
            body = self.text.rstrip("\n")
            return f"```text\n{body}\n```"
        return self.text.strip()


class MarkdownExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[Block] = []
        self.skip_depth = 0
        self.current_kind: str | None = None
        self.current_level = 0
        self.current_parts: list[str] = []
        self.table_rows: list[list[tuple[str, bool]]] | None = None
        self.current_row: list[tuple[str, bool]] | None = None
        self.current_cell_parts: list[str] | None = None
        self.current_cell_header = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "br":
            self._append_text("\n")
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._start_block("heading", int(tag[1]))
        elif tag in {"p", "li", "dd", "dt"}:
            self._start_block("text")
        elif tag == "pre":
            self._start_block("code")
        elif tag == "table":
            self.table_rows = []
        elif tag == "tr" and self.table_rows is not None:
            self.current_row = []
        elif tag in {"th", "td"} and self.current_row is not None:
            self.current_cell_parts = []
            self.current_cell_header = tag == "th"

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "dd", "dt", "pre"}:
            self._flush_block()
        elif tag in {"th", "td"} and self.current_row is not None and self.current_cell_parts is not None:
            cell_text = collapse_ws(unescape("".join(self.current_cell_parts)))
            self.current_row.append((cell_text, self.current_cell_header))
            self.current_cell_parts = None
        elif tag == "tr" and self.table_rows is not None and self.current_row is not None:
            if any(cell for cell, _ in self.current_row):
                self.table_rows.append(self.current_row)
            self.current_row = None
        elif tag == "table" and self.table_rows is not None:
            table_text = render_table(self.table_rows)
            if table_text:
                self.blocks.append(Block(kind="text", text=table_text))
            self.table_rows = None

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.current_cell_parts is not None:
            self.current_cell_parts.append(data)
        else:
            self._append_text(data)

    def _start_block(self, kind: str, level: int = 0) -> None:
        self._flush_block()
        self.current_kind = kind
        self.current_level = level
        self.current_parts = []

    def _append_text(self, data: str) -> None:
        if self.current_kind is None:
            return
        self.current_parts.append(data)

    def _flush_block(self) -> None:
        if self.current_kind is None:
            return
        raw = "".join(self.current_parts)
        if self.current_kind == "code":
            text = raw.strip("\n")
        else:
            text = collapse_ws(unescape(raw))
        if text:
            self.blocks.append(Block(kind=self.current_kind, text=text, level=self.current_level))
        self.current_kind = None
        self.current_level = 0
        self.current_parts = []


def render_table(rows: list[list[tuple[str, bool]]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    normalized: list[list[str]] = []
    header_row_index: int | None = None
    for idx, row in enumerate(rows):
        texts = [cell for cell, _ in row]
        flags = [is_header for _, is_header in row]
        padded = texts + [""] * (width - len(texts))
        normalized.append(padded)
        if header_row_index is None and any(flags):
            header_row_index = idx
    if width == 0:
        return ""
    if header_row_index is None:
        headers = [f"col{i + 1}" for i in range(width)]
        data_rows = normalized
    else:
        headers = normalized[header_row_index]
        data_rows = normalized[:header_row_index] + normalized[header_row_index + 1 :]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in data_rows:
        if any(cell for cell in row):
            lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def decode_html(raw: bytes, content_type: str | None) -> str:
    candidates: list[str] = []
    if content_type:
        match = re.search(r"charset=([\w-]+)", content_type, re.IGNORECASE)
        if match:
            candidates.append(match.group(1))
    meta_match = re.search(br"<meta[^>]+charset=['\"]?([\w-]+)", raw, re.IGNORECASE)
    if meta_match:
        candidates.append(meta_match.group(1).decode("ascii", errors="ignore"))
    candidates.extend(["utf-8", "gb18030", "gbk"])
    seen: set[str] = set()
    for encoding in candidates:
        normalized = encoding.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        raw = response.read()
        content_type = response.headers.get("Content-Type")
    return decode_html(raw, content_type)


def trim_blocks(blocks: list[Block], start_markers: Iterable[str]) -> list[Block]:
    rendered = [block.render() for block in blocks if block.render()]
    if not rendered:
        return []
    start_index = 0
    markers = [marker for marker in start_markers if marker]
    if markers:
        for idx, text in enumerate(rendered):
            if any(marker in text for marker in markers):
                start_index = idx
                break
    end_index = len(rendered)
    for idx in range(start_index, len(rendered)):
        text = rendered[idx]
        if any(marker in text for marker in FOOTER_MARKERS):
            end_index = idx
            break
    deduped: list[str] = []
    for text in rendered[start_index:end_index]:
        if deduped and deduped[-1] == text:
            continue
        deduped.append(text)
    return [Block(kind="text", text=text) if not text.startswith("#") and not text.startswith("```") else Block(kind="text", text=text) for text in deduped]


def extract_markdown(html_text: str, spec: PageSpec, fetched_on: str) -> str:
    parser = MarkdownExtractor()
    parser.feed(html_text)
    parser.close()
    trimmed = trim_blocks(parser.blocks, spec.start_markers)
    body = "\n\n".join(block.text if block.text.startswith("#") or block.text.startswith("```") else block.text for block in trimmed)
    if not body.strip():
        body = collapse_ws(re.sub(r"<[^>]+>", " ", html_text))
    header = [
        f"# {spec.title}",
        "",
        f"- Official URL: {spec.url}",
        f"- Fetched On: {fetched_on}",
        f"- Tags: {', '.join(spec.tags)}",
        f"- Normalized Reference: {spec.normalized_reference}",
        f"- Conflict Priority: {spec.conflict_priority}",
        "",
        "## Extracted Content",
        "",
    ]
    return "\n".join(header) + body.strip() + "\n"


def build_source_map(skill_dir: Path, specs: Iterable[PageSpec], fetched_on: str) -> str:
    lines = [
        "# XtQuant Source Map",
        "",
        f"- Fetched On: {fetched_on}",
        "- Conflict priority: `1` is highest authority, `4` is lowest.",
        "- Resolution rule: prefer the newest dated entry in `download_xtquant.html`, then module pages, then examples/dictionaries, then FAQ pages.",
        "",
        "| Slug | Title | Tags | Conflict Priority | Official URL | Local Snapshot | Normalized Reference |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for spec in specs:
        snapshot_path = f"references/raw/{spec.slug}.md"
        lines.append(
            f"| `{spec.slug}` | {spec.title} | {', '.join(spec.tags)} | {spec.conflict_priority} | {spec.url} | `{snapshot_path}` | `{spec.normalized_reference}` |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Raw snapshots are extracted Markdown, not a byte-for-byte HTML mirror.")
    lines.append("- Keep the repo copy as the source of truth; use `scripts/install_xtquant_skill.ps1` to deploy to `~/.codex/skills`.")
    return "\n".join(lines) + "\n"


def resolve_skill_dir(cli_value: str | None) -> Path:
    if cli_value:
        return Path(cli_value).resolve()
    return Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Refresh official xtquant reference snapshots.")
    parser.add_argument("--skill-dir", help="Path to the xtquant skill directory.")
    parser.add_argument(
        "--include-inner-core",
        action="store_true",
        help="Also fetch the xtquant-relevant built-in Python core pages.",
    )
    args = parser.parse_args(argv)

    skill_dir = resolve_skill_dir(args.skill_dir)
    refs_dir = skill_dir / "references"
    raw_dir = refs_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    specs = list(BASE_SPECS)
    if args.include_inner_core:
        specs.extend(INNER_CORE_SPECS)

    fetched_on = dt.date.today().isoformat()
    failures: list[str] = []
    for spec in specs:
        try:
            html_text = fetch_html(spec.url)
            markdown = extract_markdown(html_text, spec, fetched_on)
            (raw_dir / f"{spec.slug}.md").write_text(markdown, encoding="utf-8")
            print(f"[OK] {spec.slug}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{spec.slug}: {exc}")
            print(f"[ERR] {spec.slug}: {exc}", file=sys.stderr)

    source_map = build_source_map(skill_dir, specs, fetched_on)
    (refs_dir / "source-map.md").write_text(source_map, encoding="utf-8")
    print(f"[OK] source-map.md ({len(specs)} entries)")

    if failures:
        print("\nRefresh completed with failures:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
