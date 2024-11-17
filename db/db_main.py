import streamlit as st
import sqlite3
import os
from datetime import datetime
from .db_init import init_database
from .db_backup import backup_database, restore_database
from .db_scholar import query_scholar_papers
from .db_crossref import query_crossref_papers
from .db_verified import query_verified_papers
from .db_fulltext import query_paper_fulltext

class DatabaseManager:
    def __init__(self, db_path="db/paper.db"):
        self.db_path = db_path
        self.ensure_db_exists()
        
    def ensure_db_exists(self):
        """确保数据库文件存在"""
        if not os.path.exists(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def render_db_management(self):
        """渲染数据库管理界面"""
        st.title("论文数据管理")
        
        # 显示数据库基本信息
        self.show_db_info()
        
        # 创建二级功能标签页
        tabs = st.tabs([
            "数据库初始化", 
            "数据库备份与恢复", 
            "Scholar论文查询",
            "CrossRef论文查询",
            "验证论文查询",
            "已下载论文全文"
        ])
        
        # 数据库初始化
        with tabs[0]:
            st.subheader("数据库初始化")
            if st.button("初始化数据库", key="init_db"):
                with st.spinner("正在初始化数据库..."):
                    init_database(self.db_path)
                st.success("数据库初始化完成")
        
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
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            
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
            st.error(f"获取数据库信息失败: {str(e)}")
    
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

def render_database_management():
    """渲染数据库管理界面的入口函数"""
    db_manager = DatabaseManager()
    db_manager.render_db_management() 