# 内置 Python 使用须知

当问题涉及 `ContextInfo`、`init` / `after_init` / `handlebar`、线程模型、`run script failed`、为什么状态会丢时，读本文件。

## 最重要的约束
- 不建议把长期状态存在 `ContextInfo` 自定义属性里。
- 官方明确说 `ContextInfo` 会随着 bar 切换回滚到上一根 bar 的结束状态。
- 如果没有完全理解这个机制，优先用普通全局变量或自建状态对象。

## 系统函数
- `init(ContextInfo)`：只在策略启动时跑一次；部分接口在它执行完成前不可用。
- `after_init(ContextInfo)`：在 `init` 之后、第一次 `handlebar` 之前调用一次；适合放一次性取数或立即下单逻辑。
- `handlebar(ContextInfo)`：历史阶段按 bar 顺序执行，实时阶段每个新 tick 都会驱动。
- 定时器相关：`ContextInfo.schedule_run`、`ContextInfo.cancel_schedule_run`、`ContextInfo.run_time`

## 线程 / 进程模型
- QMT 内置 Python 不能依赖多线程、多进程方案。
- 所有策略共享同一线程；任意策略阻塞都会拖住其他策略。
- 所以内置 Python 策略里不要写长期阻塞、死循环、长时间 `sleep`、重锁等待。

## 主图驱动
- 内置策略默认由主图 K 线 / 实时快照驱动。
- 盘中每个新的快照也会触发 `handlebar`。
- 需要过滤非最后一根 bar 时，用 `ContextInfo.is_last_bar()`。

## 常见运行问题
- 安装路径尽量不要放 `C:`；如果只能放 `C:`，按官方建议用管理员权限启动。
- `run script failed` 首先排查 Python 路径是否指向 `{安装目录}\\bin.x64` 一类的正确位置。

## 回答策略
- 只要用户问“为什么变量没保留”“为什么盘中逻辑反复触发”，先解释 `ContextInfo` 回滚和主图驱动。
- 只要用户问“能不能在内置 Python 里开多线程”，先回答官方限制，再给原生 xtquant 作为替代方向。

## 原始资料
- `../raw/inner-user-attention.md`
- `../raw/inner-system-function.md`
- `../raw/inner-question-answer.md`
