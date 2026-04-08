# 内置 Python 变量约定

当问题涉及 `symbol_code`、运行模式、账号类型、`ContextInfo` 常用属性、主连 / 加权连续合约时，读本文件。

## 代码与账号
- 迅投统一代码格式：`code.market`，例如 `000001.SZ`
- 常见账号类型：
  - `STOCK`
  - `FUTURE`

## 运行模式
- 文档定义了四种模式：
  - 调试运行模式
  - 回测模式
  - 模拟信号模式
  - 实盘交易模式
- 回答“为什么看到了信号却没真实下单”时，先确认是不是还在模拟信号模式。

## 主连与加权连续
- 期货主力连续合约和加权连续合约都主要面向回测。
- 文档明确说主连是简单拼接、未做平滑；加权连续更平滑。

## 高频 `ContextInfo` 属性
- `ContextInfo.start` / `ContextInfo.end`
- `ContextInfo.capital`
- `ContextInfo.period`
- `ContextInfo.barpos`
- `ContextInfo.time_tick_size`
- `ContextInfo.stockcode`
- `ContextInfo.market`
- `ContextInfo.dividend_type`
- `ContextInfo.benchmark`
- `ContextInfo.do_back_test`

## 回答策略
- 用户问“当前周期 / 当前 bar / 当前市场 / 当前复权方式是什么”时，优先从这些属性回答。
- 用户问“某段代码为什么在回测和实盘行为不同”，先确认运行模式。

## 原始资料
- `../raw/inner-variable-convention.md`
