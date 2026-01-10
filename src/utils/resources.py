#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源管理工具
"""

import os
import sys
from PySide6.QtGui import QIcon, QPixmap


def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的路径
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # 开发环境路径
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_path, relative_path)


def get_app_icon():
    """获取应用程序图标"""
    icon_path = get_resource_path("assets/icon.png")
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    else:
        # 如果图标文件不存在，返回默认图标
        return QIcon()


def create_default_icon():
    """创建默认图标（如果没有图标文件）"""
    # 创建一个简单的默认图标
    pixmap = QPixmap(64, 64)
    pixmap.fill()
    return QIcon(pixmap)