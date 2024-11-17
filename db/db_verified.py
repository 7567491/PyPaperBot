import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

def query_verified_papers(conn: sqlite3.Connection):
    """验证论文查询界面"""
    
    # 搜索条件
    st.markdown("##### 搜索条件")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        title_query = st.text_input("标题关键词", key="verified_db_title_query")
        year_from = st.number_input(
            "发表年份从", 
            min_value=1900, 
            max_value=2024, 
            value=2000,
            key="verified_db_year_from"
        )
    with col2:
        author_query = st.text_input("作者关键词", key="verified_db_author_query")
        year_to = st.number_input(
            "到", 
            min_value=1900, 
            max_value=2024, 
            value=2024,
            key="verified_db_year_to"
        )
    with col3:
        verification_status = st.selectbox(
            "验证状态",
            options=[
                "全部",
                "待验证",
                "完全匹配",
                "部分匹配",
                "不匹配"
            ],
            index=0
        )
        min_match_score = st.slider(
            "最小匹配度",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1
        )
    
    # 构建查询
    query = """
    SELECT 
        v.id, v.doi, v.title, v.authors, v.year,
        v.journal, v.citations_count, v.url,
        v.verification_status, v.match_score,
        v.verification_timestamp,
        s.scholar_link,
        c.publisher, c.type
    FROM verified_papers v
    LEFT JOIN scholar_papers s ON v.scholar_id = s.id
    LEFT JOIN crossref_papers c ON v.crossref_id = c.id
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
    if verification_status != "全部":
        status_map = {
            "待验证": 0,
            "完全匹配": 1,
            "部分匹配": 2,
            "不匹配": 3
        }
        query += " AND v.verification_status = ?"
        params.append(status_map[verification_status])
    if min_match_score > 0:
        query += " AND v.match_score >= ?"
        params.append(min_match_score)
    
    query += " ORDER BY v.verification_timestamp DESC"
    
    # 执行查询
    try:
        df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            # 显示结果统计
            st.success(f"找到 {len(df)} 条记录")
            
            # 格式化数据
            df['verification_timestamp'] = pd.to_datetime(df['verification_timestamp'])
            df['verification_status'] = df['verification_status'].map({
                0: '待验证',
                1: '完全匹配',
                2: '部分匹配',
                3: '不匹配'
            })
            
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
                    "citations_count": "引用数",
                    "url": "URL",
                    "verification_status": "验证状态",
                    "match_score": "匹配度",
                    "verification_timestamp": "验证时间",
                    "scholar_link": "Scholar链接",
                    "publisher": "出版商",
                    "type": "类型"
                },
                hide_index=True
            )
            
            # 导出功能
            if st.button("导出到Excel"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"verified_papers_{timestamp}.xlsx"
                df.to_excel(f"db/export/{filename}", index=False)
                st.success(f"数据已导出到: {filename}")
                
        else:
            st.info("未找到匹配的记录")
            
    except Exception as e:
        st.error(f"查询出错: {str(e)}") 