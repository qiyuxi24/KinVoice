"""
日志配置 —— 基于 loguru
"""
# 日志系统-记录系统的工作状况

import sys
from loguru import logger
from app.config import settings

# 移除默认的 handler，避免重复日志
logger.remove()

# 添加控制台输出，配置格式和级别
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
    level=settings.LOG_LEVEL.upper(),
    colorize=True,
    backtrace=True,      # 异常回溯更详细
    diagnose=True,       # 显示变量值（开发时可用，生产环境可关闭）
)

# 直接暴露 logger 实例，其他模块 from app.utils.logger import logger 即可
__all__ = ["logger"]
