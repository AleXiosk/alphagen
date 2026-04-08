# 内置 Python FAQ

当问题涉及 `ContextInfo` 回滚、`quickTrade` 选值、为什么查不到最新委托、为什么不能阻塞、全推与订阅的区别时，读本文件。

## `ContextInfo` 回滚
- `ContextInfo` 是逐 bar 保存的，不是普通 Python 对象。
- 盘中每个分笔都会触发 `handlebar`，但只有 bar 结束时最后一次调用对 `ContextInfo` 的修改才会保留下来。
- 因此：
  - `ContextInfo` 不适合存“立刻生效”的盘中状态
  - 如果需要立即下单，FAQ 建议把状态放到普通全局变量里，并配合 `quickTrade=2`

## `quickTrade`
- FAQ 给出的场景化建议：
  - `handlebar` 逐 K 线下单：`0`
  - `handlebar` 盘中立刻下单：`1`
  - 定时器 / `init` / `after_init` / 回调里下单：`2`

## 查询与回报不是柜台即时真相
- 文档明确说 `get_trade_detail_data` 与四类交易回调都基于客户端本地缓存，不是“调用时直接查柜台”。
- 有交易主推的柜台大约 `50ms` 刷新一次；没有交易主推的柜台大约 `1-6` 秒刷新一次。
- 所以“刚卖出立刻查不到对应委托 / 资金没变”并不一定是下单失败。

## 线程限制
- QMT 所有策略在同一线程里执行。
- 任何阻塞都会拖住所有策略。
- 如果用户真的需要多线程 / 多进程方案，FAQ 直接建议考虑极简模式配合原生 `xtquant`。

## 原始资料
- `../raw/inner-question-answer.md`
