#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口界面 - 重构版本
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QFrame
from qfluentwidgets import (
    PushButton, StrongBodyLabel, CaptionLabel, setThemeColor
)

from .pages import ImageStitcherPage, ImageCompressPage, ImageResizePage, ImageGridSplitPage, ImageCropPage, ImageGeminiWatermarkPage
from ..utils.resources import get_app_icon


# 统一的导航按钮样式
NAV_BUTTON_STYLE = """
    PushButton {
        background: transparent;
        border: none;
        border-radius: 6px;
        padding: 10px 16px;
        text-align: left;
        font-size: 14px;
    }
    PushButton:hover {
        background-color: rgba(0, 0, 0, 0.05);
    }
    PushButton:checked {
        background-color: #0078D4;
        color: white;
    }
"""


class ImageToolboxWindow(QWidget):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片工具箱")
        self.resize(1100, 720)
        self.setMinimumSize(800, 600)
        self.setWindowIcon(get_app_icon())
        setThemeColor('#0078D4')
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧导航栏
        self.setup_navigation(layout)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background-color: #e8e8e8;")
        separator.setFixedWidth(1)
        layout.addWidget(separator)

        # 右侧内容区域
        self.setup_content_area(layout)

    def setup_navigation(self, layout):
        """设置左侧导航栏"""
        nav_widget = QWidget()
        nav_widget.setFixedWidth(200)
        nav_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f8f8;
            }
        """)
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(16, 24, 16, 24)
        nav_layout.setSpacing(4)

        # Logo/标题
        logo_label = StrongBodyLabel("图片工具箱")
        logo_label.setStyleSheet("font-size: 18px; color: #333; padding: 8px 0 16px 4px;")
        nav_layout.addWidget(logo_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e0e0e0;")
        line.setFixedHeight(1)
        nav_layout.addWidget(line)

        nav_layout.addSpacing(12)

        # 导航按钮
        self.stitch_btn = PushButton("图片拼接")
        self.stitch_btn.setCheckable(True)
        self.stitch_btn.setChecked(True)
        self.stitch_btn.clicked.connect(lambda: self.switch_page(0))
        self.stitch_btn.setStyleSheet(NAV_BUTTON_STYLE)
        nav_layout.addWidget(self.stitch_btn)

        self.compress_nav_btn = PushButton("图片压缩")
        self.compress_nav_btn.setCheckable(True)
        self.compress_nav_btn.clicked.connect(lambda: self.switch_page(1))
        self.compress_nav_btn.setStyleSheet(NAV_BUTTON_STYLE)
        nav_layout.addWidget(self.compress_nav_btn)

        self.resize_nav_btn = PushButton("尺寸统一")
        self.resize_nav_btn.setCheckable(True)
        self.resize_nav_btn.clicked.connect(lambda: self.switch_page(2))
        self.resize_nav_btn.setStyleSheet(NAV_BUTTON_STYLE)
        nav_layout.addWidget(self.resize_nav_btn)

        self.split_nav_btn = PushButton("图片等分")
        self.split_nav_btn.setCheckable(True)
        self.split_nav_btn.clicked.connect(lambda: self.switch_page(3))
        self.split_nav_btn.setStyleSheet(NAV_BUTTON_STYLE)
        nav_layout.addWidget(self.split_nav_btn)

        self.crop_nav_btn = PushButton("图片分割")
        self.crop_nav_btn.setCheckable(True)
        self.crop_nav_btn.clicked.connect(lambda: self.switch_page(4))
        self.crop_nav_btn.setStyleSheet(NAV_BUTTON_STYLE)
        nav_layout.addWidget(self.crop_nav_btn)

        self.gemini_watermark_btn = PushButton("Gemini水印")
        self.gemini_watermark_btn.setCheckable(True)
        self.gemini_watermark_btn.clicked.connect(lambda: self.switch_page(5))
        self.gemini_watermark_btn.setStyleSheet(NAV_BUTTON_STYLE)
        nav_layout.addWidget(self.gemini_watermark_btn)

        self.nav_buttons = [self.stitch_btn, self.compress_nav_btn, self.resize_nav_btn, self.split_nav_btn, self.crop_nav_btn, self.gemini_watermark_btn]

        nav_layout.addStretch()

        # 版本信息
        version_label = CaptionLabel("v1.0.0")
        version_label.setStyleSheet("color: #999; padding: 4px;")
        nav_layout.addWidget(version_label)

        layout.addWidget(nav_widget)

    def setup_content_area(self, layout):
        """设置右侧内容区域"""
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: white;")
        layout.addWidget(self.stack, 1)

        # 添加页面
        self.stitch_page = ImageStitcherPage()
        self.stack.addWidget(self.stitch_page)

        self.compress_page = ImageCompressPage()
        self.stack.addWidget(self.compress_page)

        self.resize_page = ImageResizePage()
        self.stack.addWidget(self.resize_page)

        self.split_page = ImageGridSplitPage()
        self.stack.addWidget(self.split_page)

        self.crop_page = ImageCropPage()
        self.stack.addWidget(self.crop_page)

        self.gemini_watermark_page = ImageGeminiWatermarkPage()
        self.stack.addWidget(self.gemini_watermark_page)

    def switch_page(self, index):
        """切换页面"""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)