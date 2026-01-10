#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片等分参数设置卡片
"""

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt
from qfluentwidgets import (
    CardWidget, TitleLabel, CaptionLabel, SpinBox, ComboBox,
    PushButton, LineEdit, Slider, InfoBar, InfoBarPosition, StrongBodyLabel, BodyLabel
)


class GridSplitParamsCard(CardWidget):
    """图片等分参数设置卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # 第一行：等分设置
        row1 = QHBoxLayout()
        row1.setSpacing(32)

        # 宽度等分
        x_group = QHBoxLayout()
        x_group.setSpacing(12)
        x_label = BodyLabel("宽度等分")
        x_label.setStyleSheet("color: #666;")
        x_group.addWidget(x_label)
        self.x_splits_spin = SpinBox()
        self.x_splits_spin.setRange(1, 20)
        self.x_splits_spin.setValue(2)
        self.x_splits_spin.setMinimumWidth(150)
        x_group.addWidget(self.x_splits_spin)
        row1.addLayout(x_group)

        # 高度等分
        y_group = QHBoxLayout()
        y_group.setSpacing(12)
        y_label = BodyLabel("高度等分")
        y_label.setStyleSheet("color: #666;")
        y_group.addWidget(y_label)
        self.y_splits_spin = SpinBox()
        self.y_splits_spin.setRange(1, 20)
        self.y_splits_spin.setValue(2)
        self.y_splits_spin.setMinimumWidth(150)
        y_group.addWidget(self.y_splits_spin)
        row1.addLayout(y_group)

        row1.addStretch()
        layout.addLayout(row1)

        # 第二行：预览信息
        self.preview_label = BodyLabel("将等分为 4 个图片块（2行 × 2列）")
        self.preview_label.setStyleSheet("""
            BodyLabel {
                color: #0078D4;
                font-weight: 600;
                padding: 8px 12px;
                background-color: #E3F2FD;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.preview_label)

        # 第三行：输出格式
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        format_label = BodyLabel("输出格式")
        format_label.setStyleSheet("color: #666;")
        format_label.setMinimumWidth(70)
        row3.addWidget(format_label)

        self.format_combo = ComboBox()
        self.format_combo.addItems(["保持原格式", "JPEG", "PNG", "WEBP"])
        self.format_combo.setMinimumWidth(150)
        row3.addWidget(self.format_combo)
        row3.addStretch(1)

        layout.addLayout(row3)

        # 第四行：输出质量
        row4 = QHBoxLayout()
        row4.setSpacing(12)

        quality_label = BodyLabel("输出质量")
        quality_label.setStyleSheet("color: #666;")
        quality_label.setMinimumWidth(70)
        row4.addWidget(quality_label)

        quality_input_layout = QHBoxLayout()
        quality_input_layout.setSpacing(12)

        self.quality_slider = Slider(Qt.Horizontal)
        self.quality_slider.setRange(10, 100)
        self.quality_slider.setValue(95)
        self.quality_slider.setMinimumWidth(250)
        quality_input_layout.addWidget(self.quality_slider)

        self.quality_value_label = StrongBodyLabel("95")
        self.quality_value_label.setStyleSheet("""
            StrongBodyLabel {
                color: #0078D4;
                font-size: 16px;
                font-weight: 600;
                min-width: 40px;
            }
        """)
        self.quality_slider.valueChanged.connect(
            lambda v: self.quality_value_label.setText(str(v))
        )
        quality_input_layout.addWidget(self.quality_value_label)
        quality_input_layout.addStretch(1)

        row4.addLayout(quality_input_layout)
        layout.addLayout(row4)

        # 第五行：输出目录
        row5 = QHBoxLayout()
        row5.setSpacing(12)

        dir_label = BodyLabel("输出目录")
        dir_label.setStyleSheet("color: #666;")
        dir_label.setMinimumWidth(70)
        row5.addWidget(dir_label)

        self.output_dir_edit = LineEdit()
        self.output_dir_edit.setPlaceholderText("留空则保存到原图片目录")
        row5.addWidget(self.output_dir_edit, 1)

        self.browse_btn = PushButton("浏览")
        self.browse_btn.setMinimumWidth(80)
        self.browse_btn.clicked.connect(self.browse_output_dir)
        row5.addWidget(self.browse_btn)

        layout.addLayout(row5)

        # 添加说明
        note_label = BodyLabel("注意：等分后的图片将保存在一个新建的子文件夹中")
        note_label.setStyleSheet("""
            BodyLabel {
                color: #999;
                font-style: italic;
            }
        """)
        layout.addWidget(note_label)

        # 连接信号
        self.x_splits_spin.valueChanged.connect(self.update_preview)
        self.y_splits_spin.valueChanged.connect(self.update_preview)

    def update_preview(self):
        """更新预览信息"""
        x_splits = self.x_splits_spin.value()
        y_splits = self.y_splits_spin.value()
        total = x_splits * y_splits
        self.preview_label.setText(f"将等分为 {total} 个图片块（{y_splits}行 × {x_splits}列）")

    def browse_output_dir(self):
        """浏览输出目录"""
        from PySide6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def get_params(self):
        """获取参数"""
        output_format = self.format_combo.currentText()
        if output_format == "保持原格式":
            output_format = None

        return {
            'x_splits': self.x_splits_spin.value(),
            'y_splits': self.y_splits_spin.value(),
            'quality': self.quality_slider.value(),
            'output_format': output_format,
            'output_dir': self.output_dir_edit.text().strip() or None
        }