# 因子与数据浏览器

当问题涉及迅投因子、因子公式、`download_metatable_data`、`get_metatable_list`、BARRA 表、`download_tabular_data`、宽表转长表时，读本文件。

## 迅投因子
- 先更新元表：`xtdata.download_metatable_data()`
- 再拿中英文映射：`xtdata.get_metatable_list()`
- 下载某类因子时，常用流程是把中文分类名反转成英文表名，再 `download_history_data(...)`
- Python 侧读取常见路径：
  - `{安装目录}\\datadir\\EP\\{factor_name}_Xdat2\\data.fe`
- 因子公式里常用：
  - `EXTDATA2`
  - `EXTDATARANK2`
  - `EXTDATABLOCKRANK2`

## 数据浏览器
- 数据浏览器覆盖清洗后的财务和 BARRA 等高级数据。
- 常见流程：
  1. `download_metatable_data()`
  2. `get_metatable_list()`
  3. `download_tabular_data(...)`
  4. `get_tabular_data(...)`
- `get_tabular_data` 常返回宽表；官方示例明确建议用 `melt` 转成长表。
- 因子中英文映射表 `CNE1D_100_Factors` 很关键，回答时可以主动提示。

## 回答策略
- 用户问“某个因子表名是什么”，优先让 `get_metatable_list()` 成为入口。
- 用户问“为什么 DataFrame 列很多、像宽表”，直接提醒官方推荐做 `melt`。
- 用户问“能否在公式里直接取因子值/排名”，优先给 `EXTDATA2` / `EXTDATARANK2` / `EXTDATABLOCKRANK2`。

## 原始资料
- `../raw/dictionary-xuntou-factor.md`
- `../raw/dictionary-data-browser.md`
