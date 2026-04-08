# 场内基金与债券

当问题涉及 ETF 申赎清单、IOPV、基金实时申赎、场内基金 tick、可转债基础信息、转股价或转债行情时，读本文件。

## 场内基金
- 基础信息仍可用 `xtdata.get_instrument_detail(stock_code)`。
- ETF 相关重点接口：
  - `xtdata.get_etf_info()`
  - `get_etf_iopv(stock_code)`
  - `period='etfstatistics'` 的实时申赎数据
- 场内基金 tick 数据仍遵循：
  - 先 `subscribe_quote(...)` 取实时
  - 历史部分可 `download_history_data(...)`
  - 再 `get_market_data_ex(...)`

## 债券 / 可转债
- 可转债信息需要：
  1. `xtdata.download_cb_data()`
  2. `xtdata.get_cb_info(bond_code)`
- 官方明确说明这部分是 VIP 权限函数。
- `get_cb_info` 可回答：
  - 正股代码 / 名称
  - 转股起止日
  - 初始 / 最新转股价
  - 强赎价格 / 触发价
  - 到期赎回价
  - 纯债 YTM
- 转债行情读取也沿用通用 `xtdata` 行情模式，支持 `tick`、`1m`、`1d` 等周期。

## 回答策略
- 用户问“转债最新转股价 / 强赎价 / 到期赎回价”时，优先指向 `get_cb_info`。
- 用户问“ETF 成分股、申赎篮子、IOPV”时，优先指向基金页，不要误导到通用股票字段表。

## 原始资料
- `../raw/dictionary-floorfunds.md`
- `../raw/dictionary-bond.md`
