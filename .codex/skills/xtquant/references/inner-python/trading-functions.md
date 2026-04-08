# 内置 Python 交易函数

当问题涉及 `passorder`、`quickTrade`、`algo_passorder`、`smart_algo_passorder`、`get_trade_detail_data`、`get_value_by_order_id` 时，读本文件。

## 最重要的接口
- `passorder`：综合下单函数，最常见
- `algo_passorder`：拆单 / 算法交易
- `smart_algo_passorder`：智能算法单（如 VWAP）
- `get_trade_detail_data`：查账号、委托、成交、持仓等
- `get_value_by_order_id`：按委托号取委托或成交

## `quickTrade` 语义
- `0`：默认；只在 K 线结束有效
- `1`：当前 bar 为最新 bar 时，运行到就触发
- `2`：不判断 bar 状态，运行到就触发；历史 bar 也可能触发，必须谨慎
- 在 `after_init`、定时器回调、行情回调、交易回调里下单时，FAQ 明确建议传 `2`

## `userOrderId` / 投资备注
- 如果传了 `userOrderId`，通常也应同时给出 `strategyName` 与 `quickTrade`
- 它会出现在委托 / 成交对象里，可用于状态跟踪

## 查询类接口怎么讲
- `get_trade_detail_data` 常用于按账号取 `order` / `deal` / `position` / `account`
- `strategyName` 可用于过滤本地策略名对应的子集
- `get_value_by_order_id` 适合按单号追踪状态

## 回答策略
- 用户如果想把内置 `passorder` 翻成原生 `xttrader`，不要只翻函数名；要把 `quickTrade` 的触发时机一起翻译成事件驱动逻辑。
- 用户如果问“为什么明明执行了 `passorder` 却没委托”，先查运行模式，再查 `quickTrade`。

## 原始资料
- `../raw/inner-trading-function.md`
- `../raw/inner-question-answer.md`
