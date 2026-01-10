#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini 水印移除页面
"""

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, CaptionLabel, PushButton, PrimaryPushButton,
    ProgressBar, InfoBar, InfoBarPosition, MessageBox
)

from ..components.file_list_widget import FileListWidget
from ..components.params_card import GeminiWatermarkParamsCard
from ...core.gemini_watermark_remover import GeminiWatermarkThread


class ImageGeminiWatermarkPage(QWidget):
    """Gemini 水印移除页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # 标题区域
        title = TitleLabel("Gemini 水印移除")
        layout.addWidget(title)

        subtitle = CaptionLabel("自动移除 Gemini AI 生成图片右下角的水印，支持批量处理")
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # 文件列表组件
        self.file_list = FileListWidget()
        self.file_list.files_changed.connect(self.on_files_changed)
        layout.addWidget(self.file_list)

        # 参数设置卡片
        self.params_card = GeminiWatermarkParamsCard()
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

        self.process_btn = PrimaryPushButton("开始处理")
        self.process_btn.setMinimumWidth(120)
        self.process_btn.clicked.connect(self.start_processing)
        bottom_layout.addWidget(self.process_btn)

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

    def start_processing(self):
        """开始处理"""
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

        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.thread = GeminiWatermarkThread(
            image_files,
            output_dir,
            params['output_format'],
            params['quality']
        )
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.status.connect(lambda s: self.status_label.setText(s))
        self.thread.finished.connect(self.on_processing_finished)
        self.thread.error.connect(self.on_processing_error)
        self.thread.overwrite_request.connect(self.on_overwrite_request)
        self.thread.start()

    def on_processing_finished(self, results):
        """处理完成"""
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        # 检查是否有错误
        error_info = None
        success_count = 0

        for result in results:
            if 'errors' in result:
                error_info = result
            elif 'input' in result:
                success_count += 1

        # 显示结果
        if error_info:
            failed_count = len(error_info['errors'])
            self.status_label.setText(f"完成 {success_count} 个，失败 {failed_count} 个")

            if success_count > 0:
                InfoBar.success(
                    title="部分完成",
                    content=f"成功处理 {success_count} 张图片，{failed_count} 张失败\n{error_info['error_summary']}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=8000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="处理失败",
                    content=f"所有图片都无法处理:\n{error_info['error_summary']}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=8000,
                    parent=self
                )
        else:
            self.status_label.setText(f"完成，已处理 {success_count} 张图片")
            InfoBar.success(
                title="完成",
                content=f"已成功移除 {success_count} 张图片的水印",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def on_processing_error(self, error_msg):
        """处理错误"""
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("处理失败")
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
