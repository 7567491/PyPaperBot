import sqlite3
import json
from datetime import datetime
from typing import List
import streamlit as st
import logging
from PyPaperBot.Paper import Paper
from PyPaperBot.utils.log import log_message

def save_scholar_papers(conn: sqlite3.Connection, papers: List[Paper], search_query: str) -> bool:
    """保存Scholar搜索结果到数据库"""
    logger = logging.getLogger(__name__)
    status_text = st.empty()
    
    try:
        # 检查连接是否有效
        if not conn:
            error_msg = "数据库连接无效"
            logger.error(error_msg)
            log_message(error_msg, "error", "数据库")
            status_text.error(error_msg)
            return False
            
        # 检查papers是否有效
        if not papers:
            error_msg = "没有要保存的论文数据"
            logger.error(error_msg)
            log_message(error_msg, "error", "数据库")
            status_text.error(error_msg)
            return False
            
        cursor = conn.cursor()
        total = len(papers)
        
        # 记录开始保存
        start_msg = f"开始保存 {total} 篇Scholar论文到数据库"
        logger.info(start_msg)
        log_message(start_msg, "info", "数据库")
        status_text.text(start_msg)
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scholar_papers'")
        if not cursor.fetchone():
            error_msg = "scholar_papers表不存在"
            logger.error(error_msg)
            log_message(error_msg, "error", "数据库")
            status_text.error(error_msg)
            return False
        
        success_count = 0
        for i, paper in enumerate(papers, 1):
            try:
                # 记录每篇论文的保存
                paper_msg = f"正在保存第 {i}/{total} 篇Scholar论文: {paper.title}"
                logger.debug(paper_msg)
                log_message(paper_msg, "debug", "数据库")
                status_text.text(paper_msg)
                
                # 检查必要字段
                if not paper.title:
                    logger.warning(f"论文缺少标题，跳过: {paper}")
                    continue
                
                # 准备数据
                raw_data = {
                    'title': paper.title,
                    'authors': paper.authors,
                    'year': paper.year,
                    'doi': getattr(paper, 'DOI', None),
                    'scholar_link': paper.scholar_link,
                    'citations_count': getattr(paper, 'cites_num', 0)
                }
                
                # 记录要插入的数据
                logger.debug(f"准备插入数据: {raw_data}")
                
                # 执行插入
                cursor.execute("""
                    INSERT OR REPLACE INTO scholar_papers (
                        title, authors, year, doi, scholar_link,
                        citations_count, search_query, raw_data,
                        search_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    paper.title,
                    paper.authors,
                    paper.year,
                    getattr(paper, 'DOI', None),
                    paper.scholar_link,
                    getattr(paper, 'cites_num', 0),
                    search_query,
                    json.dumps(raw_data)
                ))
                
                success_count += 1
                # 记录成功
                success_msg = f"成功保存Scholar论文: {paper.title}"
                logger.debug(success_msg)
                log_message(success_msg, "debug", "数据库")
                
            except sqlite3.Error as e:
                # 记录SQL错误
                error_msg = f"SQL错误: {str(e)}, 论文: {paper.title}"
                logger.error(error_msg)
                log_message(error_msg, "error", "数据库")
                continue
                
            except Exception as e:
                # 记录其他错误
                error_msg = f"保存Scholar论文失败: {paper.title} - {str(e)}"
                logger.error(error_msg, exc_info=True)
                log_message(error_msg, "error", "数据库")
                continue
        
        # 提交事务
        conn.commit()
        
        # 记录完成
        final_msg = f"成功保存 {success_count}/{total} 篇Scholar论文到数据库"
        logger.info(final_msg)
        log_message(final_msg, "success", "数据库")
        status_text.success(final_msg)
        
        # 验证保存结果
        cursor.execute("SELECT COUNT(*) FROM scholar_papers WHERE search_query = ?", (search_query,))
        saved_count = cursor.fetchone()[0]
        verify_msg = f"数据库验证: 找到 {saved_count} 条记录"
        logger.info(verify_msg)
        log_message(verify_msg, "info", "数据库")
        
        return True
        
    except sqlite3.Error as e:
        # 记录SQL错误
        conn.rollback()
        error_msg = f"数据库错误: {str(e)}"
        logger.error(error_msg)
        log_message(error_msg, "error", "数据库")
        status_text.error(error_msg)
        return False
        
    except Exception as e:
        # 记录其他错误
        conn.rollback()
        error_msg = f"保存Scholar论文到数据库失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        log_message(error_msg, "error", "数据库")
        status_text.error(error_msg)
        return False

def save_crossref_papers(conn: sqlite3.Connection, papers: List[Paper]) -> bool:
    """保存CrossRef搜索结果到数据库"""
    logger = logging.getLogger(__name__)
    status_text = st.empty()
    
    try:
        # 检查连接是否有效
        if not conn:
            error_msg = "数据库连接无效"
            logger.error(error_msg)
            log_message(error_msg, "error", "数据库")
            status_text.error(error_msg)
            return False
            
        # 检查papers是否有效
        if not papers:
            error_msg = "没有要保存的论文数据"
            logger.error(error_msg)
            log_message(error_msg, "error", "数据库")
            status_text.error(error_msg)
            return False
            
        cursor = conn.cursor()
        total = len(papers)
        
        # 记录开始保存
        start_msg = f"开始保存 {total} 篇CrossRef论文到数据库"
        logger.info(start_msg)
        log_message(start_msg, "info", "数据库")
        status_text.text(start_msg)
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crossref_papers'")
        if not cursor.fetchone():
            error_msg = "crossref_papers表不存在"
            logger.error(error_msg)
            log_message(error_msg, "error", "数据库")
            status_text.error(error_msg)
            return False
        
        success_count = 0
        for i, paper in enumerate(papers, 1):
            try:
                # 记录每篇论文的保存
                paper_msg = f"正在保存第 {i}/{total} 篇CrossRef论文: {paper.title}"
                logger.debug(paper_msg)
                log_message(paper_msg, "debug", "数据库")
                status_text.text(paper_msg)
                
                # 检查必要字段
                if not paper.DOI:
                    logger.warning(f"论文缺少DOI，跳过: {paper.title}")
                    continue
                
                # 执行插入
                cursor.execute("""
                    INSERT OR REPLACE INTO crossref_papers (
                        doi, title, authors, year, journal,
                        publisher, language, type, references_count,
                        is_referenced_by_count, url, metadata_score,
                        raw_metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    paper.DOI,
                    paper.title,
                    paper.authors,
                    paper.year,
                    getattr(paper, 'jurnal', None),
                    getattr(paper, 'publisher', None),
                    getattr(paper, 'language', None),
                    getattr(paper, 'type', None),
                    getattr(paper, 'references_count', 0),
                    getattr(paper, 'is_referenced_by_count', 0),
                    getattr(paper, 'url', None),
                    getattr(paper, 'metadata_count', 0),
                    json.dumps(paper.__dict__)
                ))
                
                success_count += 1
                # 记录成功
                success_msg = f"成功保存CrossRef论文: {paper.title}"
                logger.debug(success_msg)
                log_message(success_msg, "debug", "数据库")
                
            except sqlite3.Error as e:
                # 记录SQL错误
                error_msg = f"SQL错误: {str(e)}, 论文: {paper.title}"
                logger.error(error_msg)
                log_message(error_msg, "error", "数据库")
                continue
                
            except Exception as e:
                # 记录其他错误
                error_msg = f"保存CrossRef论文失败: {paper.title} - {str(e)}"
                logger.error(error_msg, exc_info=True)
                log_message(error_msg, "error", "数据库")
                continue
        
        # 提交事务
        conn.commit()
        
        # 记录完成
        final_msg = f"成功保存 {success_count}/{total} 篇CrossRef论文到数据库"
        logger.info(final_msg)
        log_message(final_msg, "success", "数据库")
        status_text.success(final_msg)
        
        # 验证保存结果
        cursor.execute("SELECT COUNT(*) FROM crossref_papers WHERE doi IN (%s)" % 
                      ','.join('?' * len(papers)), [p.DOI for p in papers])
        saved_count = cursor.fetchone()[0]
        verify_msg = f"数据库验证: 找到 {saved_count} 条记录"
        logger.info(verify_msg)
        log_message(verify_msg, "info", "数据库")
        
        return True
        
    except sqlite3.Error as e:
        # 记录SQL错误
        conn.rollback()
        error_msg = f"数据库错误: {str(e)}"
        logger.error(error_msg)
        log_message(error_msg, "error", "数据库")
        status_text.error(error_msg)
        return False
        
    except Exception as e:
        # 记录其他错误
        conn.rollback()
        error_msg = f"保存CrossRef论文到数据库失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        log_message(error_msg, "error", "数据库")
        status_text.error(error_msg)
        return False

def save_verified_papers(conn: sqlite3.Connection, papers: List[Paper]) -> bool:
    """保存验证结果到数据库"""
    logger = logging.getLogger(__name__)
    status_text = st.empty()
    
    try:
        # 检查连接是否有效
        if not conn:
            error_msg = "数据库连接无效"
            logger.error(error_msg)
            log_message(error_msg, "error", "数据库")
            status_text.error(error_msg)
            return False
            
        # 检查papers是否有效
        if not papers:
            error_msg = "没有要保存的论文数据"
            logger.error(error_msg)
            log_message(error_msg, "error", "数据库")
            status_text.error(error_msg)
            return False
            
        cursor = conn.cursor()
        total = len(papers)
        
        # 记录开始保存
        start_msg = f"开始保存 {total} 篇验证论文到数据库"
        logger.info(start_msg)
        log_message(start_msg, "info", "数据库")
        status_text.text(start_msg)
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verified_papers'")
        if not cursor.fetchone():
            error_msg = "verified_papers表不存在"
            logger.error(error_msg)
            log_message(error_msg, "error", "数据库")
            status_text.error(error_msg)
            return False
        
        success_count = 0
        for i, paper in enumerate(papers, 1):
            try:
                # 记录每篇论文的保存
                paper_msg = f"正在保存第 {i}/{total} 篇验证论文: {paper.title}"
                logger.debug(paper_msg)
                log_message(paper_msg, "debug", "数据库")
                status_text.text(paper_msg)
                
                # 查找scholar_id
                cursor.execute(
                    "SELECT id FROM scholar_papers WHERE doi = ? OR title = ?",
                    (getattr(paper, 'DOI', None), paper.title)
                )
                scholar_result = cursor.fetchone()
                scholar_id = scholar_result[0] if scholar_result else None
                
                # 查找crossref_id
                cursor.execute(
                    "SELECT id FROM crossref_papers WHERE doi = ?",
                    (getattr(paper, 'DOI', None),)
                )
                crossref_result = cursor.fetchone()
                crossref_id = crossref_result[0] if crossref_result else None
                
                # 执行插入
                cursor.execute("""
                    INSERT OR REPLACE INTO verified_papers (
                        doi, scholar_id, crossref_id, title,
                        authors, year, journal, citations_count,
                        url, verification_status, match_score,
                        verification_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    getattr(paper, 'DOI', None),
                    scholar_id,
                    crossref_id,
                    paper.title,
                    paper.authors,
                    paper.year,
                    getattr(paper, 'jurnal', None),
                    getattr(paper, 'cites_num', 0),
                    getattr(paper, 'url', None),
                    1 if getattr(paper, 'validated', False) else 0,
                    getattr(paper, 'match_score', 0.0)
                ))
                
                success_count += 1
                # 记录成功
                success_msg = f"成功保存验证论文: {paper.title}"
                logger.debug(success_msg)
                log_message(success_msg, "debug", "数据库")
                
            except sqlite3.Error as e:
                # 记录SQL错误
                error_msg = f"SQL错误: {str(e)}, 论文: {paper.title}"
                logger.error(error_msg)
                log_message(error_msg, "error", "数据库")
                continue
                
            except Exception as e:
                # 记录其他错误
                error_msg = f"保存验证论文失败: {paper.title} - {str(e)}"
                logger.error(error_msg, exc_info=True)
                log_message(error_msg, "error", "数据库")
                continue
        
        # 提交事务
        conn.commit()
        
        # 记录完成
        final_msg = f"成功保存 {success_count}/{total} 篇验证论文到数据库"
        logger.info(final_msg)
        log_message(final_msg, "success", "数据库")
        status_text.success(final_msg)
        
        # 验证保存结果
        cursor.execute("SELECT COUNT(*) FROM verified_papers WHERE verification_timestamp >= datetime('now', '-1 minute')")
        saved_count = cursor.fetchone()[0]
        verify_msg = f"数据库验证: 最近一分钟内保存了 {saved_count} 条记录"
        logger.info(verify_msg)
        log_message(verify_msg, "info", "数据库")
        
        return True
        
    except sqlite3.Error as e:
        # 记录SQL错误
        conn.rollback()
        error_msg = f"数据库错误: {str(e)}"
        logger.error(error_msg)
        log_message(error_msg, "error", "数据库")
        status_text.error(error_msg)
        return False
        
    except Exception as e:
        # 记录其他错误
        conn.rollback()
        error_msg = f"保存验证论文到数据库失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        log_message(error_msg, "error", "数据库")
        status_text.error(error_msg)
        return False