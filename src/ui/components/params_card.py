#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数配置卡片组件
"""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFileDialog, QWidget
from PySide6.QtCore import Signal, Qt
from qfluentwidgets import (
    CardWidget, BodyLabel, RadioButton, ComboBox, SwitchButton,
    SpinBox, LineEdit, PushButton, Slider, StrongBodyLabel
)


class StitchParamsCard(CardWidget):
    """拼接参数配置卡片"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_dir = ""
        self.setStyleSheet("CardWidget { border-radius: 8px; }")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # 第一行：拼接方向
        row1 = QHBoxLayout()
        row1.setSpacing(32)

        # 拼接方向
        dir_group = QHBoxLayout()
        dir_group.setSpacing(12)
        dir_label = BodyLabel("拼接方向")
        dir_label.setStyleSheet("color: #666;")
        dir_group.addWidget(dir_label)
        self.horizontal_radio = RadioButton("水平")
        self.horizontal_radio.setChecked(True)
        dir_group.addWidget(self.horizontal_radio)
        self.vertical_radio = RadioButton("垂直")
        dir_group.addWidget(self.vertical_radio)
        row1.addLayout(dir_group)

        # 对齐方式
        align_group = QHBoxLayout()
        align_group.setSpacing(12)
        align_label = BodyLabel("对齐方式")
        align_label.setStyleSheet("color: #666;")
        align_group.addWidget(align_label)
        self.align_combo = ComboBox()
        self.align_combo.setMinimumWidth(180)
        self.align_combo.addItems(["居中对齐", "顶部对齐", "底部对齐", "等比例放大", "等比例缩小"])
        align_group.addWidget(self.align_combo)
        row1.addLayout(align_group)

        self.horizontal_radio.toggled.connect(self.update_align_options)
        self.vertical_radio.toggled.connect(self.update_align_options)

        row1.addStretch()
        layout.addLayout(row1)

        # 第二行：缩放选项
        row2 = QHBoxLayout()
        row2.setSpacing(32)

        compress_group = QHBoxLayout()
        compress_group.setSpacing(12)
        compress_label = BodyLabel("启用缩放")
        compress_label.setStyleSheet("color: #666;")
        compress_group.addWidget(compress_label)
        self.compress_switch = SwitchButton()
        self.compress_switch.checkedChanged.connect(self.toggle_compress)
        compress_group.addWidget(self.compress_switch)
        row2.addLayout(compress_group)

        scale_group = QHBoxLayout()
        scale_group.setSpacing(12)
        scale_label = BodyLabel("缩放比例")
        scale_label.setStyleSheet("color: #666;")
        scale_group.addWidget(scale_label)
        self.scale_spin = SpinBox()
        self.scale_spin.setRange(1, 100)
        self.scale_spin.setValue(100)
        self.scale_spin.setSuffix("%")
        self.scale_spin.setMinimumWidth(150)
        self.scale_spin.setEnabled(False)
        scale_group.addWidget(self.scale_spin)
        row2.addLayout(scale_group)

        row2.addStretch()
        layout.addLayout(row2)

        # 第三行：输出目录
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        dir_label = BodyLabel("输出目录")
        dir_label.setStyleSheet("color: #666;")
        dir_label.setMinimumWidth(70)
        row3.addWidget(dir_label)

        self.dir_edit = LineEdit()
        self.dir_edit.setPlaceholderText("留空则保存到首张图片所在目录")
        row3.addWidget(self.dir_edit, 1)

        self.dir_btn = PushButton("浏览")
        self.dir_btn.setMinimumWidth(80)
        self.dir_btn.clicked.connect(self.select_output_dir)
        row3.addWidget(self.dir_btn)

        layout.addLayout(row3)

        # 第四行：文件名
        row4 = QHBoxLayout()
        row4.setSpacing(12)

        name_label = BodyLabel("文件名")
        name_label.setStyleSheet("color: #666;")
        name_label.setMinimumWidth(70)
        row4.addWidget(name_label)

        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("留空则自动生成")
        row4.addWidget(self.name_edit, 1)

        # 占位，保持对齐
        spacer = QWidget()
        spacer.setMinimumWidth(80)
        row4.addWidget(spacer)

        layout.addLayout(row4)

    def toggle_compress(self, checked):
        self.scale_spin.setEnabled(checked)

    def update_align_options(self):
        current_text = self.align_combo.currentText()
        self.align_combo.clear()
        
        if self.horizontal_radio.isChecked():
            options = ["居中对齐", "顶部对齐", "底部对齐", "等比例放大", "等比例缩小"]
        else:
            options = ["居中对齐", "左侧对齐", "右侧对齐", "等比例放大", "等比例缩小"]
        
        self.align_combo.addItems(options)
        if current_text in options:
            self.align_combo.setCurrentText(current_text)

    def select_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir = directory
            self.dir_edit.setText(directory)

    def get_params(self):
        """获取参数配置"""
        # 映射对齐选项
        align_map = {
            "等比例放大": "等比例放大到同一尺寸",
            "等比例缩小": "等比例缩小到同一尺寸"
        }
        align_mode = align_map.get(self.align_combo.currentText(), self.align_combo.currentText())
        
        return {
            'compress_enabled': self.compress_switch.isChecked(),
            'scale': self.scale_spin.value(),
            'output_dir': self.output_dir,
            'output_name': self.name_edit.text(),
            'is_horizontal': self.horizontal_radio.isChecked(),
            'align_mode': align_mode
        }


class CompressParamsCard(CardWidget):
    """压缩参数配置卡片"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_dir = ""
        self.setStyleSheet("CardWidget { border-radius: 8px; }")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # 第一行：缩放和格式
        row1 = QHBoxLayout()
        row1.setSpacing(32)

        # 缩放比例
        scale_group = QHBoxLayout()
        scale_group.setSpacing(12)
        scale_label = BodyLabel("缩放比例")
        scale_label.setStyleSheet("color: #666;")
        scale_group.addWidget(scale_label)
        self.scale_spin = SpinBox()
        self.scale_spin.setRange(1, 100)
        self.scale_spin.setValue(100)
        self.scale_spin.setSuffix("%")
        self.scale_spin.setMinimumWidth(150)
        scale_group.addWidget(self.scale_spin)
        row1.addLayout(scale_group)

        # 输出格式
        format_group = QHBoxLayout()
        format_group.setSpacing(12)
        format_label = BodyLabel("输出格式")
        format_label.setStyleSheet("color: #666;")
        format_group.addWidget(format_label)
        self.format_combo = ComboBox()
        self.format_combo.addItems(["保持原格式", "JPEG", "PNG", "WEBP"])
        self.format_combo.setMinimumWidth(150)
        format_group.addWidget(self.format_combo)
        row1.addLayout(format_group)

        row1.addStretch()
        layout.addLayout(row1)

        # 第二行：输出质量
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        quality_label = BodyLabel("输出质量")
        quality_label.setStyleSheet("color: #666;")
        quality_label.setMinimumWidth(70)
        row2.addWidget(quality_label)

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

        row2.addLayout(quality_input_layout)
        layout.addLayout(row2)

        # 第三行：输出目录
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        dir_label = BodyLabel("输出目录")
        dir_label.setStyleSheet("color: #666;")
        dir_label.setMinimumWidth(70)
        row3.addWidget(dir_label)

        self.dir_edit = LineEdit()
        self.dir_edit.setPlaceholderText("留空则保存到原图片目录")
        row3.addWidget(self.dir_edit, 1)

        self.dir_btn = PushButton("浏览")
        self.dir_btn.setMinimumWidth(80)
        self.dir_btn.clicked.connect(self.select_output_dir)
        row3.addWidget(self.dir_btn)

        layout.addLayout(row3)

    def select_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir = directory
            self.dir_edit.setText(directory)

    def get_params(self):
        """获取参数配置"""
        format_text = self.format_combo.currentText()
        output_format = None if format_text == "保持原格式" else format_text

        return {
            'scale': self.scale_spin.value(),
            'quality': self.quality_slider.value(),
            'output_format': output_format,
            'output_dir': self.output_dir
        }


class ResizeParamsCard(CardWidget):
    """尺寸统一参数配置卡片"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_dir = ""
        self.setStyleSheet("CardWidget { border-radius: 8px; }")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # 第一行：目标尺寸选择
        row1 = QHBoxLayout()
        row1.setSpacing(32)

        # 尺寸模式
        mode_group = QHBoxLayout()
        mode_group.setSpacing(12)
        mode_label = BodyLabel("目标尺寸")
        mode_label.setStyleSheet("color: #666;")
        mode_group.addWidget(mode_label)

        self.max_radio = RadioButton("最大尺寸")
        self.max_radio.setChecked(True)
        mode_group.addWidget(self.max_radio)

        self.min_radio = RadioButton("最小尺寸")
        mode_group.addWidget(self.min_radio)

        row1.addLayout(mode_group)
        row1.addStretch()
        layout.addLayout(row1)

        # 第二行：输出格式
        row2 = QHBoxLayout()
        row2.setSpacing(32)

        # 输出格式
        format_group = QHBoxLayout()
        format_group.setSpacing(12)
        format_label = BodyLabel("输出格式")
        format_label.setStyleSheet("color: #666;")
        format_group.addWidget(format_label)
        self.format_combo = ComboBox()
        self.format_combo.addItems(["保持原格式", "JPEG", "PNG", "WEBP"])
        self.format_combo.setMinimumWidth(150)
        format_group.addWidget(self.format_combo)
        row2.addLayout(format_group)

        row2.addStretch()
        layout.addLayout(row2)

        # 第三行：输出质量
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        quality_label = BodyLabel("输出质量")
        quality_label.setStyleSheet("color: #666;")
        quality_label.setMinimumWidth(70)
        row3.addWidget(quality_label)

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

        row3.addLayout(quality_input_layout)
        layout.addLayout(row3)

        # 第四行：输出目录
        row4 = QHBoxLayout()
        row4.setSpacing(12)

        dir_label = BodyLabel("输出目录")
        dir_label.setStyleSheet("color: #666;")
        dir_label.setMinimumWidth(70)
        row4.addWidget(dir_label)

        self.dir_edit = LineEdit()
        self.dir_edit.setPlaceholderText("留空则保存到原图片目录")
        row4.addWidget(self.dir_edit, 1)

        self.dir_btn = PushButton("浏览")
        self.dir_btn.setMinimumWidth(80)
        self.dir_btn.clicked.connect(self.select_output_dir)
        row4.addWidget(self.dir_btn)

        layout.addLayout(row4)

    def select_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir = directory
            self.dir_edit.setText(directory)

    def get_params(self):
        """获取参数配置"""
        format_text = self.format_combo.currentText()
        output_format = None if format_text == "保持原格式" else format_text
        resize_mode = "max" if self.max_radio.isChecked() else "min"

        return {
            'resize_mode': resize_mode,
            'quality': self.quality_slider.value(),
            'output_format': output_format,
            'output_dir': self.output_dir
        }


class GeminiWatermarkParamsCard(CardWidget):
    """Gemini 水印移除参数配置卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_dir = ""
        self.setStyleSheet("CardWidget { border-radius: 8px; }")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # 第一行：说明文字
        row1 = QHBoxLayout()
        info_label = BodyLabel("自动移除 Gemini AI 生成图片右下角的水印")
        info_label.setStyleSheet("color: #666;")
        row1.addWidget(info_label)
        row1.addStretch()
        layout.addLayout(row1)

        # 第二行：输出格式
        row2 = QHBoxLayout()
        row2.setSpacing(32)

        format_group = QHBoxLayout()
        format_group.setSpacing(12)
        format_label = BodyLabel("输出格式")
        format_label.setStyleSheet("color: #666;")
        format_group.addWidget(format_label)
        self.format_combo = ComboBox()
        self.format_combo.addItems(["保持原格式", "JPEG", "PNG", "WEBP"])
        self.format_combo.setMinimumWidth(150)
        format_group.addWidget(self.format_combo)
        row2.addLayout(format_group)

        row2.addStretch()
        layout.addLayout(row2)

        # 第三行：质量控制
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        quality_label = BodyLabel("输出质量")
        quality_label.setStyleSheet("color: #666;")
        quality_label.setMinimumWidth(70)
        row3.addWidget(quality_label)

        quality_input_layout = QHBoxLayout()
        quality_input_layout.setSpacing(12)

        self.quality_slider = Slider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
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

        row3.addLayout(quality_input_layout)
        layout.addLayout(row3)

        # 第四行：输出目录
        row4 = QHBoxLayout()
        row4.setSpacing(12)

        dir_label = BodyLabel("输出目录")
        dir_label.setStyleSheet("color: #666;")
        dir_label.setMinimumWidth(70)
        row4.addWidget(dir_label)

        self.dir_edit = LineEdit()
        self.dir_edit.setPlaceholderText("留空则保存到原图片目录")
        row4.addWidget(self.dir_edit, 1)

        self.dir_btn = PushButton("浏览")
        self.dir_btn.setMinimumWidth(80)
        self.dir_btn.clicked.connect(self.select_output_dir)
        row4.addWidget(self.dir_btn)

        layout.addLayout(row4)

    def select_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir = directory
            self.dir_edit.setText(directory)

    def get_params(self):
        """获取参数配置"""
        format_text = self.format_combo.currentText()
        output_format = None if format_text == "保持原格式" else format_text

        return {
            'output_format': output_format,
            'quality': self.quality_slider.value(),
            'output_dir': self.output_dir
        }