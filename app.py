import os
import sys
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 然后再导入Searcher
from PyPaperBot.Searcher import Searcher

import streamlit as st
import logging
from datetime import datetime
from collections import deque

# 设置页面配置
st.set_page_config(
    page_title="PyPaperBot Web",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 自定义CSS样式
st.markdown("""
    <style>
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
    .stTab {
        color: white;
    }
    .log-container {
        height: 600px;
        overflow-y: auto;
        background-color: rgba(0, 0, 0, 0.2);
        padding: 10px;
        border-radius: 5px;
    }
    .log-entry {
        margin-bottom: 5px;
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

# 初始化日志队列
if 'log_queue' not in st.session_state:
    st.session_state.log_queue = deque(maxlen=100)  # 最多保存100条日志

def log_message(message, level="info", module="系统"):
    """记录日志消息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color_map = {
        "info": "#FFFFFF",      # 白色
        "success": "#00FF00",   # 绿色
        "warning": "#FFD700",   # 黄色
        "error": "#FF0000",     # 红色
        "debug": "#808080"      # 灰色
    }
    color = color_map.get(level, "white")
    log_entry = {
        'timestamp': timestamp,
        'level': level.upper(),
        'module': module,
        'message': message,
        'color': color
    }
    st.session_state.log_queue.append(log_entry)

# 创建三列布局
left_sidebar, main_content, right_sidebar = st.columns([1, 2, 1])

# 左侧边栏
with left_sidebar:
    st.sidebar.title("PyPaperBot Web")
    st.sidebar.markdown("---")

    # 初始化 session_state
    if 'current_function' not in st.session_state:
        st.session_state.current_function = None

    # 左侧边栏按钮
    if st.sidebar.button("论文搜索功能"):
        st.session_state.current_function = "论文搜索功能"
        log_message("切换到论文搜索功能", "info", "导航")
    if st.sidebar.button("论文下载功能"):
        st.session_state.current_function = "论文下载功能"
        log_message("切换到论文下载功能", "info", "导航")
    if st.sidebar.button("论文过滤功能"):
        st.session_state.current_function = "论文过滤功能"
        log_message("切换到论文过滤功能", "info", "导航")
    if st.sidebar.button("论文数据管理"):
        st.session_state.current_function = "论文数据管理"
        log_message("切换到论文数据管理", "info", "导航")
    if st.sidebar.button("配置管理"):
        st.session_state.current_function = "配置管理"
        log_message("切换到配置管理", "info", "导航")

# 右侧边栏（日志面板）
with right_sidebar:
    st.markdown("### 系统日志")
    
    # 清除日志按钮
    if st.button("清除日志"):
        st.session_state.log_queue.clear()
        log_message("日志已清除", "info", "日志系统")
    
    # 显示日志容器
    st.markdown("""
        <div class="log-container" style="
            height: 800px;
            overflow-y: auto;
            background-color: rgba(0, 0, 0, 0.2);
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            margin-top: 10px;
        ">
    """, unsafe_allow_html=True)
    
    # 显示所有日志，按时间倒序
    for log in reversed(list(st.session_state.log_queue)):
        st.markdown(
            f'<div class="log-entry" style="color: {log["color"]}; margin-bottom: 5px;">'
            f'[{log["timestamp"]}]<br>'
            f'[{log["level"]}] [{log["module"]}]<br>'
            f'{log["message"]}'
            f'</div>',
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

# 主要内容区域
with main_content:
    if st.session_state.current_function is None:
        st.session_state.current_function = "论文搜索功能"
        log_message("进入论文搜索功能", "info", "系统")
        
    if st.session_state.current_function == "论文搜索功能":
        tabs = st.tabs(["Google Scholar搜索", "CrossRef查询", "DOI搜索"])
        
        with tabs[0]:  # Google Scholar搜索
            st.subheader("Google Scholar搜索")
            query = st.text_input("输入搜索关键词", value="Digital Workplace")
            scholar_pages = st.text_input("Scholar页数 (例如: 1-3 或 5)", value="1")
            min_year = st.number_input("最早发表年份", min_value=1900, max_value=2024, value=2000)
            
            if st.button("开始搜索", key="scholar_search"):
                log_message("开始Scholar搜索请求", "info", "搜索")
                log_message(f"搜索关键词: {query}", "debug", "搜索")
                log_message(f"搜索页数: {scholar_pages}", "debug", "搜索")
                log_message(f"最早年份: {min_year}", "debug", "搜索")
                
                searcher = Searcher()
                try:
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
                        for i, paper in enumerate(result['papers'], 1):
                            log_message(f"显示论文 {i}: {paper.title}", "debug", "搜索结果")
                            with st.expander(f"{i}. {paper.title}"):
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    if paper.authors:
                                        st.write(f"**作者:** {paper.authors}")
                                    if paper.year:
                                        st.write(f"**年份:** {paper.year}")
                                    if paper.doi:
                                        st.write(f"**DOI:** {paper.doi}")
                                    if paper.url:
                                        st.write(f"**URL:** [{paper.url}]({paper.url})")
                                with col2:
                                    if hasattr(paper, 'citations'):
                                        st.write(f"**引用次数:** {paper.citations}")
                                    if st.button("添加到下载队列", key=f"download_{i}"):
                                        log_message(f"添加论文到下载队列: {paper.title}", "info", "下载队列")
                                        st.success("已添加到下载队列")
                                        
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
            use_doi_filename = st.checkbox("使用DOI作为文件名")
            scihub_mirror = st.text_input("SciHub镜像网址", value="https://sci-hub.se")
            
            if st.button("开始下载", key="start_download"):
                log_message("开始下载论文", "info", "下载")
                log_message(f"下载目录: {download_dir}", "debug", "下载")
                log_message(f"使用DOI作为文件名: {use_doi_filename}", "debug", "下载")
                log_message(f"SciHub镜像网址: {scihub_mirror}", "debug", "下载")
                # TODO: 实现下载逻辑
            
        with tabs[1]:  # 代理设置
            st.subheader("代理设置")
            proxy = st.text_input("代理服务器 (格式: protocol://ip:port)")
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

# 底部状态栏
st.markdown("---")
st.markdown("PyPaperBot Web Interface - 开发中") 