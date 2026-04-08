# Linux版xtquant快速开始指南

- Official URL: https://dict.thinktrader.net/nativeApi/Linux%E7%89%88xtquant%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B%E6%8C%87%E5%8D%97.html
- Fetched On: 2026-04-03
- Tags: native, linux, xtdata-only
- Normalized Reference: references/native/linux.md
- Conflict Priority: 2

## Extracted Content
## # 所需环境

### # 1.下载xtquant的linux版压缩包

提示

Linux版需要用户权限为投研专业版及以上

Linux环境下仅支持数据获取功能(xtdata)，不支持交易(xttrade)

用户中心在新窗口打开

若您的账号拥有所需权限

您将在 用户中心 -> 下载中心 看到如下页面

### # 2.解压并配置路径

压缩包内的文件结构基本如下图所示

linux下新建一xtquant文件夹，将压缩包内全部文件解压至xtquant中。

将xtquant文件夹加入python搜索目录。

### # 3.Python版本选择

所支持的版本将于包名中显式列出

如：

支持python3.6，3.7，3.8，3.9，3.10，3.11，3.12

### # 4.linux系统版本

## # 常见问题

无法找到xtquant模块

请检查python搜索目录是否包含xtquant文件夹

无法打开动态库

在确保符合所需环境的要求后，如仍出现该问题，也许与您所使用的复杂环境相关，可尝试以下方法解决：

方法1.手动将压缩包中.libs文件夹下的文件拷贝至 系统根目录下的 /lib 或 /lib64 中（推荐） 方法2.export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/test/linux_pack/xtquan/.libs

数据接口无法返回数据

请检查系统时间是否校准，在确保时间正常后重新获取数据。
