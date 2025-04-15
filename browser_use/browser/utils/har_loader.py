"""
HAR文件加载工具 - 用于从HAR文件加载Cookie和页面数据
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from playwright.async_api import BrowserContext as PlaywrightBrowserContext

logger = logging.getLogger(__name__)

class HarLoader:
    """
    从HAR文件加载数据到browser-use的工具类
    可以加载Cookie和其他有用的会话数据
    """
    
    @staticmethod
    async def load_cookies_from_har(
        context: PlaywrightBrowserContext, 
        har_file_path: str,
        filter_domains: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        从HAR文件加载cookies到Playwright的浏览器上下文
        
        Args:
            context: Playwright的BrowserContext对象
            har_file_path: HAR文件的路径
            filter_domains: 可选的域名过滤列表，只加载这些域名的Cookie
            
        Returns:
            加载的Cookie列表
        """
        # 确保文件存在
        har_path = Path(har_file_path)
        if not har_path.exists():
            raise FileNotFoundError(f"HAR文件不存在: {har_file_path}")
        
        # 读取HAR文件内容
        with open(har_path, 'r', encoding='utf-8') as file:
            try:
                har_data = json.load(file)
            except json.JSONDecodeError:
                logger.error(f"无法解析HAR文件: {har_file_path}")
                raise
        
        # 提取Cookie
        cookies = []
        processed_cookies = set()  # 用于跟踪已处理的cookie，避免重复
        
        for entry in har_data.get('log', {}).get('entries', []):
            request_url = entry.get('request', {}).get('url', '')
            
            # 如果提供了过滤域名，检查当前URL是否匹配
            if filter_domains:
                domain = urlparse(request_url).netloc
                if not any(domain.endswith(d) for d in filter_domains):
                    continue
            
            # 处理请求中的Cookie
            for cookie in entry.get('request', {}).get('cookies', []):
                cookie_key = f"{cookie.get('name')}@{cookie.get('domain')}"
                
                # 跳过已处理的相同Cookie
                if cookie_key in processed_cookies:
                    continue
                processed_cookies.add(cookie_key)
                
                # 创建符合Playwright格式的cookie对象
                # 处理expires字段，确保是数字类型
                expires_value = cookie.get('expires', -1)
                if expires_value is not None and not isinstance(expires_value, (int, float)):
                    try:
                        # 尝试将字符串转换为数字
                        expires_value = float(expires_value)
                    except (ValueError, TypeError):
                        # 如果无法转换，使用默认值-1（会话结束时过期）
                        expires_value = -1
                        logger.warning(f"Cookie '{cookie.get('name')}' 的expires值无效，已设置为-1")
                
                cookie_obj = {
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    'domain': cookie.get('domain'),
                    'path': cookie.get('path', '/'),
                    'expires': expires_value,
                    'httpOnly': cookie.get('httpOnly', False),
                    'secure': cookie.get('secure', False),
                    'sameSite': cookie.get('sameSite', 'Lax')
                }
                cookies.append(cookie_obj)
            
            # 也处理响应中设置的Cookie
            for header in entry.get('response', {}).get('headers', []):
                if header.get('name', '').lower() == 'set-cookie':
                    # TODO: 解析set-cookie头，需要更复杂的解析逻辑
                    # 当前实现简化，仅处理请求中的Cookie
                    pass
        
        # 将Cookie添加到浏览器上下文
        if cookies:
            logger.info(f"从HAR文件加载了 {len(cookies)} 个Cookie")
            await context.add_cookies(cookies)
        else:
            logger.warning("HAR文件中未找到Cookie")
        
        return cookies
    
    @staticmethod
    def extract_urls_from_har(
        har_file_path: str, 
        filter_domains: Optional[List[str]] = None,
        status_filter: Optional[List[int]] = None
    ) -> List[str]:
        """
        从HAR文件提取URL
        
        Args:
            har_file_path: HAR文件的路径
            filter_domains: 可选的域名过滤列表
            status_filter: 可选的HTTP状态码过滤列表
            
        Returns:
            URL列表
        """
        # 读取HAR文件内容
        with open(har_file_path, 'r', encoding='utf-8') as file:
            har_data = json.load(file)
        
        urls = []
        for entry in har_data.get('log', {}).get('entries', []):
            url = entry.get('request', {}).get('url', '')
            status = entry.get('response', {}).get('status', 0)
            
            # 应用状态码过滤
            if status_filter and status not in status_filter:
                continue
                
            # 应用域名过滤
            if filter_domains:
                domain = urlparse(url).netloc
                if not any(domain.endswith(d) for d in filter_domains):
                    continue
                    
            urls.append(url)
        
        return urls
