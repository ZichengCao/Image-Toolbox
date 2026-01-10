#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件列表组件
"""

import os
from PIL import Image
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from qfluentwidgets import (
    ScrollArea, SimpleCardWidget, BodyLabel, CaptionLabel, 
    StrongBodyLabel, TransparentToolButton, FluentIcon
)


class FileListWidget(QWidget):
    """文件列表组件"""
    files_changed = Signal(list)  # 文件列表变化信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_files = []
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 文件列表滚动区域
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(220)
        self.scroll_area.setStyleSheet("""
            ScrollArea {
                background-color: #fafafa;
                border: 2px dashed #d0d0d0;
                border-radius: 12px;
            }
        """)

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(20, 20, 20, 20)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        # 空状态提示
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(12)

        empty_icon = BodyLabel("📁")
        empty_icon.setStyleSheet("font-size: 48px;")
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_icon)

        empty_title = StrongBodyLabel("拖拽图片到此处")
        empty_title.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_title)

        self.scroll_layout.addWidget(self.empty_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        valid_files = []
        invalid_files = []

        for file in files:
            if os.path.isfile(file):
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.webp']:
                    # 验证文件是否真的是有效的图片
                    if self._is_valid_image(file):
                        if file not in self.image_files:
                            valid_files.append(file)
                    else:
                        invalid_files.append(os.path.basename(file))

        if valid_files:
            self.image_files.extend(valid_files)
            self.update_file_list()
            self.files_changed.emit(self.image_files)

        # 可以添加提示告诉用户哪些文件无效（可选）

    def _is_valid_image(self, filepath):
        """验证文件是否是有效的图片"""
        try:
            # 检查文件大小
            if os.path.getsize(filepath) == 0:
                return False

            # 尝试打开图片验证
            with Image.open(filepath) as img:
                # 尝试读取图片尺寸来验证图片数据
                img.verify()
            return True
        except Exception:
            return False

    def update_file_list(self, show_size=False):
        """更新文件列表显示"""
        while self.scroll_layout.count() > 0:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.image_files:
            self.empty_widget = QWidget()
            empty_layout = QVBoxLayout(self.empty_widget)
            empty_layout.setAlignment(Qt.AlignCenter)
            empty_layout.setSpacing(12)

            empty_icon = BodyLabel("📁")
            empty_icon.setStyleSheet("font-size: 48px;")
            empty_icon.setAlignment(Qt.AlignCenter)
            empty_layout.addWidget(empty_icon)

            empty_title = StrongBodyLabel("拖拽图片到此处")
            empty_title.setAlignment(Qt.AlignCenter)
            empty_layout.addWidget(empty_title)

            self.scroll_layout.addWidget(self.empty_widget)
            return

        for filepath in self.image_files:
            item_widget = SimpleCardWidget()
            item_widget.setStyleSheet("SimpleCardWidget { border-radius: 6px; }")
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(16, 10, 12, 10)

            filename = os.path.basename(filepath)
            name_label = BodyLabel(filename)
            name_label.setToolTip(filepath)
            item_layout.addWidget(name_label, 1)

            # 显示文件大小或图片尺寸
            if show_size:
                try:
                    with Image.open(filepath) as img:
                        size_str = f"{img.width}×{img.height}"
                except Exception:
                    size_str = "未知"
            else:
                size = os.path.getsize(filepath)
                size_str = self.format_size(size)
            
            size_label = CaptionLabel(size_str)
            size_label.setStyleSheet("color: #888;")
            item_layout.addWidget(size_label)

            del_btn = TransparentToolButton(FluentIcon.CLOSE)
            del_btn.setFixedSize(28, 28)
            del_btn.clicked.connect(lambda checked, f=filepath: self.remove_file(f))
            item_layout.addWidget(del_btn)

            self.scroll_layout.addWidget(item_widget)

        self.scroll_layout.addStretch()

    def format_size(self, size):
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    def remove_file(self, filepath):
        """移除文件"""
        if filepath in self.image_files:
            self.image_files.remove(filepath)
            self.update_file_list()
            self.files_changed.emit(self.image_files)

    def clear_files(self):
        """清空文件列表"""
        self.image_files.clear()
        self.update_file_list()
        self.files_changed.emit(self.image_files)

    def get_files(self):
        """获取文件列表"""
        return self.image_files.copy()

    def set_files(self, files):
        """设置文件列表"""
        self.image_files = files.copy()
        self.update_file_list()
        self.files_changed.emit(self.image_files)