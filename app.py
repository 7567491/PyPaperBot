import streamlit as st
from PyPaperBot.utils.log import setup_logging, init_log_queue, render_log_sidebar, log_message
from PyPaperBot.utils.fun import (
    handle_download,
    find_default_paper,
    format_paper_display,
    handle_scholar_search,
    calculate_pagination,
    get_page_papers,
    create_table_data,
    get_table_column_config
)
from PyPaperBot.CrossRefConnector import CrossRefConnector
from collections import deque
from PyPaperBot.utils.cross import CrossValidator
from db.db_main import render_database_management

# 设置页面配置
st.set_page_config(
    page_title="PyPaperBot Web",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化日志队列（移到最前面）
if 'log_queue' not in st.session_state:
    st.session_state.log_queue = deque(maxlen=1000)

# 配置日志系统
setup_logging()
init_log_queue()

# 创建两列布局
main_area, right_sidebar = st.columns([5, 1])  # 5:1 的比例

# 主区域（包含左侧边栏和主内容）
with main_area:
    # 使用原有的左侧边栏
    left_sidebar = st.sidebar
    with left_sidebar:
        st.title("PyPaperBot Web")
        st.markdown("---")
        
        # 初始化 session_state，默认显示论文搜索功能
        if 'current_function' not in st.session_state:
            st.session_state.current_function = "论文搜索功能"  # 设置默认值
        
        # 左侧边栏按钮
        if st.button("论文搜索功能"):
            st.session_state.current_function = "论文搜索功能"
        if st.button("论文下载功能"):
            st.session_state.current_function = "论文下载功能"
        if st.button("论文过滤功能"):
            st.session_state.current_function = "论文过滤功能"
        if st.button("论文数据管理"):
            st.session_state.current_function = "论文数据管理"
        if st.button("配置管理"):
            st.session_state.current_function = "配置管理"
    
    # 主内容区域
    if st.session_state.current_function == "论文搜索功能":
        tabs = st.tabs(["Google Scholar搜索", "CrossRef查询", "验证论文"])
        
        with tabs[0]:  # Google Scholar搜索
            st.subheader("Google Scholar搜索")
            query = st.text_input("输入搜索关键词", value="Digital Workplace")
            scholar_pages = st.text_input("Scholar页数 (例如: 1-3 或 5)", value="1")
            min_year = st.number_input(
                "最早发表年份", 
                min_value=1900, 
                max_value=2024, 
                value=2000,
                key="scholar_min_year"
            )
            
            if st.button("开始搜索", key="scholar_search"):
                result = handle_scholar_search(query, scholar_pages, min_year)
                
                if result and result['success']:
                    papers = result['papers']
                    total_pages, items_per_page = calculate_pagination(papers)
                    
                    # 添加页码选择
                    if total_pages > 1:
                        current_page = st.selectbox(
                            "选择页码",
                            range(1, total_pages + 1),
                            format_func=lambda x: f"第 {x} 页"
                        )
                    else:
                        current_page = 1
                    
                    # 获取当前页的论文
                    current_papers, start_idx, end_idx = get_page_papers(papers, current_page, items_per_page)
                    
                    # 创建表格数据
                    table_data = create_table_data(current_papers, start_idx)
                    
                    # 显示表格
                    if table_data:
                        st.data_editor(
                            table_data,
                            column_config=get_table_column_config(),
                            disabled=True,
                            hide_index=True
                        )
                        
                        # 显示分页信息
                        st.markdown(f"显示 {start_idx + 1} 到 {end_idx} 条，共 {len(papers)} 条")
                        
                        # 添加下载选择和按钮
                        st.markdown("### 下载选项")
                        
                        # 找出默认论文
                        default_paper, max_citations = find_default_paper(current_papers)
                        
                        # 创建多选框
                        selected_papers = st.multiselect(
                            "选择要下载的论文",
                            options=current_papers,
                            default=[default_paper] if default_paper else None,
                            format_func=format_paper_display,
                            help="默认选择引用次数最高的论文。可以选择多篇论文一起下载。"
                        )
                        
                        # 下载按钮和选择信息显示
                        col1, col2 = st.columns([1, 4])
                        if col1.button("下载选中论文", disabled=len(selected_papers) == 0):
                            handle_download(selected_papers, "downloads")
                        
                        # 显示选中论文的详细信息
                        if selected_papers:
                            col2.markdown(
                                f"已选择 {len(selected_papers)} 篇论文 "
                                f"(包含引用次数最高的论文: {max_citations} 次)" if max_citations > 0 else 
                                f"已选择 {len(selected_papers)} 篇论文"
                            )

        with tabs[1]:  # CrossRef查询
            st.subheader("CrossRef查询")
            
            # 主要搜索项 - 论文标题
            title_query = st.text_input(
                "论文标题",
                value="The digital workplace is key to digital innovation",
                help="输入要搜索的论文标题（必填项）"
            )
            
            # 可选搜索项
            with st.expander("高级搜索选项（可选）"):
                col1, col2 = st.columns(2)
                with col1:
                    author_query = st.text_input(
                        "作者",
                        value="",
                        help="输入作者姓名",
                        key="crossref_author"
                    )
                    journal_query = st.text_input(
                        "期刊名称",
                        value="",
                        help="输入期刊名称",
                        key="crossref_journal"
                    )
                with col2:
                    year_query = st.text_input(
                        "发表年份",
                        value="",
                        help="输入具体年份，如：2020",
                        key="crossref_year"
                    )
                    doi_query = st.text_input(
                        "DOI",
                        value="",
                        help="输入论文DOI",
                        key="crossref_doi"
                    )
                
                max_results = st.number_input(
                    "最大结果数",
                    min_value=1,
                    max_value=100,
                    value=20,
                    help="限制返回的最大结果数量",
                    key="crossref_max_results"
                )
            
            # 搜索按钮
            if st.button("开始搜索", key="crossref_search"):
                if not title_query:
                    st.error("请输入论文标题")
                else:
                    try:
                        # 创建CrossRef连接器实例
                        crossref = CrossRefConnector()
                        log_message(f"开始CrossRef搜索，标题: {title_query}", "info", "CrossRef")
                        
                        # 构建搜索参数
                        search_params = {
                            'title': title_query,
                            'author': author_query,
                            'year': year_query,
                            'journal': journal_query,
                            'doi': doi_query,
                            'max_results': max_results
                        }
                        log_message(f"搜索参数: {search_params}", "debug", "CrossRef")
                        
                        # 执行搜索
                        papers = crossref.search_with_filters(**search_params)
                        
                        if papers:
                            if len(papers) == 1 and papers[0].title.lower() == title_query.lower():
                                # 精确匹配的情况，使用清单模式显示
                                st.success("找到精确匹配的论文")
                                paper = papers[0]
                                
                                # 使用列表显示详细元数据
                                st.markdown("### 论文详细信息")
                                
                                # 基础书目信息
                                st.markdown("#### 基础书目信息")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"**标题：** {paper.title}")
                                    st.markdown(f"**作者：** {paper.authors}")
                                    st.markdown(f"**DOI：** {paper.DOI if paper.DOI else 'N/A'}")
                                with col2:
                                    st.markdown(f"**年份：** {paper.year if paper.year else 'N/A'}")
                                    st.markdown(f"**期刊：** {paper.jurnal if paper.jurnal else 'N/A'}")
                                    st.markdown(f"**元数据完整度：** {paper.metadata_count} 个有效字段")
                                
                                # 添加下载按钮
                                if st.button("下载此论文"):
                                    handle_download([paper], "downloads")
                                    
                            else:
                                # 相关匹配的情况，使用表格模式显示
                                st.info(f"未找到精确匹配，显示 {len(papers)} 篇相关论文")
                                
                                # 创建表格数据
                                table_data = create_table_data(papers)
                                
                                # 显示表格
                                if table_data:
                                    st.data_editor(
                                        table_data,
                                        column_config=get_table_column_config(),
                                        disabled=True,
                                        hide_index=True
                                    )
                                    
                                    # 显示结果数量
                                    st.markdown(f"共找到 {len(papers)} 篇论文")
                                    
                                    # 添加下载选择和按钮
                                    st.markdown("### 下载选项")
                                    
                                    # 找出默认论文（第一篇）
                                    default_paper = papers[0] if papers else None
                                    
                                    # 创建多选框
                                    selected_papers = st.multiselect(
                                        "选择要下载的论文",
                                        options=papers,
                                        default=[default_paper] if default_paper else None,
                                        format_func=lambda x: (
                                            f"{x.title} "
                                            f"({x.year if x.year else 'N/A'}) "
                                            f"[DOI: {x.DOI if hasattr(x, 'DOI') else 'N/A'}]"
                                        ),
                                        help="可以选择多篇论文一起下载"
                                    )
                                    
                                    # 下载按钮和选择信息显示
                                    col1, col2 = st.columns([1, 4])
                                    if col1.button("下载选中论文", 
                                                 disabled=len(selected_papers) == 0,
                                                 key="crossref_download"):
                                        handle_download(selected_papers, "downloads")
                                    
                                    # 显示选中数量
                                    if selected_papers:
                                        col2.markdown(f"已选择 {len(selected_papers)} 篇论文")
                        else:
                            st.warning("未找到任何结果")
                            log_message("CrossRef搜索未返回结果", "warning", "CrossRef")
                            
                    except Exception as e:
                        error_msg = f"CrossRef搜索出错: {str(e)}"
                        st.error(error_msg)
                        log_message(error_msg, "error", "CrossRef")

        with tabs[2]:  # 验证论文
            st.subheader("论文验证")
            
            # 搜索输入
            query = st.text_input(
                "输入搜索关键词",
                value="Digital Workplace",
                help="输入要搜索和验证的论文关键词"
            )
            
            # 搜索选项
            col1, col2 = st.columns(2)
            with col1:
                max_results = st.number_input(
                    "最大结果数",
                    min_value=1,
                    max_value=50,
                    value=10,
                    help="Scholar搜索返回的最大结果数"
                )
            with col2:
                min_year = st.number_input(
                    "最早发表年份",
                    min_value=1900,
                    max_value=2024,
                    value=2000,
                    key="validate_min_year"
                )
            
            if st.button("开始验证", key="validate_search"):
                try:
                    validator = CrossValidator()
                    result = validator.validate_papers(query, max_results, min_year)
                    
                    if result['success']:
                        # 首先显示Scholar搜索结果
                        st.subheader("Google Scholar搜索结果")
                        scholar_table = create_table_data(result['scholar_papers'])
                        st.data_editor(
                            scholar_table,
                            column_config=get_table_column_config(),
                            disabled=True,
                            hide_index=True
                        )
                        
                        # 显示验证结果
                        st.subheader("CrossRef验证结果")
                        validated_table = validator.create_validation_table(result['validated_papers'])
                        st.data_editor(
                            validated_table,
                            column_config=validator.get_table_column_config(),
                            disabled=True,
                            hide_index=True
                        )
                        
                        # 显示��证统计
                        st.success(result['message'])
                        
                        # 添加下载选项
                        validated_papers = [p for p in result['validated_papers'] if p.validated]
                        if validated_papers:
                            st.markdown("### 下载选项")
                            selected_papers = st.multiselect(
                                "选择要下载的论文",
                                options=validated_papers,
                                format_func=lambda x: f"{x.title} ({x.year if x.year else 'N/A'})",
                                help="只显示已通过验证的论文"
                            )
                            
                            if st.button("下载选中论文", disabled=len(selected_papers) == 0):
                                handle_download(selected_papers, "downloads")
                    else:
                        st.error(result['message'])
                        
                except Exception as e:
                    error_msg = f"验证过程发生错误: {str(e)}"
                    st.error(error_msg)
                    log_message(error_msg, "error", "验证")

    elif st.session_state.current_function == "论文下载功能":
        # [保持原有的论文下载功能代码不变...]
        
    elif st.session_state.current_function == "论文过滤功能":
        # [保持原有的论文过滤功能代码不变...]
        
    elif st.session_state.current_function == "论文数据管理":
        # 调用数据库管理功能
        render_database_management()
        
    elif st.session_state.current_function == "配置管理":
        # [保持原有的配置管理功能代码不变...]

# 右侧日志面板
with right_sidebar:
    render_log_sidebar(right_sidebar) 