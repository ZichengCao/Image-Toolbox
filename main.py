#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片工具箱 - 主程序入口
"""

import sys
from PySide6.QtWidgets import QApplication

from src.ui.main_window import ImageToolboxWindow
from src.utils.resources import get_app_icon


def main():
    app = QApplication(sys.argv)

    # 设置应用程序图标
    app.setWindowIcon(get_app_icon())
    
    # 设置应用程序信息
    app.setApplicationName("Image Stitcher")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Image Stitcher")

    window = ImageToolboxWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()