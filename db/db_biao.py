import sqlite3
import json
import os
from pathlib import Path

def get_db_info():
    """获取数据库信息并输出"""
    try:
        # 获取项目根目录
        root_dir = Path(__file__).parent
        db_path = root_dir / "paper.db"
        
        # 检查数据库文件是否存在
        if not db_path.exists():
            print(f"错误：数据库文件不存在: {db_path}")
            return
            
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        db_structure = {}
        
        print("\n=== 数据库表结构 ===\n")
        
        # 遍历每个表，获取结构
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"\n表名: {table_name}")
            print("-" * 50)
            
            table_info = {}
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                is_nullable = "NOT NULL" if col[3] else "NULL"
                is_pk = "PRIMARY KEY" if col[5] else ""
                
                # 打印列信息
                print(f"{col_name}: {col_type} {is_nullable} {is_pk}")
                
                # 存储列信息
                table_info[col_name] = f"{col_type} {is_nullable} {is_pk}".strip()
            
            db_structure[table_name] = table_info
        
        # 输出到JSON文件
        json_path = root_dir / "db.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(db_structure, f, indent=4, ensure_ascii=False)
        
        print(f"\n表结构已保存至: {json_path}")
        
        # 打印统计信息
        print("\n=== 数据库统计信息 ===\n")
        
        for table_name in db_structure.keys():
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"{table_name} 表共有 {count} 条记录")
            
            # 对特定表进行更详细的统计
            if table_name == 'paper':
                # 统计有DOI的论文数量
                cursor.execute("SELECT COUNT(*) FROM paper WHERE doi IS NOT NULL")
                doi_count = cursor.fetchone()[0]
                print(f"- 其中有DOI的论文: {doi_count} 篇")
                
                # 统计引用次数最多的论文
                cursor.execute("SELECT title, citations FROM paper ORDER BY citations DESC LIMIT 1")
                most_cited = cursor.fetchone()
                if most_cited:
                    print(f"- 引用最多的论文: {most_cited[0]} (被引用 {most_cited[1]} 次)")
            
            elif table_name == 'author':
                # 统计作者的论文数量分布
                cursor.execute("""
                    SELECT a.name, COUNT(pa.paper_id) as paper_count 
                    FROM author a 
                    LEFT JOIN paper_author pa ON a.id = pa.author_id 
                    GROUP BY a.id 
                    ORDER BY paper_count DESC 
                    LIMIT 1
                """)
                top_author = cursor.fetchone()
                if top_author:
                    print(f"- 发表论文最多的作者: {top_author[0]} ({top_author[1]} 篇)")
    
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    get_db_info() 