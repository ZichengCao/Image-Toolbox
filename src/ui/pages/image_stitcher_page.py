#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片拼接页面
"""

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from qfluentwidgets import (
    TitleLabel, CaptionLabel, ScrollArea, PushButton, PrimaryPushButton,
    ProgressBar, InfoBar, InfoBarPosition, MessageBox
)

from ..components.thumbnail_card import ThumbnailCard
from ..components.params_card import StitchParamsCard
from ...core.image_processor import StitchThread


class ImageStitcherPage(QWidget):
    """图片拼接页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_files = []
        self.thumbnail_cards = []
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # 标题区域
        title = TitleLabel("图片拼接")
        layout.addWidget(title)

        subtitle = CaptionLabel("拖拽图片到下方区域，支持 PNG、JPG、JPEG、BMP、WEBP 格式")
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # 缩略图滚动区域
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
        self.scroll_layout = QHBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(24, 24, 24, 24)
        self.scroll_layout.setSpacing(16)
        self.scroll_layout.setAlignment(Qt.AlignCenter)

        # 空状态提示
        self.setup_empty_state()
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

        # 参数设置卡片
        self.params_card = StitchParamsCard()
        layout.addWidget(self.params_card)

        # 弹性空间
        layout.addStretch(1)

        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 底部操作栏
        self.setup_bottom_bar(layout)

    def setup_empty_state(self):
        """设置空状态提示"""
        from qfluentwidgets import BodyLabel, StrongBodyLabel
        
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

        self.stitch_btn = PrimaryPushButton("开始拼接")
        self.stitch_btn.setMinimumWidth(120)
        self.stitch_btn.clicked.connect(self.start_stitching)
        bottom_layout.addWidget(self.stitch_btn)

        layout.addLayout(bottom_layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        valid_files = []

        for file in files:
            if os.path.isfile(file):
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.webp']:
                    valid_files.append(file)

        if valid_files:
            self.image_files.extend(valid_files)
            self.image_files.sort()
            self.update_thumbnail_list()
            self.status_label.setText(f"已添加 {len(valid_files)} 张，共 {len(self.image_files)} 张")

    def update_thumbnail_list(self):
        """更新缩略图列表"""
        if self.image_files:
            self.empty_widget.setVisible(False)
            self.scroll_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        else:
            self.scroll_layout.setAlignment(Qt.AlignCenter)

        for card in self.thumbnail_cards:
            card.deleteLater()
        self.thumbnail_cards.clear()

        for idx, filepath in enumerate(self.image_files):
            card = ThumbnailCard(filepath, idx, self)
            card.moved.connect(self.move_image)
            card.delete_requested.connect(self.delete_image)
            self.scroll_layout.addWidget(card)
            self.thumbnail_cards.append(card)

    def move_image(self, from_index, to_index):
        """移动图片"""
        if 0 <= from_index < len(self.image_files) and 0 <= to_index < len(self.image_files):
            item = self.image_files.pop(from_index)
            self.image_files.insert(to_index, item)
            self.update_thumbnail_list()
            self.status_label.setText(f"已调整顺序，共 {len(self.image_files)} 张")

    def delete_image(self, index):
        """删除图片"""
        if 0 <= index < len(self.image_files):
            filename = os.path.basename(self.image_files[index])
            w = MessageBox("确认删除", f"确定要删除 '{filename}' 吗？", self)
            if w.exec():
                self.image_files.pop(index)
                self.update_thumbnail_list()
                if not self.image_files:
                    self.empty_widget.setVisible(True)
                    self.scroll_layout.setAlignment(Qt.AlignCenter)
                    self.status_label.setText("就绪")
                else:
                    self.status_label.setText(f"已删除，剩余 {len(self.image_files)} 张")

    def clear_list(self):
        """清空列表"""
        if not self.image_files:
            return
        w = MessageBox("确认清空", "确定要清空所有图片吗？", self)
        if w.exec():
            self.image_files.clear()
            for card in self.thumbnail_cards:
                card.deleteLater()
            self.thumbnail_cards.clear()
            self.empty_widget.setVisible(True)
            self.scroll_layout.setAlignment(Qt.AlignCenter)
            self.status_label.setText("就绪")

    def start_stitching(self):
        """开始拼接"""
        if len(self.image_files) < 2:
            InfoBar.warning(
                title="提示",
                content="请至少添加 2 张图片",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        self.stitch_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        params = self.params_card.get_params()
        
        self.thread = StitchThread(
            self.image_files,
            params['compress_enabled'],
            params['scale'],
            params['output_dir'],
            params['output_name'],
            params['is_horizontal'],
            params['align_mode']
        )
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.status.connect(lambda s: self.status_label.setText(s))
        self.thread.finished.connect(self.on_stitch_finished)
        self.thread.error.connect(self.on_stitch_error)
        self.thread.overwrite_request.connect(self.on_overwrite_request)
        self.thread.start()

    def on_stitch_finished(self, output_path):
        """拼接完成"""
        self.stitch_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("拼接完成")
        InfoBar.success(
            title="完成",
            content=f"已保存至: {output_path}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )

    def on_stitch_error(self, error_msg):
        """拼接错误"""
        self.stitch_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("拼接失败")
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