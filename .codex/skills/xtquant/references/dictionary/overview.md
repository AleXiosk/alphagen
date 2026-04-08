# 数据字典导航

当问题是“这个字段在哪页”“某类资产应该查哪个文档”“token 模式如何在数据字典路线下初始化”时，先读本文件。

## 数据字典首页能解决什么
- token 初始化与基础数据获取
- 多进程数据服务：`xtdc.listen(...)` + 其他进程 `xtdata.connect(...)`
- 资产类别导航：股票、行业概念、指数、期货、期权、场内基金、债券
- FAQ 与场景化示例
- 迅投因子与数据浏览器

## 首页的高频模式
- 基础用法：
  - `xtdc.set_token(...)`
  - 可选 `xtdc.set_data_home_dir(...)`
  - `xtdc.init()`
  - 再用 `xtdata` 取交易日、板块、合约信息
- 多进程数据服务：
  - 进程 1：`xtdc.listen(port=...)` + `xtdata.run()`
  - 进程 2：`xtdata.connect(port=...)`

## 导航
- 股票与通用证券字段：`stock.md`
- 板块、行业、指数：`industry-index.md`
- 期货、期权：`futures-options.md`
- 场内基金、债券：`fund-bond.md`
- 因子、数据浏览器：`factors-data-browser.md`
- FAQ、场景化示例：`faq-scenarios.md`

## 回答时要主动提醒
- 数据字典很多页面默认也沿用“先下载 / 再订阅 / 再读取”的 `xtdata` 模式。
- 数据字典页经常把“原生 Python”和“内置 Python”混排；回答时先说明当前示例属于哪一类。

## 原始资料
- `../raw/dictionary-home.md`
- `../source-map.md`
