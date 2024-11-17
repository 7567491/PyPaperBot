import logging
import requests
from typing import List, Optional, Any
from .Paper import Paper

class CrossRefConnector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.crossref.org"
        self.headers = {
            "User-Agent": "PyPaperBot/1.0 (https://github.com/ferru97/PyPaperBot)"
        }
        self.logger.info("初始化CrossRef连接器")
        
    def search(self, query: str) -> List[Paper]:
        """
        使用CrossRef API搜索论文
        
        Args:
            query: 搜索关键词
            
        Returns:
            List[Paper]: 搜索到的论文列表
        """
        self.logger.info(f"开始CrossRef搜索: {query}")
        papers = []
        
        try:
            # 构建请求URL
            url = f"{self.base_url}/works"
            params = {
                "query": query,
                "rows": 100,  # 每页结果数
                "select": "DOI,title,author,published-print,published-online,URL"
            }
            self.logger.debug(f"请求URL: {url}")
            self.logger.debug(f"请求参数: {params}")
            
            # 发送请求
            self.logger.info("发送CrossRef API请求...")
            response = requests.get(
                url,
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            
            # 解析响应
            data = response.json()
            self.logger.info(f"收到响应，状态码: {response.status_code}")
            self.logger.debug(f"响应头: {response.headers}")
            
            items = data.get("items", [])
            self.logger.info(f"找到 {len(items)} 个结果")
            
            # 处理每个结果
            for item in items:
                try:
                    paper = self._parse_crossref_item(item)
                    if paper:
                        papers.append(paper)
                        self.logger.debug(f"成功解析论文: {paper.title}")
                except Exception as e:
                    self.logger.warning(f"解析CrossRef结果出错: {str(e)}")
                    continue
                    
            self.logger.info(f"成功解析 {len(papers)} 篇论文")
            return papers
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"CrossRef API请求失败: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"CrossRef搜索过程出错: {str(e)}")
            raise
            
    def get_paper_by_doi(self, doi: str) -> Optional[Paper]:
        """
        通过DOI获取论文信息
        
        Args:
            doi: 论文DOI
            
        Returns:
            Optional[Paper]: 论文对象，如果未找到返回None
        """
        self.logger.debug(f"通过DOI获取论文: {doi}")
        
        try:
            url = f"{self.base_url}/works/{doi}"
            self.logger.debug(f"请求URL: {url}")
            
            response = requests.get(
                url,
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            return self._parse_crossref_item(data)
            
        except Exception as e:
            self.logger.error(f"获取DOI论文信息出错: {str(e)}")
            raise
            
    def _parse_crossref_item(self, item: dict) -> Optional[Paper]:
        """
        解析CrossRef API返回的论文数据
        
        Args:
            item: CrossRef API返回的论文数据
            
        Returns:
            Optional[Paper]: 解析后的Paper对象
        """
        try:
            # 提取标题
            title = item.get("title", [None])[0]
            if not title:
                self.logger.warning("论文缺少标题，跳过")
                return None
                
            self.logger.debug(f"解析论文: {title}")
            
            # 创建Paper对象（只使用构造函数支持的参数）
            paper = Paper(
                title=title,
                scholar_link=item.get("URL"),  # URL作为scholar_link
                year=None,  # 稍后设置
                authors=None  # 稍后设置
            )
            
            # 设置DOI（作为属性设置）
            paper.DOI = item.get("DOI")
            if paper.DOI:
                self.logger.debug(f"DOI: {paper.DOI}")
            
            # 解析作者
            authors = item.get("author", [])
            paper.authors = ", ".join(
                f"{author.get('given', '')} {author.get('family', '')}"
                for author in authors
            )
            self.logger.debug(f"作者: {paper.authors}")
            
            # 解析年份
            if "published-print" in item:
                paper.year = str(item["published-print"]["date-parts"][0][0])
            elif "published-online" in item:
                paper.year = str(item["published-online"]["date-parts"][0][0])
            if paper.year:
                self.logger.debug(f"年份: {paper.year}")
            
            # 设置期刊信息
            if "container-title" in item:
                paper.jurnal = item["container-title"][0] if item["container-title"] else None
                if paper.jurnal:
                    self.logger.debug(f"期刊: {paper.jurnal}")
            
            return paper
            
        except Exception as e:
            self.logger.warning(f"解析CrossRef论文数据出错: {str(e)}")
            return None 
            
    def search_with_filters(self, title: str, author: str = "", year: str = "", 
                          journal: str = "", doi: str = "", max_results: int = 5) -> List[Paper]:
        """使用标题搜索论文"""
        self.logger.info(f"开始CrossRef搜索")
        self.logger.debug(f"搜索标题: '{title}'")
        
        try:
            # 构建请求URL和参数
            url = f"{self.base_url}/works"
            params = {
                "query": title,
                "rows": 20,  # 获取更多结果用于精确匹配
                "sort": "score",
                "order": "desc"
            }
            
            self.logger.debug(f"请求URL: {url}")
            self.logger.debug(f"请求参数: {params}")
            
            # 发送请求
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            # 解析响应
            data = response.json()
            message = data.get('message', {})
            items = message.get("items", [])
            
            # 查找精确匹配
            exact_match = None
            for item in items:
                item_title = item.get("title", [None])[0]
                if item_title and item_title.lower() == title.lower():
                    exact_match = item
                    self.logger.info("找到精确匹配的论文")
                    break
            
            if exact_match:
                # 记录精确匹配论文的详细元数据
                self.logger.info("\n" + "="*50 + "\n精确匹配论文元数据:")
                
                # 基础书目信息
                self.log_metadata("标题", exact_match.get("title", [None])[0])
                self.log_metadata("DOI", exact_match.get("DOI"))
                self.log_metadata("作者", self._format_authors(exact_match.get("author", [])))
                self.log_metadata("出版日期(印刷)", self._format_date(exact_match.get("published-print")))
                self.log_metadata("出版日期(在线)", self._format_date(exact_match.get("published-online")))
                self.log_metadata("期刊", exact_match.get("container-title", [None])[0])
                self.log_metadata("卷号", exact_match.get("volume"))
                self.log_metadata("期号", exact_match.get("issue"))
                self.log_metadata("页码", exact_match.get("page"))
                self.log_metadata("出版商", exact_match.get("publisher"))
                self.log_metadata("类型", exact_match.get("type"))
                self.log_metadata("URL", exact_match.get("URL"))
                
                # 创建Paper对象
                paper = Paper(
                    title=exact_match.get("title", [None])[0],
                    authors=self._format_authors(exact_match.get("author", [])),
                    year=self._get_year(exact_match),
                )
                paper.jurnal = exact_match.get("container-title", [None])[0]
                paper.DOI = exact_match.get("DOI")
                
                self.logger.info("="*50)
                return [paper]  # 返回精确匹配的论文
                
            else:
                # 没有精确匹配，返回相关度最高的5篇
                self.logger.info("未找到精确匹配，返回相关度最高的5篇论文")
                papers = []
                for item in items[:5]:
                    try:
                        # 记录论文元数据
                        self.logger.info(f"\n{'='*50}\n相关论文元数据:")
                        
                        # 记录所有可用的元数据
                        for key, value in item.items():
                            if value:
                                self.log_metadata(key, value)
                        
                        # 统计有效元数据数量
                        valid_metadata_count = sum(1 for v in item.values() if v is not None and v != [] and v != "")
                        
                        # 创建Paper对象
                        paper = Paper(
                            title=item.get("title", [None])[0],
                            authors=self._format_authors(item.get("author", [])),
                            year=self._get_year(item),
                        )
                        paper.jurnal = item.get("container-title", [None])[0]
                        paper.metadata_count = valid_metadata_count
                        paper.DOI = item.get("DOI")
                        
                        papers.append(paper)
                        self.logger.info(f"{'='*50}")
                        
                    except Exception as e:
                        self.logger.warning(f"解析结果出错: {str(e)}", exc_info=True)
                        continue
                
                self.logger.info(f"成功解析 {len(papers)} 篇相关论文")
                return papers
            
        except Exception as e:
            self.logger.error(f"CrossRef搜索出错: {str(e)}", exc_info=True)
            raise

    def log_metadata(self, field: str, value: Any):
        """记录元数据到日志"""
        try:
            if isinstance(value, list):
                if value and isinstance(value[0], dict):
                    # 处理复杂的列表类型（如作者列表）
                    formatted_value = self._format_complex_list(value)
                else:
                    # 处理简单的列表类型
                    formatted_value = ", ".join(str(v) for v in value if v)
            elif isinstance(value, dict):
                # 处理字典类型
                formatted_value = ", ".join(f"{k}: {v}" for k, v in value.items() if v)
            else:
                formatted_value = str(value)
            
            if formatted_value:
                self.logger.info(f"{field}: {formatted_value}")
        except Exception as e:
            self.logger.warning(f"格式化元数据出错 ({field}): {str(e)}")

    def _format_authors(self, authors: List[dict]) -> str:
        """格式化作者信息"""
        return ", ".join(
            f"{author.get('given', '')} {author.get('family', '')} "
            f"(ORCID: {author.get('ORCID', 'N/A')})"
            for author in authors
        )

    def _format_date(self, date_info: dict) -> str:
        """格式化日期信息"""
        if not date_info:
            return "N/A"
        parts = date_info.get("date-parts", [[]])[0]
        return "-".join(str(p) for p in parts)

    def _format_licenses(self, licenses: List[dict]) -> str:
        """格式化许可证信息"""
        return "; ".join(lic.get("URL", "") for lic in licenses)

    def _format_funders(self, funders: List[dict]) -> str:
        """格式化资助信息"""
        return "; ".join(
            f"{funder.get('name', '')} ({', '.join(funder.get('award', []))})"
            for funder in funders
        )

    def _get_year(self, item: dict) -> Optional[str]:
        """获取年份"""
        if "published-print" in item:
            return str(item["published-print"]["date-parts"][0][0])
        elif "published-online" in item:
            return str(item["published-online"]["date-parts"][0][0])
        return None

    def _format_complex_list(self, items: List[dict]) -> str:
        """格式化复杂的列表类型数据"""
        try:
            formatted_items = []
            for item in items:
                if isinstance(item, dict):
                    # 过滤掉空值
                    item_str = ", ".join(f"{k}: {v}" for k, v in item.items() if v)
                    if item_str:
                        formatted_items.append(item_str)
            return " | ".join(formatted_items)
        except Exception as e:
            self.logger.warning(f"格式化复杂列表出错: {str(e)}")
            return str(items)