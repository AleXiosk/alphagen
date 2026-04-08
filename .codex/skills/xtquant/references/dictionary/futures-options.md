# 期货与期权

当问题涉及期货市场代码、主力连续、仓单、席位、期权列表、期权详情、商品期权 / ETF 期权 / 股指期权时，读本文件。

## 期货
- 市场代码映射：
  - `SHFE -> SF`
  - `DCE -> DF`
  - `CZCE -> ZF`
  - `CFFEX -> IF`
  - `INE -> INE`
  - `GFEX -> GF`
- 主要能力：
  - 获取交易日历
  - 获取当前所有期货代码
  - 获取合约基础信息
  - 获取当前主力合约 / 历史主力合约
  - 获取日线、tick、盘口、结算价与持仓量
  - 仓单：`period='warehousereceipt'`
  - 席位：`period='futureholderrank'`
- 历史主力合约数据要先 `download_history_data(..., period='historymaincontract')`，再 `get_market_data_ex(...)`

## 期权
- 页面同时覆盖内置 Python 与原生 Python。
- 主要能力：
  - 获取指定标的对应的期权品种列表
  - 获取期权合约列表
  - 获取期权详情
  - 获取期权行情
  - 获取过期期权合约代码
  - 获取期权全推数据
  - 期权 VIX
- BSM 定价与隐含波动率在内置 Python 页面里也有示例。
- 最新数据通常先订阅，历史数据先下载，再 `get_market_data_ex(...)`。

## 回答策略
- 只要涉及“商品期权 / 股指期权 / ETF 期权是否支持”，优先说明 `get_option_detail_data` 与版本页近两年持续在扩展这一块。
- 只要涉及“主连 / 加权连续”，区分原生 `xtdata` 与内置 Python 回测语义，不要直接混答。

## 原始资料
- `../raw/dictionary-future.md`
- `../raw/dictionary-option.md`
- `../raw/native-download-xtquant.md`
