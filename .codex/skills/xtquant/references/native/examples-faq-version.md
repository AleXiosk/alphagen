# 原生 Python 示例、FAQ 与版本变更

当问题涉及“官方怎么写”“这个版本支持吗”“为什么连接失败 / 端口占用 / remark 被截断”“该引用哪个版本说明”时，读本文件。

## 权威顺序
1. `../raw/native-download-xtquant.md`
2. `../raw/native-xtdata.md` / `../raw/native-xttrader.md`
3. `../raw/native-code-examples.md`
4. `../raw/native-question-function.md`

## 必须记住的版本冲突
- `../raw/native-start-now.md`：写 Python `3.6`-`3.12`
- `../raw/native-linux-guide.md`：也写 Python `3.6`-`3.12`
- `../raw/native-question-function.md`：旧 FAQ 仍写 `3.6`-`3.11`
- `../raw/native-download-xtquant.md`：`2025-05-16` 条目写“支持 Python `3.13`”

回答兼容性问题时，用这句话式样：
- “按 `2025-05-16` 的版本下载页条目，xtquant 已支持 Python `3.13`；但快速开始与 Linux 指南页面仍写到 `3.12`，原生 FAQ 甚至还停留在 `3.11`，这些旧页没有完全同步。”

## 常见报错处理
- `NO module named 'xtquant.IPythonAPiClient'`
  - 先检查 Python 大版本是否在官方支持范围内，再检查是否 64 位。
- 连接失败返回 `-1`
  - 先检查客户端是否已启动且登录正确
  - 再检查路径是否指向 `userdata_mini` / `userdata`
  - 再检查 `session` 是否冲突、是否小于 3 秒重复连接
  - 再检查是否因安装在 `C:` 导致权限问题
- `xtdc.init` 监听 `58609` 失败
  - 常见原因是已有另一个 `xtdc` 进程占了默认端口
  - 解决路径是 `xtdc.init(False)` + `xtdc.listen(port=...)`

## 官方示例里值得复用的模式
- token 模式 + 固定端口 / 端口范围监听
- `xtdc.set_allow_optmize_address(...)` 优选站点
- `xtdc.set_kline_mirror_markets(...)` 开启指定市场 K 线全推
- 交易回调里配合宽松时序线程做查询
- 断线重连示例仅供参考，官方明确提醒“不是线程安全的”

## 回答风格要求
- 版本问题必须带日期。
- FAQ 问题先给“最小可执行排查顺序”，再补原因。
- 如果用户贴的是老示例，主动指出它可能对应旧版本行为。

## 原始资料
- `../raw/native-download-xtquant.md`
- `../raw/native-question-function.md`
- `../raw/native-code-examples.md`
- `../raw/native-start-now.md`
