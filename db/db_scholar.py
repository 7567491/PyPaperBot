import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
from PyPaperBot.utils.log import log_message

def query_scholar_papers(conn: sqlite3.Connection):
    """Scholar论文查询界面"""
    
    # 搜索条件
    st.markdown("##### 搜索条件")
    col1, col2 = st.columns(2)
    
    with col1:
        title_query = st.text_input("标题关键词", key="scholar_db_title_query")
        year_from = st.number_input(
            "发表年份从", 
            min_value=1900, 
            max_value=2024, 
            value=2000,
            key="scholar_db_year_from"  # 添加唯一key
        )
    with col2:
        author_query = st.text_input("作者关键词", key="scholar_db_author_query")
        year_to = st.number_input(
            "到", 
            min_value=1900, 
            max_value=2024, 
            value=2024,
            key="scholar_db_year_to"  # 添加唯一key
        )
    
    # 构建查询
    query = """
    SELECT 
        id, title, authors, year, doi, scholar_link, 
        citations_count, search_query, search_timestamp,
        download_status
    FROM scholar_papers 
    WHERE 1=1
    """
    params = []
    
    if title_query:
        query += " AND title LIKE ?"
        params.append(f"%{title_query}%")
    if author_query:
        query += " AND authors LIKE ?"
        params.append(f"%{author_query}%")
    if year_from:
        query += " AND CAST(year AS INTEGER) >= ?"
        params.append(year_from)
    if year_to:
        query += " AND CAST(year AS INTEGER) <= ?"
        params.append(year_to)
    
    query += " ORDER BY search_timestamp DESC"
    
    # 执行查询
    try:
        df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            # 显示结果统计
            st.success(f"找到 {len(df)} 条记录")
            
            # 格式化数据
            df['search_timestamp'] = pd.to_datetime(df['search_timestamp'])
            df['download_status'] = df['download_status'].map({
                0: '未处理',
                1: '已验证',
                2: '已下载'
            })
            
            # 显示数据表格
            st.dataframe(
                df,
                column_config={
                    "id": "ID",
                    "title": "标题",
                    "authors": "作者",
                    "year": "年份",
                    "doi": "DOI",
                    "scholar_link": "Scholar链接",
                    "citations_count": "引用数",
                    "search_query": "搜索关键词",
                    "search_timestamp": "���索时间",
                    "download_status": "下载状态"
                },
                hide_index=True
            )
            
            # 导出功能
            if st.button("导出到Excel", key="export_scholar_results"):
                try:
                    # 创建导出目录
                    export_dir = os.path.join("db", "export")
                    os.makedirs(export_dir, exist_ok=True)
                    
                    # 导出文件
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"scholar_papers_{timestamp}.xlsx"
                    export_path = os.path.join(export_dir, filename)
                    
                    df.to_excel(export_path, index=False)
                    st.success(f"数据已导出到: {filename}")
                    log_message(f"Scholar论文数据导出成功: {filename}", "success", "数据库")
                except Exception as e:
                    error_msg = f"导出失败: {str(e)}"
                    st.error(error_msg)
                    log_message(error_msg, "error", "数据库")
                
        else:
            st.info("未找到匹配的记录")
            
    except Exception as e:
        st.error(f"查询出错: {str(e)}") 