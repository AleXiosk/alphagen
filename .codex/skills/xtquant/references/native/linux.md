# Linux 指南

当问题涉及 Linux 安装、动态库、`xtdata` on Linux、是否支持交易时，读本文件。

## 关键结论
- Linux 版只支持数据获取功能 `xtdata`，不支持交易 `xttrade` / `xttrader`。
- 官方页面要求用户权限为“投研专业版及以上”。

## 环境要求
- Linux 指南页面写明支持 Python `3.6`-`3.12`。
- 这与版本页 `2025-05-16` 新增 Python `3.13` 支持并不完全一致；回答时要明确“Linux 指南仍写到 `3.12`”。

## 安装要求
- 新建一个 `xtquant` 目录，把 Linux 压缩包全部内容解压进去。
- 把该 `xtquant` 目录加入 Python 搜索路径。
- 如果报动态库打不开，官方给了两种方案：
  - 把 `.libs` 中的库手动复制到 `/lib` 或 `/lib64`
  - 或设置 `LD_LIBRARY_PATH`

## 常见问题
- 找不到 `xtquant` 模块：先查 Python 搜索路径。
- 无法打开动态库：优先查 `.libs` 与系统库路径。
- 数据接口无返回：先检查系统时间是否校准。

## 回答边界
- 用户问 Linux 下实盘交易时，不要给出 `xttrade` 或 `xttrader` 方案；要直接说明官方 Linux 指南只支持 `xtdata`。
- 若用户坚持 Linux 交易，只能说明这超出该官方页面支持范围。

## 原始资料
- `../raw/native-linux-guide.md`
- `../raw/native-download-xtquant.md`
