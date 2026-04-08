# FAQ 与场景化示例

当问题涉及 token 刷新、K 线缺失、站点切换后是否要重订阅、数据何时完整、盘前准备、市场状态判断时，读本文件。

## 高频 FAQ
- token 失效并更换后：
  - 需要让 `xtdatacenter` 用新 token 重新连行情
  - 下游 `xtdata` 会断开
  - 断开重连后需要重新订阅
- K 线缺失：
  - `get_market_data_ex` 取标准 K 线时可以 `fill_data=True`
  - 特色数据不适用这个填充逻辑
- 切行情站点后要不要重订阅：
  - 内置 Python：要
  - `xtquant.xtdata`：通常不用，除非连接断开

## 官方给出的时间点
- 大部分股票在 `15:00` 左右收盘，尾盘竞价后完整行情通常要延后几秒，官方示例给到大约 `15:00:03`
- 如果需要创业板 / 科创板盘后定价交易数据，等到 `15:30` 后
- 期货通常 `15:00` 后有收盘价，`16:30` 左右有结算价

## 场景化示例
- 判断市场状态并抓最新分钟 K 线：
  - 订阅 `subscribe_whole_quote`
  - 用最新 tick 时间判断是否到了分钟线收束时点
  - 再 `get_full_kline`
- 盘前准备：
  - 判断交易日是否切换
  - `download_sector_data()`
  - `download_history_contracts()`
  - 更新财务与历史 K 线
- 交易时段过滤：
  - 官方示例给了股票 / 期货的时间段判断样式

## 回答策略
- 这类问题优先给“执行顺序”，不是只解释概念。
- 如果用户要写批量更新脚本，这页和 `native/xtdata.md` 一起看。

## 原始资料
- `../raw/dictionary-question-answer.md`
- `../raw/dictionary-scenario-based-example.md`
