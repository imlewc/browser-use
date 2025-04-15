"""
HAR文件扩展模块 - 为Browser和BrowserContext提供HAR文件加载功能
"""

import logging
from typing import List, Optional

from browser_use.browser.utils.har_loader import HarLoader

logger = logging.getLogger(__name__)

class HarExtension:
    """为Browser和BrowserContext提供HAR文件操作扩展"""
    
    @staticmethod
    async def load_from_har(context, har_file_path: str, filter_domains: Optional[List[str]] = None) -> None:
        """
        从HAR文件加载Cookie到浏览器上下文
        
        Args:
            context: BrowserContext实例
            har_file_path: HAR文件的路径
            filter_domains: 可选的域名过滤列表，只加载这些域名的Cookie
        """
        # 获取Playwright的context对象
        session = await context.get_session()
        if not session or not session.context:
            logger.error("无法获取有效的浏览器会话，请确保浏览器已初始化")
            return
        
        # 使用HarLoader加载Cookie
        try:
            await HarLoader.load_cookies_from_har(
                session.context, 
                har_file_path,
                filter_domains
            )
            logger.info(f"成功从HAR文件 {har_file_path} 加载数据")
        except Exception as e:
            logger.error(f"加载HAR文件失败: {str(e)}")
            raise
    
    @staticmethod
    def extract_urls_from_har(
        har_file_path: str, 
        filter_domains: Optional[List[str]] = None,
        status_filter: Optional[List[int]] = [200]
    ) -> List[str]:
        """
        从HAR文件提取URL
        
        Args:
            har_file_path: HAR文件的路径
            filter_domains: 可选的域名过滤列表
            status_filter: 可选的HTTP状态码过滤列表，默认只提取状态码为200的URL
            
        Returns:
            URL列表
        """
        return HarLoader.extract_urls_from_har(
            har_file_path, 
            filter_domains,
            status_filter
        )
