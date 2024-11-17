import streamlit as st
import sqlite3
import os
from datetime import datetime
import traceback
from .db_init import init_database
from .db_backup import backup_database, restore_database
from .db_scholar import query_scholar_papers
from .db_crossref import query_crossref_papers
from .db_verified import query_verified_papers
from .db_fulltext import query_paper_fulltext
from .db_utils import save_scholar_papers, save_crossref_papers, save_verified_papers
from PyPaperBot.utils.log import log_message
from typing import List
import pandas as pd

class DatabaseManager:
    def __init__(self, db_path="db/paper.db"):
        self.db_path = db_path
        self.ensure_db_exists()
        
    def ensure_db_exists(self):
        """确保数据库文件存在，只在第一次运行时初始化"""
        try:
            if not os.path.exists(self.db_path):
                log_message("数据库文件不存在，开始初始化...", "info", "数据库")
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
                init_database(self.db_path)
                log_message("数据库初始化完成", "success", "数据库")
            else:
                # 检查数据库是否可以正常连接
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    # 检查是否存在所需的表
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = {row[0] for row in cursor.fetchall()}
                    required_tables = {
                        'scholar_papers', 'crossref_papers', 
                        'verified_papers', 'paper_fulltext'
                    }
                    
                    if not required_tables.issubset(tables):
                        missing_tables = required_tables - tables
                        log_message(f"数据库缺少必要的表: {missing_tables}，需要初始化", "warning", "数据库")
                        init_database(self.db_path)
                        log_message("数据库表初始化完成", "success", "数据库")
                    else:
                        log_message("数据库结构完整，可以正常使用", "info", "数据库")
                    
                    conn.close()
                except sqlite3.Error as e:
                    log_message(f"数据库连接测试失败: {str(e)}", "error", "数据库")
                    raise
                    
        except Exception as e:
            error_msg = f"数据库初始化失败: {str(e)}"
            log_message(error_msg, "error", "数据库")
            raise
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            conn = sqlite3.connect(self.db_path)
            log_message(f"成功连接数据库: {self.db_path}", "debug", "数据库")
            return conn
        except Exception as e:
            error_msg = f"数据库连接失败: {str(e)}"
            log_message(error_msg, "error", "数据库")
            raise
    
    def render_db_management(self):
        """渲染数据库管理界面"""
        st.title("论文数据管理")
        
        try:
            # 显示数据库基本信息
            self.show_db_info()
            
            # 创建二级功能标签页
            tabs = st.tabs([
                "数据库查询", 
                "数据库备份与恢复", 
                "Scholar论文查询",
                "CrossRef论文查询",
                "验证论文查询",
                "已下载论文全文"
            ])
            
            # 数据库查询标签页
            with tabs[0]:
                st.subheader("数据库查询")
                
                # 显示最近保存的记录
                st.markdown("#### 最近保存的记录")
                try:
                    conn = self.get_connection()
                    cursor = conn.cursor()
                    
                    # Scholar论文
                    with st.expander("最近保存的Scholar论文", expanded=True):
                        cursor.execute("""
                            SELECT title, authors, year, doi, search_timestamp 
                            FROM scholar_papers 
                            ORDER BY search_timestamp DESC 
                            LIMIT 5
                        """)
                        recent_scholar = cursor.fetchall()
                        if recent_scholar:
                            df_scholar = pd.DataFrame(recent_scholar, 
                                columns=["标题", "作者", "年份", "DOI", "保存时间"])
                            df_scholar["保存时间"] = pd.to_datetime(df_scholar["保存时间"])
                            st.dataframe(df_scholar, hide_index=True)
                        else:
                            st.info("暂无Scholar论文记录")
                    
                    # CrossRef论文
                    with st.expander("最近保存的CrossRef论文", expanded=True):
                        cursor.execute("""
                            SELECT title, authors, year, doi, verification_timestamp 
                            FROM crossref_papers 
                            ORDER BY verification_timestamp DESC 
                            LIMIT 5
                        """)
                        recent_crossref = cursor.fetchall()
                        if recent_crossref:
                            df_crossref = pd.DataFrame(recent_crossref, 
                                columns=["标题", "作者", "年份", "DOI", "保存时间"])
                            df_crossref["保存时间"] = pd.to_datetime(df_crossref["保存时间"])
                            st.dataframe(df_crossref, hide_index=True)
                        else:
                            st.info("暂无CrossRef论文记录")
                    
                    # 验证论文
                    with st.expander("最近保存的验证论文", expanded=True):
                        cursor.execute("""
                            SELECT title, authors, year, doi, verification_timestamp,
                                   CASE verification_status
                                       WHEN 0 THEN '待验证'
                                       WHEN 1 THEN '完全匹配'
                                       WHEN 2 THEN '部分匹配'
                                       WHEN 3 THEN '不匹配'
                                   END as status
                            FROM verified_papers 
                            ORDER BY verification_timestamp DESC 
                            LIMIT 5
                        """)
                        recent_verified = cursor.fetchall()
                        if recent_verified:
                            df_verified = pd.DataFrame(recent_verified, 
                                columns=["标题", "作者", "年份", "DOI", "保存时间", "验证状态"])
                            df_verified["保存时间"] = pd.to_datetime(df_verified["保存时间"])
                            st.dataframe(df_verified, hide_index=True)
                        else:
                            st.info("暂无验证论文记录")
                    
                    conn.close()
                    
                except Exception as e:
                    error_msg = f"获取最近保存记录失败: {str(e)}"
                    log_message(error_msg, "error", "数据库")
                    st.error(error_msg)
                
                # 显示数据库表结构
                st.markdown("#### 数据库表结构")
                
                # 定义所有表
                tables = {
                    "scholar_papers": "Scholar搜索结果表",
                    "crossref_papers": "CrossRef验证结果表",
                    "verified_papers": "验证匹配的论文表",
                    "paper_fulltext": "论文全文表"
                }
                
                # 显示每个表的信息
                for table_name, description in tables.items():
                    with st.expander(f"{description} ({table_name})"):
                        # 获取表结构
                        schema = self.get_table_schema(table_name)
                        
                        # 获取记录数
                        count = self.get_table_count(table_name)
                        
                        # 显示表信息
                        st.markdown(f"##### 表结构")
                        
                        # 创建表结构数据
                        schema_data = []
                        for col in schema:
                            schema_data.append({
                                "序号": col[0],
                                "字段名": col[1],
                                "类型": col[2],
                                "是否可空": "否" if col[3] else "是",
                                "默认值": col[4] if col[4] is not None else "无",
                                "主键": "是" if col[5] else "否"
                            })
                        
                        # 显示表结构
                        st.dataframe(
                            schema_data,
                            column_config={
                                "序号": st.column_config.NumberColumn("序号", width=70),
                                "字段名": st.column_config.TextColumn("字段名", width=150),
                                "类型": st.column_config.TextColumn("类型", width=100),
                                "是否可空": st.column_config.TextColumn("是否可空", width=100),
                                "默认值": st.column_config.TextColumn("默认值", width=100),
                                "主键": st.column_config.TextColumn("主键", width=70)
                            },
                            hide_index=True
                        )
                        
                        # 显示记录数
                        st.info(f"当前记录数: {count}")
                        
                        # 显示表索引
                        st.markdown("##### 表索引")
                        cursor = self.get_connection().cursor()
                        cursor.execute(f"SELECT * FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}'")
                        indexes = cursor.fetchall()
                        
                        if indexes:
                            for idx in indexes:
                                st.code(idx[4], language="sql")  # 显示索引创建语句
                        else:
                            st.text("无索引")
            
            # 数据库备份与恢复
            with tabs[1]:
                st.subheader("数据库备份与恢复")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### 数据库备份")
                    if st.button("创建备份", key="create_backup"):
                        backup_file = backup_database(self.db_path)
                        if backup_file:
                            st.success(f"备份创建成功: {backup_file}")
                    
                with col2:
                    st.markdown("##### 数据库恢复")
                    backup_files = self.get_backup_files()
                    if backup_files:
                        selected_backup = st.selectbox(
                            "选择要恢复的备份文件",
                            backup_files,
                            format_func=lambda x: os.path.basename(x)
                        )
                        if st.button("恢复数据库", key="restore_db"):
                            if restore_database(selected_backup, self.db_path):
                                st.success("数据库恢复成功")
                    else:
                        st.info("没有可用的备份文件")
            
            # Scholar论文查询
            with tabs[2]:
                st.subheader("Scholar论文查询")
                query_scholar_papers(self.get_connection())
            
            # CrossRef论文查询
            with tabs[3]:
                st.subheader("CrossRef论文查询")
                query_crossref_papers(self.get_connection())
            
            # 验证论文查询
            with tabs[4]:
                st.subheader("验证论文查询")
                query_verified_papers(self.get_connection())
            
            # 已下载论文全文
            with tabs[5]:
                st.subheader("已下载论文全文")
                query_paper_fulltext(self.get_connection())
            
        except Exception as e:
            error_msg = f"数据库管理界面渲染失败: {str(e)}"
            log_message(error_msg, "error", "数据库")
            st.error(error_msg)
    
    def show_db_info(self):
        """显示数据库基本信息"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 获取各表的记录数
            stats = {}
            tables = [
                "scholar_papers",
                "crossref_papers",
                "verified_papers",
                "paper_fulltext"
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats[table] = count
                    log_message(f"表 {table} 记录数: {count}", "debug", "数据库")
                except Exception as e:
                    log_message(f"获取表 {table} 记录数失败: {str(e)}", "error", "数据库")
                    stats[table] = 0
            
            # 显示统计信息
            st.markdown("#### 数据库统计")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Scholar论文", stats["scholar_papers"])
            with col2:
                st.metric("CrossRef论文", stats["crossref_papers"])
            with col3:
                st.metric("验证论文", stats["verified_papers"])
            with col4:
                st.metric("已下载全文", stats["paper_fulltext"])
                
            conn.close()
            
        except Exception as e:
            error_msg = f"获取数据库信息失败: {str(e)}"
            log_message(error_msg, "error", "数据库")
            st.error(error_msg)
    
    def get_backup_files(self):
        """获取备份文件列表"""
        backup_dir = "db/backup"
        if not os.path.exists(backup_dir):
            return []
        return [
            os.path.join(backup_dir, f) 
            for f in os.listdir(backup_dir) 
            if f.endswith('.db')
        ]
    
    def get_table_schema(self, table_name: str) -> List[tuple]:
        """获取表结构"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema = cursor.fetchall()
            conn.close()
            return schema
        except Exception as e:
            log_message(f"获取表{table_name}结构失败: {str(e)}", "error", "数据库")
            return []
    
    def get_table_count(self, table_name: str) -> int:
        """获取表记录数"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            log_message(f"获取表{table_name}记录数失败: {str(e)}", "error", "数据库")
            return 0
    
    def save_search_results(self, data_type: str, papers: List, search_query: str = None):
        """保存搜索结果到数据库"""
        try:
            if not papers:
                log_message("没有可保存的论文数据", "error", "数据库")
                return False
                
            # 连接数据库
            os.makedirs("db", exist_ok=True)
            log_message(f"连接数据库: {self.db_path}", "info", "数据库")
            conn = sqlite3.connect(self.db_path)
            
            success = False
            if data_type == "scholar":
                success = save_scholar_papers(conn, papers, search_query)
            elif data_type == "crossref":
                success = save_crossref_papers(conn, papers)
            elif data_type == "verified":
                success = save_verified_papers(conn, papers)
                
            conn.close()
            return success
            
        except Exception as e:
            error_msg = f"保存{data_type}论文到数据库失败: {str(e)}"
            log_message(error_msg, "error", "数据库")
            log_message(f"错误详情: {traceback.format_exc()}", "error", "数据库")
            return False
    
    def handle_save_button(self, data_type: str, container, papers: List, search_query: str = None):
        """处理保存按钮点击事件"""
        col1, col2 = container.columns([1, 3])
        save_button = col1.button("存入数据库", key=f"save_{data_type}")
        status_area = col2.empty()
        
        if save_button:
            try:
                if not papers:
                    status_area.error("没有可保存的论文数据")
                    return
                    
                status_area.info(f"正在保存 {len(papers)} 篇论文...")
                if self.save_search_results(data_type, papers, search_query):
                    status_area.success(f"成功保存 {len(papers)} 篇论文到数据库")
                else:
                    status_area.error("保存失败")
                    
            except Exception as e:
                error_msg = f"保存失败: {str(e)}"
                status_area.error(error_msg)
                log_message(error_msg, "error", "数据库")
                log_message(f"错误详情: {traceback.format_exc()}", "error", "数据库")

def render_database_management():
    """渲染数据库管理界面的入口函数"""
    try:
        db_manager = DatabaseManager()
        db_manager.render_db_management()
    except Exception as e:
        error_msg = f"数据库管理功能初始化失败: {str(e)}"
        log_message(error_msg, "error", "数据库")
        st.error(error_msg) 