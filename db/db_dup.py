import sqlite3
import streamlit as st
import os
from PyPaperBot.utils.log import log_message
from .db_backup import backup_database

def deduplicate_database(db_path: str) -> bool:
    """数据库去重"""
    try:
        # 自动备份
        backup_file = backup_database(db_path)
        if not backup_file:
            raise Exception("自动备份失败，中止去重操作")
        log_message(f"数据库已备份: {backup_file}", "info", "数据库")
        
        conn = sqlite3.connect(db_path)
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