import sqlite3
from pathlib import Path
import pandas as pd
from colorama import init, Fore, Style

# 初始化colorama
init()

def print_info(msg):
    """打印普通信息"""
    print(f"{Style.NORMAL}{msg}{Style.RESET_ALL}")

def print_success(msg):
    """打印成功信息"""
    print(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")

def print_error(msg):
    """打印错误信息"""
    print(f"{Fore.RED}{msg}{Style.RESET_ALL}")

def get_table_info(conn, table_name):
    """获取表结构信息"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print_info(f"\n表 {table_name} 的结构:")
    for col in columns:
        print_info(f"列名: {col[1]}, 类型: {col[2]}")
    return [col[1] for col in columns]

def export_papers_to_excel():
    """将论文信息导出到Excel文件"""
    # 获取数据库路径
    root_dir = Path(__file__).parent.parent
    db_path = root_dir / "db" / "paper.db"
    
    # 确保excel目录存在
    excel_dir = root_dir / "excel"
    excel_dir.mkdir(exist_ok=True)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        
        # 获取表结构
        columns = get_table_info(conn, "verified_papers")
        
        # 构建查询语句，包含所有列
        query = f"""
        SELECT *
        FROM verified_papers 
        ORDER BY citations_count DESC NULLS LAST
        """
        
        # 读取数据到DataFrame
        df = pd.read_sql_query(query, conn)
        
        # 添加序号列
        df.insert(0, '序号', range(1, len(df) + 1))
        
        # 添加已下载状态列
        def check_paper_downloaded(title):
            pdf_dir = root_dir / "pdf"
            if not pdf_dir.exists():
                return "否"
            
            invalid_chars = '<>:"/\\|?*'
            safe_title = ''.join(c for c in title if c not in invalid_chars)
            safe_title_lower = safe_title.lower()
            
            try:
                for pdf_file in pdf_dir.glob("*.pdf"):
                    existing_name = pdf_file.stem.lower()
                    if existing_name == safe_title_lower:
                        return "是"
            except Exception:
                pass
            return "否"
        
        df['已下载'] = df['title'].apply(check_paper_downloaded)
        
        # 列名映射
        column_mapping = {
            'id': 'ID',
            'title': '标题',
            'doi': 'DOI',
            'citations_count': '引用数',
            'url': 'URL',
            'year': '年份',
            'venue': '发表期刊/会议',
            'publisher': '出版商',
            'authors': '作者',
            'keywords': '关键词',
            'abstract': '摘要',
            'references': '参考文献',
            'pdf_link': 'PDF链接'
        }
        
        # 重命名存在的列
        existing_columns = df.columns.tolist()
        for eng, chn in column_mapping.items():
            if eng in existing_columns:
                df = df.rename(columns={eng: chn})
        
        # 获取下一个可用的文件名
        def get_next_filename(total_papers):
            i = 1
            while True:
                filename = f"{i:03d}-AI论文-{total_papers}篇.xlsx"
                if not (excel_dir / filename).exists():
                    return filename
                i += 1
        
        filename = get_next_filename(len(df))
        excel_path = excel_dir / filename
        
        # 导出到Excel
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        print_success(f"\n成功导出论文信息到: {excel_path}")
        print_info(f"总共导出 {len(df)} 篇论文")
        print_info(f"导出的列: {', '.join(df.columns)}")
        
    except sqlite3.Error as e:
        print_error(f"数据库错误: {e}")
    except Exception as e:
        print_error(f"导出过程中出错: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    export_papers_to_excel() 