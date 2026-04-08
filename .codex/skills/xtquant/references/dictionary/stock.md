# 股票数据

当问题涉及股票基础信息、财务、订单流、资金流向、问董秘、北向南向、交易日历或股票字段表时，读本文件。

## 基础信息
- 核心入口是 `xtdata.get_instrument_detail(stock_code)`。
- 页面给了非常完整的字段表，包含 `ExchangeID`、`InstrumentID`、`InstrumentName`、`ProductType`、`OpenDate`、`ExpireDate`、`UpStopPrice`、`DownStopPrice`、`FloatVolume`、`TotalVolume`、`PriceTick` 等。
- 文档写明该信息“每交易日 9 点更新”。

## 历史与实时
- 股票行情仍遵循 `download_history_data` + `subscribe_quote` + `get_market_data_ex` 的三段式。
- 对标准 K 线，`fill_data=True` 可用于缺口填充。

## 财务
- 原生 Python：`xtdata.get_financial_data` / `xtdata.download_financial_data`
- 内置 Python：`ContextInfo.get_financial_data` / `ContextInfo.get_raw_financial_data`
- 财务分表包括：
  - 资产负债表
  - 利润表
  - 现金流量表
  - 股本表
  - 主要指标
  - 十大股东 / 十大流通股东
  - 股东数

## 这页还能回答
- 资金流向
- 订单流
- 龙虎榜
- 北向 / 南向资金与持股
- 交易所公告
- ST 历史
- 交易日历

## 回答策略
- 只要用户问“某个字段是什么意思”，优先把字段名、类型、含义从这页说清楚。
- 若用户问“股票和别的资产共用哪些接口”，要说明 `get_instrument_detail` 是跨资产的通用入口之一。

## 原始资料
- `../raw/dictionary-stock.md`
