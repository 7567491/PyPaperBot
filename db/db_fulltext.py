import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

def query_paper_fulltext(conn: sqlite3.Connection):
    """论文全文查询界面"""
    
    # 搜索条件
    st.markdown("##### 搜索条件")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        title_query = st.text_input("标题关键词", key="fulltext_title_query")
        year_from = st.number_input("发表年份从", min_value=1900, max_value=2024, value=2000)
    with col2:
        author_query = st.text_input("作者关键词", key="fulltext_author_query")
        year_to = st.number_input("到", min_value=1900, max_value=2024, value=2024)
    with col3:
        download_status = st.selectbox(
            "下载状态",
            options=[
                "全部",
                "未下载",
                "下载成功",
                "下载失败"
            ],
            index=0
        )
        download_source = st.selectbox(
            "下载来源",
            options=[
                "全部",
                "Scholar",
                "SciHub",
                "SciDB"
            ],
            index=0
        )
    
    # 构建查询
    query = """
    SELECT 
        f.id, f.doi, f.file_path, f.file_size,
        f.content_type, f.download_source,
        f.download_timestamp, f.download_status,
        f.error_message, f.retry_count,
        v.title, v.authors, v.year, v.journal
    FROM paper_fulltext f
    LEFT JOIN verified_papers v ON f.doi = v.doi
    WHERE 1=1
    """
    params = []
    
    if title_query:
        query += " AND v.title LIKE ?"
        params.append(f"%{title_query}%")
    if author_query:
        query += " AND v.authors LIKE ?"
        params.append(f"%{author_query}%")
    if year_from:
        query += " AND CAST(v.year AS INTEGER) >= ?"
        params.append(year_from)
    if year_to:
        query += " AND CAST(v.year AS INTEGER) <= ?"
        params.append(year_to)
    if download_status != "全部":
        status_map = {
            "未下载": 0,
            "下载成功": 1,
            "下载失败": 2
        }
        query += " AND f.download_status = ?"
        params.append(status_map[download_status])
    if download_source != "全部":
        query += " AND f.download_source = ?"
        params.append(download_source)
    
    query += " ORDER BY f.download_timestamp DESC"
    
    # 执行查询
    try:
        df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            # 显示结果统计
            st.success(f"找到 {len(df)} 条记录")
            
            # 格式化数据
            df['download_timestamp'] = pd.to_datetime(df['download_timestamp'])
            df['download_status'] = df['download_status'].map({
                0: '未下载',
                1: '下载成功',
                2: '下载失败'
            })
            df['file_size'] = df['file_size'].apply(
                lambda x: f"{x/1024/1024:.2f} MB" if x else "N/A"
            )
            
            # 显示数据表格
            st.dataframe(
                df,
                column_config={
                    "id": "ID",
                    "doi": "DOI",
                    "title": "标题",
                    "authors": "作者",
                    "year": "年份",
                    "journal": "期刊",
                    "file_path": "文件路径",
                    "file_size": "文件大小",
                    "content_type": "文件类型",
                    "download_source": "下载来源",
                    "download_status": "下载状态",
                    "download_timestamp": "下载时间",
                    "error_message": "错误信息",
                    "retry_count": "重试次数"
                },
                hide_index=True
            )
            
            # 导出功能
            if st.button("导出到Excel"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"paper_fulltext_{timestamp}.xlsx"
                df.to_excel(f"db/export/{filename}", index=False)
                st.success(f"数据已导出到: {filename}")
            
            # 批量操作
            st.markdown("##### 批量操作")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("重试失败的下载"):
                    failed_dois = df[df['download_status'] == '下载失败']['doi'].tolist()
                    if failed_dois:
                        st.info(f"将重试 {len(failed_dois)} 篇论文的下载")
                        # TODO: 实现重试下载逻辑
                    else:
                        st.info("没有需要重试的下载")
            
            with col2:
                if st.button("清理无效文件"):
                    invalid_files = df[
                        (df['download_status'] == '下载成功') & 
                        df['file_path'].apply(lambda x: not os.path.exists(x) if x else True)
                    ]
                    if not invalid_files.empty:
                        st.warning(f"发现 {len(invalid_files)} 个无效文件记录")
                        # TODO: 实现清理逻辑
                    else:
                        st.success("未发现无效文件记录")
                
        else:
            st.info("未找到匹配的记录")
            
    except Exception as e:
        st.error(f"查询出错: {str(e)}") 