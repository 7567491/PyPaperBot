import logging
from typing import List, Optional, Dict, Any
import streamlit as st
from .Scholar import ScholarSearcher
from .CrossRefConnector import CrossRefConnector
from .Paper import Paper

class Searcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scholar = ScholarSearcher()
        self.crossref = CrossRefConnector()
        
    def search_scholar(self, query: str, pages: List[int], min_year: int = None) -> List[Paper]:
        """
        使用Google Scholar搜索论文
        
        Args:
            query: 搜索关键词
            pages: 要搜索的页码列表
            min_year: 最早发表年份
            
        Returns:
            List[Paper]: 搜索到的论文列表
        """
        self.logger.info(f"开始Google Scholar搜索: {query}")
        papers = []
        
        try:
            for page in pages:
                self.logger.info(f"正在搜索第 {page} 页...")
                try:
                    self.logger.debug(f"调用ScholarSearcher.search_page: query='{query}', page={page}")
                    page_papers = self.scholar.search_page(query, page)
                    self.logger.debug(f"第 {page} 页搜索到 {len(page_papers)} 篇论文")
                    
                    if min_year:
                        self.logger.debug(f"应用年份过滤: min_year={min_year}")
                        filtered_papers = [p for p in page_papers if p.year and int(p.year) >= min_year]
                        self.logger.debug(f"过滤后剩余 {len(filtered_papers)} 篇论文")
                        page_papers = filtered_papers
                        
                    papers.extend(page_papers)
                    self.logger.info(f"当前共收集到 {len(papers)} 篇论文")
                    
                except Exception as e:
                    self.logger.error(f"搜索第 {page} 页时出错: {str(e)}", exc_info=True)
                    continue
                
            self.logger.info(f"搜索完成，共找到 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            self.logger.error(f"Google Scholar搜索出错: {str(e)}", exc_info=True)
            raise
            
    def search_crossref(self, query: str) -> List[Paper]:
        """
        使用CrossRef搜索论文
        
        Args:
            query: 搜索关键词
            
        Returns:
            List[Paper]: 搜索到的论文列表
        """
        self.logger.info(f"开始CrossRef搜索: {query}")
        
        try:
            papers = self.crossref.search(query)
            self.logger.info(f"搜索完成，共找到 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            self.logger.error(f"CrossRef搜索出错: {str(e)}")
            raise
            
    def search_by_doi(self, dois: List[str]) -> List[Paper]:
        """
        通过DOI搜索论文
        
        Args:
            dois: DOI列表
            
        Returns:
            List[Paper]: 搜索到的论文列表
        """
        self.logger.info(f"开始DOI搜索，共 {len(dois)} 个DOI")
        papers = []
        
        try:
            for doi in dois:
                try:
                    paper = self.crossref.get_paper_by_doi(doi)
                    if paper:
                        papers.append(paper)
                        self.logger.debug(f"成功获取DOI论文: {doi}")
                except Exception as e:
                    self.logger.warning(f"获取DOI论文失败 {doi}: {str(e)}")
                    continue
                    
            self.logger.info(f"DOI搜索完成，成功获取 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            self.logger.error(f"DOI搜索出错: {str(e)}")
            raise
            
    def parse_pages_input(self, pages_str: str) -> List[int]:
        """
        解析页数输入
        
        Args:
            pages_str: 页数字符串，如 "1-3" 或 "5"
            
        Returns:
            List[int]: 页码列表
        """
        try:
            if '-' in pages_str:
                start, end = map(int, pages_str.split('-'))
                return list(range(start, end + 1))
            else:
                return [int(pages_str)]
        except ValueError:
            raise ValueError("页数格式错误，请使用数字或范围（例如：1-3）") 

    def handle_scholar_search(self, query: str, scholar_pages: str, min_year: int) -> Dict[str, Any]:
        """
        处理Google Scholar搜索请求
        
        Args:
            query: 搜索关键词
            scholar_pages: 页数字符串
            min_year: 最早发表年份
            
        Returns:
            Dict[str, Any]: 包含搜索结果和状态的字典
        """
        result = {
            'success': False,
            'message': '',
            'papers': None,
            'error': None
        }
        
        self.logger.info(f"开始处理Scholar搜索请求: query='{query}', pages='{scholar_pages}', min_year={min_year}")
        
        if not query:
            self.logger.warning("搜索关键词为空")
            result['message'] = "搜索关键词不能为空"
            return result
            
        if not scholar_pages:
            self.logger.warning("Scholar页数为空")
            result['message'] = "Scholar页数不能为空"
            return result
            
        try:
            # 解析页数
            self.logger.debug(f"正在解析页数: {scholar_pages}")
            try:
                pages = self.parse_pages_input(scholar_pages)
                self.logger.info(f"页数解析结果: {pages}")
            except ValueError as e:
                self.logger.error(f"页数格式错误: {str(e)}")
                result['message'] = f"页数格式错误: {str(e)}"
                result['error'] = str(e)
                return result
                
            # 执行搜索
            self.logger.info(f"开始执行Scholar搜索...")
            self.logger.debug(f"搜索参数: query='{query}', pages={pages}, min_year={min_year}")
            
            try:
                papers = self.search_scholar(query, pages, min_year)
                self.logger.debug(f"原始搜索结果数量: {len(papers)}")
                
                if not papers:
                    self.logger.warning("未找到符合条件的论文")
                    result['message'] = "未找到符合条件的论文"
                    return result
                    
                # 记录每篇论文的基本信息
                for i, paper in enumerate(papers, 1):
                    self.logger.debug(f"论文 {i}:")
                    self.logger.debug(f"  标题: {paper.title}")
                    self.logger.debug(f"  作者: {paper.authors if hasattr(paper, 'authors') else 'N/A'}")
                    self.logger.debug(f"  年份: {paper.year if hasattr(paper, 'year') else 'N/A'}")
                    self.logger.debug(f"  DOI: {paper.doi if hasattr(paper, 'doi') else 'N/A'}")
                    self.logger.debug(f"  引用数: {paper.citations if hasattr(paper, 'citations') else 'N/A'}")
                    
                result['success'] = True
                result['papers'] = papers
                result['message'] = f"搜索完成，找到 {len(papers)} 篇论文"
                self.logger.info(result['message'])
                return result
                
            except Exception as e:
                self.logger.error(f"执行搜索时出错: {str(e)}", exc_info=True)
                result['message'] = f"搜索过程出错: {str(e)}"
                result['error'] = str(e)
                return result
                
        except Exception as e:
            self.logger.error(f"处理搜索请求时出错: {str(e)}", exc_info=True)
            result['message'] = f"搜索过程出错: {str(e)}"
            result['error'] = str(e)
            return result

    def handle_crossref_search(self, query: str) -> Dict[str, Any]:
        """
        处理CrossRef搜索请求
        
        Args:
            query: 搜索关键词
            
        Returns:
            Dict[str, Any]: 包含搜索结果和状态的字典
        """
        result = {
            'success': False,
            'message': '',
            'papers': None,
            'error': None
        }
        
        if not query:
            result['message'] = "搜索关键词不能为空"
            return result
            
        try:
            papers = self.search_crossref(query)
            
            if not papers:
                result['message'] = "未找到符合条件的论文"
                return result
                
            result['success'] = True
            result['papers'] = papers
            result['message'] = f"搜索完成，找到 {len(papers)} 篇论文"
            return result
            
        except Exception as e:
            result['message'] = f"搜索过程出错: {str(e)}"
            result['error'] = str(e)
            return result

    def handle_doi_search(self, doi_input: str, doi_file: Optional[Any] = None) -> Dict[str, Any]:
        """
        处理DOI搜索请求
        
        Args:
            doi_input: DOI输入文本
            doi_file: 上传的DOI文件
            
        Returns:
            Dict[str, Any]: 包含搜索结果和状态的字典
        """
        result = {
            'success': False,
            'message': '',
            'papers': None,
            'error': None
        }
        
        dois = []
        
        # 处理文本输入的DOI
        if doi_input:
            dois.extend([doi.strip() for doi in doi_input.split('\n') if doi.strip()])
            
        # 处理上传文件中的DOI
        if doi_file:
            try:
                content = doi_file.read().decode()
                dois.extend([doi.strip() for doi in content.split('\n') if doi.strip()])
            except Exception as e:
                result['message'] = f"读取DOI文件出错: {str(e)}"
                result['error'] = str(e)
                return result
                
        if not dois:
            result['message'] = "未提供任何DOI"
            return result
            
        try:
            papers = self.search_by_doi(dois)
            
            if not papers:
                result['message'] = "未找到符合条件的论文"
                return result
                
            result['success'] = True
            result['papers'] = papers
            result['message'] = f"搜索完成，找到 {len(papers)} 篇论文"
            return result
            
        except Exception as e:
            result['message'] = f"搜索过程出错: {str(e)}"
            result['error'] = str(e)
            return result