#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块
"""

import logging
import os
from typing import Optional


def setup_logging(
    log_file: Optional[str] = None,
    log_level: int = logging.INFO,
    enable_console: bool = True
) -> logging.Logger:
    """配置日志系统
    
    Args:
        log_file: 日志文件路径，如果为 None 则不记录到文件
        log_level: 日志级别
        enable_console: 是否在控制台输出日志
        
    Returns:
        配置好的 logger 实例
    """
    logger = logging.getLogger('ImageStitcher')
    logger.setLevel(log_level)
    
    if logger.handlers:
        logger.handlers.clear()
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger
    
    Args:
        name: logger 名称
        
    Returns:
        logger 实例
    """
    return logging.getLogger(f'ImageStitcher.{name}')
