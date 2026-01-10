#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片压缩页面
"""

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, CaptionLabel, PushButton, PrimaryPushButton,
    ProgressBar, InfoBar, InfoBarPosition, MessageBox
)

from ..components.file_list_widget import FileListWidget
from ..components.params_card import CompressParamsCard
from ...core.image_processor import CompressThread


class ImageCompressPage(QWidget):
    """图片压缩页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # 标题区域
        title = TitleLabel("图片压缩")
        layout.addWidget(title)

        subtitle = CaptionLabel("拖拽图片到下方区域，支持批量压缩处理")
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # 文件列表组件
        self.file_list = FileListWidget()
        self.file_list.files_changed.connect(self.on_files_changed)
        layout.addWidget(self.file_list)

        # 参数设置卡片
        self.params_card = CompressParamsCard()
        layout.addWidget(self.params_card)

        # 弹性空间
        layout.addStretch(1)

        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 底部操作栏
        self.setup_bottom_bar(layout)

    def setup_bottom_bar(self, layout):
        """设置底部操作栏"""
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)

        self.status_label = CaptionLabel("就绪")
        self.status_label.setStyleSheet("color: #666;")
        bottom_layout.addWidget(self.status_label, 1)

        self.clear_btn = PushButton("清空")
        self.clear_btn.setMinimumWidth(80)
        self.clear_btn.clicked.connect(self.clear_list)
        bottom_layout.addWidget(self.clear_btn)

        self.compress_btn = PrimaryPushButton("开始压缩")
        self.compress_btn.setMinimumWidth(120)
        self.compress_btn.clicked.connect(self.start_compress)
        bottom_layout.addWidget(self.compress_btn)

        layout.addLayout(bottom_layout)

    def on_files_changed(self, files):
        """文件列表变化时的处理"""
        if files:
            self.status_label.setText(f"共 {len(files)} 张图片")
        else:
            self.status_label.setText("就绪")

    def clear_list(self):
        """清空列表"""
        if not self.file_list.get_files():
            return
        w = MessageBox("确认清空", "确定要清空所有图片吗？", self)
        if w.exec():
            self.file_list.clear_files()
            self.status_label.setText("就绪")

    def start_compress(self):
        """开始压缩"""
        image_files = self.file_list.get_files()
        if not image_files:
            InfoBar.warning(
                title="提示",
                content="请先添加图片",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        params = self.params_card.get_params()
        output_dir = params['output_dir'] or os.path.dirname(image_files[0])

        self.compress_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.thread = CompressThread(
            image_files,
            output_dir,
            params['scale'],
            params['quality'],
            params['output_format']
        )
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.status.connect(lambda s: self.status_label.setText(s))
        self.thread.finished.connect(self.on_compress_finished)
        self.thread.error.connect(self.on_compress_error)
        self.thread.overwrite_request.connect(self.on_overwrite_request)
        self.thread.start()

    def on_compress_finished(self, results):
        """压缩完成"""
        self.compress_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        total_original = sum(r['original_size'] for r in results)
        total_new = sum(r['new_size'] for r in results)
        ratio = (1 - total_new / total_original) * 100 if total_original > 0 else 0

        self.status_label.setText(f"完成，节省 {ratio:.1f}%")
        InfoBar.success(
            title="完成",
            content=f"已处理 {len(results)} 张图片，体积减少 {ratio:.1f}%",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )

    def on_compress_error(self, error_msg):
        """压缩错误"""
        self.compress_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("压缩失败")
        InfoBar.error(
            title="错误",
            content=error_msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
    
    def on_overwrite_request(self, file_path):
        """处理文件覆盖请求"""
        filename = os.path.basename(file_path)
        w = MessageBox("确认覆盖", f"文件 '{filename}' 已存在，是否要覆盖？", self)
        self.thread.set_overwrite_allowed(w.exec())