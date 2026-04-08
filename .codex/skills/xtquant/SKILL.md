---
name: xtquant
description: "中文优先的 ThinkTrader/QMT/xtquant 参考技能，覆盖原生 Python 的 xtdatacenter、xtdata、xttrader，以及 xtquant 直接相关的内置 Python ContextInfo、行情函数、交易函数、quickTrade 与常见坑。Use when the task mentions xtquant, xtdata, xttrader, xtdatacenter, MiniQMT, QMT, ThinkTrader, ContextInfo, token/data-service setup, market data retrieval, trading APIs, built-in/native migration, Linux xtdata-only deployment, or xtquant troubleshooting."
---

# XtQuant

默认用中文回答，除非用户明确要求其他语言。

## 路由顺序
1. 先判断任务属于哪一类：
   - 原生 Python：`from xtquant import xtdatacenter, xtdata, xttrader`
   - 内置 Python：`ContextInfo`、`passorder`、`get_trade_detail_data`、`handlebar`
   - Linux 数据服务：Linux 环境、`xtdata` only、动态库问题
   - 混合迁移：把内置 Python / QMT 策略翻译成原生 Python，或反过来
2. 先读对应的人工整理参考，再按需打开 raw 快照：
   - 原生总览与安装：`references/native/overview.md`
   - 行情：`references/native/xtdata.md`
   - 交易：`references/native/xttrader.md`
   - 版本、FAQ、官方示例：`references/native/examples-faq-version.md`
   - Linux：`references/native/linux.md`
   - 数据字典导航：`references/dictionary/overview.md`
   - 内置 Python：`references/inner-python/*.md`
3. 需要精确字段、参数表、长示例、版本条目时，先查 `references/source-map.md`，再打开对应 `references/raw/*.md`。

## 强制规则
- 先引用本 skill 的本地参考，再补充官方 URL；不要只给外链。
- 文档冲突时按这个优先级处理：
  1. `references/raw/native-download-xtquant.md`
  2. 对应模块页，如 `native-xtdata.md`、`native-xttrader.md`
  3. 数据字典与内置 Python正文
  4. FAQ
- 处理版本冲突时必须写具体日期。
  - 当前已知关键冲突：
    - `start_now.html` 与 Linux 指南都写到 Python `3.6`-`3.12`
    - 原生 FAQ 仍写 `3.6`-`3.11`
    - 版本页 `2025-05-16` 条目明确写了 Python `3.13`
- 不要混淆三种行情动作：
  - `download_*`：把历史/静态数据补到本地
  - `subscribe_*`：订阅实时流/回调
  - `get_*`：从本地缓存或当前连接读取；`get_market_data_ex` 会拼接本地历史与实时数据
- 不要把内置 Python 和原生 Python 混为一谈：
  - 内置 Python 的 `ContextInfo` 有逐 bar 回滚语义
  - 内置 Python 的 `passorder` 受 `quickTrade` 影响
  - 原生 Python 的 `xttrader` 是独立的回调式交易 API
- Linux 指南只支持 `xtdata`，不支持交易 `xttrade` / `xttrader`。用户问 Linux 交易时要直接指出这一点。

## 工作流

### 1. 原生 Python
- 先用 `references/native/overview.md` 判断是 MiniQMT 直连、token 模式、还是 `xtdc.listen` 多进程数据服务。
- 行情问题读 `references/native/xtdata.md`。
- 交易问题读 `references/native/xttrader.md`。
- 报错、兼容性、版本差异读 `references/native/examples-faq-version.md`。

### 2. 数据字典
- 先用 `references/dictionary/overview.md` 判断属于股票、板块/指数、期货/期权、基金/债券、因子/数据浏览器、还是 FAQ/场景化示例。
- 字段级问题要落到具体子文件；如果用户要完整字段表，再开相应 raw 快照。

### 3. 内置 Python
- 先读 `references/inner-python/usage-notes.md`，确认线程模型、`ContextInfo` 回滚、`init/after_init/handlebar` 语义。
- 参数和上下文对象定义读 `references/inner-python/variable-conventions.md`。
- 行情函数读 `references/inner-python/data-functions.md`。
- 下单、查询、`passorder` / `quickTrade` 读 `references/inner-python/trading-functions.md`。
- 常见坑读 `references/inner-python/faq.md`。

### 4. 混合迁移
- 内置 Python -> 原生 Python：
  - 先保留“数据准备 / 行情驱动 / 下单触发 / 状态保存”四段逻辑
  - 把 `ContextInfo` 状态改为普通 Python 状态对象或全局状态
  - 把 `passorder` 映射成 `xttrader` 的报单/撤单/查询组合
  - 把 `quickTrade` 语义翻译成“何时真正下单”的控制逻辑，不要机械一一映射
- 原生 Python -> 内置 Python：
  - 先确认是否真的需要 `ContextInfo`
  - 明确哪些逻辑必须在 `after_init` 或回调里执行
  - 明确 `passorder` 的 `quickTrade` 取值，否则很容易漏单或只在 bar 结束时发单

## 关键参考
- 索引：`references/source-map.md`
- 原生总览：`references/native/overview.md`
- 行情：`references/native/xtdata.md`
- 交易：`references/native/xttrader.md`
- 版本与 FAQ：`references/native/examples-faq-version.md`
- Linux：`references/native/linux.md`
- 数据字典导航：`references/dictionary/overview.md`
- 内置 Python 注意事项：`references/inner-python/usage-notes.md`

## 刷新与安装
- 重新抓官方页面并更新 raw 快照：
  - `python scripts/refresh_xtquant_refs.py --skill-dir <skill-dir> --include-inner-core`
- 安装到全局 skill 目录：
  - `powershell -File scripts/install_xtquant_skill.ps1 -Source <repo-skill-dir> -Target <global-skill-dir>`
- 这个仓库里的 skill 是唯一真源。全局目录只做部署，不要反向修改。
