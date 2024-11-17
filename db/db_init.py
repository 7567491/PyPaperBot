import sqlite3
import os
import logging

def init_database(db_path: str) -> bool:
    """初始化数据库"""
    logger = logging.getLogger(__name__)
    
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建Scholar搜索结果表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS scholar_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            authors TEXT,
            year TEXT,
            doi TEXT,
            scholar_link TEXT,
            citations_count INTEGER,
            scholar_id TEXT,
            search_query TEXT,
            search_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw_data TEXT,
            download_status INTEGER DEFAULT 0,
            UNIQUE(doi) ON CONFLICT REPLACE
        )
        """)
        
        # 创建CrossRef验证结果表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crossref_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            authors TEXT,
            year TEXT,
            journal TEXT,
            volume TEXT,
            issue TEXT,
            pages TEXT,
            publisher TEXT,
            published_print_date TEXT,
            published_online_date TEXT,
            issn TEXT,
            language TEXT,
            type TEXT,
            abstract TEXT,
            references_count INTEGER,
            is_referenced_by_count INTEGER,
            url TEXT,
            license TEXT,
            subjects TEXT,
            funders TEXT,
            metadata_score INTEGER,
            verification_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw_metadata TEXT,
            UNIQUE(doi) ON CONFLICT REPLACE
        )
        """)
        
        # 创建验证匹配的论文表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS verified_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi TEXT UNIQUE NOT NULL,
            scholar_id INTEGER,
            crossref_id INTEGER,
            title TEXT NOT NULL,
            authors TEXT,
            year TEXT,
            journal TEXT,
            citations_count INTEGER,
            url TEXT,
            verification_status INTEGER DEFAULT 0,
            match_score FLOAT,
            verification_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scholar_id) REFERENCES scholar_papers(id),
            FOREIGN KEY (crossref_id) REFERENCES crossref_papers(id),
            UNIQUE(doi) ON CONFLICT REPLACE
        )
        """)
        
        # 创建论文全文表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_fulltext (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi TEXT UNIQUE NOT NULL,
            file_path TEXT,
            file_size INTEGER,
            file_hash TEXT,
            content_type TEXT,
            download_source TEXT,
            download_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            download_status INTEGER DEFAULT 0,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            pdf_data BLOB,
            FOREIGN KEY (doi) REFERENCES verified_papers(doi),
            UNIQUE(doi) ON CONFLICT REPLACE
        )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scholar_doi ON scholar_papers(doi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scholar_title ON scholar_papers(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crossref_doi ON crossref_papers(doi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crossref_title ON crossref_papers(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_verified_doi ON verified_papers(doi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fulltext_doi ON paper_fulltext(doi)")
        
        conn.commit()
        conn.close()
        
        logger.info("数据库初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        return False 