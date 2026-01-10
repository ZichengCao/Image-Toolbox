#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尺寸统一页面
"""

import os
from PIL import Image
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, CaptionLabel, PushButton, PrimaryPushButton,
    ProgressBar, InfoBar, InfoBarPosition, MessageBox
)

from ..components.file_list_widget import FileListWidget
from ..components.params_card import ResizeParamsCard
from ...core.image_processor import ResizeThread


class ImageResizePage(QWidget):
    """尺寸统一页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # 标题区域
        title = TitleLabel("尺寸统一")
        layout.addWidget(title)

        subtitle = CaptionLabel("将多张不同尺寸的图片统一调整为相同分辨率")
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # 文件列表组件
        self.file_list = FileListWidget()
        self.file_list.files_changed.connect(self.on_files_changed)
        layout.addWidget(self.file_list)

        # 参数设置卡片
        self.params_card = ResizeParamsCard()
        self.params_card.max_radio.toggled.connect(self.update_size_info)
        self.params_card.min_radio.toggled.connect(self.update_size_info)
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

        self.resize_btn = PrimaryPushButton("开始处理")
        self.resize_btn.setMinimumWidth(120)
        self.resize_btn.clicked.connect(self.start_resize)
        bottom_layout.addWidget(self.resize_btn)

        layout.addLayout(bottom_layout)

    def on_files_changed(self, files):
        """文件列表变化时的处理"""
        # 更新文件列表显示，显示图片尺寸
        self.file_list.update_file_list(show_size=True)
        self.update_size_info()

    def update_size_info(self):
        """更新尺寸信息显示"""
        image_files = self.file_list.get_files()
        if not image_files:
            self.status_label.setText("就绪")
            return

        try:
            sizes = []
            for filepath in image_files:
                with Image.open(filepath) as img:
                    sizes.append((img.width, img.height))
            
            if self.params_card.max_radio.isChecked():
                target_w = max(w for w, h in sizes)
                target_h = max(h for w, h in sizes)
                mode_text = "最大"
            else:
                target_w = min(w for w, h in sizes)
                target_h = min(h for w, h in sizes)
                mode_text = "最小"
            
            self.status_label.setText(f"共 {len(image_files)} 张，目标尺寸：{target_w}×{target_h} ({mode_text})")
        except Exception as e:
            self.status_label.setText(f"共 {len(image_files)} 张")

    def clear_list(self):
        """清空列表"""
        if not self.file_list.get_files():
            return
        w = MessageBox("确认清空", "确定要清空所有图片吗？", self)
        if w.exec():
            self.file_list.clear_files()
            self.status_label.setText("就绪")

    def start_resize(self):
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

        self.resize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.thread = ResizeThread(
            image_files,
            output_dir,
            params['resize_mode'],
            params['quality'],
            params['output_format']
        )
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.status.connect(lambda s: self.status_label.setText(s))
        self.thread.finished.connect(self.on_resize_finished)
        self.thread.error.connect(self.on_resize_error)
        self.thread.overwrite_request.connect(self.on_overwrite_request)
        self.thread.start()

    def on_resize_finished(self, results):
        """处理完成"""
        self.resize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("处理完成")
        
        # 显示结果信息
        if results:
            target_size = results[0]['new_size']
            InfoBar.success(
                title="完成",
                content=f"已处理 {len(results)} 张图片\n统一尺寸为：{target_size}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def on_resize_error(self, error_msg):
        """处理错误"""
        self.resize_btn.setEnabled(True)
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