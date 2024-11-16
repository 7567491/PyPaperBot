import logging
import re
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from .Paper import Paper

class ScholarSearcher:
    def __init__(self, chrome_version: int = None):
        self.logger = logging.getLogger(__name__)
        self.chrome_version = chrome_version
        self.base_url = "https://scholar.google.com"
        
    def search_page(self, query: str, page: int) -> List[Paper]:
        """
        搜索单页论文
        
        Args:
            query: 搜索关键词
            page: 页码
            
        Returns:
            List[Paper]: 搜索到的论文列表
        """
        self.logger.debug(f"搜索Scholar页面 {page}: {query}")
        papers = []
        driver = None
        
        try:
            # 设置Chrome选项
            options = Options()
            options.add_argument('--headless')  # 无头模式
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # 创建Chrome实例
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)  # 设置页面加载超时
            
            # 构建搜索URL
            start = (page - 1) * 10
            url = f"{self.base_url}/scholar?q={query}&start={start}&hl=zh-CN"
            self.logger.debug(f"访问URL: {url}")
            
            # 访问页面
            driver.get(url)
            
            # 等待搜索结果加载
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "gs_ri"))
                )
                self.logger.debug("搜索结果加载完成")
            except Exception as e:
                self.logger.error(f"等待搜索结果超时: {str(e)}")
                raise
            
            # 解析搜索结果
            results = driver.find_elements(By.CLASS_NAME, "gs_ri")
            self.logger.debug(f"找到 {len(results)} 个搜索结果")
            
            for i, result in enumerate(results, 1):
                try:
                    # 提取论文信息
                    title_elem = result.find_element(By.CLASS_NAME, "gs_rt")
                    title = title_elem.text.replace('[PDF] ', '').replace('[HTML] ', '')
                    authors_elem = result.find_element(By.CLASS_NAME, "gs_a")
                    authors = authors_elem.text
                    
                    # 获取URL
                    try:
                        url = title_elem.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    except:
                        url = None
                        self.logger.warning(f"论文 {i} 未找到URL")
                    
                    # 创建Paper对象
                    paper = Paper(
                        title=title,
                        authors=authors,
                        url=url
                    )
                    
                    # 提取年份
                    year_match = re.search(r'\b(19|20)\d{2}\b', authors)
                    if year_match:
                        paper.year = year_match.group()
                        self.logger.debug(f"论文 {i} 年份: {paper.year}")
                    
                    # 提取引用次数
                    cite_elem = result.find_elements(By.CSS_SELECTOR, ".gs_fl a")
                    for elem in cite_elem:
                        cite_text = elem.text
                        if "被引用" in cite_text or "引用" in cite_text:
                            citations_match = re.search(r'\d+', cite_text)
                            if citations_match:
                                paper.citations = int(citations_match.group())
                                self.logger.debug(f"论文 {i} 引用次数: {paper.citations}")
                            break
                    
                    papers.append(paper)
                    self.logger.debug(f"成功解析论文 {i}: {title}")
                    
                except Exception as e:
                    self.logger.warning(f"解析第 {i} 个搜索结果时出错: {str(e)}")
                    continue
            
            self.logger.info(f"成功解析 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            self.logger.error(f"Scholar搜索出错: {str(e)}", exc_info=True)
            raise
            
        finally:
            if driver:
                try:
                    driver.quit()
                    self.logger.debug("Chrome驱动已关闭")
                except:
                    pass
