import streamlit as st
from PyPaperBot.Searcher import Searcher
from PyPaperBot.Downloader import Downloader
from PyPaperBot.utils.log import log_message

def handle_download(selected_papers, download_dir, use_doi_filename=False, scihub_mirror="https://sci-hub.se"):
    """处理论文下载"""
    try:
        # 检查下载目录
        if not download_dir:
            st.error("请先设置下载目录")
            log_message("未设置下载目录", "error", "下载")
            return False
            
        # 创建下载器实例
        downloader = Downloader(
            download_dir=download_dir,
            use_doi_as_filename=use_doi_filename,
            scihub_mirror=scihub_mirror
        )
        log_message(f"初始化下载器: 目录={download_dir}, DOI文件名={use_doi_filename}", "info", "下载")
        
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 开始下载
        total_papers = len(selected_papers)
        successful_downloads = 0
        failed_downloads = []
        
        for i, paper in enumerate(selected_papers, 1):
            try:
                status_text.text(f"正在下载 ({i}/{total_papers}): {paper.title}")
                log_message(f"开始下载论文: {paper.title}", "info", "下载")
                
                # 记录论文信息
                log_message(f"论文信息:", "debug", "下载")
                log_message(f"  标题: {paper.title}", "debug", "下载")
                log_message(f"  DOI: {paper.DOI if hasattr(paper, 'DOI') else 'N/A'}", "debug", "下载")
                log_message(f"  URL: {paper.scholar_link if hasattr(paper, 'scholar_link') else 'N/A'}", "debug", "下载")
                
                # 尝试下载
                result = downloader.download_paper(paper)
                
                if result:
                    successful_downloads += 1
                    log_message(f"论文下载成功: {paper.title}", "success", "下载")
                else:
                    failed_downloads.append(paper.title)
                    log_message(f"论文下载失败: {paper.title}", "error", "下载")
                
                # 更新进度
                progress = int((i / total_papers) * 100)
                progress_bar.progress(progress)
                
            except Exception as e:
                failed_downloads.append(paper.title)
                log_message(f"下载过程出错: {paper.title} - {str(e)}", "error", "下载")
                continue
            
        # 显示下载结果
        if successful_downloads > 0:
            st.success(f"成功下载 {successful_downloads} 篇论文")
            log_message(f"下载完成: 成功 {successful_downloads} 篇", "success", "下载")
        
        if failed_downloads:
            st.error(f"下载失败 {len(failed_downloads)} 篇论文")
            log_message(f"下载失败论文列表:", "error", "下载")
            for title in failed_downloads:
                log_message(f"  - {title}", "error", "下载")
        
        # 清理进度显示
        progress_bar.empty()
        status_text.empty()
        
        return successful_downloads > 0
        
    except Exception as e:
        log_message(f"下载功能发生错误: {str(e)}", "error", "下载", exc_info=True)
        st.error(f"下载功能发生错误: {str(e)}")
        return False

def find_default_paper(papers):
    """找出引用次数最高的论文"""
    default_paper = None
    max_citations = -1
    for paper in papers:
        citations = getattr(paper, 'cites_num', 0) or 0
        if citations > max_citations:
            max_citations = citations
            default_paper = paper
    
    # 如果没有找到引用次数最高的论文，就选择第一篇
    if not default_paper and papers:
        default_paper = papers[0]
        
    return default_paper, max_citations

def format_paper_display(paper):
    """格式化论文显示文本"""
    return (
        f"{paper.title} "
        f"({paper.year if paper.year else 'N/A'}) "
        f"[引用: {paper.cites_num if hasattr(paper, 'cites_num') and paper.cites_num else '0'}]"
    )

def handle_scholar_search(query: str, scholar_pages: str, min_year: int):
    """处理Scholar搜索请求"""
    try:
        searcher = Searcher()
        return searcher.handle_scholar_search(query, scholar_pages, min_year)
    except Exception as e:
        log_message(f"搜索过程发生异常: {str(e)}", "error", "搜索")
        st.error(f"搜索过程发生异常: {str(e)}")
        return None

def calculate_pagination(papers, items_per_page=20):
    """计算分页信息"""
    total_pages = (len(papers) + items_per_page - 1) // items_per_page
    return total_pages, items_per_page

def get_page_papers(papers, current_page, items_per_page):
    """获取当前页的论文"""
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(papers))
    return papers[start_idx:end_idx], start_idx, end_idx

def create_table_data(papers, start_idx=0):
    """创建表格数据"""
    table_data = []
    for i, paper in enumerate(papers, start_idx + 1):
        row = {
            "作者": paper.authors if paper.authors else "N/A",
            "年份": paper.year if paper.year else "N/A",
            "标题": paper.title,
            "期刊": paper.jurnal if paper.jurnal else "N/A",
            "元数据数量": getattr(paper, 'metadata_count', 0)
        }
        table_data.append(row)
    return table_data

def get_table_column_config():
    """获取表格列配置"""
    return {
        "作者": st.column_config.TextColumn(
            "作者",
            width="large"
        ),
        "年份": st.column_config.TextColumn(
            "年份",
            width="small"
        ),
        "标题": st.column_config.TextColumn(
            "标题",
            width="large"
        ),
        "期刊": st.column_config.TextColumn(
            "期刊",
            width="medium"
        ),
        "元数据数量": st.column_config.NumberColumn(
            "元数据数量",
            width="small",
            help="获取到的有效元数据字段数量"
        )
    } 