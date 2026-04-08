# 原生 Python 总览

当问题涉及 `xtdatacenter`、`xtdata`、`xttrader`、MiniQMT/QMT 连接、token、数据服务、环境兼容时，先读本文件。

## 先建立正确心智模型
- `xtquant` 原生 Python 依赖已启动的 MiniQMT / QMT 客户端。
- `xtdatacenter` 负责 token 模式、数据目录和对外提供数据服务。
- `xtdata` 负责行情、财务、合约、板块、交易日等数据读取。
- `xttrader` 负责交易 API、查询和交易回调。

## 环境与版本
- `references/raw/native-start-now.md` 写的是 64 位 Python `3.6`-`3.12`。
- `references/raw/native-question-function.md` 仍写 `3.6`-`3.11`，这是旧 FAQ。
- `references/raw/native-download-xtquant.md` 的 `2025-05-16` 条目明确写了 Python `3.13` 支持。
- 回答“最新支持哪个 Python”时，优先引用 `2025-05-16` 版本条目，并说明旧页面仍未完全同步。

## 连接方式
- 直连 MiniQMT：客户端登录后，原生 Python 直接连本机客户端。
- token 模式：先 `xtdc.set_token(...)`，再 `xtdc.init()`。
- 多进程数据服务：一个进程 `xtdc.listen(...)` + `xtdata.run()`；其他进程 `xtdata.connect(port=...)`。

## 路径与权限
- 极简版路径指向 `userdata_mini`，投研端路径指向 `userdata`。
- 装在 `C:` 时更容易遇到权限问题；官方 FAQ 建议避免安装到 `C:`，否则要用管理员权限运行。
- 同一个 `session` 的两次 Python 进程连接之间需要间隔至少 3 秒。

## 先去哪份文档
- 行情 / 订阅 / 历史补数：`xtdata.md`
- 交易 / 回调 / 下单 / 撤单 / 查询：`xttrader.md`
- 报错 / 版本 / 官方示例：`examples-faq-version.md`
- Linux：`linux.md`

## 原始资料
- `../raw/native-start-now.md`
- `../raw/native-question-function.md`
- `../raw/native-download-xtquant.md`
- `../raw/dictionary-home.md`
