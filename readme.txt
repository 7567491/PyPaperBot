[![捐赠](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/ferru97)

# 新闻：PyPaperBot 开发重启！
### 加入 [Telegram](https://t.me/pypaperbotdatawizards) 频道以获取更新、报告错误或请求自定义数据挖掘脚本。
---

# PyPaperBot

PyPaperBot 是一个使用 Google Scholar、Crossref、SciHub 和 SciDB 来**下载学术论文和 bibtex** 的 Python 工具。
该工具尝试从不同来源下载论文，如 Scholar 提供的 PDF、Scholar 相关链接和 Scihub。
PyPaperbot 还能下载每篇论文的 **bibtex** 信息。

## 功能特点

- 根据查询下载论文
- 根据论文 DOI 下载论文
- 根据 Google Scholar 链接下载论文
- 生成已下载论文的 Bibtex
- 按年份、期刊和引用次数筛选下载的论文

## 安装方法

### 普通用户

使用 `pip` 从 pypi 安装：

```bash
pip install PyPaperBot
```

如果在 Windows 上遇到 *error: Microsoft Visual C++ 14.0 is required..* 错误，请尝试安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/it/visual-cpp-build-tools/) 或 [Visual Studio](https://visualstudio.microsoft.com/it/downloads/)

### Termux 用户

由于无法直接安装 numpy....

```bash
pkg install wget
wget https://its-pointless.github.io/setup-pointless-repo.sh
pkg install numpy
export CFLAGS="-Wno-deprecated-declarations -Wno-unreachable-code"
pip install pandas
```

然后：

```bash
pip install PyPaperBot
```

## 使用方法

PyPaperBot 参数：

| 参数                        | 描述                                                                                                                                                                              | 类型   |
|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| \-\-query                   | 在 Google Scholar 上搜索的查询词或 Google Scholar 页面链接                                                                                                                        | string |
| \-\-cites                   | 论文 ID（从搜索引用时 scholar 地址栏获取），用于仅获取该论文的引用                                                                                                              | string |
| \-\-doi                     | 要下载论文的 DOI（此选项仅使用 SciHub 下载）                                                                                                                                     | string |
| \-\-doi-file                | 包含要下载论文 DOI 列表的 .txt 文件                                                                                                                                              | string |
| \-\-scholar-pages           | 要检查的 Google Scholar 页面数量或范围。每页最多显示 10 篇论文                                                                                                                   | string |
| \-\-dwn-dir                 | 保存结果的目录路径                                                                                                                                                               | string |
| \-\-min-year                | 要下载论文的最早发表年份                                                                                                                                                         | int    |
| \-\-max-dwn-year            | 按年份排序要下载的最大论文数量                                                                                                                                                   | int    |
| \-\-max-dwn-cites           | 按引用次数排序要下载的最大论文数量                                                                                                                                               | int    |
| \-\-journal-filter          | 期刊过滤器的 CSV 文件路径（更多信息请参见 github）                                                                                                                              | string |
| \-\-restrict                | 0：仅下载 Bibtex - 1：仅下载论文 PDF                                                                                                                                             | int    |
| \-\-scihub-mirror           | 从 sci-hub 下载论文的镜像网站。如果未设置，将自动选择                                                                                                                           | string |
| \-\-annas-archive-mirror    | 从 Annas Archive (SciDB) 下载论文的镜像网站。如果未设置，将使用 https://annas-archive.se                                                                                    | string |
| \-\-scholar-results         | 当 \-\-scholar-pages=1 时要下载的 scholar 结果数量                                                                                                                               | int    |
| \-\-proxy                   | 要使用的代理。请指定要使用的协议                                                                                                                                                 | string |
| \-\-single-proxy            | 使用单个代理。如果使用 --proxy 出现错误，建议使用此选项                                                                                                                         | string |
| \-\-selenium-chrome-version | 机器上安装的 Chrome 版本的前三位数字。如果提供，将使用 selenium 进行 scholar 搜索。这有助于避免机器人检测，但必须安装 Chrome                                                   | int    |
| \-\-use-doi-as-filename     | 如果提供，文件将使用唯一的 DOI 作为文件名，而不是默认的论文标题                                                                                                                 | bool   |
| \-h                         | 显示帮助信息                                                                                                                                                                      | --     |

### 注意事项

以下参数组中只能使用其中一个：

- *\-\-query*、*\-\-doi-file* 和 *\-\-doi*
- *\-\-max-dwn-year* 和 *\-\-max-dwn-cites*

*\-\-scholar-pages*、*\-\-query* 和 *\-\-file* 中必须使用其中一个
使用 *\-\-query* 时必须指定 *\-\-scholar-pages*
*\-\-dwn-dir* 参数是必需的

*\-\-journal-filter* 参数需要一个 CSV 文件路径，该文件包含期刊名称列表，每个期刊名称都配对一个布尔值，表示是否考虑该期刊（0：不考虑/1：考虑）[示例](https://github.com/ferru97/PyPaperBot/blob/master/file_examples/jurnals.csv)

*\-\-doi-file* 参数需要一个 txt 文件路径，该文件包含要下载的论文 DOI 列表，每行一个 DOI [示例](https://github.com/ferru97/PyPaperBot/blob/master/file_examples/papers.txt)

在使用所有其他参数后使用 --proxy 参数，并指定要使用的协议。请参考示例以了解如何使用该选项。

## SciHub 访问

如果您所在的国家屏蔽了 SciHub 访问，请考虑使用免费的 VPN 服务，如 [ProtonVPN](https://protonvpn.com/)
另外，您也可以使用上述代理选项。

## 使用示例

使用镜像 https://sci-hub.do 从前 3 页中下载最多 30 篇 2018 年之后的论文：

```bash
python -m PyPaperBot --query="Machine learning" --scholar-pages=3  --min-year=2018 --dwn-dir="C:\User\example\papers" --scihub-mirror="https://sci-hub.do"
```

下载第 4 到第 7 页（包含第 7 页）的论文：

```bash
python -m PyPaperBot --query="Machine learning" --scholar-pages=4-7 --dwn-dir="C:\User\example\papers"
```

根据 DOI 下载论文：

```bash
python -m PyPaperBot --doi="10.0086/s41037-711-0132-1" --dwn-dir="C:\User\example\papers" -use-doi-as-filename
```

根据包含 DOI 的文件下载论文：

```bash
python -m PyPaperBot --doi-file="C:\User\example\papers\file.txt" --dwn-dir="C:\User\example\papers"
```

如果不起作用，请尝试使用 *py* 替代 *python*，例如：

```bash
py -m PyPaperBot --doi="10.0086/s41037-711-0132-1" --dwn-dir="C:\User\example\papers"
```

搜索引用某篇论文的文章（在搜索引用时从 scholar 地址栏找到 ID）：

```bash
python -m PyPaperBot --cites=3120460092236365926
```

使用代理：

```bash
python -m PyPaperBot --query=rheumatoid+arthritis --scholar-pages=1 --scholar-results=7 --dwn-dir=/download --proxy="http://1.1.1.1::8080,https://8.8.8.8::8080"
```
```bash
python -m PyPaperBot --query=rheumatoid+arthritis --scholar-pages=1 --scholar-results=7 --dwn-dir=/download -single-proxy=http://1.1.1.1::8080
```

在 termux 中，您可以直接使用 ```PyPaperBot``` 后跟参数...

## 贡献

欢迎在 **dev** 分支上提出任何更改、修复和改进建议

### 待办事项

文件结构
PyPaperBot/
├── LICENSE                     # MIT许可证文件
├── README.md                   # 项目说明文档
├── setup.py                    # 包安装配置文件
├── requirements.txt            # 项目依赖列表
├── file_examples/              # 示例文件目录
│   ├── journals.csv           # 期刊过滤器示例文件
│   └── papers.txt             # DOI列表示例文件
│
├── PyPaperBot/                # 主程序包目录
│   ├── __init__.py            # 包初始化文件
│   ├── __main__.py            # 程序入口点
│   ├── Downloader.py          # 论文下载核心实现
│   ├── Paper.py               # 论文对象模型定义
│   ├── PaperFilters.py        # 论文过滤器实现
│   ├── Searcher.py            # 搜索功能实现
│   ├── Scholar.py             # Google Scholar交互实现
│   ├── CrossRefConnector.py   # CrossRef API连接器
│   ├── Proxy.py               # 代理服务器管理
│   └── Errors.py              # 自定义错误类定义
│
└── tests/                     # 测试目录
    ├── __init__.py            # 测试包初始化
    ├── test_downloader.py     # 下载功能测试
    ├── test_paper.py          # 论文对象
    └── test_searcher.py       # 搜索功能测试

根据以下功能，使用Streamlit开发一个Web应用，整体使用暗色主题

一级功能使用左侧边栏，功能使用按钮，按钮白色，黄色边框，不填充
二级功能使用Tab，Tab文字为白色
右侧边栏显示详细的系统日志，根据不同类型日志显示不同颜色

功能设计：论文搜索功能

1.一级功能：搜索协调与管理
文件：Searcher.py
功能：整合所有搜索来源，协调搜索流程，管理搜索结果缓存，提供统一的搜索接口
二级功能：Google Scholar搜索
文件：Scholar.py
功能：实现Google Scholar页面爬取，处理搜索结果解析，管理反爬虫策略，支持Selenium模式
二级功能：CrossRef查询
文件：CrossRefConnector.py
功能：通过CrossRef API获取论文元数据，解析DOI信息，处理API访问限制

2. 论文下载功能
一级功能：下载管理
文件：Downloader.py
功能：管理多源下载流程，处理下载重试，保存文件，错误恢复
二级功能：代理管理
文件：Proxy.py
功能：配置代理服务器，管理代理池，自动切换代理，验证代理有效性

3. 论文过滤功能
一级功能：过滤器管理
文件：PaperFilters.py
功能：管理和协调所有过滤规则，提供过滤器组合接口
二级功能：具体过滤器
文件：PaperFilters.py的子类
功能：
年份过滤器
引用次数过滤器
期刊名称过滤器
自定义规则过滤器

4. 论文数据管理
一级功能：论文对象管理
文件：Paper.py
功能：定义论文数据结构，管理论文元数据
二级功能：数据处理
文件：Paper.py的方法
功能：
生成bibtex
文件命名规则处理
元数据格式化
数据验证

5. 程序控制功能
一级功能：主程序控制
文件：__main__.py
功能：程序入口点，参数解析，主流程控制
二级功能：错误处理
文件：Errors.py
功能：
定义异常类型
错误信息管理
异常处理流程
用户反馈生成

6. 配置管理功能
一级功能：全局配置
文件：分散在各模块中
功能：管理全局参数，配置文件处理
二级功能：模块配置
文件：各个模块的配置部分
功能：
下载配置
搜索配置
代理配置
过滤器配置

7. 文件处理功能
一级功能：文件管理
文件：Downloader.py部分功能
功能：管理下载文件，处理文件保存
二级功能：文件操作
文件：分散在各模块中
功能：
文件读写
格式转换
临时文件管理
目录管理

8. 网络访问功能
一级功能：网络请求管理
文件：分散在各模块中
功能：管理所有网络请求，处理网络错误
二级功能：具体请求处理
文件：各个模块的网络访问部分
功能：
HTTP请求处理
会话管理
超时处理
重试机制