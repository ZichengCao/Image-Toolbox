#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片工具箱 - 主程序入口
"""

import sys
import os
import logging
from PySide6.QtWidgets import QApplication

from src.ui.main_window import ImageToolboxWindow
from src.utils.resources import get_app_icon
from src.utils.logging_config import setup_logging


def main():
    # 初始化日志系统
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    log_file = os.path.join(log_dir, 'image_stitcher.log')
    setup_logging(log_file=log_file, log_level=logging.INFO)
    
    app = QApplication(sys.argv)

    # 设置应用程序图标
    app.setWindowIcon(get_app_icon())
    
    # 设置应用程序信息
    app.setApplicationName("图片工具箱")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Image Toolbox")

    window = ImageToolboxWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()