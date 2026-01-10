#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缩略图卡片组件
"""

import os
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QApplication
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QPixmap, QDrag
from qfluentwidgets import SimpleCardWidget, BodyLabel, CaptionLabel, TransparentToolButton, FluentIcon


class ThumbnailCard(SimpleCardWidget):
    """缩略图卡片"""
    moved = Signal(int, int)  # from_index, to_index
    delete_requested = Signal(int)  # 删除请求信号

    def __init__(self, filepath, index, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.index = index
        self.drag_start_pos = None
        self.parent_widget = parent

        self.setFixedSize(160, 200)
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 图片预览
        try:
            # 使用简单的方式加载图片
            pixmap = QPixmap(self.filepath)
            pixmap = pixmap.scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            img_label = QLabel()
            img_label.setPixmap(pixmap)
            img_label.setAlignment(Qt.AlignCenter)
            img_label.setFixedSize(130, 130)
            layout.addWidget(img_label, 0, Qt.AlignCenter)

        except Exception as e:
            error_label = BodyLabel("❌ 加载失败")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)

        # 文件名
        filename = os.path.basename(self.filepath)
        if len(filename) > 20:
            filename = filename[:17] + "..."
        name_label = CaptionLabel(filename)
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        # 序号和删除按钮布局
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        index_label = CaptionLabel(f"#{self.index + 1}")
        index_label.setAlignment(Qt.AlignLeft)
        index_label.setStyleSheet("color: gray;")
        bottom_layout.addWidget(index_label)
        
        bottom_layout.addStretch()
        
        # 删除按钮
        delete_btn = TransparentToolButton(FluentIcon.DELETE)
        delete_btn.setFixedSize(16, 16)
        delete_btn.setToolTip("删除此图片")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.index))
        bottom_layout.addWidget(delete_btn)
        
        layout.addLayout(bottom_layout)

    def update_index(self, new_index):
        """更新序号显示"""
        self.index = new_index
        # 找到序号标签并更新
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and hasattr(item, 'layout') and item.layout():
                for j in range(item.layout().count()):
                    widget = item.layout().itemAt(j).widget()
                    if isinstance(widget, CaptionLabel) and widget.text().startswith('#'):
                        widget.setText(f"#{new_index + 1}")
                        return

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if self.drag_start_pos is None:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return

        # 开始拖拽
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.index))
        drag.setMimeData(mime_data)
        
        # 设置拖拽时的预览图
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(80, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        drop_action = drag.exec(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            from_index = int(event.mimeData().text())
            to_index = self.index
            if from_index != to_index:
                self.moved.emit(from_index, to_index)
            event.acceptProposedAction()

    def mouseReleaseEvent(self, event):
        self.drag_start_pos = None
        super().mouseReleaseEvent(event)