import logging
from datetime import datetime
from collections import deque
import streamlit as st

class StreamlitHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        level_name = record.levelname
        module_name = record.name
        
        # 映射日志级别到我们的颜色系统
        level_map = {
            'DEBUG': 'debug',
            'INFO': 'info',
            'WARNING': 'warning',
            'ERROR': 'error',
            'CRITICAL': 'error'
        }
        level = level_map.get(level_name, 'info')
        
        # 使用全局log_message函数记录日志
        log_message(log_entry, level, module_name)

def setup_logging():
    """配置日志系统"""
    # 配置根日志记录器
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    # 添加Streamlit处理器
    streamlit_handler = StreamlitHandler()
    streamlit_handler.setFormatter(
        logging.Formatter('%(message)s')
    )
    logger.addHandler(streamlit_handler)

    # 设置各个模块的日志级别
    logging.getLogger('PyPaperBot.Scholar').setLevel(logging.DEBUG)
    logging.getLogger('PyPaperBot.Searcher').setLevel(logging.DEBUG)
    logging.getLogger('PyPaperBot.CrossRefConnector').setLevel(logging.DEBUG)

def init_log_queue():
    """初始化日志队列"""
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
    color = color_map.get(level.lower(), "white")
    log_entry = {
        'timestamp': timestamp,
        'level': level.upper(),
        'module': module,
        'message': message,
        'color': color
    }
    st.session_state.log_queue.append(log_entry)

def render_log_sidebar(container):
    """渲染日志侧边栏"""
    container.markdown("### 系统日志")
    
    # 清除日志按钮
    if container.button("清除日志"):
        st.session_state.log_queue.clear()
        log_message("日志已清除", "info", "日志系统")
    
    # 显示日志容器
    container.markdown("""
        <div class="log-container" style="
            height: 800px;
            overflow-y: auto;
            background-color: rgba(0, 0, 0, 0.2);
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            margin-top: 10px;
            white-space: pre-wrap;
            word-wrap: break-word;
        ">
    """, unsafe_allow_html=True)
    
    # 显示所有日志，按时间倒序
    for log in reversed(list(st.session_state.log_queue)):
        container.markdown(
            f'<div class="log-entry" style="color: {log["color"]}; margin-bottom: 5px;">'
            f'[{log["timestamp"]}] '
            f'[{log["level"]}] '
            f'[{log["module"]}] '
            f'{log["message"]}'
            f'</div>',
            unsafe_allow_html=True
        )
    
    container.markdown('</div>', unsafe_allow_html=True) 