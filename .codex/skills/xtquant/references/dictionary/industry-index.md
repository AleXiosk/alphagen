# 行业、板块与指数

当问题涉及板块列表、板块成分、过期板块、行业分类、指数合约列表、指数权重时，读本文件。

## 行业 / 板块
- 先下载板块分类信息：`xtdata.download_sector_data()`
- 若要历史过期板块或退市标的相关信息，先 `xtdata.download_history_contracts()`
- 主要接口：
  - `xtdata.get_sector_list()`
  - `xtdata.get_stock_list_in_sector(sector_name)`
- 官方示例覆盖了这些名称模式：
  - 指数板块：`沪深300`
  - 概念板块：`GN上海`
  - 申万行业：`SW1汽车`
  - 过期板块：`过期上证A股`

## 指数
- 获取指数合约列表的套路是：
  1. `xtdata.get_sector_list()`
  2. `xtdata.get_stock_list_in_sector('沪深指数')`
- 获取指数成分权重：
  - 先确保板块 / 权重数据已下载
  - 再 `xtdata.get_index_weight(index_code)`
- 页面还给了“迅投一级行业板块加权指数”相关示例。

## 行情模式
- 指数行情同样走 `download_history_data` + `subscribe_quote` + `get_market_data_ex`
- 指数权重属于静态 / 半静态信息，先下载再查

## 回答时的边界
- 用户如果问“为什么板块为空”，优先查是否未执行 `download_sector_data()`。
- 用户如果问“过期 / 退市板块”，优先提醒 `download_history_contracts()`。

## 原始资料
- `../raw/dictionary-industry.md`
- `../raw/dictionary-indexes.md`
