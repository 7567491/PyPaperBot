import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

def query_crossref_papers(conn: sqlite3.Connection):
    """CrossRef论文查询界面"""
    
    # 搜索条件
    st.markdown("##### 搜索条件")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        title_query = st.text_input("标题关键词", key="crossref_title_query")
        year_from = st.number_input("发表年份从", min_value=1900, max_value=2024, value=2000)
    with col2:
        author_query = st.text_input("作者关键词", key="crossref_author_query")
        year_to = st.number_input("到", min_value=1900, max_value=2024, value=2024)
    with col3:
        journal_query = st.text_input("期刊关键词", key="crossref_journal_query")
        min_metadata = st.number_input("最小元数据数量", min_value=0, value=0)
    
    # 构建查询
    query = """
    SELECT 
        id, doi, title, authors, year, journal,
        publisher, language, type, references_count,
        is_referenced_by_count, metadata_score,
        verification_timestamp
    FROM crossref_papers 
    WHERE 1=1
    """
    params = []
    
    if title_query:
        query += " AND title LIKE ?"
        params.append(f"%{title_query}%")
    if author_query:
        query += " AND authors LIKE ?"
        params.append(f"%{author_query}%")
    if journal_query:
        query += " AND journal LIKE ?"
        params.append(f"%{journal_query}%")
    if year_from:
        query += " AND CAST(year AS INTEGER) >= ?"
        params.append(year_from)
    if year_to:
        query += " AND CAST(year AS INTEGER) <= ?"
        params.append(year_to)
    if min_metadata:
        query += " AND metadata_score >= ?"
        params.append(min_metadata)
    
    query += " ORDER BY verification_timestamp DESC"
    
    # 执行查询
    try:
        df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            # 显示结果统计
            st.success(f"找到 {len(df)} 条记录")
            
            # 格式化数据
            df['verification_timestamp'] = pd.to_datetime(df['verification_timestamp'])
            
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
                    "publisher": "出版商",
                    "language": "语言",
                    "type": "类型",
                    "references_count": "参考文献数",
                    "is_referenced_by_count": "被引用数",
                    "metadata_score": "元数据分数",
                    "verification_timestamp": "验证时间"
                },
                hide_index=True
            )
            
            # 导出功能
            if st.button("导出到Excel"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"crossref_papers_{timestamp}.xlsx"
                df.to_excel(f"db/export/{filename}", index=False)
                st.success(f"数据已导出到: {filename}")
                
        else:
            st.info("未找到匹配的记录")
            
    except Exception as e:
        st.error(f"查询出错: {str(e)}") 