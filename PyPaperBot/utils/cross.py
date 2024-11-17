import logging
import streamlit as st
from typing import Dict, List, Any
from ..Scholar import ScholarSearcher
from ..CrossRefConnector import CrossRefConnector
from ..Paper import Paper

class CrossValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scholar = ScholarSearcher()
        self.crossref = CrossRefConnector()
        
    def validate_papers(self, query: str, max_results: int = 10, min_year: int = None) -> Dict[str, Any]:
        """搜索并验证论文"""
        result = {
            'success': False,
            'message': '',
            'scholar_papers': [],
            'validated_papers': [],
            'validated_count': 0
        }
        
        try:
            # 第一步：Google Scholar搜索
            st.info("正在执行Google Scholar搜索...")
            progress_bar = st.progress(0)
            self.logger.info(f"开始Google Scholar搜索: {query}")
            
            scholar_papers = self.scholar.search_page(query, 1)
            if min_year:
                scholar_papers = [p for p in scholar_papers if p.year and int(p.year) >= min_year]
            scholar_papers = scholar_papers[:max_results]
            
            # 显示Scholar搜索结果
            st.success(f"Google Scholar搜索完成，找到 {len(scholar_papers)} 篇论文")
            result['scholar_papers'] = scholar_papers
            
            # 第二步：CrossRef验证
            st.info("开始CrossRef验证...")
            self.logger.info(f"开始验证 {len(scholar_papers)} 篇论文")
            
            validated_papers = []
            for i, paper in enumerate(scholar_papers):
                try:
                    # 更新进度条
                    progress = (i + 1) / len(scholar_papers)
                    progress_bar.progress(progress)
                    st.text(f"正在验证第 {i+1}/{len(scholar_papers)} 篇论文")
                    
                    self.logger.info(f"验证论文: {paper.title}")
                    
                    # 使用CrossRef搜索验证
                    crossref_results = self.crossref.search_with_filters(
                        title=paper.title,
                        max_results=1
                    )
                    
                    if crossref_results:
                        crossref_paper = crossref_results[0]
                        # 合并信息
                        paper.DOI = crossref_paper.DOI
                        paper.jurnal = crossref_paper.jurnal
                        paper.metadata_count = getattr(crossref_paper, 'metadata_count', 0)
                        
                        # 记录验证信息
                        paper.validated = True
                        paper.validation_source = "CrossRef"
                        validated_papers.append(paper)
                        self.logger.info(f"论文验证成功: {paper.title}")
                        self.logger.debug(f"DOI: {paper.DOI}")
                        self.logger.debug(f"期刊: {paper.jurnal}")
                    else:
                        self.logger.warning(f"论文未能通过CrossRef验证: {paper.title}")
                        paper.validated = False
                        validated_papers.append(paper)
                        
                except Exception as e:
                    self.logger.error(f"验证过程出错: {str(e)}")
                    paper.validated = False
                    validated_papers.append(paper)
            
            # 清理进度显示
            progress_bar.empty()
            
            # 统计验证结果
            validated_count = sum(1 for p in validated_papers if p.validated)
            self.logger.info(f"验证完成: {validated_count}/{len(validated_papers)} 篇论文通过验证")
            
            result['success'] = True
            result['validated_papers'] = validated_papers
            result['validated_count'] = validated_count
            result['message'] = f"验证完成: {validated_count}/{len(validated_papers)} 篇论文通过验证"
            
            return result
            
        except Exception as e:
            error_msg = f"论文验证过程出错: {str(e)}"
            self.logger.error(error_msg)
            result['message'] = error_msg
            return result

    def create_validation_table(self, papers: List[Paper]) -> List[Dict[str, Any]]:
        """创建验证结果表格数据"""
        table_data = []
        for i, paper in enumerate(papers, 1):
            row = {
                "序号": i,
                "标题": paper.title,
                "作者": paper.authors if paper.authors else "N/A",
                "年份": paper.year if paper.year else "N/A",
                "引用数": paper.cites_num if hasattr(paper, 'cites_num') else 0,
                "验证状态": "✓ 已验证" if paper.validated else "✗ 未验证",
                "DOI": paper.DOI if paper.DOI else "N/A",
                "期刊": paper.jurnal if paper.jurnal else "N/A"
            }
            table_data.append(row)
        return table_data

    def get_table_column_config(self):
        """获取表格列配置"""
        return {
            "序号": st.column_config.NumberColumn(
                "序号",
                width="small"
            ),
            "标题": st.column_config.TextColumn(
                "标题",
                width="large"
            ),
            "作者": st.column_config.TextColumn(
                "作者",
                width="medium"
            ),
            "年份": st.column_config.TextColumn(
                "年份",
                width="small"
            ),
            "引用数": st.column_config.NumberColumn(
                "引用数",
                width="small"
            ),
            "验证状态": st.column_config.TextColumn(
                "验证状态",
                width="small"
            ),
            "DOI": st.column_config.TextColumn(
                "DOI",
                width="medium"
            ),
            "期刊": st.column_config.TextColumn(
                "期刊",
                width="medium"
            )
        } 