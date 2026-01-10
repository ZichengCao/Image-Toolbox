#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片分割页面 - 支持交互式选择和自定义分割区域
"""

import os
from typing import List, Tuple, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem, QScrollArea, QFrame
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainter, QBrush, QPixmap, QImage, QPolygonF
from qfluentwidgets import (
    TitleLabel, CaptionLabel, PushButton, PrimaryPushButton,
    ProgressBar, InfoBar, InfoBarPosition, MessageBox, ComboBox,
    CardWidget, StrongBodyLabel, FluentIcon, IconWidget, Slider, BodyLabel, LineEdit
)

from ..components.file_list_widget import FileListWidget
from ...core.image_processor import CropSplitThread


class ImageCropPage(QWidget):
    """图片分割页面 - 支持交互式选择和自定义分割区域"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_file: Optional[str] = None
        self.crop_regions: List[Tuple[float, float, float, float]] = []
        self.current_mode = "rectangle"
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
        layout.setSpacing(24)

        # 标题区域
        title = TitleLabel("图片分割")
        layout.addWidget(title)

        subtitle = CaptionLabel("通过交互方式在图片上绘制分割区域，支持矩形、圆形和多边形")
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # 文件列表组件（只允许单个文件）
        self.file_list = FileListWidget()
        self.file_list.files_changed.connect(self.on_files_changed)
        self.file_list.setAcceptDrops(True)
        layout.addWidget(self.file_list)

        # 图片预览和工具栏
        self.setup_preview_section(layout)

        # 参数设置区域
        self.setup_params_section(layout)

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

    def setup_preview_section(self, layout):
        """设置图片预览区域"""
        preview_card = CardWidget()
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        preview_layout.setSpacing(16)

        # 卡片标题
        header = QHBoxLayout()
        icon = IconWidget(FluentIcon.PALETTE)
        icon.setFixedSize(22, 22)
        header.addWidget(icon)

        title = StrongBodyLabel("图片预览")
        title.setStyleSheet("font-size: 15px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch(1)
        preview_layout.addLayout(header)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #e0e0e0;")
        preview_layout.addWidget(line)

        # 图形视图
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setMinimumHeight(350)
        self.view.setMaximumHeight(500)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setStyleSheet("""
            QGraphicsView {
                background-color: #fafafa;
                border: 2px dashed #d0d0d0;
                border-radius: 12px;
            }
        """)
        preview_layout.addWidget(self.view)

        # 工具栏
        tools_layout = QHBoxLayout()
        tools_layout.setSpacing(12)

        mode_label = CaptionLabel("添加分割区域：")
        mode_label.setStyleSheet("color: #666;")
        tools_layout.addWidget(mode_label)

        self.add_rect_btn = PushButton("矩形")
        self.add_rect_btn.setIcon(FluentIcon.TAG)
        self.add_rect_btn.clicked.connect(self.add_rectangle_region)
        tools_layout.addWidget(self.add_rect_btn)

        self.add_circle_btn = PushButton("圆形")
        self.add_circle_btn.setIcon(FluentIcon.TAG)
        self.add_circle_btn.clicked.connect(self.add_circle_region)
        tools_layout.addWidget(self.add_circle_btn)

        self.add_polygon_btn = PushButton("多边形")
        self.add_polygon_btn.setIcon(FluentIcon.FLAG)
        self.add_polygon_btn.clicked.connect(self.add_polygon_region)
        tools_layout.addWidget(self.add_polygon_btn)

        tools_layout.addSpacing(20)

        self.clear_regions_btn = PushButton("清空区域")
        self.clear_regions_btn.setIcon(FluentIcon.DELETE)
        self.clear_regions_btn.clicked.connect(self.clear_regions)
        tools_layout.addWidget(self.clear_regions_btn)

        tools_layout.addStretch(1)
        preview_layout.addLayout(tools_layout)

        # 提示信息
        hint_label = CaptionLabel("提示：点击按钮添加形状，在预览区域拖拽移动位置，选中后按 Delete 键删除")
        hint_label.setStyleSheet("color: #999; font-style: italic;")
        preview_layout.addWidget(hint_label)

        layout.addWidget(preview_card)

    def setup_params_section(self, layout):
        """设置参数区域"""
        params_card = CardWidget()
        params_layout = QVBoxLayout(params_card)
        params_layout.setContentsMargins(24, 20, 24, 20)
        params_layout.setSpacing(20)

        # 第一行：输出格式
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        format_label = BodyLabel("输出格式")
        format_label.setStyleSheet("color: #666;")
        format_label.setMinimumWidth(70)
        row1.addWidget(format_label)

        self.format_combo = ComboBox()
        self.format_combo.addItems(["保持原格式", "JPEG", "PNG", "WEBP"])
        self.format_combo.setMinimumWidth(150)
        row1.addWidget(self.format_combo)
        row1.addStretch(1)

        params_layout.addLayout(row1)

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
        params_layout.addLayout(row2)

        # 第三行：输出目录
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        dir_label = BodyLabel("输出目录")
        dir_label.setStyleSheet("color: #666;")
        dir_label.setMinimumWidth(70)
        row3.addWidget(dir_label)

        self.output_dir_edit = LineEdit()
        self.output_dir_edit.setPlaceholderText("留空则保存到原图片目录")
        row3.addWidget(self.output_dir_edit, 1)

        self.browse_btn = PushButton("浏览")
        self.browse_btn.setIcon(FluentIcon.FOLDER)
        self.browse_btn.setMinimumWidth(80)
        self.browse_btn.clicked.connect(self.browse_output_dir)
        row3.addWidget(self.browse_btn)

        params_layout.addLayout(row3)

        layout.addWidget(params_card)

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

        self.crop_btn = PrimaryPushButton("开始分割")
        self.crop_btn.setMinimumWidth(120)
        self.crop_btn.clicked.connect(self.start_crop)
        self.crop_btn.setEnabled(False)
        bottom_layout.addWidget(self.crop_btn)

        layout.addLayout(bottom_layout)

    def on_files_changed(self, files):
        """文件列表变化时的处理"""
        if len(files) > 1:
            self.file_list.set_files([files[0]])
            InfoBar.warning(
                title="提示",
                content="图片分割只支持单个文件，已自动选择第一个文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        if files:
            filename = os.path.basename(files[0])
            self.image_file = files[0]
            self.status_label.setText(f"已选择: {filename}")
            self.crop_btn.setEnabled(True)
            self.load_image(files[0])
        else:
            self.image_file = None
            self.status_label.setText("请选择一张图片")
            self.crop_btn.setEnabled(False)
            self.scene.clear()

    def load_image(self, filepath: str):
        """加载图片到预览区域"""
        try:
            pixmap = QPixmap(filepath)
            self.scene.clear()
            self.pixmap_item = self.scene.addPixmap(pixmap)
            self.scene.setSceneRect(pixmap.rect())

            # 调整视图大小以适应图片
            self.view.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

            # 添加提示文本
            if not self.scene.items():
                from qfluentwidgets import TextWidget
                hint = self.scene.addText("请添加分割区域")
                hint.setDefaultTextColor(QColor("#999"))

        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"无法加载图片: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def add_rectangle_region(self):
        """添加矩形分割区域"""
        if not self.image_file:
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

        # 获取图片尺寸
        if hasattr(self, 'pixmap_item'):
            rect = self.pixmap_item.boundingRect()
            x, y = rect.width() / 4, rect.height() / 4
            w, h = rect.width() / 2, rect.height() / 2
        else:
            x, y, w, h = 50, 50, 100, 80

        # 创建矩形区域
        rect_item = QGraphicsRectItem(x, y, w, h)
        rect_item.setPen(QPen(QColor("#0078D4"), 2, Qt.PenStyle.SolidLine))
        rect_item.setBrush(QBrush(QColor(0, 120, 212, 30)))
        rect_item.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        rect_item.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        rect_item.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self.scene.addItem(rect_item)
        self.current_mode = "rectangle"

        InfoBar.success(
            title="已添加",
            content="矩形分割区域已添加，拖拽可移动位置",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def add_circle_region(self):
        """添加圆形分割区域"""
        if not self.image_file:
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

        # 获取图片尺寸
        if hasattr(self, 'pixmap_item'):
            rect = self.pixmap_item.boundingRect()
            x, y = rect.width() / 4, rect.height() / 4
            w, h = rect.width() / 2, rect.height() / 2
        else:
            x, y, w, h = 50, 50, 100, 80

        # 创建圆形区域
        ellipse_item = QGraphicsEllipseItem(x, y, w, h)
        ellipse_item.setPen(QPen(QColor("#0078D4"), 2, Qt.PenStyle.SolidLine))
        ellipse_item.setBrush(QBrush(QColor(0, 120, 212, 30)))
        ellipse_item.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
        ellipse_item.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        ellipse_item.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self.scene.addItem(ellipse_item)
        self.current_mode = "circle"

        InfoBar.success(
            title="已添加",
            content="圆形分割区域已添加，拖拽可移动位置",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def add_polygon_region(self):
        """添加多边形分割区域"""
        if not self.image_file:
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

        # 获取图片尺寸
        if hasattr(self, 'pixmap_item'):
            rect = self.pixmap_item.boundingRect()
            cx, cy = rect.width() / 2, rect.height() / 2
            size = min(rect.width(), rect.height()) / 3
        else:
            cx, cy, size = 50, 40, 40

        # 创建多边形区域（默认为三角形）
        polygon = QPolygonF([
            QPointF(cx, cy - size),
            QPointF(cx + size, cy + size),
            QPointF(cx - size, cy + size)
        ])

        polygon_item = QGraphicsPolygonItem(polygon)
        polygon_item.setPen(QPen(QColor("#0078D4"), 2, Qt.PenStyle.SolidLine))
        polygon_item.setBrush(QBrush(QColor(0, 120, 212, 30)))
        polygon_item.setFlag(QGraphicsPolygonItem.GraphicsItemFlag.ItemIsMovable, True)
        polygon_item.setFlag(QGraphicsPolygonItem.GraphicsItemFlag.ItemIsSelectable, True)
        polygon_item.setFlag(QGraphicsPolygonItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self.scene.addItem(polygon_item)
        self.current_mode = "polygon"

        InfoBar.success(
            title="已添加",
            content="多边形分割区域已添加，拖拽可移动位置",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def clear_regions(self):
        """清空所有分割区域"""
        if not hasattr(self, 'pixmap_item'):
            self.scene.clear()
            self.crop_regions.clear()
            return

        # 只清除形状，保留图片
        items_to_remove = []
        for item in self.scene.items():
            if item != self.pixmap_item:
                items_to_remove.append(item)

        for item in items_to_remove:
            self.scene.removeItem(item)

        self.crop_regions.clear()

        InfoBar.info(
            title="已清空",
            content="所有分割区域已清空",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def clear_list(self):
        """清空列表"""
        if not self.file_list.get_files():
            return
        w = MessageBox("确认清空", "确定要清空图片吗？", self)
        if w.exec():
            self.file_list.clear_files()
            self.image_file = None
            self.scene.clear()
            self.crop_regions.clear()
            self.status_label.setText("请选择一张图片")
            self.crop_btn.setEnabled(False)

    def browse_output_dir(self):
        """浏览输出目录"""
        from PySide6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def start_crop(self):
        """开始分割"""
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

        # 获取图片尺寸用于计算比例
        if hasattr(self, 'pixmap_item'):
            img_rect = self.pixmap_item.boundingRect()
            img_width = img_rect.width()
            img_height = img_rect.height()
        else:
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

        # 获取所有分割区域（只支持矩形）
        regions = []
        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem):
                # 获取矩形的边界，并转换为比例坐标
                rect = item.sceneBoundingRect()
                x = rect.x() / img_width
                y = rect.y() / img_height
                width = rect.width() / img_width
                height = rect.height() / img_height
                regions.append((x, y, width, height))
            elif isinstance(item, QGraphicsEllipseItem):
                # 圆形也使用外接矩形
                rect = item.sceneBoundingRect()
                x = rect.x() / img_width
                y = rect.y() / img_height
                width = rect.width() / img_width
                height = rect.height() / img_height
                regions.append((x, y, width, height))
            # 多边形暂不支持，使用其边界框
            elif isinstance(item, QGraphicsPolygonItem):
                rect = item.sceneBoundingRect()
                x = rect.x() / img_width
                y = rect.y() / img_height
                width = rect.width() / img_width
                height = rect.height() / img_height
                regions.append((x, y, width, height))

        if not regions:
            InfoBar.warning(
                title="提示",
                content="请先添加至少一个分割区域",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        params = self.get_params()
        output_dir = params['output_dir'] or os.path.dirname(image_files[0])

        self.crop_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.thread = CropSplitThread(
            image_files[0],
            output_dir,
            regions,
            params['quality'],
            params['output_format']
        )
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.status.connect(lambda s: self.status_label.setText(s))
        self.thread.finished.connect(self.on_crop_finished)
        self.thread.error.connect(self.on_crop_error)
        self.thread.overwrite_request.connect(self.on_overwrite_request)
        self.thread.start()

    def get_params(self):
        """获取参数"""
        output_format = self.format_combo.currentText()
        if output_format == "保持原格式":
            output_format = None

        return {
            'quality': self.quality_slider.value(),
            'output_format': output_format,
            'output_dir': self.output_dir_edit.text().strip() or None
        }

    def on_crop_finished(self, results):
        """分割完成"""
        self.crop_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        filename = os.path.basename(self.file_list.get_files()[0])
        self.status_label.setText(f"完成分割: {filename}")

        InfoBar.success(
            title="完成",
            content=f"已将图片分割为 {len(results)} 个图片块",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )

    def on_crop_error(self, error_msg):
        """分割错误"""
        self.crop_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("分割失败")
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
