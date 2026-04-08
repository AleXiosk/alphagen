# 原生 Python `xtdata`

当问题涉及行情、交易日、合约、板块、财务、历史下载、实时订阅、`get_market_data_ex`、`xtdata.run()` 时，读本文件。

## 核心规则
- `xtdata` 本质上是和 MiniQMT 建立连接，由客户端处理行情请求后再回传给 Python。
- 对“读取型接口”，先确保本地已有对应数据；没有就先 `download_*`。
- 对“订阅型接口”，数据到来后经回调返回；要保持进程活着，通常需要 `xtdata.run()`。

## 三类动作不要混淆
- `download_history_data(...)`：补本地历史行情；同步执行。
- `subscribe_quote(...)` / `subscribe_whole_quote(...)`：订阅实时流。
- `get_market_data_ex(...)`：读取数据；对标准行情会自动拼接本地历史与实时数据。

## 标准用法
- Level1 历史部分：`download_history_data`
- Level1 实时部分：`subscribe_*`
- 统一读取：`get_market_data_ex`
- Level2：只有实时订阅与读取，没有稳定历史持久化；跨交易日后会清理。

## 高频回答模板
- “为什么取不到历史 K 线”：先确认是否已经 `download_history_data(...)`。
- “为什么订阅后程序立即退出”：用了回调但没阻塞主线程，应该 `xtdata.run()`。
- “为什么 1m K 线有缺口”：`fill_data=True` 只适用于标准 K 线，不适用于特色数据。
- “为什么切站点后要不要重订阅”：`xtquant.xtdata` 侧通常不用，除非连接真的断开；内置 Python 侧需要重新订阅。

## 重点接口
- 行情：`subscribe_quote`、`unsubscribe_quote`、`subscribe_whole_quote`、`get_full_tick`
- 读取：`get_market_data_ex`、`get_local_data`
- 历史补数：`download_history_data`、`download_history_data2`
- 财务：`get_financial_data`、`download_financial_data`
- 合约与基础信息：`get_instrument_detail`、`get_instrument_type`
- 板块与指数权重：`get_sector_list`、`get_stock_list_in_sector`、`download_sector_data`、`get_index_weight`
- 交易日与节假日：`get_trading_dates`、`get_trading_calendar`、`download_holiday_data`

## 已知重要版本点
- `2023-11-09`：`download_history_data` 增加增量下载参数。
- `2024-01-19`：`get_market_data_ex` 支持 `1w`、`1mon`、`1q`、`1hy`、`1y`。
- `2024-05-15`：新增 `get_full_kline()`。
- `2025-05-16`：`xtdata` 获取函数支持 `datetime` 时间范围，`get_market_data()` / `get_market_data_ex()` 支持 ATM 市场，`get_instrument_detail()` 新增 `TradingDay` 等更新。

## 回答时要主动提醒
- 历史数据先下载，实时数据先订阅。
- `get_market_data_ex` 是主路径；除非用户明确需要旧接口，不要优先推荐 `get_market_data` / `get_local_data`。
- `xtdata` 问题里，“客户端当前是否有数据、是否登录正确、是否切到正确服务器”经常比 Python 代码本身更关键。

## 原始资料
- `../raw/native-xtdata.md`
- `../raw/native-code-examples.md`
- `../raw/dictionary-scenario-based-example.md`
- `../raw/dictionary-question-answer.md`
