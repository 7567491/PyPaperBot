import os
import requests
import logging
from urllib.parse import urljoin
from .Paper import Paper

class Downloader:
    def __init__(self, download_dir="downloads", use_doi_as_filename=False, scihub_mirror="https://sci-hub.se"):
        self.logger = logging.getLogger(__name__)
        self.download_dir = download_dir
        self.use_doi_as_filename = use_doi_as_filename
        self.scihub_mirror = scihub_mirror
        
        # 确保下载目录存在
        os.makedirs(download_dir, exist_ok=True)
        self.logger.info(f"初始化下载器: 目录={download_dir}")
    
    def download_paper(self, paper: Paper) -> bool:
        """
        下载论文，尝试多个来源
        
        Args:
            paper: Paper对象
            
        Returns:
            bool: 下载是否成功
        """
        if not paper.canBeDownloaded():
            self.logger.warning(f"论文无法下载: {paper.title} (缺少DOI或URL)")
            return False
            
        self.logger.info(f"开始下载论文: {paper.title}")
        
        # 首先尝试从Scholar链接下载
        if paper.scholar_link:
            self.logger.info("尝试从Scholar链接下载...")
            if self._download_from_scholar(paper):
                return True
                
        # 然后尝试从SciHub下载
        if paper.DOI:
            self.logger.info("尝试从SciHub下载...")
            if self._download_from_scihub(paper):
                return True
                
        self.logger.error(f"所有下载尝试均失败: {paper.title}")
        return False
    
    def _download_from_scholar(self, paper: Paper) -> bool:
        """从Scholar链接下载"""
        try:
            response = requests.get(paper.scholar_link, timeout=30)
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('application/pdf'):
                return self._save_pdf(response.content, paper)
            else:
                self.logger.warning("Scholar链接不是直接的PDF")
                return False
        except Exception as e:
            self.logger.error(f"从Scholar下载失败: {str(e)}")
            return False
    
    def _download_from_scihub(self, paper: Paper) -> bool:
        """从SciHub下载"""
        try:
            # 构建SciHub URL
            scihub_url = urljoin(self.scihub_mirror, paper.DOI)
            self.logger.debug(f"SciHub URL: {scihub_url}")
            
            # 获取页面
            response = requests.get(scihub_url, timeout=30)
            if response.status_code != 200:
                self.logger.warning(f"SciHub返回错误状态码: {response.status_code}")
                return False
                
            # 解析PDF链接
            # TODO: 实现PDF链接提取逻辑
            pdf_url = None  # 需要从页面中提取
            
            if pdf_url:
                # 下载PDF
                pdf_response = requests.get(pdf_url, timeout=30)
                if pdf_response.status_code == 200:
                    return self._save_pdf(pdf_response.content, paper)
                    
            self.logger.warning("无法从SciHub获取PDF链接")
            return False
            
        except Exception as e:
            self.logger.error(f"从SciHub下载失败: {str(e)}")
            return False
    
    def _save_pdf(self, content: bytes, paper: Paper) -> bool:
        """保存PDF文件"""
        try:
            # 获取文件名
            filename = paper.getFileName()
            filepath = os.path.join(self.download_dir, filename)
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(content)
                
            self.logger.info(f"PDF保存成功: {filepath}")
            paper.downloaded = True
            return True
            
        except Exception as e:
            self.logger.error(f"保存PDF失败: {str(e)}")
            return False
