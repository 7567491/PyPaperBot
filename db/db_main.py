import streamlit as st
import sqlite3
import os
from datetime import datetime
import traceback
from .db_init import init_database
from .db_backup import backup_database, restore_database, get_backup_info, update_database_stats, display_db_stats
from .db_scholar import query_scholar_papers
from .db_crossref import query_crossref_papers
from .db_verified import query_verified_papers
from .db_fulltext import query_paper_fulltext
from .db_utils import save_scholar_papers, save_crossref_papers, save_verified_papers
from PyPaperBot.utils.log import log_message
from typing import List
import pandas as pd
import json
from .db_dup import deduplicate_database

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
            # 创建二级功能标签页
            tabs = st.tabs([
                "数据库查询", 
                "数据库备份与恢复", 
                "数据库去重",
                "Scholar论文查询",
                "CrossRef论文查询",
                "验证论文查询",
                "已下载论文全文"
            ])
            
            # 数据库查询标签页
            with tabs[0]:
                st.subheader("数据库查询")
                
                # 首先显示数据库统计
                st.markdown("#### 数据库统计")
                try:
                    conn = self.get_connection()
                    cursor = conn.cursor()
                    
                    # 获取各表的统计信息
                    tables = {
                        'scholar_papers': ('Scholar论文', 'search_timestamp'),
                        'crossref_papers': ('CrossRef论文', 'verification_timestamp'),
                        'verified_papers': ('验证论文', 'verification_timestamp'),
                        'paper_fulltext': ('已下载全文', 'download_timestamp')
                    }
                    
                    # 创建四列布局显示统计数据
                    cols = st.columns(len(tables))
                    
                    for i, (table, (desc, timestamp_col)) in enumerate(tables.items()):
                        # 获取记录数
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        
                        # 获取最新记录时间
                        cursor.execute(f"SELECT MAX({timestamp_col}) FROM {table}")
                        latest_time = cursor.fetchone()[0]
                        
                        # 在对应列显示统计信息
                        with cols[i]:
                            st.metric(
                                label=desc,
                                value=count,
                                help=f"最新记录: {latest_time if latest_time else 'N/A'}"
                            )
                    
                    conn.close()
                    
                    # 显示分割线
                    st.markdown("---")
                    
                except Exception as e:
                    error_msg = f"获取数据库统计信息失败: {str(e)}"
                    log_message(error_msg, "error", "数据库")
                    st.error(error_msg)
                
                # 然后显示最近保存的记录
                st.markdown("#### 最近保存的记录")
                
                try:
                    conn = self.get_connection()
                    cursor = conn.cursor()
                    
                    # 显示最近保存的Scholar论文
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
                    
                    # 显示最近保存的CrossRef论文
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
                    
                    # 显示最近保存的验证论文
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
            
            # 数据库备份与恢复标签页
            with tabs[1]:
                st.subheader("数据库备份与恢复")
                
                # 显示数据库统计信息
                try:
                    stats_file = os.path.join("db", "backup", "list.json")
                    if os.path.exists(stats_file):
                        with open(stats_file, 'r', encoding='utf-8') as f:
                            stats = json.load(f)
                        display_db_stats(stats)
                    else:
                        # 首次创建统计信息
                        update_database_stats(self.db_path, os.path.join("db", "backup"))
                        with open(stats_file, 'r', encoding='utf-8') as f:
                            stats = json.load(f)
                        display_db_stats(stats)
                except Exception as e:
                    st.error(f"读取数据库统计信息失败: {str(e)}")
                
                st.markdown("---")
                
                # 备份和恢复操作
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 创建备份")
                    if st.button("创建新备份", key="create_backup"):
                        try:
                            backup_file = backup_database(self.db_path)
                            if backup_file:
                                # 更新统计信息
                                update_database_stats(self.db_path, os.path.join("db", "backup"))
                                st.success(f"备份创建成功: {os.path.basename(backup_file)}")
                                st.rerun()  # 刷新显示
                        except Exception as e:
                            st.error(f"备份创建失败: {str(e)}")
                
                with col2:
                    st.markdown("#### 恢复数据库")
                    backup_files = [
                        f for f in os.listdir("db/backup") 
                        if f.endswith('.db')
                    ] if os.path.exists("db/backup") else []
                    
                    if backup_files:
                        selected_backup = st.selectbox(
                            "选择要恢复的备份文件",
                            backup_files,
                            format_func=lambda x: x
                        )
                        
                        # 显示选中备份的详细信息
                        if selected_backup and 'backups' in stats:
                            backup_info = stats['backups'].get(selected_backup, {})
                            if backup_info:
                                st.markdown("**备份信息：**")
                                file_info = backup_info.get('file_info', {})
                                st.markdown(f"- 文件大小：{file_info.get('size', 'N/A')}")
                                st.markdown(f"- 备份时间：{file_info.get('modified', 'N/A')}")
                                
                                tables = backup_info.get('tables', {})
                                total_records = sum(table.get('count', 0) for table in tables.values())
                                st.markdown(f"- 总记录数：{total_records}")
                        
                        if st.button("恢复数据库", key="restore_db"):
                            try:
                                backup_path = os.path.join("db/backup", selected_backup)
                                if restore_database(backup_path, self.db_path):
                                    # 更新统计信息
                                    update_database_stats(self.db_path, os.path.join("db", "backup"))
                                    st.success("数据库恢复成功")
                                    st.rerun()  # 刷新显示
                            except Exception as e:
                                st.error(f"数据库恢复失败: {str(e)}")
                    else:
                        st.info("没有可用的备份文件")
            
            # 数据库去重标签页
            with tabs[2]:
                st.subheader("数据库去重")
                
                # 显示当前数据库状态
                try:
                    conn = self.get_connection()
                    cursor = conn.cursor()
                    
                    # 获取各表的记录数
                    tables = {
                        'scholar_papers': 'Scholar论文',
                        'crossref_papers': 'CrossRef论文',
                        'verified_papers': '验证论文'
                    }
                    
                    # 显示当前状态
                    st.markdown("#### 当前数据库状态")
                    cols = st.columns(len(tables))
                    
                    for i, (table, desc) in enumerate(tables.items()):
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        cols[i].metric(desc, count)
                    
                    conn.close()
                    
                    # 去重说明
                    st.markdown("""
                    #### 去重规则
                    1. **Scholar论文表**
                       - 优先使用DOI进行去重
                       - 对于没有DOI的记录，使用标题进行去重
                       - 保留最早保存的记录
                       
                    2. **CrossRef论文表**
                       - 使用DOI作为唯一标识进行去重
                       - 保留最新的元数据记
                       
                    3. **验证论文表**
                       - 使用DOI和Scholar ID的组合进行去重
                       - 保留验证分数最高的记录
                       
                    **注意：** 
                    - 去重操作前会自动备份数据库
                    - 去重操作不可撤销
                    - 建议在去重前检查数据库备份
                    """)
                    
                    # 去重操作
                    st.markdown("#### 执行去重")
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        if st.button("开始去重", key="start_dedup", type="primary"):
                            deduplicate_database(self.db_path)
                    with col2:
                        st.info("点击按钮开始去重操作，过程中请勿刷新页面")
                    
                except Exception as e:
                    error_msg = f"获取数据库状态失败: {str(e)}"
                    log_message(error_msg, "error", "数据库")
                    st.error(error_msg)
            
            # Scholar论文查询标签页
            with tabs[3]:
                st.subheader("Scholar论文查询")
                query_scholar_papers(self.get_connection())
            
            # CrossRef论文查询标签页
            with tabs[4]:
                st.subheader("CrossRef论文查询")
                query_crossref_papers(self.get_connection())
            
            # 验证论文查询标签页
            with tabs[5]:
                st.subheader("验证论文查询")
                query_verified_papers(self.get_connection())
            
            # 已下载论文全文标签页
            with tabs[6]:
                st.subheader("已下载论文全文")
                query_paper_fulltext(self.get_connection())
            
        except Exception as e:
            error_msg = f"数据库管理界面渲染失败: {str(e)}"
            log_message(error_msg, "error", "数据库")
            st.error(error_msg)
            # 显示详细错误信息
            st.error(f"错误详情: {traceback.format_exc()}")
    
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
    
    def deduplicate_database(self):
        """数据库去重"""
        try:
            # 自动备份
            backup_file = backup_database(self.db_path)
            if not backup_file:
                raise Exception("自动备份失败，中止去重操作")
            log_message(f"数据库已备份: {backup_file}", "info", "数据库")
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 显示进度条和状态
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 获取原始记录数
            original_counts = {}
            tables = {
                'scholar_papers': ('title', 'doi'),
                'crossref_papers': ('title', 'doi'),
                'verified_papers': ('title', 'doi')
            }
            
            for table, (title_col, doi_col) in tables.items():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                original_counts[table] = cursor.fetchone()[0]
            
            total_original = sum(original_counts.values())
            status_text.text("开始去重...")
            log_message("开始数据库去重操作", "info", "数据库")
            
            # 去重处理
            dedup_counts = {}
            current_progress = 0
            
            for i, (table, (title_col, doi_col)) in enumerate(tables.items()):
                status_text.text(f"正在处理 {table}...")
                log_message(f"开始处理表 {table}", "info", "数据库")
                
                # 基于DOI去重
                cursor.execute(f"""
                    DELETE FROM {table} 
                    WHERE rowid NOT IN (
                        SELECT MIN(rowid) 
                        FROM {table} 
                        WHERE {doi_col} IS NOT NULL 
                        GROUP BY {doi_col}
                    )
                    AND {doi_col} IS NOT NULL
                """)
                
                # 基于标题去重（对于没有DOI的记录）
                cursor.execute(f"""
                    DELETE FROM {table} 
                    WHERE rowid NOT IN (
                        SELECT MIN(rowid) 
                        FROM {table} 
                        WHERE {doi_col} IS NULL 
                        GROUP BY {title_col}
                    )
                    AND {doi_col} IS NULL
                """)
                
                # 获取去重后的记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                current_count = cursor.fetchone()[0]
                dedup_counts[table] = current_count
                
                # 更新进度
                current_progress = (i + 1) / len(tables)
                progress_bar.progress(current_progress)
                
                removed_count = original_counts[table] - current_count
                status_text.text(f"表 {table} 去重完成: 删除了 {removed_count} 条重复记录")
                log_message(f"表 {table} 去重完成: 原有 {original_counts[table]} 条记录，删除了 {removed_count} 条重复记录，剩余 {current_count} 条记录", "info", "数据库")
            
            # 提交更改
            conn.commit()
            conn.close()
            
            # 显示最终结果
            total_removed = sum(original_counts.values()) - sum(dedup_counts.values())
            final_msg = f"""
            去重完成！
            原始记录总数: {total_original}
            删除重复记录: {total_removed}
            剩余记录总数: {sum(dedup_counts.values())}
            
            详细统计:
            - Scholar论文: {original_counts['scholar_papers']} -> {dedup_counts['scholar_papers']} (-{original_counts['scholar_papers'] - dedup_counts['scholar_papers']})
            - CrossRef论文: {original_counts['crossref_papers']} -> {dedup_counts['crossref_papers']} (-{original_counts['crossref_papers'] - dedup_counts['crossref_papers']})
            - 验证论文: {original_counts['verified_papers']} -> {dedup_counts['verified_papers']} (-{original_counts['verified_papers'] - dedup_counts['verified_papers']})
            """
            
            progress_bar.progress(1.0)
            status_text.success(final_msg)
            log_message("数据库去重操作完成", "success", "数据库")
            
            return True
            
        except Exception as e:
            error_msg = f"数据库去重失败: {str(e)}"
            log_message(error_msg, "error", "数据库")
            if 'status_text' in locals():
                status_text.error(error_msg)
            return False

def render_database_management():
    """渲染数据库管理界面的入口函数"""
    try:
        db_manager = DatabaseManager()
        db_manager.render_db_management()
    except Exception as e:
        error_msg = f"数据库管理功��初始化失败: {str(e)}"
        log_message(error_msg, "error", "数据库")
        st.error(error_msg) 