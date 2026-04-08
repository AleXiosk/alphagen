# 数据字典首页

- Official URL: https://dict.thinktrader.net/dictionary/
- Fetched On: 2026-04-03
- Tags: dictionary, overview
- Normalized Reference: references/dictionary/overview.md
- Conflict Priority: 3

## Extracted Content
基础用法 - 获取数据

进阶用法 - 数据服务

3.如何在投研端中使用

更新日志

2023.11

2023.11.01

2023.11.21

2023.11.22

2023.12

2023.12.07

2023.12.08

2023.12.14

2023.12.20

2023.12.25

2024.01.05

股票数据

行业概念数据

指数数据

期货数据

期权数据

场内基金

债券数据

常见问题

场景化示例

迅投因子

数据浏览器

## # 概述

欢迎使用迅投数据服务！本数据字典为您在使用过程中提供相关指导，您可以通过搜索相关数据，找到对应的描述、用法、参数、返回、示例。

如果您是 QMT 基础行情用户，遇到相关问题的时候，请查阅VIP 行情用户优势对比，找到对应问题描述，如没有对应内容，可联系客服反馈。

如果您想成为 VIP 行情用户，请查阅VIP 行情用户-购买流程，进行购买。

如果您已经是 VIP 行情用户，请查阅VIP 行情用户-使用流程，学习使用。

其他问题，欢迎您联系客服反馈。

## # VIP 行情用户优势对比

### # 通用功能对比

| 数据类型 | 券商版权限 | 基础版权限 | 投研版权限 |
| --- | --- | --- | --- |
| 仿真交易权限 | 不支持 | 支持所有品种：股票、期货、期权 | 支持所有品种：股票、期货、期权 |
| Python交易权限 | 支持 | 支持 | 支持 |
| 图表交易权限 | 不支持 | 不支持 | 支持 |
| 直连期货交易 | 不支持 | 不支持 | 支持 |
| 高级 VBA、Python 函数 | 不支持 | 不支持 | 支持 |
| 专属微信组工程师指导 | 不支持 | 不支持 | 支持 |
|  |  |  | VIP行情权限 |
| 行情数量 | 100 个限制 | 100 个限制 | 300个限制 |
| 盘口档位 | 最高 1 档 | 仅最新价 | 最高 5 档 |
| 品种 | 只支持股票 | 只支持股票 | 支持所有品种：股票、期货 |
| 下载数据-历史范围 | 5m-1年1m-1年tick-1个月 | 5m-1年1m-1年tick-1个月 | 5m-3年1m-3年tick-1年 |
| 下载数据-流速 | 限制 | 限制 | 无限制 |
| 期权 | 不支持 | 不支持 | 需购买开通权限 |
| 因子数据 | 不支持 | 不支持 | 需购买开通权限 |
| 北向、资金流、沪港通数据在新窗口打开 | 不支持 | 不支持 | 支持 |
| 行业、商品指数行情数据在新窗口打开 | 不支持 | 不支持 | 支持 |
| 现货、仓单、席位数据在新窗口打开 | 不支持 | 不支持 | 支持 |
| 可转债数据在新窗口打开 | 不支持 | 不支持 | 支持 |
| ETF申赎清单数据在新窗口打开 | 不支持 | 不支持 | 需购买开通权限 |

### # 行情站点对比

普通行情使用的行情站点与VIP行情也有区别，更换VIP行情站点，能够带来更好的行情体验，添加方式如下：

#### # VIP行情站点

| 地点 | 网址 | 端口 |
| --- | --- | --- |
| VIP迅投绍兴电信 | vipsxmd1.thinktrader.net | 55310 |
| VIP迅投绍兴电信 | vipsxmd2.thinktrader.net | 55310 |
| VIP迅投郑州联通 | ltzzmd2.thinktrader.net | 55300 |
| VIP迅投郑州联通 | ltzzmd1.thinktrader.net | 55300 |
| VIP迅投郑州电信 | dxzzmd1.thinktrader.net | 55300 |
| VIP迅投郑州电信 | dxzzmd2.thinktrader.net | 55300 |

| 地点 | IP地址 | 端口 |
| --- | --- | --- |
| VIP迅投绍兴电信 | 115.231.218.73 | 55310 |
| VIP迅投绍兴电信 | 115.231.218.79 | 55310 |
| VIP迅投郑州联通 | 42.228.16.211 | 55300 |
| VIP迅投郑州联通 | 42.228.16.210 | 55300 |
| VIP迅投郑州电信 | 36.99.48.20 | 55300 |
| VIP迅投郑州电信 | 36.99.48.21 | 55300 |

#### # 普通行情站点

| 地点 | 网址 | 端口 |
| --- | --- | --- |
| 迅投浦东电信 | shmd1.thinktrader.net | 55300 |
| 迅投浦东电信 | shmd2.thinktrader.net | 55300 |
| 迅投东莞电信 | szmd1.thinktrader.net | 55300 |
| 迅投东莞电信 | szmd2.thinktrader.net | 55300 |

| 地点 | IP地址 | 端口 |
| --- | --- | --- |
| 迅投浦东电信 | 43.242.96.162 | 55300 |
| 迅投浦东电信 | 43.242.96.164 | 55300 |
| 迅投东莞电信 | 218.16.123.121 | 55300 |
| 迅投东莞电信 | 218.16.123.122 | 55300 |

## # 如何成为 VIP 行情用户

### # 购买流程

#### # 步骤一：注册登录

在迅投研官网在新窗口打开使用手机号注册你的投研账号。

提示

记录好你的密码，后续会很重要

#### # 步骤二：购买权限

登录你的投研账号，访问投研服务页面在新窗口打开，选择行情用户 VIP，并支付。

支付方式支持微信支付、支付宝以及对公转账，其中对公转账信息如下：

公司名：成都睿智融科科技有限公司

账户号：4402235009000153959

开户行：中国工商银行成都高新城南支行

#### # 步骤三：查看权限

支付成功后，你就可以在个人中心在新窗口打开看到您的服务已经开启相应时长的使用权限

### # 使用流程

#### # 1.如何在券商 QMT 中使用

登录你的券商 QMT 后，点击行情，进入行情面板

找到迅投行情主站（包括北京、上海、东莞等），点击修改

在弹窗中将用户名和密码修改为自己的投研账号密码，点击确认

点击链接，即可在券商 QMT 中使用行情用户 VIP 权限

执行以上同样的操作，找到迅投资管行情，点击修改

最后，点击右上角全推行情，在下拉框中选择五档全推

提示

第五步，若不修改迅投资管行情的账号密码，不设置将无法收到五档全推

第六步，若不修改全推行情，也无法收到五档全推

操作演示

#### # 2.如何使用 Token

在你的迅投研官网的个人中心在新窗口打开，迅投投研服务平台 - 用户中心 - 个人设置 - 接口 TOKEN ，找到你的接口 TOKEN

接口 TOKEN 一次生成一个，刷新后前一个 TOKEN 失效（刷新有间隔限制，请勿频繁刷新）

接口 TOKEN 具体用法如下：

##### # 下载指定 xtquant 包

提示

请提前下载指定 xtquant 包，

Windows:下载链接在新窗口打开 或在cmd窗口中运行指令

```text
pip install xtquant -i https://pypi.tuna.tsinghua.edu.cn/simple
```

##### # 基础用法 - 获取数据

```text
# 导入 xtdatacenter 模块
from xtquant import xtdatacenter as xtdc  
  
'''  
设置用于登录行情服务的token，此接口应该先于 init_quote 调用

token可以从投研用户中心获取
https://xuntou.net/#/userInfo
'''  
xtdc.set_token('这里输入token')
  
'''  
设置数据存储根目录，此接口应该先于 init_quote 调用  
datacenter 启动后，会在 data_home_dir 目录下建立若干目录存储数据  
此接口不是必须调用，如果不设置，会使用默认路径
'''  
# xtdc.set_data_home_dir('data') 

'''
函数用法可通过以下方式查看：
'''
# print(help(xtdc.set_data_home_dir))  
  
'''  
初始化行情模块  
'''  
xtdc.init()

'''
初始化需要一定时间，完成后即可按照数据字典的对应引导使用
'''

# 导入 xtdata
from xtquant import xtdata  

# 获取交易日期
tdl = xtdata.get_trading_dates('SH')  
print(tdl[-10:])  

# 获取板块列表
sl = xtdata.get_stock_list_in_sector('沪深A股')  
print(sl[::100])  

# 输出平安银行的相关信息 
data = xtdata.get_instrument_detail("000001.SZ")  
print(data)

# 其他数据获取的方法请参考数据字典：http://dict.thinktrader.net/dictionary/stock.html  
```

```text
[1697558400000, 1697644800000, 1697731200000, 1697990400000, 1698076800000, 1698163200000, 1698249600000, 1698336000000, 1698595200000, 1698681600000]

['000001.SZ', '000507.SZ', '000652.SZ', '000809.SZ', '000961.SZ', '001336.SZ', '002087.SZ', '002191.SZ', '002294.SZ', '002395.SZ', '002505.SZ', '002608.SZ', '002715.SZ', '002826.SZ', '002935.SZ', '003043.SZ', '300107.SZ', '300211.SZ', '300316.SZ', '300425.SZ', '300528.SZ', '300630.SZ', '300735.SZ', '300840.SZ', '300945.SZ', '301050.SZ', '301168.SZ', '301291.SZ', '301487.SZ', '600101.SH', '600222.SH', '600351.SH', '600496.SH', '600611.SH', '600732.SH', '600846.SH', '600995.SH', '601360.SH', '601919.SH', '603088.SH', '603220.SH', '603380.SH', '603638.SH', '603826.SH', '605003.SH', '605499.SH', '688101.SH', '688215.SH', '688330.SH', '688500.SH', '688629.SH']

{'ExchangeID': 'SZ', 'InstrumentID': '000001', 'InstrumentName': '平安银行', 'ProductID': '', 'ProductName': '', 'ExchangeCode': '000001', 'UniCode': '000001', 'CreateDate': '0', 'OpenDate': '19910403', 'ExpireDate': 99999999, 'PreClose': 10.450000000000001, 'SettlementPrice': 10.450000000000001, 'UpStopPrice': 11.5, 'DownStopPrice': 9.41, 'FloatVolume': 19405546950.0, 'TotalVolume': 19405918198.0, 'LongMarginRatio': 1.7976931348623157e+308, 'ShortMarginRatio': 1.7976931348623157e+308, 'PriceTick': 0.01, 'VolumeMultiple': 1, 'MainContract': 2147483647, 'LastVolume': 2147483647, 'InstrumentStatus': 0, 'IsTrading': False, 'IsRecent': False, 'ProductTradeQuota': -1582372688, 'ContractTradeQuota': -476598553, 'ProductOpenInterestQuota': -1662614912, 'ContractOpenInterestQuota': -1582504276}
```

##### # 进阶用法 - 数据服务

当您已经实现基础用法，成功获取数据后，随即可能会有新的需求：

如果我有多个策略，在不同进程中运行，都要获取数据，而 Token 只支持单点访问，该怎么办？

我们同样提供数据服务，您可以在一个进程中启动数据服务，其他进程连接该数据服务，实现您想要的效果，具体演示如下：

进程 1

```text
    ### 进程1 启动xtdatacenter监听

    from xtquant import xtdatacenter as xtdc

    xtdc.set_token('这里输入token')

    print('xtdc.init')
    xtdc.init() # 初始化行情模块，加载合约数据，会需要大约十几秒的时间
    print('done')

    # 为其他进程的xtdata提供服务时启动server，单进程使用不需要
    print('xtdc.listen')
    listen_addr = xtdc.listen(port = 58610)
    print(f'done, listen_addr:{listen_addr}')

    from xtquant import xtdata
    print('running')
    xtdata.run() #循环，维持程序运行
```

```text
xtdc.init

done
xtdc.listen
done, listen_addr:('0.0.0.0', 58610)
running
```

进程 2

```text
from xtquant import xtdata
'''
连接数据服务指定的端口
'''
xtdata.connect(port=58610)


# 以下即可正常执行获取数据的操作
tdl = xtdata.get_trading_dates('SH')
print(tdl[-10:])

sl = xtdata.get_stock_list_in_sector('沪深A股')
print(sl[::100])

# 结合数据字典：http://dict.thinktrader.net/dictionary/stock.html

# 输出平安银行信息的中文名称
data = xtdata.get_instrument_detail("000001.SZ")
print(data)
```

```text
[1698249600000, 1698336000000, 1698595200000, 1698681600000, 1698768000000, 1698854400000, 1698940800000, 1699200000000, 1699286400000, 1699372800000]
['000001.SZ', '000507.SZ', '000652.SZ', '000809.SZ', '000961.SZ', '001333.SZ', '002086.SZ', '002190.SZ', '002293.SZ', '002394.SZ', '002502.SZ', '002607.SZ', '002714.SZ', '002825.SZ', '002933.SZ', '003042.SZ', '300106.SZ', '300210.SZ', '300315.SZ', '300424.SZ', '300527.SZ', '300629.SZ', '300733.SZ', '300839.SZ', '300943.SZ', '301049.SZ', '301167.SZ', '301290.SZ', '301486.SZ', '600100.SH', '600221.SH', '600350.SH', '600495.SH', '600610.SH', '600731.SH', '600845.SH', '600993.SH', '601339.SH', '601918.SH', '603086.SH', '603217.SH', '603377.SH', '603633.SH', '603822.SH', '603998.SH', '605398.SH', '688098.SH', '688211.SH', '688327.SH', '688496.SH', '688626.SH']
{'ExchangeID': 'SZ', 'InstrumentID': '000001', 'InstrumentName': '平安银行', 'ProductID': '', 'ProductName': '', 'ExchangeCode': '000001', 'UniCode': '000001', 'CreateDate': '0', 'OpenDate': '19910403', 'ExpireDate': 99999999, 'PreClose': 10.6, 'SettlementPrice': 10.6, 'UpStopPrice': 11.66, 'DownStopPrice': 9.540000000000001, 'FloatVolume': 19405546950.0, 'TotalVolume': 19405918198.0, 'LongMarginRatio': 1.7976931348623157e+308, 'ShortMarginRatio': 1.7976931348623157e+308, 'PriceTick': 0.01, 'VolumeMultiple': 1, 'MainContract': 2147483647, 'LastVolume': 2147483647, 'InstrumentStatus': 0, 'IsTrading': False, 'IsRecent': False, 'ProductTradeQuota': 0, 'ContractTradeQuota': 0, 'ProductOpenInterestQuota': 6, 'ContractOpenInterestQuota': 0}
```

遇到问题，请参考常见问题Token 使用相关

#### # 3.如何在投研端中使用

购买投研端的用户默认拥有行情用户 VIP 权限，且已经自动配置好

投研端的用户可以在券商 QMT 中使用，具体参考如何在券商 QMT 中使用

投研端的用户同样可以在后台找到接口 TOKEN，具体参考如何使用 Token

## # 更新日志

### # 2023.11

#### # 2023.11.01

更新 快速开始

补充可转债数据字段

优化部分描述

#### # 2023.11.21

更新K线全推示例

更新界面操作-独立python进程

新添加get_trade_detail_data - POSITION_STATISTICS结构

#### # 2023.11.22

增加常见pandas问题及处理方案

### # 2023.12

#### # 2023.12.07

新增历史涨跌停价数据

新增历史ST数据下载方式

新增获取历史期权合约方法

更新财务数据获取方式

修正 get_etf_info 示例

#### # 2023.12.08

优化文档显示内容

#### # 2023.12.14

新增 TOP10HOLDER/TOP10FLOWHOLDER - 十大股东/十大流通股东

新增 SHAREHOLDER - 股东数

#### # 2023.12.20

修复文档描述错误

#### # 2023.12.25

增加get_etf_info字段描述

优化VIP行情对比

#### # 2024.01.05

增加回测复权方式说明

增加openInt变化状态说明

优化文档显示内容

股票数据
