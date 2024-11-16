import logging
import requests
from typing import List, Optional
from .Paper import Paper

class CrossRefConnector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.crossref.org"
        self.headers = {
            "User-Agent": "PyPaperBot/1.0 (https://github.com/ferru97/PyPaperBot)"
        }
        
    def search(self, query: str) -> List[Paper]:
        """
        使用CrossRef API搜索论文
        
        Args:
            query: 搜索关键词
            
        Returns:
            List[Paper]: 搜索到的论文列表
        """
        self.logger.debug(f"CrossRef搜索: {query}")
        papers = []
        
        try:
            response = requests.get(
                f"{self.base_url}/works",
                params={"query": query},
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            for item in items:
                try:
                    paper = self._parse_crossref_item(item)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    self.logger.warning(f"解析CrossRef结果出错: {str(e)}")
                    continue
                    
            return papers
            
        except Exception as e:
            self.logger.error(f"CrossRef API请求出错: {str(e)}")
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
            response = requests.get(
                f"{self.base_url}/works/{doi}",
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
            title = item.get("title", [None])[0]
            if not title:
                return None
                
            paper = Paper(
                title=title,
                doi=item.get("DOI"),
                url=item.get("URL")
            )
            
            # 解析作者
            authors = item.get("author", [])
            paper.authors = ", ".join(
                f"{author.get('given', '')} {author.get('family', '')}"
                for author in authors
            )
            
            # 解析年份
            if "published-print" in item:
                paper.year = str(item["published-print"]["date-parts"][0][0])
            elif "published-online" in item:
                paper.year = str(item["published-online"]["date-parts"][0][0])
                
            return paper
            
        except Exception as e:
            self.logger.warning(f"解析CrossRef论文数据出错: {str(e)}")
            return None 