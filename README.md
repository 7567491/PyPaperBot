新闻：PyPaperBot 开发重新启动！
加入 Telegram 频道以获取最新更新、报告错误或请求自定义数据挖掘脚本。
PyPaperBot
PyPaperBot 是一个使用 Google Scholar、Crossref、SciHub 和 SciDB 来下载科学论文和 bibtex 的 Python 工具。
该工具尝试从不同来源下载论文，如 Scholar 提供的 PDF、Scholar 相关链接和 Scihub。
PyPaperbot 还能下载每篇论文的 bibtex。

功能特点
根据查询下载论文
根据论文 DOI 下载论文
根据 Google Scholar 链接下载论文
生成已下载论文的 Bibtex
按年份、期刊和引用次数过滤下载的论文
安装
普通用户
使用 pip 从 pypi 安装：

复制
pip install PyPaperBot
如果在 Windows 上遇到错误提示 error: Microsoft Visual C++ 14.0 is required..，请尝试安装 Microsoft C++ Build Tools 或 Visual Studio

Termux 用户
由于 numpy 无法直接安装....

复制
pkg install wget
wget https://its-pointless.github.io/setup-pointless-repo.sh
pkg install numpy
export CFLAGS="-Wno-deprecated-declarations -Wno-unreachable-code"
pip install pandas
然后

复制
pip install PyPaperBot
使用方法
PyPaperBot 参数：

参数	描述	类型
--query	在 Google Scholar 上进行的查询或 Google Scholar 页面链接	string
--cites	论文 ID（从搜索引用时 scholar 地址栏获取），如果你只想获取该论文的引用	string
--doi	要下载的论文的 DOI（此选项仅使用 SciHub 下载）	string
--doi-file	包含要下载的论文 DOI 列表的 .txt 文件	string
--scholar-pages	要检查的 Google Scholar 页面数量或范围。每页最多 10 篇论文	string
--dwn-dir	保存结果的目录路径	string
--min-year	要下载的论文的最小发表年份	int
--max-dwn-year	按年份排序要下载的最大论文数量	int
--max-dwn-cites	按引用次数排序要下载的最大论文数量	int
--journal-filter	期刊过滤器的 CSV 文件路径（更多信息请参见 github）	string
--restrict	0:仅下载 Bibtex - 1:仅下载论文 PDF	int
--scihub-mirror	从 sci-hub 下载论文的镜像。如果未设置，将自动选择	string
--annas-archive-mirror	从 Annas Archive (SciDB) 下载论文的镜像。如果未设置，将使用 https://annas-archive.se	string
--scholar-results	当 --scholar-pages=1 时要下载的 scholar 结果数量	int
--proxy	要使用的代理。请指定要使用的协议	string
--single-proxy	使用单个代理。如果使用 --proxy 出现错误，建议使用此选项	string
--selenium-chrome-version	机器上安装的 chrome 版本的前三位数字。如果提供，将使用 selenium 进行 scholar 搜索。这有助于避免机器人检测，但必须安装 chrome	int
--use-doi-as-filename	如果提供，文件将使用唯一的 DOI 作为文件名，而不是默认的论文标题	bool
-h	显示帮助	--
注意
以下组中只能使用其中一个参数

--query、--doi-file 和 --doi
--max-dwn-year 和 max-dwn-cites
--scholar-pages、--query 和 --file 参数中必须使用其中一个
使用 --query 时，--scholar-pages 参数是必需的
--dwn-dir 参数是必需的

--journal-filter 参数需要一个 CSV 文件的路径，该文件包含期刊名称列表，每个期刊名称都配对一个布尔值，表示是否考虑该期刊（0：不考虑/1：考虑）示例

--doi-file 参数需要一个 txt 文件的路径，该文件包含要下载的论文 DOI 列表，每行一个 DOI 示例

在所有其他参数之后使用 --proxy 参数，并指定要使用的协议。请参见示例以了解如何使用该选项。

SciHub 访问
如果在您的国家被禁止访问 SciHub，请考虑使用免费的 VPN 服务，如 ProtonVPN
此外，您也可以使用上述代理选项。

示例
根据查询从前 3 页下载最多 30 篇 2018 年之后的论文，使用镜像 https://sci-hub.do：

复制
python -m PyPaperBot --query="Machine learning" --scholar-pages=3  --min-year=2018 --dwn-dir="C:\User\example\papers" --scihub-mirror="https://sci-hub.do"
根据查询下载第 4 到第 7 页（包括第 7 页）的论文：

复制
python -m PyPaperBot --query="Machine learning" --scholar-pages=4-7 --dwn-dir="C:\User\example\papers"
根据 DOI 下载论文：

复制
python -m PyPaperBot --doi="10.0086/s41037-711-0132-1" --dwn-dir="C:\User\example\papers" -use-doi-as-filename`
根据包含 DOI 的文件下载论文：

复制
python -m PyPaperBot --doi-file="C:\User\example\papers\file.txt" --dwn-dir="C:\User\example\papers"`
如果不起作用，请尝试使用 py 而不是 python，例如：

复制
py -m PyPaperBot --doi="10.0086/s41037-711-0132-1" --dwn-dir="C:\User\example\papers"`
搜索引用另一篇论文的论文（在搜索引用时从 scholar 地址栏找到 ID）：

复制
python -m PyPaperBot --cites=3120460092236365926
使用代理：

复制
python -m PyPaperBot --query=rheumatoid+arthritis --scholar-pages=1 --scholar-results=7 --dwn-dir=/download --proxy="http://1.1.1.1::8080,https://8.8.8.8::8080"
复制
python -m PyPaperBot --query=rheumatoid+arthritis --scholar-pages=1 --scholar-results=7 --dwn-dir=/download -single-proxy=http://1.1.1.1::8080
在 termux 中，你可以直接使用 PyPaperBot 后跟参数...

贡献
欢迎在 dev 分支上提出任何更改、修复和改进，为该项目做出贡献

待办事项
测试
代码文档
总体改进
免责声明
本应用仅用于教育目的。我不对您选择如何使用本应用负责。