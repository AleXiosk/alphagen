# 原生 Python `xttrader`

当问题涉及下单、撤单、查询、交易回调、`XtQuantTrader` 生命周期、宽松时序、资金划拨或银证转账时，读本文件。

## 核心模型
- `xttrader` 是回调优先的交易 API，不是“请求后立刻拿到最终柜台状态”的同步 RPC。
- 正确流程通常是：
  1. 创建 `XtQuantTrader(path, session_id)`
  2. 注册 `XtQuantTraderCallback`
  3. 启动交易线程 / 建立连接
  4. 订阅账号
  5. 报单、撤单、查询
  6. 通过回调追踪结果

## 路径、账号、会话
- MiniQMT 用 `userdata_mini`，投研端用 `userdata`。
- 不同 Python 策略要使用不同 `session_id`。
- 同一个 `session` 的两次 Python 进程连接需要间隔至少 3 秒。

## 同步 / 异步接口
- 同步：`order_stock`、`cancel_order_stock`
- 异步：`order_stock_async`、`cancel_order_stock_async`
- 查询：`query_asset`、`query_orders`、`query_trades`、`query_positions`、`query_data`
- 导出：`export_data`，`query_data` 实际上是“导出后读回再删除临时文件”

## 回调必须覆盖的重点
- `on_disconnected`
- `on_account_status`
- `on_stock_order`
- `on_stock_trade`
- `on_order_error`
- `on_cancel_error`
- `on_order_stock_async_response`

## 时序与缓存
- 交易推送与查询依赖客户端本地缓存，不保证与柜台绝对同步。
- 如果在交易回调里直接做查询，可能卡住回调线程；可以开启 `XtQuantTrader.set_relaxed_response_order_enabled`，但会引入更宽松、也更不确定的时序。
- 回答“为什么查不到刚下的单 / 资金没立刻变化”时，要先指出缓存刷新与推送时序问题。

## 常见坑
- 极简版 `order_remark` 长度限制：最多 24 个英文字符，中文按 3 字节计；超出会被截断。
- 如果 `userdata_mini` 下没有 `up_queue_xtquant`，通常是券商没给该账号开通下单权限。
- `down_queue` 文件大量增长，通常和频繁换 `session` 有关。

## 版本重点
- `2025-05-16`：增加银证转账、银行卡流水、期货与期权资金划转、北交所支持、交易对象字段扩展。
- `2022-11-28`：`set_relaxed_response_order_enabled` 引入。

## 原始资料
- `../raw/native-xttrader.md`
- `../raw/native-code-examples.md`
- `../raw/native-question-function.md`
