# 内置 Python 行情函数

当问题涉及 `ContextInfo.get_market_data_ex`、内置 Python 订阅、下载、财务读取、引用函数与 `xtdata` 的关系时，读本文件。

## 核心接口
- 下载：
  - `download_history_data`
- 行情：
  - `ContextInfo.get_market_data_ex`
  - `ContextInfo.get_full_tick`
  - `ContextInfo.subscribe_quote`
  - `ContextInfo.subscribe_whole_quote`
  - `ContextInfo.unsubscribe_quote`
- 模型：
  - `subscribe_formula`
  - `unsubscribe_formula`
  - `call_formula`
  - `call_formula_batch`

## 财务
- `ContextInfo.get_financial_data`
- `ContextInfo.get_raw_financial_data`
- 以及常见财务字段表与辅助函数

## 与原生 `xtdata` 的关系
- 内置 Python 和原生 `xtdata` 共享很多概念，但调用入口不同。
- 回答“这段 `xtdata` 代码能不能改成内置 Python”时：
  - 先保留“下载 / 订阅 / 读取”三段结构
  - 再把入口改成 `ContextInfo.*`

## 回答策略
- 如果用户问内置 Python 的实时行情为什么没触发，先查是否在 `init` 里正确订阅，是否依赖 `handlebar` / 回调驱动。
- 如果用户问 `ContextInfo.get_local_data` 或 `get_history_data`，可指出文档里把它们标成“不推荐”。

## 原始资料
- `../raw/inner-data-function.md`
