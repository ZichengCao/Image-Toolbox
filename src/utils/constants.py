#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常量配置模块
"""

# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.bmp', '.webp']

# 图片格式映射
IMAGE_FORMAT_MAP = {
    'JPG': 'JPEG',
    'JPEG': 'JPEG',
    'PNG': 'PNG',
    'WEBP': 'WEBP',
    'BMP': 'BMP'
}

# 文件扩展名映射
FILE_EXTENSION_MAP = {
    'JPEG': '.jpg',
    'PNG': '.png',
    'WEBP': '.webp',
    'BMP': '.bmp'
}

# 默认配置
DEFAULT_QUALITY = 95
DEFAULT_SCALE = 80
DEFAULT_RESIZE_MODE = "max"
DEFAULT_SPLIT_X = 2
DEFAULT_SPLIT_Y = 2

# 线程同步配置
OVERWRITE_CONFIRM_TIMEOUT = 100  # ms (已废弃，使用 QWaitCondition 替代)

# UI 配置
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 720
NAVIGATION_WIDTH = 200
THUMBNAIL_WIDTH = 160
THUMBNAIL_HEIGHT = 200
THUMBNAIL_IMAGE_SIZE = 130
SCROLL_AREA_HEIGHT = 220

# 颜色配置
THEME_COLOR = '#0078D4'
BACKGROUND_COLOR = '#f8f8f8'
BORDER_COLOR = '#e8e8e8'
BORDER_DASHED_COLOR = '#d0d0d0'
TEXT_COLOR = '#333333'
SUBTITLE_COLOR = '#666666'
CAPTION_COLOR = '#888888'

# 对齐模式
ALIGN_MODES = {
    'horizontal': ["居中对齐", "顶部对齐", "底部对齐", "等比例放大", "等比例缩小"],
    'vertical': ["居中对齐", "左侧对齐", "右侧对齐", "等比例放大", "等比例缩小"]
}

ALIGN_MODE_MAPPING = {
    "等比例放大": "等比例放大到同一尺寸",
    "等比例缩小": "等比例缩小到同一尺寸"
}

# 缩放范围
SCALE_MIN = 1
SCALE_MAX = 100

# 质量范围
QUALITY_MIN = 1
QUALITY_MAX = 100

# 分割范围
SPLIT_MIN = 1
SPLIT_MAX = 20

# InfoBar 配置
INFOBAR_DURATION_WARNING = 3000
INFOBAR_DURATION_SUCCESS = 5000
INFOBAR_DURATION_ERROR = 5000

# 进度配置
PROGRESS_ANALYSIS = 10
PROGRESS_LOADING = 30
PROGRESS_CALCULATING = 50
PROGRESS_STITCHING_START = 50
PROGRESS_STITCHING_END = 80
PROGRESS_SAVING = 90
PROGRESS_COMPLETE = 100
PROGRESS_SPLIT_START = 20
PROGRESS_SPLIT_END = 90
