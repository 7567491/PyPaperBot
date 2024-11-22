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
from db.db_backup import backup_database, restore_database
from db.db_utils import save_scholar_papers, save_crossref_papers, save_verified_papers
import sqlite3
from datetime import datetime
import pandas as pd
import os
import traceback

# 设置页面配置
st.set_page_config(
    page_title="PyPaperBot Web",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/PyPaperBot',
        'Report a bug': "https://github.com/your-repo/PyPaperBot/issues",
        'About': "# PyPaperBot Web\n论文搜索和管理工具"
    }
)

# 初始化日队列（移到最前面）
if 'log_queue' not in st.session_state:
    st.session_state.log_queue = deque(maxlen=1000)

# 配置日志系统
setup_logging()
init_log_queue()

# 在文件开头添加session_state初始化
if 'search_results' not in st.session_state:
    st.session_state.search_results = {
        'scholar': None,
        'crossref': None,
        'verified': None
    }

# 在文件开头添加状态变量
if 'db_states' not in st.session_state:
    st.session_state.db_states = {
        'scholar': {'saving': False, 'message': None},
        'crossref': {'saving': False, 'message': None},
        'verified': {'saving': False, 'message': None}
    }

# 在文件开头添加状态变量
if 'ui_states' not in st.session_state:
    st.session_state.ui_states = {
        'search_status': None,  # 搜索状态
        'save_status': None,    # 保存状态
        'error_message': None,  # 错误信息
        'success_message': None # 成功信息
    }

# 添加状态显示函数
def show_status():
    """显示当前状态"""
    if st.session_state.ui_states['error_message']:
        st.error(st.session_state.ui_states['error_message'])
        st.session_state.ui_states['error_message'] = None
        
    if st.session_state.ui_states['success_message']:
        st.success(st.session_state.ui_states['success_message'])
        st.session_state.ui_states['success_message'] = None
        
    if st.session_state.ui_states['search_status']:
        st.info(st.session_state.ui_states['search_status'])
        
    if st.session_state.ui_states['save_status']:
        st.info(st.session_state.ui_states['save_status'])

# 添加页面标题和说明
st.title("PyPaperBot Web")
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    </style>
    <div class="main-title">论文搜索与管理系统</div>
    <div class="sub-title">支持Google Scholar搜索、CrossRef验证和数据库管理</div>
    """, unsafe_allow_html=True)

# 添加功能说明
with st.expander("功能说明"):
    st.markdown("""
    ### 主要功能
    1. **Google Scholar搜索**
       - 支持关键词搜索
       - 可设置年份范围
       - 显示引用次数
       
    2. **CrossRef验证**
       - 验证论文元数据
       - 获取DOI信息
       - 显示出版信息
       
    3. **数据管理**
       - 保存搜索结果
       - 管理验证记录
       - 导出数据
    """)

# 添加状态栏
status_container = st.container()
with status_container:
    show_status()

# 定义回调函数
def handle_save_scholar():
    st.session_state.db_states['scholar']['saving'] = True

def handle_save_crossref():
    st.session_state.db_states['crossref']['saving'] = True

def handle_save_verified():
    st.session_state.db_states['verified']['saving'] = True

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
            st.session_state.current_function = "论文搜索功能"
        
        # 左侧边栏按钮
        if st.button("论文搜索功能"):
            st.session_state.current_function = "论文搜索功能"
        if st.button("论文查看"):
            st.session_state.current_function = "论文查看"
        if st.button("单个论文下载"):
            st.session_state.current_function = "单个论文下载"
        if st.button("论文批量下载"):
            st.session_state.current_function = "论文批量下载"
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
                with st.spinner("正在搜索..."):
                    # 显示进度条
                    progress_bar = st.progress(0)
                    progress_text = st.empty()
                    
                    # 更新进度 - 开始搜索
                    progress_bar.progress(0.3)
                    progress_text.text("正在连接Google Scholar...")
                    
                    result = handle_scholar_search(query, scholar_pages, min_year)
                    
                    if result and result['success']:
                        papers = result['papers']
                        # 保存到session_state并记录日志
                        st.session_state.search_results['scholar'] = {
                            'papers': papers,
                            'query': query,
                            'timestamp': datetime.now().isoformat()
                        }
                        log_message(f"保存 {len(papers)} 篇Scholar论文到session_state", "info", "搜索")
                        
                        # 更新进度 - 获取结果
                        progress_bar.progress(0.6)
                        progress_text.text("正在处理搜索结果...")
                        
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
                        
                        # 获取当前页的文
                        current_papers, start_idx, end_idx = get_page_papers(papers, current_page, items_per_page)
                        
                        # 创建表格数据
                        table_data = create_table_data(current_papers, start_idx)
                        
                        # 更新进度 - 完成
                        progress_bar.progress(1.0)
                        progress_text.text("搜索完成")
                        
                        # 显示表格
                        if table_data:
                            st.data_editor(
                                table_data,
                                column_config=get_table_column_config(),
                                disabled=True,
                                hide_index=True
                            )
                            
                            # 显示分页信息
                            st.markdown(f"显示第 {start_idx + 1} 到 {end_idx} 条，共 {len(papers)} 条")
                            
                            # 直接储到数据库
                            try:
                                status_area = st.empty()
                                status_area.info("正在保存到数据库...")
                                
                                # 连接数据库
                                db_path = os.path.join("db", "paper.db")
                                log_message(f"连接数据库: {db_path}", "info", "数据库")
                                conn = sqlite3.connect(db_path)
                                
                                # 保存论文
                                if save_scholar_papers(conn, papers, query):
                                    status_area.success(f"成功保存 {len(papers)} 篇论文到数据库")
                                    log_message(f"成功保存 {len(papers)} 篇Scholar论文", "success", "数据库")
                                conn.close()
                                
                            except Exception as e:
                                error_msg = f"保存失败: {str(e)}"
                                status_area.error(error_msg)
                                log_message(error_msg, "error", "数据库")
                                log_message(f"错误详情: {traceback.format_exc()}", "error", "数据库")

        with tabs[1]:  # CrossRef查询
            st.subheader("CrossRef查询")
            
            # 主要搜索 - 论文标题
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
                        help="输入期刊称",
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
                        with st.spinner("正在搜索..."):
                            # 显示进度条
                            progress_bar = st.progress(0)
                            progress_text = st.empty()
                            
                            # 更新进度 - 开始搜索
                            progress_bar.progress(0.3)
                            progress_text.text("正在连接CrossRef...")
                            
                            # 建CrossRef连接器实例
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
                            
                            # 更新进度 - 执行搜索
                            progress_bar.progress(0.6)
                            progress_text.text("正在搜索论文...")
                            
                            # 执行搜索
                            papers = crossref.search_with_filters(**search_params)
                            # 保存到session_state并记录日志
                            st.session_state.search_results['crossref'] = {
                                'papers': papers,
                                'params': search_params,
                                'timestamp': datetime.now().isoformat()
                            }
                            log_message(f"保存 {len(papers)} 篇CrossRef论文到session_state", "info", "搜索")
                            
                            # 更新进度 - 完成
                            progress_bar.progress(1.0)
                            progress_text.text("搜索完成")
                            
                            if papers:
                                if len(papers) == 1 and papers[0].title.lower() == title_query.lower():
                                    # 精确匹配的情况，使用清单模式显示
                                    st.success("找到精确匹配的论文")
                                    paper = papers[0]
                                    
                                    # 使用列表显示详细元数据
                                    st.markdown("### 论文详细信息")
                                    
                                    # 基础书目息
                                    st.markdown("#### 基础书目信息")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown(f"**题：** {paper.title}")
                                        st.markdown(f"**作者：** {paper.authors}")
                                        st.markdown(f"**DOI：** {paper.DOI if paper.DOI else 'N/A'}")
                                    with col2:
                                        st.markdown(f"**年份：** {paper.year if paper.year else 'N/A'}")
                                        st.markdown(f"**期刊：** {paper.jurnal if paper.jurnal else 'N/A'}")
                                        st.markdown(f"**元数据完整度：** {paper.metadata_count} 个有效字段")
                                    
                                    # 直接存储到数据库
                                    try:
                                        status_area = st.empty()
                                        status_area.info("正在保存到数据库...")
                                        
                                        # 连接数据库
                                        db_path = os.path.join("db", "paper.db")
                                        log_message(f"连接数据库: {db_path}", "info", "数据库")
                                        conn = sqlite3.connect(db_path)
                                        
                                        # 保存论文
                                        if save_crossref_papers(conn, papers):
                                            status_area.success(f"成功保存 {len(papers)} 篇论文到数据库")
                                            log_message(f"成功保存 {len(papers)} 篇CrossRef论文", "success", "数据库")
                                        conn.close()
                                        
                                    except Exception as e:
                                        error_msg = f"保存失败: {str(e)}"
                                        status_area.error(error_msg)
                                        log_message(error_msg, "error", "数据库")
                                        log_message(f"错误详情: {traceback.format_exc()}", "error", "数据库")
                                else:
                                    # 相关匹配的情况使用表格模式显示
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
                                        
                                        # 直接存储到数据库
                                        try:
                                            status_area = st.empty()
                                            status_area.info("正在保存到数据库...")
                                            
                                            # 连接数据库
                                            db_path = os.path.join("db", "paper.db")
                                            log_message(f"连接数据库: {db_path}", "info", "数据库")
                                            conn = sqlite3.connect(db_path)
                                            
                                            # 保存论文
                                            if save_crossref_papers(conn, papers):
                                                status_area.success(f"成功保存 {len(papers)} 篇论文到数据库")
                                                log_message(f"成功保存 {len(papers)} 篇CrossRef论文", "success", "数据库")
                                            conn.close()
                                            
                                        except Exception as e:
                                            error_msg = f"保存失败: {str(e)}"
                                            status_area.error(error_msg)
                                            log_message(error_msg, "error", "数据库")
                                            log_message(f"错误详情: {traceback.format_exc()}", "error", "数据库")
                            else:
                                st.warning("未找到任何结果")
                                log_message("CrossRef搜索未返回结果", "warning", "CrossRef")
                            
                            # 清理进度显示
                            progress_bar.empty()
                            progress_text.empty()
                            
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
                help="输入要索和验证的论文关键词"
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
                        # 保存到session_state并记录日志
                        st.session_state.search_results['verified'] = {
                            'papers': result['validated_papers'],
                            'scholar_papers': result['scholar_papers'],
                            'validated_count': result['validated_count'],
                            'timestamp': datetime.now().isoformat()
                        }
                        log_message(f"保存验证结果到session_state: {result['validated_count']} 篇论文", "info", "验证")
                        
                        # 显示验证结果
                        st.subheader("验证结果")
                        validated_table = validator.create_validation_table(result['validated_papers'])
                        st.data_editor(
                            validated_table,
                            column_config=validator.get_table_column_config(),
                            disabled=True,
                            hide_index=True
                        )
                        
                        # 显示验证统计
                        st.success(result['message'])
                        
                        # 直接存储到数据库
                        try:
                            status_area = st.empty()
                            status_area.info("正在保存到数据库...")
                            
                            # 连接数据库
                            db_path = os.path.join("db", "paper.db")
                            log_message(f"连接数据库: {db_path}", "info", "数据库")
                            conn = sqlite3.connect(db_path)
                            
                            try:
                                # 首先保存Scholar论文
                                log_message("保存Scholar论文...", "info", "数据库")
                                if save_scholar_papers(conn, result['scholar_papers'], query):
                                    log_message(f"成功保存 {len(result['scholar_papers'])} 篇Scholar论文", "success", "数据库")
                                    
                                    # 保存验证论文
                                    log_message("保存验证论文...", "info", "数据库")
                                    if save_verified_papers(conn, result['validated_papers']):
                                        success_msg = f"成功保存 {result['validated_count']} 篇验证论文到数据库"
                                        status_area.success(success_msg)
                                        log_message(success_msg, "success", "数据库")
                                    else:
                                        status_area.error("保存验证论文失败")
                                        log_message("保存验证论文失败", "error", "数据库")
                                else:
                                    status_area.error("保存Scholar论文失败")
                                    log_message("保存Scholar论文失败", "error", "数据库")
                                    
                            except Exception as e:
                                conn.rollback()
                                error_msg = f"保存过程出错: {str(e)}"
                                status_area.error(error_msg)
                                log_message(error_msg, "error", "数据库")
                                log_message(f"错误详情: {traceback.format_exc()}", "error", "数据库")
                            finally:
                                conn.close()
                                log_message("数据库连接已关闭", "info", "数据库")
                                
                        except Exception as e:
                            error_msg = f"数据库操作失败: {str(e)}"
                            st.error(error_msg)
                            log_message(error_msg, "error", "数据库")
                            log_message(f"错误详情: {traceback.format_exc()}", "error", "数据库")
                    else:
                        st.error(result['message'])
                        
                except Exception as e:
                    error_msg = f"验证过程发生错误: {str(e)}"
                    st.error(error_msg)
                    log_message(error_msg, "error", "验证")

    elif st.session_state.current_function == "论文下载功能":
        st.subheader("论文下载功能")
        st.info("此功能正在开发中...")
        
    elif st.session_state.current_function == "论文过滤功能":
        st.subheader("论文过滤功能")
        st.info("此功能正在开发中...")
        
    elif st.session_state.current_function == "论文数据管理":
        try:
            # 导入数据库管理模块
            from db.db_main import DatabaseManager
            
            # 创建数据库管理器实例
            db_manager = DatabaseManager()
            
            # 渲染数据库管理界面
            db_manager.render_db_management()
            
        except Exception as e:
            error_msg = f"数据库管理功能出错: {str(e)}"
            log_message(error_msg, "error", "数据库")
            st.error(error_msg)
            # 显示详细错误信息
            st.error(f"错误详情: {traceback.format_exc()}")

    elif st.session_state.current_function == "配置管理":
        st.subheader("配置管理")
        st.info("此功能正在开发中...")

# 右侧日志面板
with right_sidebar:
    render_log_sidebar(right_sidebar) 