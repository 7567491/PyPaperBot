import sqlite3
from pathlib import Path
from prettytable import PrettyTable
import requests
import re
import time
from urllib.parse import quote
import sys
from colorama import init, Fore, Style

# 初始化colorama
init()

def print_info(msg):
    """打印普通信息"""
    print(f"{Style.NORMAL}{msg}{Style.RESET_ALL}")

def print_success(msg):
    """打印成功信息"""
    print(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")

def print_warning(msg):
    """打印警告信息"""
    print(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")

def print_error(msg):
    """打印错误信息"""
    print(f"{Fore.RED}{msg}{Style.RESET_ALL}")

def check_paper_downloaded(title):
    """检查论文是否已下载（忽略大小写）"""
    root_dir = Path(__file__).parent.parent
    pdf_dir = root_dir / "pdf"
    
    if not pdf_dir.exists():
        return False
        
    # 构造安全的文件名（小写）
    invalid_chars = '<>:"/\\|?*'
    safe_title = ''.join(c for c in title if c not in invalid_chars)
    safe_title_lower = safe_title.lower()  # 转换为小写
    
    # 获取所有PDF文件并比较（忽略大小写）
    try:
        for pdf_file in pdf_dir.glob("*.pdf"):
            # 移除.pdf后缀并转换为小写进行比较
            existing_name = pdf_file.stem.lower()
            if existing_name == safe_title_lower:
                return True
    except Exception as e:
        print_error(f"检查文件时出错: {str(e)}")
    
    return False

def download_paper(title, doi=None, url=None, scihub_urls=None, use_title_search=False, db_conn=None, paper_id=None):
    """下载论文
    Args:
        title: 论文标题
        doi: DOI号
        url: 数据库中存储的URL
        scihub_urls: 要使用的sci-hub镜像列表
        use_title_search: 是否使用标题搜索
        db_conn: 数据库连接
        paper_id: 论文ID，用于更新URL
    """
    print_info(f"\n开始尝试下载论文: {title}")
    
    # 首先尝试使用数据库中存储的URL
    if url:
        print_info(f"发现数据库中存储的URL: {url}")
        try:
            print_info("尝试使用存储的URL直接下载...")
            response = make_request(url, is_pdf=True)
            if response and ('pdf' in response.headers.get('content-type', '').lower() or 
                           int(response.headers.get('content-length', 0)) > 1000):
                pdf_path = get_pdf_path(title)
                actual_size = save_pdf(response, pdf_path)
                print_success(f"使用存储URL下载成功！文件大小: {actual_size/1024:.1f}KB")
                return True
            else:
                print_warning("存储的URL无法直接下载PDF，将尝试其他方式")
        except Exception as e:
            print_error(f"使用存储URL下载失败: {str(e)}")
    
    # 如果没有提供镜像列表，使用默认的第一个镜像
    if scihub_urls is None:
        scihub_urls = ["https://sci-hub.se/"]
    
    def update_paper_url(new_url):
        """更新数据库中的论文URL"""
        if db_conn and paper_id:
            try:
                cursor = db_conn.cursor()
                cursor.execute("""
                    UPDATE verified_papers 
                    SET url = ? 
                    WHERE id = ?
                """, (new_url, paper_id))
                db_conn.commit()
                print_success(f"已更新数据库中的URL: {new_url}")
            except sqlite3.Error as e:
                print_error(f"更新URL时发生错误: {str(e)}")
    
    # 构造安全的文件名
    invalid_chars = '<>:"/\\|?*'
    safe_title = ''.join(c for c in title if c not in invalid_chars)
    
    # 确保pdf目录存在
    root_dir = Path(__file__).parent.parent
    pdf_dir = root_dir / "pdf"
    pdf_dir.mkdir(exist_ok=True)
    
    pdf_path = pdf_dir / f"{safe_title}.pdf"
    
    # 如果文件已存在，跳过下载
    if pdf_path.exists():
        print_warning("论文已存在，跳过下载")
        return False
        
    # 添加更多请求头，模拟真实浏览器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    def extract_pdf_link(html_content):
        """从HTML中提取PDF链接"""
        # 尝试多种可能的模式
        patterns = [
            r'<button[^>]*onclick="location.href=\'([^\']+)\'[^>]*>save<',  # sci-hub save按钮
            r'<button[^>]*onclick="location.href=\'([^\']+)\'',  # 通用按钮链接
            r'(?<=location.href=\').+?(?=\')',  # 单引号模式
            r'(?<=location.href=").+?(?=")',    # 双引号模式
            r'<iframe[^>]*src="([^"]+)"',       # iframe src模式
            r'<embed[^>]*src="([^"]+)"',        # embed src模式
            r'(?<=sci-hub.se/downloads/)[^"]+(?=\/[^"\/]+\.pdf)',  # 下载链接模式
            r'https?://[^\s<>"]+?\.pdf',        # 直接PDF链接
            r'<a[^>]*href="([^"]*\.pdf)"',  # 普通PDF链接
            r'<meta[^>]*content="([^"]*\.pdf)"',  # meta标签中的PDF链接
            r'window\.location\.href\s*=\s*[\'"]([^\'"]+)[\'"]',  # JavaScript跳转
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                print_info(f"使用模式 {pattern} 找到链接")
                return matches[0]
        
        # 如果上述模式都没找到，尝试查找save按钮后的链接
        if 'save' in html_content.lower():
            print_info("找到save按钮，尝试提取链接")
            save_button_pos = html_content.lower().find('save')
            if save_button_pos != -1:
                # 在save按钮附近查找链接
                nearby_content = html_content[max(0, save_button_pos-200):save_button_pos+200]
                print_info(f"save按钮附近内容: {nearby_content}")
                
                # 尝试提取href或onclick中的链接
                href_matches = re.findall(r'href=[\'"]([^\'"]+)[\'"]', nearby_content)
                onclick_matches = re.findall(r'onclick=[\'"][^\'"]+=[\'"](https?://[^\'"]+)[\'"]', nearby_content)
                
                if href_matches:
                    print_info("从href中找到链接")
                    return href_matches[0]
                elif onclick_matches:
                    print_info("从onclick中找到链接")
                    return onclick_matches[0]
        
        return None

    # 在每次请求之间添加短暂延迟
    def make_request(url, is_pdf=False):
        time.sleep(1)  # 添加1秒延迟
        try:
            response = requests.get(url, headers=headers, timeout=30 if is_pdf else 10)
            return response
        except requests.exceptions.RequestException as e:
            print_error(f"请求失败: {e}")
            return None

    # 修改PDF下载和保存部分
    def save_pdf(response, path):
        """保存PDF文件并返回文件大小"""
        with open(path, 'wb') as f:
            content = response.content
            f.write(content)
        return len(content)  # 返回实际内容大小
    
    # 先尝试使用DOI下载
    if doi:
        print_info(f"使用DOI尝试下载: {doi}")
        for base_url in scihub_urls:
            try:
                url = base_url + doi
                print_info(f"尝试从 {url}")
                response = make_request(url)
                if not response:  # 检查response是否为None
                    continue
                print_info(f"状态码: {response.status_code}")
                
                # 保存HTML用于调试
                with open("debug_response.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print_info("已保存响应内容到debug_response.html")
                
                # 使用新的提取函数
                pdf_link = extract_pdf_link(response.text)
                if pdf_link:
                    if not pdf_link.startswith('http'):
                        pdf_url = 'https:' + pdf_link if pdf_link.startswith('//') else base_url + pdf_link
                    else:
                        pdf_url = pdf_link
                    
                    print_info(f"找到PDF链接: {pdf_url}")
                    pdf_response = make_request(pdf_url, is_pdf=True)
                    if not pdf_response:  # 检查pdf_response是否为None
                        continue
                        
                    # 获取内容类型和长度
                    content_type = pdf_response.headers.get('content-type', '').lower()
                    content_length = int(pdf_response.headers.get('content-length', 0))
                    print_info(f"PDF响应类型: {content_type}")
                    print_info(f"PDF响应大小: {content_length} bytes")
                    
                    if 'pdf' in content_type or content_length > 1000:
                        # 使用新的保存函数
                        actual_size = save_pdf(pdf_response, pdf_path)
                        print_success(f"下载成功！文件大小: {actual_size/1024:.1f}KB")
                        return True
                    else:
                        print_warning(f"响应可能不是PDF (类型: {content_type}, 大小: {content_length}字节)")
                else:
                    print_warning("未找到PDF链接")
            except Exception as e:
                print_error(f"尝试失败: {str(e)}")
                print_error(f"错误类型: {type(e).__name__}")
                continue
    
    # 根据use_title_search参数决定是否使用标题搜索
    if use_title_search and not doi:  # 如果启用标题搜索且没有DOI
        print_info(f"使用标题尝试下载: {title}")
        encoded_title = quote(title)
        for base_url in scihub_urls:
            try:
                url = base_url + encoded_title
                print_info(f"尝试从 {url}")
                response = make_request(url)
                print_info(f"状态码: {response.status_code}")
                
                pdf_link = extract_pdf_link(response.text)
                if pdf_link:
                    if not pdf_link.startswith('http'):
                        pdf_url = 'https:' + pdf_link if pdf_link.startswith('//') else base_url + pdf_link
                    else:
                        pdf_url = pdf_link
                    
                    print_info(f"找到PDF链接: {pdf_url}")
                    pdf_response = make_request(pdf_url, is_pdf=True)
                    
                    content_type = pdf_response.headers.get('content-type', '').lower()
                    content_length = int(pdf_response.headers.get('content-length', 0))
                    
                    if 'pdf' in content_type or content_length > 1000:
                        # 使用新的保存函数
                        actual_size = save_pdf(pdf_response, pdf_path)
                        print_success(f"下载成功！文件大小: {actual_size/1024:.1f}KB")
                        return True
                    else:
                        print_warning(f"响应可能不是PDF (类型: {content_type}, 大小: {content_length}字节)")
                else:
                    print_warning("未找到PDF链接")
            except Exception as e:
                print_error(f"尝试失败: {str(e)}")
                print_error(f"错误类型: {type(e).__name__}")
                continue
    elif not doi:
        print_warning("没有DOI且未启用标题搜索，跳过下载")
        return False
    
    print_error("所有下载尝试均失败")
    return False

def get_download_params(total_papers):
    """获取用户输入的下载范围和参数
    Args:
        total_papers: 论文总数
    Returns:
        tuple: (start_index, end_index, mirror_count, use_title_search)
    """
    while True:
        try:
            print_info("\n=== 下载设置 ===")
            print_info(f"论文序号范围为: 1 - {total_papers}")
            print_info("示例: '1 10' 表示下载第1篇到第10篇论文")
            print_info("直接按回车将下载所有论文")
            
            # 获取下载范围
            range_input = input("请输入下载范围(开始序号 结束序号): ").strip()
            if not range_input:
                start, end = 1, total_papers
            else:
                start, end = map(int, range_input.split())
                if start < 1 or end > total_papers or start > end:
                    print_error(f"无效范围！请输入1到{total_papers}之间的数字，且起始序号要小于结束序号")
                    continue

            # 获取镜像数量
            print_info("\n请选择使用的Sci-Hub镜像数量(1-3):")
            print_info("数量越多成功率越高，但下载速度可能变慢")
            print_info("直接按回车默认使用1个镜像")
            mirror_input = input("镜像数量(1-3): ").strip()
            mirror_count = 1 if not mirror_input else int(mirror_input)
            if mirror_count < 1 or mirror_count > 3:
                print_error("镜像数量必须在1-3之间")
                continue

            # 是否使用标题搜索
            print_info("\n是否在DOI搜索失败后使用标题搜索？")
            print_info("使用标题搜索可能提高成功率，但可能下载到错误文献")
            print_info("直接按回车默认不使用标题搜索")
            use_title = input("使用标题搜索(y/N): ").strip().lower()
            use_title_search = use_title == 'y'

            return start, end, mirror_count, use_title_search

        except ValueError:
            print_error("输入格式错误！请重新输入")
        except Exception as e:
            print_error(f"输入错误: {str(e)}")

def display_and_download_papers():
    """显示论文信息并尝试下载用户选择范围内的论文"""
    # 获取数据库路径
    root_dir = Path(__file__).parent.parent
    db_path = root_dir / "db" / "paper.db"
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='verified_papers'
        """)
        if not cursor.fetchone():
            print_error("错误：verified_papers 表不存在")
            return
            
        # 创建表格对象
        table = PrettyTable()
        table.field_names = ["序号", "论文标题", "引用数", "已下载"]
        
        # 设置表格样式
        table.align = "l"  # 左对齐
        table.max_width = 100  # 增加最大宽度显示更多标题内容
        
        # 查询验证过的论文，按引用数降序排列
        cursor.execute("""
            SELECT id, title, citations_count, doi, url 
            FROM verified_papers 
            ORDER BY citations_count DESC NULLS LAST
        """)
        papers = cursor.fetchall()
        
        # 添加数据到表格，使用显示顺序的序号
        for index, paper in enumerate(papers, 1):  # 从1开始编号
            is_downloaded = check_paper_downloaded(paper[1])
            title = paper[1][:97] + "..." if len(paper[1]) > 100 else paper[1]
            row = [index, title, paper[2] or 0, "1" if is_downloaded else "0"]  # 使用index而不是paper[0]
            table.add_row(row)
        
        # 打印统计信息
        print_info(f"\n=== 论文统计信息 ===")
        print_info(f"总论文数: {len(papers)}")
        downloaded_count = sum(1 for paper in papers if check_paper_downloaded(paper[1]))
        print_info(f"已下载论文数: {downloaded_count}")
        print_info("\n=== 论文列表 ===")
        print(table)
        
        # 替换原来的get_download_range调用
        download_params = get_download_params(len(papers))
        if not download_params:
            print_error("下载已取消")
            return
        
        start_index, end_index, mirror_count, use_title_search = download_params
        
        # 根据用户选择截取镜像列表
        scihub_urls = [
            "https://sci-hub.se/",
            "https://sci-hub.ru/",
            "https://sci-hub.st/"
        ][:mirror_count]
        
        print_success(f"\n=== 下载配置 ===")
        print_info(f"下载范围: 第 {start_index} 到第 {end_index} 篇论文")
        print_info(f"使用镜像数量: {mirror_count}")
        print_info(f"使用标题搜索: {'是' if use_title_search else '否'}")
        
        # 下载部分
        print_info("\n=== 开始下载流程 ===")
        attempt_count = 0
        success_count = 0
        
        # 只处理用户选择范围内的论文
        selected_papers = papers[start_index-1:end_index]
        total_selected = len(selected_papers)
        
        for i, paper in enumerate(selected_papers, start_index):
            title = paper[1]
            doi = paper[3]
            url = paper[4]  # 获取存储的URL
            paper_id = paper[0]  # 获取论文ID
            
            if not check_paper_downloaded(title):
                attempt_count += 1
                print_info(f"\n尝试下载第 {i} 篇论文:")
                print_info(f"标题: {title}")
                print_info(f"DOI: {doi if doi else '无'}")
                print_info(f"存储URL: {url if url else '无'}")
                print_info(f"引用数: {paper[2] or 0}")
                
                if download_paper(
                    title, 
                    doi=doi, 
                    url=url,
                    scihub_urls=scihub_urls, 
                    use_title_search=use_title_search,
                    db_conn=conn,
                    paper_id=paper_id
                ):
                    success_count += 1
                    print_success(f"论文下载成功！当前进度: 成功{success_count}篇/尝试{attempt_count}篇 (选择范围内共{total_selected}篇)")
                else:
                    print_error(f"此论文下载失败 (已尝试{attempt_count}篇，成功{success_count}篇)")
                    print_warning("将尝试下一篇")
            else:
                print_warning(f"\n第 {i} 篇论文已下载，跳过")
        
        # 打印最终统计
        print_info("\n=== 下载统计 ===")
        print_info(f"选择范围: 第{start_index}篇 到 第{end_index}篇")
        print_info(f"总共尝试: {attempt_count}篇")
        print_success(f"成功下载: {success_count}篇")
        print_error(f"下载失败: {attempt_count - success_count}篇")
        print_info("\n下载流程结束")
        
    except sqlite3.Error as e:
        print_error(f"数据库错误: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    display_and_download_papers() 