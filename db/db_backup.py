import os
import shutil
import logging
from datetime import datetime

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
            logger.error("数据库文件不存在")
            return None
            
        # 创建备份目录
        backup_dir = os.path.join(os.path.dirname(db_path), "backup")
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"paper_db_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # 复制数据库文件
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"数据库备份成功: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"数据库备份失败: {str(e)}")
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
            logger.error("备份文件不存在")
            return False
            
        # 复制备份文件到目标位置
        shutil.copy2(backup_path, db_path)
        
        logger.info(f"数据库恢复成功: {backup_path} -> {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"数据库恢复失败: {str(e)}")
        return False 