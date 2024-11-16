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
            # 初始化Chrome选项
            self.logger.info("正在初始化Chrome选项...")
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # 安装和启动ChromeDriver
            self.logger.info("正在安装ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            
            self.logger.info("正在启动Chrome浏览器...")
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)
            
            # 构建和访问URL
            start = (page - 1) * 10
            url = f"{self.base_url}/scholar?q={query}&start={start}&hl=zh-CN"
            self.logger.info(f"正在访问Google Scholar: {url}")
            
            try:
                driver.get(url)
                self.logger.info("页面加载请求已发送")
            except Exception as e:
                self.logger.error(f"页面加载超时或失败: {str(e)}")
                raise
            
            # 等待搜索结果
            self.logger.info("等待搜索结果加载...")
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "gs_ri"))
                )
                self.logger.info("搜索结果加载完成")
                
                # 获取并显示页面主要信息
                self.logger.info("===================== 页面信息 =====================")
                
                # 获取搜索统计信息
                try:
                    stats = driver.find_element(By.ID, "gs_ab_md")
                    if stats:
                        self.logger.info(f"搜索统计: {stats.text}")
                except:
                    self.logger.info("未找到搜索统计信息")
                
                # 获取当前页码信息
                try:
                    footer = driver.find_element(By.ID, "gs_n")
                    if footer:
                        self.logger.info(f"页码信息: {footer.text}")
                except:
                    self.logger.info("未找到页码信息")
                
                # 检查是否有验证
                if "验证" in driver.page_source or "robot" in driver.page_source.lower():
                    self.logger.warning("检测到可能需要验证码")
                
                # 获取搜索结果数量
                results = driver.find_elements(By.CLASS_NAME, "gs_ri")
                result_count = len(results)
                self.logger.info(f"本页结果数量: {result_count}")
                
                # 检查是否有警告信息
                try:
                    warnings = driver.find_elements(By.CLASS_NAME, "gs_alrt")
                    if warnings:
                        for warning in warnings:
                            self.logger.warning(f"Google Scholar警告: {warning.text}")
                except:
                    pass
                
                # 保存页面截图（可选）
                try:
                    screenshot_path = f"scholar_page_{page}.png"
                    driver.save_screenshot(screenshot_path)
                    self.logger.info(f"页面截图已保存: {screenshot_path}")
                except:
                    self.logger.warning("无法保存页面截图")
                
                self.logger.info("==================================================")
                
            except Exception as e:
                self.logger.error(f"等待搜索结果超时: {str(e)}")
                self.logger.error("可能原因：网络问题或被Google Scholar限制访问")
                raise
            
            # 解析结果
            self.logger.info("开始解析搜索结果...")
            results = driver.find_elements(By.CLASS_NAME, "gs_ri")
            result_count = len(results)
            self.logger.info(f"找到 {result_count} 个搜索结果")
            
            if result_count == 0:
                self.logger.warning("未找到任何搜索结果，可能被Google Scholar限制访问")
                return papers
            
            # 处理每个搜索结果
            for i, result in enumerate(results, 1):
                self.logger.info(f"正在处理第 {i}/{result_count} 个结果...")
                try:
                    # 提取标题
                    title_elem = result.find_element(By.CLASS_NAME, "gs_rt")
                    title = title_elem.text.replace('[PDF] ', '').replace('[HTML] ', '')
                    self.logger.debug(f"提取到标题: {title}")
                    
                    # 提取作者信息
                    authors_elem = result.find_element(By.CLASS_NAME, "gs_a")
                    authors = authors_elem.text
                    self.logger.debug(f"提取到作者信息: {authors}")
                    
                    # 获取scholar链接
                    try:
                        url_elem = title_elem.find_element(By.CSS_SELECTOR, "a")
                        scholar_link = url_elem.get_attribute("href") if url_elem else None
                        self.logger.debug(f"提取到scholar链接: {scholar_link}")
                    except:
                        scholar_link = None
                        self.logger.warning(f"论文未找到scholar链接: {title}")
                    
                    # 提取年份
                    year_match = re.search(r'\b(19|20)\d{2}\b', authors)
                    year = year_match.group() if year_match else None
                    if year:
                        self.logger.debug(f"提取到年份: {year}")
                    
                    # 提取引用次数
                    cites = None
                    try:
                        # 查找所有可能包含引用信息的元素
                        cite_elems = result.find_elements(By.CSS_SELECTOR, ".gs_fl a")
                        self.logger.debug(f"找到 {len(cite_elems)} 个可能包含引用信息的元素")
                        
                        # 记录所有找到的文本，用于调试
                        for idx, elem in enumerate(cite_elems):
                            try:
                                elem_text = elem.text
                                elem_href = elem.get_attribute("href")
                                self.logger.debug(f"元素 {idx + 1}: text='{elem_text}', href='{elem_href}'")
                            except:
                                self.logger.debug(f"元素 {idx + 1}: 无法获取文本或链接")
                        
                        # 尝试不同的引用文本模式
                        citation_patterns = [
                            (r'被引用次数[：:]\s*(\d+)', '中文冒号模式'),
                            (r'被引用\s*(\d+)\s*次', '中文被引用模式'),
                            (r'引用次数[：:]\s*(\d+)', '中文引用次数模式'),
                            (r'引用[：:]\s*(\d+)', '中文引用模式'),
                            (r'被引用[：:]\s*(\d+)', '中文被引用冒号模式'),
                            (r'引用\s*(\d+)', '中文简单模式'),
                            (r'Cited by (\d+)', '英文模式'),
                            (r'(\d+)\s*次引用', '中文后缀模式'),
                            (r'(\d+)\s*引用', '中文简单后缀模式')
                        ]
                        
                        for elem in cite_elems:
                            try:
                                cite_text = elem.text
                                self.logger.debug(f"处理引用文本: '{cite_text}'")
                                
                                for pattern, pattern_name in citation_patterns:
                                    match = re.search(pattern, cite_text)
                                    if match:
                                        cites = int(match.group(1))
                                        self.logger.info(f"使用{pattern_name}成功提取引用次数: {cites}")
                                        self.logger.debug(f"匹配模式: {pattern}")
                                        self.logger.debug(f"原始文本: {cite_text}")
                                        break
                                
                                if cites is not None:
                                    break
                                    
                            except Exception as e:
                                self.logger.warning(f"处理单个引用元素时出错: {str(e)}")
                                continue
                        
                        # 如果没有找到引用次数，尝试其他方法
                        if cites is None:
                            # 尝试查找包含"cited by"的链接
                            for elem in cite_elems:
                                try:
                                    href = elem.get_attribute("href")
                                    if href and "cites=" in href:
                                        # 从URL中提取引用数
                                        cites_match = re.search(r'cites=(\d+)', href)
                                        if cites_match:
                                            cites = int(cites_match.group(1))
                                            self.logger.info(f"从URL成功提取引用次数: {cites}")
                                            break
                                except Exception as e:
                                    self.logger.warning(f"从URL提取引用次数时出错: {str(e)}")
                                    continue
                        
                        if cites is None:
                            self.logger.warning(f"未能找到论文的引用次数: {title}")
                            # 记录页面结构，帮助调试
                            try:
                                citation_section = result.find_element(By.CLASS_NAME, "gs_fl")
                                self.logger.debug(f"引用部分HTML: {citation_section.get_attribute('innerHTML')}")
                            except:
                                self.logger.debug("无法获取引用部分的HTML结构")
                    
                    except Exception as e:
                        self.logger.error(f"提取引用次数时出错: {str(e)}", exc_info=True)
                        self.logger.debug("尝试记录元素结构以供调试")
                        try:
                            self.logger.debug(f"论文元素HTML: {result.get_attribute('innerHTML')}")
                        except:
                            self.logger.debug("无法获取论文元素的HTML结构")
                    
                    # 创建Paper对象并设置引用次数
                    paper = Paper(
                        title=title,
                        scholar_link=scholar_link,
                        scholar_page=page,
                        year=year,
                        authors=authors
                    )
                    
                    if cites is not None:
                        paper.cites_num = cites
                        self.logger.info(f"成功设置论文引用次数: {paper.cites_num}")
                    else:
                        paper.cites_num = 0  # 设置默认值
                        self.logger.warning(f"使用默认引用次数(0): {title}")
                    
                    # 提取DOI（如果有）
                    try:
                        links = result.find_elements(By.CSS_SELECTOR, ".gs_fl a")
                        for link in links:
                            href = link.get_attribute("href")
                            if href and "doi.org" in href:
                                paper.DOI = href.split("doi.org/")[-1]
                                self.logger.debug(f"提取到DOI: {paper.DOI}")
                                break
                    except:
                        self.logger.debug(f"未找到DOI: {title}")
                    
                    papers.append(paper)
                    self.logger.info(f"成功解析论文 {i}/{result_count}: {title}")
                    
                except Exception as e:
                    self.logger.error(f"解析第 {i} 个搜索结果时出错: {str(e)}", exc_info=True)
                    continue
            
            self.logger.info(f"页面解析完成，共解析 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            self.logger.error(f"Scholar搜索过程出错: {str(e)}", exc_info=True)
            raise
            
        finally:
            if driver:
                self.logger.info("正在关闭Chrome浏览器...")
                try:
                    driver.quit()
                    self.logger.info("Chrome浏览器已关闭")
                except Exception as e:
                    self.logger.error(f"关闭Chrome浏览器时出错: {str(e)}")
