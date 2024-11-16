import os
import sys
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from PyPaperBot.Searcher import Searcher
from PyPaperBot.utils.log import (
    setup_logging,
    init_log_queue,
    log_message,
    render_log_sidebar
)
from PyPaperBot.Downloader import Downloader

# 设置页面配置
st.set_page_config(
    page_title="PyPaperBot Web",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 配置日志系统
setup_logging()
init_log_queue()

# 创建三列布局
main_area, right_sidebar = st.columns([5, 1])  # 5:1 的比例

# 自定义CSS样式
st.markdown("""
    <style>
    /* 按钮样式 */
    .stButton > button {
        color: white;
        border: 2px solid #ffd700;
        background-color: transparent;
        width: 100%;
        margin-bottom: 10px;
        padding: 10px;
    }
    .stButton > button:hover {
        background-color: rgba(255, 215, 0, 0.1);
    }
    
    /* 布局样式 */
    [data-testid="stSidebar"] {
        min-width: 250px;
        max-width: 250px;
    }
    
    /* 主内容区域样式 */
    .main-content {
        margin-right: 20px;
    }
    
    /* 右侧边栏样式 */
    .stMarkdown {
        max-width: 100%;
    }
    
    /* 覆盖Streamlit默认样式 */
    .block-container {
        max-width: 100% !important;
        padding: 0 !important;
    }
    .stTab {
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# 主区域（包含左侧边栏和主内容）
with main_area:
    # 使用原有的左侧边栏
    left_sidebar = st.sidebar
    with left_sidebar:
        st.title("PyPaperBot Web")
        st.markdown("---")
        
        # 初始化 session_state
        if 'current_function' not in st.session_state:
            st.session_state.current_function = None
        
        # 左侧边栏按钮
        if st.button("论文搜索功能"):
            st.session_state.current_function = "论文搜索功能"
            log_message("切换到论文搜索功能", "info", "导航")
        if st.button("论文下载功能"):
            st.session_state.current_function = "论文下载功能"
            log_message("切换到论文下载功能", "info", "导航")
        if st.button("论文过滤功能"):
            st.session_state.current_function = "论文过滤功能"
            log_message("切换到论文过滤功能", "info", "导航")
        if st.button("论文数据管理"):
            st.session_state.current_function = "论文数据管理"
            log_message("切换到论文数据管理", "info", "导航")
        if st.button("配置管理"):
            st.session_state.current_function = "配置管理"
            log_message("切换到配置管理", "info", "导航")
    
    # 主内容区域
    if st.session_state.current_function is None:
        st.session_state.current_function = "论文搜索功能"
        log_message("进入论文搜索功能", "info", "系统")
        
    if st.session_state.current_function == "论文搜索功能":
        tabs = st.tabs(["Google Scholar搜索", "CrossRef查询", "DOI搜索"])
        
        with tabs[0]:  # Google Scholar搜索
            st.subheader("Google Scholar搜索")
            query = st.text_input("输入搜索关键词", value="Digital Workplace")
            scholar_pages = st.text_input("Scholar页数 (例如: 1-3 或 5)", value="1")
            min_year = st.number_input("最早表年份", min_value=1900, max_value=2024, value=2000)
            
            if st.button("开始搜索", key="scholar_search"):
                log_message("开始Scholar搜索请求", "info", "搜索")
                log_message(f"搜索关键词: {query}", "debug", "搜索")
                log_message(f"搜索页数: {scholar_pages}", "debug", "搜索")
                log_message(f"最早年份: {min_year}", "debug", "搜索")
                
                try:
                    searcher = Searcher()
                    result = searcher.handle_scholar_search(query, scholar_pages, min_year)
                    
                    if not result['success']:
                        log_message(result['message'], "error", "搜索")
                        if result['error']:
                            log_message(f"错误详情: {result['error']}", "error", "搜索")
                        st.error(result['message'])
                    else:
                        log_message(result['message'], "success", "搜索")
                        log_message(f"搜索到 {len(result['papers'])} 篇论文", "info", "搜索")
                        
                        # 显示搜索结果
                        st.subheader(f"搜索结果 (共 {len(result['papers'])} 篇)")
                        
                        # 计算总页数
                        papers = result['papers']
                        items_per_page = 20
                        total_pages = (len(papers) + items_per_page - 1) // items_per_page
                        
                        # 添加页码选择
                        if total_pages > 1:
                            current_page = st.selectbox(
                                "选择页码",
                                range(1, total_pages + 1),
                                format_func=lambda x: f"第 {x} 页"
                            )
                        else:
                            current_page = 1
                        
                        # 计算当前页的论文
                        start_idx = (current_page - 1) * items_per_page
                        end_idx = min(start_idx + items_per_page, len(papers))
                        current_papers = papers[start_idx:end_idx]
                        
                        # 创建表格数据
                        table_data = []
                        for i, paper in enumerate(current_papers, start_idx + 1):
                            row = {
                                "序号": i,
                                "标题": paper.title,
                                "作者": paper.authors if paper.authors else "N/A",
                                "年份": paper.year if paper.year else "N/A",
                                "DOI": paper.DOI if hasattr(paper, 'DOI') and paper.DOI else "N/A",
                                "引用数": paper.cites_num if hasattr(paper, 'cites_num') else "N/A"
                            }
                            table_data.append(row)
                        
                        # 使用st.table显示表格
                        if table_data:
                            # 显示表格
                            col_config = {
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
                                "DOI": st.column_config.TextColumn(
                                    "DOI",
                                    width="medium"
                                ),
                                "引用数": st.column_config.NumberColumn(
                                    "引用数",
                                    width="small"
                                )
                            }
                            
                            # 显示表��
                            st.data_editor(
                                table_data,
                                column_config=col_config,
                                disabled=True,
                                hide_index=True
                            )
                            
                            # 显示分页信息
                            st.markdown(f"显示第 {start_idx + 1} 到 {end_idx} 条，共 {len(papers)} 条")
                            
                            # 添加下载选择和按钮
                            st.markdown("### 下载选项")
                            
                            # 找出引用次数最高的论文
                            default_paper = None
                            max_citations = -1
                            for paper in current_papers:
                                citations = getattr(paper, 'cites_num', 0) or 0
                                if citations > max_citations:
                                    max_citations = citations
                                    default_paper = paper
                            
                            # 如果没有找到引用次数最高的论文，就选择第一篇
                            if not default_paper and current_papers:
                                default_paper = current_papers[0]
                            
                            # 创建多选框，设置默认值
                            selected_papers = st.multiselect(
                                "选择要下载的论文",
                                options=current_papers,
                                default=[default_paper] if default_paper else None,
                                format_func=lambda x: (
                                    f"{x.title} "
                                    f"({x.year if x.year else 'N/A'}) "
                                    f"[引用: {x.cites_num if hasattr(x, 'cites_num') and x.cites_num else '0'}]"
                                ),
                                help="默认选择引用次数最高的论文。可以选择多篇论文一起下载。"
                            )
                            
                            # 下载按钮和选择信息显示
                            col1, col2 = st.columns([1, 4])
                            if col1.button("下载选中论文", disabled=len(selected_papers) == 0):
                                try:
                                    # 检查下载目录
                                    if not download_dir:
                                        st.error("请先设置下载目录")
                                        log_message("未设置下载目录", "error", "下载")
                                        return
                                        
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
                                    
                                except Exception as e:
                                    log_message(f"下载功能发生错误: {str(e)}", "error", "下载", exc_info=True)
                                    st.error(f"下载功能发生错误: {str(e)}")
                            
                            # 显示选中论文的详细信息
                            if selected_papers:
                                col2.markdown(
                                    f"已择 {len(selected_papers)} 篇论文 "
                                    f"(包含引用次数最高的论文: {max_citations} 次)" if max_citations > 0 else 
                                    f"已选择 {len(selected_papers)} 篇论文"
                                )
                        else:
                            st.info("没有找到符合条件的论文")
                            
                except Exception as e:
                    log_message(f"搜索过程发生异常: {str(e)}", "error", "搜索")
                    st.error(f"搜索过程发生异常: {str(e)}")
            
        with tabs[1]:  # CrossRef查询
            st.subheader("CrossRef查询")
            crossref_query = st.text_input("输入CrossRef查询词")
            
            if st.button("查询", key="crossref_search"):
                log_message("开始CrossRef查询", "info", "搜索")
                log_message(f"查询词: {crossref_query}", "debug", "搜索")
                # TODO: 实现CrossRef查询逻辑
            
        with tabs[2]:  # DOI搜索
            st.subheader("DOI搜索")
            doi_input = st.text_area("输入DOI (每行一个)")
            doi_file = st.file_uploader("或上传DOI文件 (.txt)")
            
            if st.button("搜索", key="doi_search"):
                log_message("开始DOI搜索", "info", "搜索")
                log_message("DOI输入: " + doi_input, "debug", "搜索")
                log_message("DOI文件: " + str(doi_file), "debug", "搜索")
                # TODO: 实现DOI搜索逻辑

    elif st.session_state.current_function == "论文下载功能":
        tabs = st.tabs(["下载管理", "代理设置"])
        
        with tabs[0]:  # 下载管理
            st.subheader("下载设置")
            download_dir = st.text_input("下载目录路径")
            use_doi_filename = st.checkbox("使用DOI为文件名")
            scihub_mirror = st.text_input("SciHub镜像网址", value="https://sci-hub.se")
            
            if st.button("开始下载", key="start_download"):
                log_message("开始下载论文", "info", "下载")
                log_message(f"下载目录: {download_dir}", "debug", "下载")
                log_message(f"使用DOI作为文件名: {use_doi_filename}", "debug", "下载")
                log_message(f"SciHub镜像网址: {scihub_mirror}", "debug", "下载")
                # TODO: 实现下载逻辑
            
        with tabs[1]:  # 代理设置
            st.subheader("代理设置")
            proxy = st.text_input("代理服器 (格式: protocol://ip:port)")
            use_single_proxy = st.checkbox("使用单一代理")
            
            if st.button("保存代理设置", key="save_proxy"):
                log_message("保存代理设置", "info", "代理设置")
                log_message(f"代理服务器: {proxy}", "debug", "代理设置")
                log_message(f"使用单一代理: {use_single_proxy}", "debug", "代理设置")
                # TODO: 实现代理设置保存

    elif st.session_state.current_function == "论文过滤功能":
        st.subheader("论文过滤器")
        
        max_papers_by_year = st.number_input("每年最大论文数", min_value=1)
        max_papers_by_citations = st.number_input("按引用数最大论文数", min_value=1)
        journal_filter_file = st.file_uploader("期刊过滤器文件 (.csv)")
        
        if st.button("应用过滤器", key="apply_filters"):
            log_message("应用论文过滤器", "info", "过滤器")
            log_message(f"每年最大论文数: {max_papers_by_year}", "debug", "过滤器")
            log_message(f"按引用数最大论文数: {max_papers_by_citations}", "debug", "过滤器")
            log_message("期刊过滤器文件: " + str(journal_filter_file), "debug", "过滤器")
            # TODO: 实现过滤器逻辑

    elif st.session_state.current_function == "论文数据管理":
        tabs = st.tabs(["元数据管理", "BibTeX生成"])
        
        with tabs[0]:  # 元数据管理
            st.subheader("论文元数据管理")
            # TODO: 实现元数据管理界面
            
        with tabs[1]:  # BibTeX生成
            st.subheader("生成BibTeX")
            # TODO: 实现BibTeX生成界面

    elif st.session_state.current_function == "配置管理":
        st.subheader("系统配置")
        
        selenium_chrome_version = st.number_input("Chrome版本 (用于Selenium)", min_value=0)
        restrict_mode = st.selectbox("限制模式", ["无限制", "仅下载BibTeX", "仅下载PDF"])
        
        if st.button("保存配置", key="save_config"):
            log_message("保存系统配置", "info", "配置管理")
            log_message(f"Chrome版本: {selenium_chrome_version}", "debug", "配置管理")
            log_message(f"限制模式: {restrict_mode}", "debug", "配置管理")
            # TODO: 实现配置保存逻辑

# 右侧日志面板
with right_sidebar:
    render_log_sidebar(right_sidebar)

# 底部状态栏
st.markdown("---")
st.markdown("PyPaperBot Web Interface - 开发中") 