import sqlite3
from pathlib import Path
from prettytable import PrettyTable
import requests
import time
from urllib.parse import quote
import sys
from colorama import init, Fore, Style
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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

def get_scholar_url(title, db_conn=None, paper_id=None):
    """从Google Scholar获取论文URL
    Args:
        title: 论文标题
        db_conn: 数据库连接
        paper_id: 论文ID，用于更新URL
    """
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

    try:
        print_info("\n=== 启动Chrome浏览器 ===")
        # 使用 webdriver_manager 自动管理 ChromeDriver
        print_info("检查ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        
        # 配置Chrome选项
        print_info("配置Chrome选项...")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 初始化WebDriver
        print_info("启动Chrome...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            # 构造搜索URL
            print_info("\n=== 访问Google Scholar ===")
            search_url = f"https://scholar.google.com/scholar?q={quote(title)}"
            print_info("构造搜索URL...")
            print_info(f"URL: {search_url}")
            
            # 访问页面
            print_info("正在访问页面...")
            driver.get(search_url)
            
            print_info("等待页面加载...")
            time.sleep(2)
            
            # 等待搜索结果加载
            print_info("查找搜索结果...")
            wait = WebDriverWait(driver, 10)
            results = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "gs_ri")))
            
            if not results:
                print_warning("未找到任何搜索结果")
                return None
                
            print_success(f"找到 {len(results)} 个搜索结果")
            
            # 查找第一个结果的PDF链接
            print_info("\n=== 分析搜索结果 ===")
            for result in results[:1]:
                result_title = result.find_element(By.CSS_SELECTOR, "h3").text
                print_info(f"检查结果: {result_title}")
                
                # 尝试找到[PDF]链接
                print_info("查找PDF直接下载链接...")
                try:
                    pdf_links = result.find_elements(By.CSS_SELECTOR, "div.gs_or_ggsm a")
                    for link in pdf_links:
                        if '[PDF]' in link.text:
                            url = link.get_attribute('href')
                            print_success(f"找到PDF直接下载链接: {url}")
                            update_paper_url(url)  # 更新数据库
                            return url
                except:
                    print_warning("未找到PDF直接下载链接")
                    
                # 如果没有PDF链接，尝试找到标题链接
                print_info("查找标题链接...")
                try:
                    title_links = result.find_elements(By.CSS_SELECTOR, "h3.gs_rt a")
                    if title_links:
                        url = title_links[0].get_attribute('href')
                        print_success(f"找到标题链接: {url}")
                        update_paper_url(url)  # 更新数据库
                        return url
                except:
                    print_warning("未找到标题链接")
            
            print_warning("未找到任何可用链接")
            return None
            
        finally:
            print_info("\n=== 清理资源 ===")
            print_info("关闭Chrome浏览器...")
            driver.quit()
            print_info("浏览器已关闭")
            
    except Exception as e:
        print_error(f"获取Scholar URL失败: {str(e)}")
        print_error(f"错误类型: {type(e).__name__}")
        return None

def download_paper(title, scholar_url=None, db_conn=None, paper_id=None):
    """从Google Scholar下载论文"""
    print_info(f"\n开始尝试下载论文: {title}")
    
    if not scholar_url:
        print_info("尝试从Google Scholar获取链接...")
        scholar_url = get_scholar_url(title, db_conn, paper_id)  # 传入数据库连接和论文ID
        
    if not scholar_url:
        print_warning("无法获取下载链接，跳过下载")
        return False
        
    # 构造安全的文件名
    invalid_chars = '<>:"/\\|?*'
    safe_title = ''.join(c for c in title if c not in invalid_chars)
    
    # 确保pdf目录存在
    root_dir = Path(__file__).parent.parent
    pdf_dir = root_dir / "pdf"
    pdf_dir.mkdir(exist_ok=True)
    
    pdf_path = pdf_dir / f"{safe_title}.pdf"
    
    if pdf_path.exists():
        print_warning("论文已存在，跳过下载")
        return False
    
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    def save_pdf(response, path):
        """保存PDF文件并返回文件大小"""
        with open(path, 'wb') as f:
            content = response.content
            f.write(content)
        return len(content)
    
    try:
        # 尝试直接下载PDF
        print_info(f"尝试从链接下载: {scholar_url}")
        response = requests.get(scholar_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            content_length = int(response.headers.get('content-length', 0))
            
            print_info(f"响应状态码: {response.status_code}")
            print_info(f"内容类型: {content_type}")
            print_info(f"内容大小: {content_length} bytes")
            
            if 'pdf' in content_type or content_length > 1000:
                actual_size = save_pdf(response, pdf_path)
                print_success(f"下载成功！文件大小: {actual_size/1024:.1f}KB")
                return True
            else:
                print_warning("响应不是PDF格式")
        else:
            print_error(f"下载失败，状态码: {response.status_code}")
            
    except Exception as e:
        print_error(f"下载出错: {str(e)}")
        print_error(f"错误类型: {type(e).__name__}")
    
    return False

def get_download_range(total_papers):
    """获取用户输入的下载范围"""
    while True:
        try:
            print_info("\n请输入要下载的论文范围：")
            print_info(f"论文序号范围为: 1 - {total_papers}")
            print_info("示例: '1 10' 表示下载第1篇到第10篇论文")
            print_info("直接按回车将下载所有论文")
            
            user_input = input("请输入(开始序号 结束序号): ").strip()
            
            if not user_input:
                return 1, total_papers
                
            start, end = map(int, user_input.split())
            
            if start < 1 or end > total_papers or start > end:
                print_error(f"无效范围！请输入1到{total_papers}之间的数字，且起始序号要小于结束序号")
                continue
                
            return start, end
            
        except ValueError:
            print_error("输入格式错误！请输入两个数字，用空格分隔")
        except Exception as e:
            print_error(f"输入错误: {str(e)}")

def display_and_download_papers():
    """显示论文信息并尝试下载用户选择范围内的论文"""
    root_dir = Path(__file__).parent.parent
    db_path = root_dir / "db" / "paper.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='verified_papers'
        """)
        if not cursor.fetchone():
            print_error("错误：verified_papers 表不存在")
            return
            
        table = PrettyTable()
        table.field_names = ["序号", "论文标题", "引用数", "已下载", "URL状态"]  # 添加URL状态列
        table.align = "l"
        table.max_width = 100
        
        # 修改查询，添加url字段
        cursor.execute("""
            SELECT id, title, citations_count, url 
            FROM verified_papers 
            ORDER BY citations_count DESC NULLS LAST
        """)
        papers = cursor.fetchall()
        
        for index, paper in enumerate(papers, 1):
            is_downloaded = check_paper_downloaded(paper[1])
            title = paper[1][:97] + "..." if len(paper[1]) > 100 else paper[1]
            url_status = "有" if paper[3] else "无"  # paper[3]是URL字段
            
            row = [
                index, 
                title, 
                paper[2] or 0,  # citations_count
                "1" if is_downloaded else "0",
                url_status
            ]
            table.add_row(row)
        
        print_info(f"\n=== 论文统计信息 ===")
        print_info(f"总论文数: {len(papers)}")
        downloaded_count = sum(1 for paper in papers if check_paper_downloaded(paper[1]))
        url_count = sum(1 for paper in papers if paper[3])  # 统计有URL的论文数
        print_info(f"已下载论文数: {downloaded_count}")
        print_info(f"已存储URL论文数: {url_count}")
        print_info("\n=== 论文列表 ===")
        print(table)
        
        download_range = get_download_range(len(papers))
        if not download_range:
            print_error("下载已取消")
            return
            
        start_index, end_index = download_range
        print_success(f"\n将下载第 {start_index} 到第 {end_index} 篇论文")
        
        print_info("\n=== 开始下载流程 ===")
        attempt_count = 0
        success_count = 0
        
        selected_papers = papers[start_index-1:end_index]
        total_selected = len(selected_papers)
        
        for i, paper in enumerate(selected_papers, start_index):
            title = paper[1]
            url = paper[3]  # 获取存储的URL
            paper_id = paper[0]  # 获取论文ID
            
            if not check_paper_downloaded(title):
                attempt_count += 1
                print_info(f"\n尝试下载第 {i} 篇论文:")
                print_info(f"标题: {title}")
                print_info(f"存储URL: {url if url else '无'}")
                print_info(f"引用数: {paper[2] or 0}")
                
                # 传入数据库连接和论文ID
                if download_paper(title, scholar_url=url, db_conn=conn, paper_id=paper_id):
                    success_count += 1
                    print_success(f"论文下载成功！当前进度: 成功{success_count}篇/尝试{attempt_count}篇 (选择范围内共{total_selected}篇)")
                else:
                    print_error(f"此论文下载失败 (已尝试{attempt_count}篇，成功{success_count}篇)")
                    print_warning("将尝试下一篇")
            else:
                print_warning(f"\n第 {i} 篇论文已下载，跳过")
        
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