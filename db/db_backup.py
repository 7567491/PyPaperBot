import os
import shutil
import logging
from datetime import datetime
from PyPaperBot.utils.log import log_message
import json
import sqlite3
import streamlit as st

def backup_database(db_path: str) -> str:
    """
    备份数据库
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        str: 备份文件路径，失败返回None
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 确保数据库文件存在
        if not os.path.exists(db_path):
            error_msg = "数据库文件不存在"
            logger.error(error_msg)
            log_message(error_msg, "error", "数据库")
            return None
            
        # 创建备份目录
        backup_dir = os.path.join(os.path.dirname(db_path), "backup")
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_name = f"paper-{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # 复制数据库文件
        shutil.copy2(db_path, backup_path)
        
        success_msg = f"数据库备份成功: {backup_name}"
        logger.info(success_msg)
        log_message(success_msg, "success", "数据库")
        return backup_path
        
    except Exception as e:
        error_msg = f"数据库备份失败: {str(e)}"
        logger.error(error_msg)
        log_message(error_msg, "error", "数据库")
        return None

def restore_database(backup_path: str, db_path: str) -> bool:
    """
    从备份恢复数据库
    
    Args:
        backup_path: 备份文件路径
        db_path: 目标数据库路径
        
    Returns:
        bool: 是否恢复成功
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 确保备份文件存在
        if not os.path.exists(backup_path):
            error_msg = "备份文件不存在"
            logger.error(error_msg)
            log_message(error_msg, "error", "数据库")
            return False
            
        # 创建当前数据库的备份
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        current_backup = os.path.join(os.path.dirname(backup_path), f"paper-before-restore-{timestamp}.db")
        if os.path.exists(db_path):
            shutil.copy2(db_path, current_backup)
            log_message(f"已创建当前数据库备份: {os.path.basename(current_backup)}", "info", "数据库")
            
        # 复制备份文件到目标位置
        shutil.copy2(backup_path, db_path)
        
        success_msg = f"数据库恢复成功: {os.path.basename(backup_path)}"
        logger.info(success_msg)
        log_message(success_msg, "success", "数据库")
        return True
        
    except Exception as e:
        error_msg = f"数据库恢复失败: {str(e)}"
        logger.error(error_msg)
        log_message(error_msg, "error", "数据库")
        return False

def get_backup_info(backup_path: str) -> dict:
    """
    获取备份文件信息
    
    Args:
        backup_path: 备份文件路径
        
    Returns:
        dict: 备份文件信息
    """
    try:
        stats = os.stat(backup_path)
        return {
            'name': os.path.basename(backup_path),
            'size': f"{stats.st_size / (1024*1024):.2f} MB",
            'created': datetime.fromtimestamp(stats.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception:
        return {
            'name': os.path.basename(backup_path),
            'size': "N/A",
            'created': "N/A"
        } 

def update_database_stats(db_path: str, backup_dir: str) -> None:
    """更新数据库统计信息"""
    try:
        stats = {
            'main_db': get_db_stats(db_path),
            'backups': {}
        }
        
        # 获取所有备份文件的统计信息
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        for backup_file in backup_files:
            backup_path = os.path.join(backup_dir, backup_file)
            stats['backups'][backup_file] = get_db_stats(backup_path)
        
        # 保存到JSON文件
        stats_file = os.path.join(backup_dir, 'list.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
            
        log_message("数据库统计信息已更新", "info", "数据库")
        
    except Exception as e:
        log_message(f"更新数据库统计信息失败: {str(e)}", "error", "数据库")

def get_db_stats(db_path: str) -> dict:
    """获取数据库统计信息"""
    stats = {
        'file_info': {
            'size': f"{os.path.getsize(db_path) / (1024*1024):.2f} MB",
            'modified': datetime.fromtimestamp(os.path.getmtime(db_path)).strftime("%Y-%m-%d %H:%M:%S")
        },
        'tables': {}
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取各表的记录数和最新记录时间
        tables = {
            'scholar_papers': ('search_timestamp', '搜索论文'),
            'crossref_papers': ('verification_timestamp', 'CrossRef论文'),
            'verified_papers': ('verification_timestamp', '验证论文'),
            'paper_fulltext': ('download_timestamp', '全文下载')
        }
        
        for table, (timestamp_col, description) in tables.items():
            try:
                # 获取记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                # 获取最新记录时间
                cursor.execute(f"SELECT MAX({timestamp_col}) FROM {table}")
                latest = cursor.fetchone()[0]
                
                stats['tables'][table] = {
                    'description': description,
                    'count': count,
                    'latest': latest if latest else 'N/A'
                }
            except:
                stats['tables'][table] = {
                    'description': description,
                    'count': 0,
                    'latest': 'N/A'
                }
        
        conn.close()
        return stats
        
    except Exception as e:
        log_message(f"获取数据库统计信息失败: {str(e)}", "error", "数据库")
        return stats

def display_db_stats(stats: dict):
    """显示数据库统计信息"""
    st.markdown("#### 数据库统计信息")
    
    # 显示主数据库信息
    st.markdown("##### 主数据库")
    main_stats = stats.get('main_db', {})
    
    # 文件信息
    file_info = main_stats.get('file_info', {})
    col1, col2 = st.columns(2)
    with col1:
        st.metric("文件大小", file_info.get('size', 'N/A'))
    with col2:
        st.metric("最后修改时间", file_info.get('modified', 'N/A'))
    
    # 表统计信息
    tables = main_stats.get('tables', {})
    table_data = []
    for table_name, info in tables.items():
        table_data.append({
            "数据类型": info.get('description', '未知'),
            "记录数": info.get('count', 0),
            "最新记录时间": info.get('latest', 'N/A')
        })
    
    if table_data:
        st.dataframe(
            table_data,
            column_config={
                "数据类型": st.column_config.TextColumn("数据类型", width=150),
                "记录数": st.column_config.NumberColumn("记录数", width=100),
                "最新记录时间": st.column_config.TextColumn("最新记录时间", width=200)
            },
            hide_index=True
        )
    
    # 显示备份数据库信息
    st.markdown("##### 备份数据库")
    backup_stats = stats.get('backups', {})
    
    if backup_stats:
        backup_data = []
        for backup_name, backup_info in backup_stats.items():
            file_info = backup_info.get('file_info', {})
            tables = backup_info.get('tables', {})
            total_records = sum(table.get('count', 0) for table in tables.values())
            
            backup_data.append({
                "备份文件": backup_name,
                "文件大小": file_info.get('size', 'N/A'),
                "总记录数": total_records,
                "备份时间": file_info.get('modified', 'N/A')
            })
        
        st.dataframe(
            backup_data,
            column_config={
                "备份文件": st.column_config.TextColumn("备份文件", width=200),
                "文件大小": st.column_config.TextColumn("文件大小", width=100),
                "总记录数": st.column_config.NumberColumn("总记录数", width=100),
                "备份时间": st.column_config.TextColumn("备份时间", width=200)
            },
            hide_index=True
        )
    else:
        st.info("暂无备份数据库") 