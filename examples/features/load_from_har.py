"""
从HAR文件加载数据的例子

这个示例展示了如何:
1. 从HAR文件加载Cookie
2. 使用加载的Cookie访问网站
3. 提取HAR文件中的URL

用法:
    python load_from_har.py [har_file_path] [login_prompt]

参数:
    har_file_path: HAR文件路径
    login_prompt: 可选，自定义登录后的指令，默认询问用户名和账户信息
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent, Browser
from browser_use.browser.context import BrowserContextConfig
from browser_use.browser.extensions.har_extension import HarExtension

# 加载环境变量
load_dotenv()

# 配置日志 - 使用更详细的格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

async def main():
	logger.info('=== 开始执行 HAR 文件加载脚本 ===')

	# 从命令行参数获取HAR文件路径和登录提示
	# 处理 HAR 文件路径
	if len(sys.argv) > 1:
		har_file_path = sys.argv[1]
		logger.info(f'[步骤1] 使用命令行提供的HAR文件路径: {har_file_path}')
	else:
		# 默认HAR文件路径
		har_file_path = os.path.join(os.path.dirname(__file__), 'example.har')
		logger.info(f'[步骤1] 未提供HAR文件路径，使用默认路径: {har_file_path}')
		logger.info('用法: python load_from_har.py [har_file_path] [login_prompt]')
	
	# 处理登录提示参数
	login_prompt = "请告诉我当前登录的用户名或账户信息。"  # 默认值
	if len(sys.argv) > 2:
		login_prompt = sys.argv[2]
		logger.info(f'[步骤1.1] 使用自定义登录提示: {login_prompt}')
	else:
		logger.info('使用默认登录提示')

	# 如果HAR文件不存在，打印错误并退出
	if not Path(har_file_path).exists():
		logger.error(f'[错误] HAR文件不存在: {har_file_path}')
		logger.info('请提供有效的HAR文件路径')
		return

	logger.info(f'[步骤2] HAR文件有效，准备初始化浏览器')

	# 创建浏览器实例
	logger.info('[步骤3] 创建浏览器实例')
	try:
		# 使用默认配置创建浏览器
		browser = Browser()
		logger.info('浏览器实例创建成功')
	except Exception as e:
		logger.error(f'[错误] 创建浏览器实例失败: {str(e)}')
		return

	try:
		logger.info('[步骤4] 创建浏览器上下文')
		# 创建显式的上下文配置
		context_config = BrowserContextConfig()
		# 使用显式配置创建上下文
		context = await browser.new_context(config=context_config)
		logger.info('浏览器上下文创建成功')
	except Exception as e:
		logger.error(f'[错误] 创建浏览器上下文失败: {str(e)}')
		return

	try:
		# 从HAR文件加载Cookie
		logger.info(f'[步骤5] 开始从HAR文件加载Cookie: {har_file_path}')
		await HarExtension.load_from_har(context, har_file_path)
		logger.info('HAR文件中的Cookie加载成功')

		# 提取HAR文件中的有效URL（状态码为200的URL）
		logger.info('[步骤6] 从HAR文件提取有效URL（状态码为200）')
		urls = HarExtension.extract_urls_from_har(har_file_path, status_filter=[200])
		logger.info(f'提取到 {len(urls)} 个有效URL')
		if urls:
			logger.debug(f'部分URL示例: {urls[:3]}')

		# 找到第一个有效的URL作为起始页
		logger.info('[步骤7] 寻找合适的起始URL')
		initial_url = None
		if urls:
			# 优先选择非图片、CSS和JS资源的URL
			logger.info('筛选非媒体资源的URL')
			for url in urls:
				if not any(url.endswith(ext) for ext in ['.jpg', '.png', '.gif', '.css', '.js']):
					initial_url = url
					logger.info(f'找到合适的URL: {initial_url}')
					break

			# 如果没有找到合适的URL，使用第一个URL
			if not initial_url and urls:
				initial_url = urls[0]
				logger.info(f'使用第一个URL作为起始页: {initial_url}')

		# 如果没有找到有效URL，使用默认值
		if not initial_url:
			initial_url = 'https://www.example.com'
			logger.info(f'未找到有效URL，使用默认值: {initial_url}')
		else:
			logger.info(f'[步骤8] 确定使用初始URL: {initial_url}')

		# 创建Agent并运行任务
		logger.info('[步骤9] 创建AI代理')
		try:
			agent = Agent(
				browser_context=context,
				task=f"""
                我已经从HAR文件加载了Cookie数据。请访问以下网址查看是否已经登录:
                {initial_url}
                
                如果已登录，{login_prompt}
                如果未登录，请尝试导航到登录页面，但不要输入任何凭据。
                """,
				llm=ChatOpenAI(model='gpt-4o'),
			)
			logger.info('AI代理创建成功')

			# 运行Agent
			logger.info('[步骤10] 开始运行AI代理...')
			await agent.run()
			logger.info('AI代理任务完成')
		except Exception as e:
			logger.error(f'[错误] 创建或运行AI代理时出错: {str(e)}')

	except Exception as e:
		logger.error(f'[错误] 执行过程中发生异常: {str(e)}')
	finally:
		# 关闭浏览器
		logger.info('[步骤11] 清理资源，关闭浏览器')
		try:
			await context.close()
			logger.info('浏览器已关闭')
		except Exception as e:
			logger.error(f'[错误] 关闭浏览器时出错: {str(e)}')

		logger.info('=== HAR文件加载脚本执行完毕 ===')

if __name__ == "__main__":
    logger.info("开始执行脚本")
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"脚本执行失败: {str(e)}")
    logger.info("脚本执行结束")
