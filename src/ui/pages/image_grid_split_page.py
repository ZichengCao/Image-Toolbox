#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片等分页面
"""

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, CaptionLabel, PushButton, PrimaryPushButton,
    ProgressBar, InfoBar, InfoBarPosition, MessageBox
)

from ..components.file_list_widget import FileListWidget
from ..components.grid_split_params_card import GridSplitParamsCard
from ...core.image_processor import GridSplitThread


class ImageGridSplitPage(QWidget):
    """图片等分页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        # 创建滚动内容容器
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # 标题区域
        title = TitleLabel("图片等分")
        layout.addWidget(title)

        subtitle = CaptionLabel("选择一张图片，按指定行列数分割成多个图片块")
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # 文件列表组件（只允许单个文件）
        self.file_list = FileListWidget()
        self.file_list.files_changed.connect(self.on_files_changed)
        # 限制只能选择一个文件
        self.file_list.setAcceptDrops(True)
        layout.addWidget(self.file_list)

        # 参数设置卡片
        self.params_card = GridSplitParamsCard()
        layout.addWidget(self.params_card)

        # 弹性空间
        layout.addStretch(1)

        # 设置滚动区域的内容
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 底部操作栏
        self.setup_bottom_bar(main_layout)

    def setup_bottom_bar(self, layout):
        """设置底部操作栏"""
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)
        bottom_layout.setContentsMargins(32, 16, 32, 16)

        self.status_label = CaptionLabel("请选择一张图片")
        self.status_label.setStyleSheet("color: #666;")
        bottom_layout.addWidget(self.status_label, 1)

        self.clear_btn = PushButton("清空")
        self.clear_btn.setMinimumWidth(80)
        self.clear_btn.clicked.connect(self.clear_list)
        bottom_layout.addWidget(self.clear_btn)

        self.split_btn = PrimaryPushButton("开始等分")
        self.split_btn.setMinimumWidth(120)
        self.split_btn.clicked.connect(self.start_split)
        self.split_btn.setEnabled(False)
        bottom_layout.addWidget(self.split_btn)

        layout.addLayout(bottom_layout)

    def on_files_changed(self, files):
        """文件列表变化时的处理"""
        if len(files) > 1:
            # 如果选择了多个文件，只保留第一个
            self.file_list.set_files([files[0]])
            InfoBar.warning(
                title="提示",
                content="图片等分只支持单个文件，已自动选择第一个文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        if files:
            filename = os.path.basename(files[0])
            self.status_label.setText(f"已选择: {filename}")
            self.split_btn.setEnabled(True)
        else:
            self.status_label.setText("请选择一张图片")
            self.split_btn.setEnabled(False)

    def clear_list(self):
        """清空列表"""
        if not self.file_list.get_files():
            return
        w = MessageBox("确认清空", "确定要清空图片吗？", self)
        if w.exec():
            self.file_list.clear_files()
            self.status_label.setText("请选择一张图片")
            self.split_btn.setEnabled(False)

    def start_split(self):
        """开始等分"""
        image_files = self.file_list.get_files()
        if not image_files:
            InfoBar.warning(
                title="提示",
                content="请先选择一张图片",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        if len(image_files) > 1:
            InfoBar.warning(
                title="提示",
                content="图片等分只支持单个文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        params = self.params_card.get_params()
        output_dir = params['output_dir'] or os.path.dirname(image_files[0])

        # 检查分割参数
        if params['x_splits'] == 1 and params['y_splits'] == 1:
            InfoBar.warning(
                title="提示",
                content="分割参数无效，宽度和高度等分数不能都为1",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        self.split_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.thread = GridSplitThread(
            image_files[0],
            output_dir,
            params['x_splits'],
            params['y_splits'],
            params['quality'],
            params['output_format']
        )
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.status.connect(lambda s: self.status_label.setText(s))
        self.thread.finished.connect(self.on_split_finished)
        self.thread.error.connect(self.on_split_error)
        self.thread.overwrite_request.connect(self.on_overwrite_request)
        self.thread.start()

    def on_split_finished(self, results):
        """等分完成"""
        self.split_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        filename = os.path.basename(self.file_list.get_files()[0])
        output_folder = os.path.basename(results[0]['output_folder']) if results else ""
        self.status_label.setText(f"完成等分: {filename}")
        
        InfoBar.success(
            title="完成",
            content=f"已将图片分割为 {len(results)} 个图片块，保存在文件夹: {output_folder}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )

    def on_split_error(self, error_msg):
        """等分错误"""
        self.split_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("等分失败")
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