---
name: alphagen-csi300-data
description: "AlphaGen 项目 CSI300/CSI500 指数数据准备技能，覆盖历史指数成分提取、按交易日回放成分快照、压缩为区间、生成 instruments_csi300.csv 或 instruments_csi500.csv、用 baostock+xtquant 混合拉取行情，以及历史成分验证与常见坑。Use when the task mentions AlphaGen, CSI300, CSI500, 沪深300, 中证500, 历史指数成分, 成分股区间, instruments_csi300.csv, instruments_csi500.csv, fetch_xtquant_data.py, research_hs300_constituents.py, or wants project-specific index data prep."
---

# AlphaGen Index Data

默认用中文回答。

这个 skill 只针对当前仓库的 AlphaGen 指数数据准备实现，不要假设别的 AlphaGen fork 也有同样的脚本和输出结构。

## 先读这两个脚本
- `data_collection/research_hs300_constituents.py`
- `data_collection/fetch_xtquant_data.py`

## 路由顺序
1. 用户要“确认/研究/回放”历史指数成分，先看 `research_hs300_constituents.py`。
2. 用户要“真正生成 csi300/csi500 数据目录、stocks CSV、Qlib instruments”，先看 `fetch_xtquant_data.py`。
3. 用户想判断 `xtquant` 历史板块快照是否可信，先跑 `research_hs300_constituents.py`，再决定是否允许 `--constituent-source xtquant`。

## 强制规则
- 历史指数成分默认来源是 `baostock`，不是 `xtquant`。
- `xtquant` 在这个项目里主要负责：
  - `xtdata.get_trading_calendar()` 提供交易日历
  - 行情和因子数据拉取
  - 可选的板块历史快照研究与验证
- 只有在 `research_hs300_constituents.py` 验证通过后，才允许把 `xtquant` 用作 `--constituent-source xtquant`。
- 如果 `run_summary.json` 里：
  - `empty_snapshot_days > 0`
  - `failed_days_after_retries` 非空
  - `consistency_issue_count > 0`
  就不要直接相信该段历史成分结果。
- 代码格式必须分清：
  - `baostock`: `sh.600000` / `sz.000001`
  - `xtquant`: `<symbol>.<market>`，例如 `600000.SH`
  - `qlib`: `SH600000` / `SZ000001`
- 增量更新必须沿用 `fetch_xtquant_data.py` 的锚点逻辑，不要手工拼接旧区间：
  - `anchor_date = calendar_day.txt` 最后一个交易日
  - 从 `anchor_date` 重新回放成分快照并重算区间
  - 旧区间只保留 `end_datetime < anchor_date`

## 推荐工作流

### 1. 先研究和验证历史成分
使用 `data_collection/research_hs300_constituents.py`。

这个脚本会：
- 调 `xtdata.download_sector_data()` 和 `xtdata.get_sector_list()` 解析板块名
- 调 `xtdata.get_trading_calendar("SH", ...)` 枚举交易日
- 对每个交易日调用 `xtdata.get_stock_list_in_sector(sector_name, real_timetag=trade_date)`
- 比较相邻快照，输出变化点和稳定 period 区间

推荐命令：

```powershell
python .\data_collection\research_hs300_constituents.py `
  --sector-name 沪深300 `
  --start-date 2011-01-01 `
  --end-date 2026-04-06 `
  --output-dir .\outputs\hs300_constituents_full
```

重点检查这些输出：
- `periods.csv`: 每个稳定成分区间
- `period_members.csv`: 每个 period 的成员清单
- `changes.csv`: 换入换出日期与代码
- `daily_snapshot_summary.csv`: 每个交易日的成员数和成员哈希
- `run_summary.json`: 总体统计、空快照、失败日期、一致性问题

判定标准：
- `empty_snapshot_days == 0`
- `failed_days_after_retries` 为空
- `consistency_issue_count == 0`
- `periods.csv` 的 `n_members` 合理
- `changes.csv` 的变更日期和频率符合指数调样常识

### 2. 再生成生产用指数数据目录
使用 `data_collection/fetch_xtquant_data.py`。

CSI300 默认命令：

```powershell
python .\data_collection\fetch_xtquant_data.py `
  --sector-name 沪深300 `
  --start-date 2011-01-01 `
  --end-date 2026-04-06 `
  --constituent-source baostock `
  --out-root .\data\xtquant_csi300 `
  --mode full `
  --dump-qlib
```

CSI500 对应命令：

```powershell
python .\data_collection\fetch_xtquant_data.py `
  --sector-name 中证500 `
  --universe-name csi500 `
  --start-date 2011-01-01 `
  --end-date 2026-04-06 `
  --constituent-source baostock `
  --out-root .\data\xtquant_csi500 `
  --mode full `
  --dump-qlib
```

这个脚本会：
- 用 `baostock` 或 `xtquant` 回放每个交易日的指数成分快照
- 用 `compress_snapshots_to_intervals()` 压缩成 `code,start_datetime,end_datetime`
- 按 universe 写出 `meta/instruments_<universe>.csv`
- 拉取 `stocks/*.csv`
- 可选写出 Qlib `instruments/<universe>.txt`

增量更新命令：

```powershell
python .\data_collection\fetch_xtquant_data.py `
  --sector-name 沪深300 `
  --start-date 2011-01-01 `
  --end-date 2026-04-06 `
  --constituent-source baostock `
  --out-root .\data\xtquant_csi300 `
  --mode incremental
```

生产输出主要看：
- `data/xtquant_csi300/meta/instruments_csi300.csv`
- `data/xtquant_csi300/meta/calendar_day.txt`
- `data/xtquant_csi300/meta/symbols.txt`
- `data/xtquant_csi300/meta/manifest.json`
- `data/xtquant_csi300/stocks/*.csv`
- `data/xtquant_csi500/meta/instruments_csi500.csv`
- `data/xtquant_csi500/meta/calendar_day.txt`
- `data/xtquant_csi500/meta/symbols.txt`
- `data/xtquant_csi500/meta/manifest.json`
- `data/xtquant_csi500/stocks/*.csv`

## 历史指数成分提取的核心实现

### 研究脚本的实现思路
- 以交易日历为基准，不按自然日遍历。
- 对每个交易日抓一份成分快照。
- 把快照排序并做哈希，方便检测成分是否变化。
- 相邻交易日快照不同，就记一个 change point。
- 把连续相同的快照压成一个 `period`，这样最终得到稳定区间而不是逐日冗余表。

### 生产脚本的实现思路
- 先回放整段历史快照。
- 再在 `compress_snapshots_to_intervals()` 里维护一个 `active` 字典：
  - 股票新加入时，记录开始日期
  - 股票移出时，用上一交易日作为结束日期关闭区间
- 最后把仍然活跃的股票区间补到最后一个交易日
- 输出为 Qlib 需要的 `code,start_datetime,end_datetime`

## 已知结论与坑
- 仓库内现有 smoke 结果已经证明：`xtquant` 能解析出板块名，不等于它能可靠回放整段历史成分。
- 具体证据在：
  - `outputs/hs300_constituents_smoke/run_summary.json`
  - `outputs/hs300_constituents_smoke/daily_snapshot_summary.csv`
- 该 smoke 输出显示，`2026-03-30` 到 `2026-04-03` 这 5 个交易日 `empty_snapshot_days=5`，全部是空快照。
- 因此这个项目里默认推荐：
  - `baostock` 负责历史指数成分
  - `xtquant` 负责交易日历与行情数据
- `research_hs300_constituents.py` 对空快照的策略是记录 warning 并保留空快照，适合研究覆盖问题。
- `fetch_xtquant_data.py` 对空快照的策略是直接报错，适合生产流程尽早失败。
- `baostock` 这套实现只内置支持：
  - `沪深300`
  - `上证50`
  - `中证500`
- 如果要扩别的指数，先补 `BAOSTOCK_QUERY_BY_SECTOR_NAME`，再决定是否保留 `xtquant` fallback。
- 不要跳过 `calendar_day.txt`，区间边界必须由交易日历决定。

## 快速决策
- 用户要“最稳地拿历史 CSI300/CSI500 成分”：用 `fetch_xtquant_data.py --constituent-source baostock`
- 用户要“研究 xtquant 板块历史是否可信”：用 `research_hs300_constituents.py`
- 用户要“解释 instruments 区间为什么不对”：先查 `compress_snapshots_to_intervals()` 和 `merge_incremental_intervals()`
- 用户要“解释为什么成分快照为空”：先查 `daily_snapshot_summary.csv` 和 `run_summary.json`

## 关键文件
- `data_collection/research_hs300_constituents.py`
- `data_collection/fetch_xtquant_data.py`
- `outputs/hs300_constituents_smoke/run_summary.json`
- `outputs/hs300_constituents_smoke/daily_snapshot_summary.csv`
