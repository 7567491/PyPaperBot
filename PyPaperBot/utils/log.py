import logging
import os
from datetime import datetime
from collections import deque
import streamlit as st
import traceback

class StreamlitHandler(logging.Handler):
    def emit(self, record):
        try:
            # 获取更详细的日志信息
            log_entry = self.format(record)
            level_name = record.levelname
            module_name = record.name
            func_name = record.funcName
            line_no = record.lineno
            thread_name = record.threadName
            
            # 构建详细的日志消息
            message = record.getMessage()
            if func_name != '<module>':
                message = f"{message} [函数:{func_name}:{line_no}]"
            
            # 对于异常信息，添加完整的堆栈跟踪
            if record.exc_info:
                message = f"{message}\n{''.join(traceback.format_exception(*record.exc_info))}"
            
            # 映射日志级别到颜色系统
            level_map = {
                'DEBUG': 'debug',
                'INFO': 'info',
                'WARNING': 'warning',
                'ERROR': 'error',
                'CRITICAL': 'error'
            }
            level = level_map.get(level_name, 'info')
            
            # 记录日志
            log_message(message, level, module_name)
            
        except Exception as e:
            print(f"日志处理错误: {str(e)}")

class FileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding='utf-8'):
        # 确保日志目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        super().__init__(filename, mode, encoding)

def get_log_file_path():
    """获取日志文件路径"""
    log_dir = "log"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return os.path.join(log_dir, f"{timestamp}.log")

def setup_logging():
    """配置日志系统"""
    # 配置根日志记录器
    log_format = '%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s] [%(funcName)s:%(lineno)d] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format
    )
    logger = logging.getLogger()

    # 添加文件处理器
    file_handler = FileHandler(get_log_file_path())
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # 添加Streamlit处理器
    streamlit_handler = StreamlitHandler()
    streamlit_formatter = logging.Formatter(log_format, date_format)
    streamlit_handler.setFormatter(streamlit_formatter)
    logger.addHandler(streamlit_handler)

    # 设置详细的日志级别
    logging.getLogger('PyPaperBot').setLevel(logging.DEBUG)
    logging.getLogger('selenium').setLevel(logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.DEBUG)

    # 记录启动信息
    logger.info("="*50)
    logger.info("PyPaperBot 启动")
    logger.info(f"日志文件: {file_handler.baseFilename}")
    logger.info("="*50)

def init_log_queue():
    """初始化日志队列"""
    if 'log_queue' not in st.session_state:
        st.session_state.log_queue = deque(maxlen=1000)
    return st.session_state.log_queue

def log_message(message, level="info", module="系统"):
    """记录日志消息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
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
    # 使用container.container()创建一个固定高度的容器
    with container.container():
        # 标题和按钮使用最小必要的空间
        container.markdown("### 系统日志", help="实时显示系统运行日志")
        
        # 按钮行使用更紧凑的样式
        button_container = container.container()
        col1, col2 = button_container.columns(2)
        if col1.button("清除日志", use_container_width=True):
            st.session_state.log_queue.clear()
            log_message("日志已清除", "info", "日志系统")
        
        if col2.button("打开日志目录", use_container_width=True):
            open_log_directory()
        
        # 日志容器紧接着按钮
        container.markdown("""
            <div class="log-container" style="
                height: calc(100vh - 150px);  /* 动态计算高度 */
                overflow-y: auto;
                background-color: rgba(0, 0, 0, 0.2);
                padding: 8px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                margin-top: 5px;  /* 减小顶部边距 */
                white-space: pre-wrap;
                word-wrap: break-word;
                line-height: 1.3;
            ">
        """, unsafe_allow_html=True)
        
        # 显示所有日志，按时间倒序
        for log in reversed(list(st.session_state.log_queue)):
            # 更紧凑的日志条目样式
            message_lines = log["message"].split('\n')
            formatted_message = '<br>'.join(message_lines)
            
            container.markdown(
                f'<div class="log-entry" style="'
                f'color: {log["color"]}; '
                f'margin-bottom: 4px; '  # 减小条目间距
                f'padding: 2px 0; '      # 添加适当的内边距
                f'">'
                f'[{log["timestamp"]}] '
                f'[{log["level"]}] '
                f'[{log["module"]}]<br>'
                f'{formatted_message}'
                f'</div>',
                unsafe_allow_html=True
            )
        
        container.markdown('</div>', unsafe_allow_html=True)

def export_logs():
    """导出日志到文件"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join("log", f"export_{timestamp}.txt")
        os.makedirs("log", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            for log in list(st.session_state.log_queue):
                f.write(
                    f'[{log["timestamp"]}] [{log["level"]}] [{log["module"]}] {log["message"]}\n'
                )
        
        log_message(f"日志已导出到文件: {filename}", "success", "日志系统")
    except Exception as e:
        log_message(f"导出日志失败: {str(e)}", "error", "日志系统")

def open_log_directory():
    """打开日志目录"""
    try:
        log_dir = os.path.abspath("log")
        if os.path.exists(log_dir):
            os.startfile(log_dir) if os.name == 'nt' else os.system(f'xdg-open {log_dir}')
            log_message("已打开日志目录", "info", "日志系统")
        else:
            log_message("日志目录不存在", "warning", "日志系统")
    except Exception as e:
        log_message(f"打开日志目录失败: {str(e)}", "error", "日志系统") 