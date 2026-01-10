#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini AI 图片水印移除模块

实现原理：
1. Gemini 生成的图片水印是通过 alpha blending 叠加在右下角的
2. 水印公式: watermarked = original * (1 - alpha) + watermark * alpha
3. 已知 watermark 为白色 (255, 255, 255)，可通过逆向公式恢复原始图像:
   original = (watermarked - alpha * 255) / (1 - alpha)
4. alpha 值从预捕获的背景图中计算得出（取 RGB 最大通道值）
"""

import os
import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from datetime import datetime
import numpy as np
from PIL import Image
from PySide6.QtCore import QObject, Signal, QThread, QMutex, QWaitCondition

logger = logging.getLogger('ImageStitcher.gemini_watermark_remover')


class WatermarkConfig:
    """水印配置"""

    def __init__(self, logo_size: int, margin_right: int, margin_bottom: int):
        self.logo_size = logo_size
        self.margin_right = margin_right
        self.margin_bottom = margin_bottom


def detect_watermark_config(image_width: int, image_height: int) -> WatermarkConfig:
    """根据图片尺寸检测水印配置

    Args:
        image_width: 图片宽度
        image_height: 图片高度

    Returns:
        WatermarkConfig 对象
    """
    if image_width > 1024 and image_height > 1024:
        return WatermarkConfig(logo_size=96, margin_right=64, margin_bottom=64)
    else:
        return WatermarkConfig(logo_size=48, margin_right=32, margin_bottom=32)


def calculate_watermark_position(
    image_width: int,
    image_height: int,
    config: WatermarkConfig
) -> Dict[str, int]:
    """计算水印在图片中的位置

    Args:
        image_width: 图片宽度
        image_height: 图片高度
        config: 水印配置

    Returns:
        包含 x, y, width, height 的字典
    """
    return {
        'x': image_width - config.margin_right - config.logo_size,
        'y': image_height - config.margin_bottom - config.logo_size,
        'width': config.logo_size,
        'height': config.logo_size
    }


def calculate_alpha_map(bg_image: Image.Image) -> np.ndarray:
    """从背景捕获图像计算 alpha map

    Alpha 值取 RGB 通道的最大值，归一化到 [0, 1]

    Args:
        bg_image: PIL Image 对象（背景捕获图）

    Returns:
        Float32 类型的 numpy 数组，形状为 (height, width)
    """
    # 转换为 numpy 数组
    bg_array = np.array(bg_image)

    # 取 RGB 三个通道的最大值作为 alpha
    if bg_array.ndim == 3 and bg_array.shape[2] >= 3:
        alpha_map = np.max(bg_array[:, :, :3], axis=2).astype(np.float32)
    else:
        alpha_map = bg_array.astype(np.float32)

    # 归一化到 [0, 1]
    alpha_map = alpha_map / 255.0

    return alpha_map


class GeminiWatermarkRemover(QObject):
    """Gemini 水印移除引擎"""

    progress = Signal(int)
    status = Signal(str)
    error = Signal(str)

    # 常量
    ALPHA_THRESHOLD = 0.002
    MAX_ALPHA = 0.99
    LOGO_VALUE = 255  # 白色水印的 RGB 值

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alpha_maps: Dict[int, np.ndarray] = {}
        self._bg_images: Dict[int, Image.Image] = {}
        self._assets_dir = None

    def _get_assets_dir(self) -> Path:
        """获取资源目录路径"""
        if self._assets_dir is None:
            # 获取项目根目录
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            self._assets_dir = project_root / "assets" / "gemini_watermark"

        if not self._assets_dir.exists():
            raise FileNotFoundError(
                f"Gemini watermark assets directory not found: {self._assets_dir}\n"
                "Please run extract_bg_images.py first to generate the required background images."
            )

        return self._assets_dir

    def _load_background_image(self, size: int) -> Image.Image:
        """加载指定尺寸的背景图像

        Args:
            size: 背景图尺寸 (48 或 96)

        Returns:
            PIL Image 对象
        """
        if size not in (48, 96):
            raise ValueError(f"Unsupported background image size: {size}. Only 48 and 96 are supported.")

        if size not in self._bg_images:
            assets_dir = self._get_assets_dir()
            bg_path = assets_dir / f"bg_{size}.png"

            if not bg_path.exists():
                raise FileNotFoundError(f"Background image not found: {bg_path}")

            # 打开图片并立即加载数据到内存
            img = Image.open(bg_path)
            img.load()  # 强制加载图片数据
            self._bg_images[size] = img

        return self._bg_images[size]

    def get_alpha_map(self, size: int) -> np.ndarray:
        """获取指定尺寸的 alpha map

        Args:
            size: 水印尺寸 (48 或 96)

        Returns:
            alpha map numpy 数组
        """
        if size not in self._alpha_maps:
            bg_image = self._load_background_image(size)
            self._alpha_maps[size] = calculate_alpha_map(bg_image)
            logger.debug(f"Calculated alpha map for size {size}")

        return self._alpha_maps[size]

    def _remove_watermark_region(
        self,
        image_array: np.ndarray,
        alpha_map: np.ndarray,
        position: Dict[str, int]
    ) -> np.ndarray:
        """移除指定区域的水印

        使用 alpha blending 逆向公式:
        original = (watermarked - alpha * LOGO_VALUE) / (1 - alpha)

        Args:
            image_array: 图片 numpy 数组 (H, W, 3)
            alpha_map: alpha map (H, W)
            position: 水印位置 {x, y, width, height}

        Returns:
            处理后的图片数组
        """
        x, y, width, height = position['x'], position['y'], position['width'], position['height']

        # 提取水印区域
        watermark_region = image_array[y:y + height, x:x + width].copy()

        # 遍历每个像素进行恢复
        for row in range(height):
            for col in range(width):
                alpha = alpha_map[row, col]

                # 跳过 alpha 值太小的像素（基本没有水印）
                if alpha < self.ALPHA_THRESHOLD:
                    continue

                # 限制 alpha 最大值，避免除零错误
                alpha = min(alpha, self.MAX_ALPHA)
                one_minus_alpha = 1.0 - alpha

                # 对每个颜色通道应用逆向公式
                for c in range(3):  # RGB 三个通道
                    watermarked = watermark_region[row, col, c]
                    # original = (watermarked - alpha * 255) / (1 - alpha)
                    original = (watermarked - alpha * self.LOGO_VALUE) / one_minus_alpha
                    # 限制到 [0, 255] 范围
                    watermark_region[row, col, c] = np.clip(original, 0, 255)

        # 将处理后的区域写回原图
        image_array[y:y + height, x:x + width] = watermark_region

        return image_array

    def remove_from_file(
        self,
        input_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """从文件中移除水印

        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径（可选，默认为 input_path 后加 _no_watermark）

        Returns:
            输出文件路径
        """
        self.status.emit(f"正在加载图片: {os.path.basename(input_path)}")

        with Image.open(input_path) as img:
            # 转换为 RGB（如果不是的话）
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 处理图片
            result_img = self.remove_from_image(img)

            # 确定输出路径
            if output_path is None:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_no_watermark{ext}"

            # 保存结果
            result_img.save(output_path, quality=95)
            self.status.emit(f"已保存到: {os.path.basename(output_path)}")

        return output_path

    def remove_from_image(self, image: Image.Image) -> Image.Image:
        """从 PIL Image 对象中移除水印

        Args:
            image: PIL Image 对象

        Returns:
            移除水印后的 PIL Image 对象
        """
        width, height = image.size

        # 确保图片是 RGB 格式
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # 转换为 numpy 数组进行处理
        image_array = np.array(image).astype(np.float32)

        # 检测水印配置
        config = detect_watermark_config(width, height)

        # 计算水印位置
        position = calculate_watermark_position(width, height, config)

        self.status.emit(
            f"检测到水印配置: {config.logo_size}px, "
            f"位置: ({position['x']}, {position['y']})"
        )

        # 获取对应的 alpha map
        alpha_map = self.get_alpha_map(config.logo_size)

        # 移除水印
        self.status.emit("正在移除水印...")
        result_array = self._remove_watermark_region(image_array, alpha_map, position)

        # 转换回 PIL Image
        result_image = Image.fromarray(result_array.astype(np.uint8))

        return result_image

    def get_watermark_info(self, image_width: int, image_height: int) -> Dict[str, Any]:
        """获取水印信息（用于调试）

        Args:
            image_width: 图片宽度
            image_height: 图片高度

        Returns:
            包含水印信息的字典
        """
        config = detect_watermark_config(image_width, image_height)
        position = calculate_watermark_position(image_width, image_height, config)

        return {
            'size': config.logo_size,
            'position': position,
            'config': {
                'logo_size': config.logo_size,
                'margin_right': config.margin_right,
                'margin_bottom': config.margin_bottom
            }
        }

    @staticmethod
    def is_gemini_image(image_path: str) -> bool:
        """判断图片是否可能是 Gemini 生成的（简单判断）

        Args:
            image_path: 图片路径

        Returns:
            是否可能是 Gemini 生成的图片
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                config = detect_watermark_config(width, height)
                # Gemini 生成的图片通常有特定的尺寸范围
                return True
        except Exception:
            return False


class GeminiWatermarkThread(QThread):
    """Gemini 水印移除线程"""
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(list)
    error = Signal(str)
    overwrite_request = Signal(str)

    def __init__(
        self,
        image_files: list,
        output_dir: str,
        output_format: Optional[str] = None,
        quality: int = 95
    ):
        super().__init__()
        self.image_files = image_files
        self.output_dir = output_dir
        self.output_format = output_format
        self.quality = quality

        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.overwrite_allowed = True
        self.waiting_for_response = False

        # 获取水印移除器实例
        self.remover = GeminiWatermarkRemover()

    def set_overwrite_allowed(self, allowed: bool) -> None:
        """设置是否允许覆盖文件"""
        self.mutex.lock()
        self.overwrite_allowed = allowed
        if self.waiting_for_response:
            self.wait_condition.wakeAll()
        self.mutex.unlock()

    def run(self) -> None:
        try:
            results: list = []
            failed_files: list = []
            total = len(self.image_files)

            for i, filepath in enumerate(self.image_files):
                self.status.emit(f"正在处理 {i+1}/{total}: {os.path.basename(filepath)}")

                # 验证文件存在
                if not os.path.exists(filepath):
                    logger.error(f"File not found: {filepath}")
                    failed_files.append((filepath, "文件不存在"))
                    continue

                # 验证文件大小
                if os.path.getsize(filepath) == 0:
                    logger.error(f"File is empty: {filepath}")
                    failed_files.append((filepath, "文件为空"))
                    continue

                # 确定输出路径
                filename = os.path.basename(filepath)
                name, ext = os.path.splitext(filename)

                # 保持原始格式或使用指定格式
                if self.output_format:
                    format_ext_map = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp'}
                    ext = format_ext_map.get(self.output_format, ext)

                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                output_filename = f"{name}_no_watermark_{timestamp}{ext}"
                output_path = os.path.join(self.output_dir, output_filename)

                # 检查文件是否存在
                if os.path.exists(output_path):
                    self.mutex.lock()
                    self.waiting_for_response = True
                    self.overwrite_request.emit(output_path)
                    self.wait_condition.wait(self.mutex)
                    self.waiting_for_response = False
                    self.mutex.unlock()
                    if not self.overwrite_allowed:
                        continue

                # 处理图片
                try:
                    # 尝试打开图片，支持多种格式
                    img = None
                    try:
                        img = Image.open(filepath)
                    except Exception as e:
                        # 如果直接打开失败，尝试使用不同的格式
                        error_msg = str(e)
                        if "unrecognized" in error_msg or "cannot identify" in error_msg:
                            # 文件格式可能不正确或损坏
                            logger.error(f"Failed to open image {filepath}: {e}")
                            failed_files.append((filepath, f"图片格式无法识别: {error_msg}"))
                            continue
                        else:
                            raise

                    # 转换为 RGB
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # 移除水印
                    result_img = self.remover.remove_from_image(img)

                    # 关闭原始图片
                    img.close()

                    # 计算压缩级别（针对 PNG）
                    # 质量 100 → compress_level 0（无压缩）
                    # 质量 1 → compress_level 9（最大压缩）
                    compress_level = max(0, min(9, int((100 - self.quality) / 10)))

                    # 保存结果
                    if self.output_format == 'JPEG':
                        result_img.save(output_path, 'JPEG', quality=self.quality, optimize=True)
                    elif self.output_format == 'PNG':
                        # compress_level: 0=无压缩(最大质量), 9=最大压缩(最小文件)
                        result_img.save(output_path, 'PNG', compress_level=compress_level)
                    elif self.output_format == 'WEBP':
                        result_img.save(output_path, 'WEBP', quality=self.quality, method=6)
                    else:
                        # 保持原格式时也需要设置质量参数
                        ext_lower = ext.lower()
                        if ext_lower in ('.jpg', '.jpeg'):
                            result_img.save(output_path, 'JPEG', quality=self.quality, optimize=True)
                        elif ext_lower == '.png':
                            result_img.save(output_path, 'PNG', compress_level=compress_level)
                        elif ext_lower == '.webp':
                            result_img.save(output_path, 'WEBP', quality=self.quality, method=6)
                        else:
                            result_img.save(output_path)

                    results.append({
                        'input': filepath,
                        'output': output_path,
                        'file_size': os.path.getsize(output_path)
                    })

                except Exception as e:
                    logger.error(f"Failed to process {filepath}: {e}", exc_info=True)
                    failed_files.append((filepath, str(e)))
                    continue

                self.progress.emit(int((i + 1) / total * 100))

            # 如果有失败的文件，在结果中包含错误信息
            if failed_files:
                error_summary = "\n".join([f"- {os.path.basename(f)}: {msg}" for f, msg in failed_files])
                results.append({
                    'errors': failed_files,
                    'error_summary': f"有 {len(failed_files)} 个文件处理失败:\n{error_summary}"
                })

            self.finished.emit(results)

        except Exception as e:
            logger.error(f"GeminiWatermarkThread error: {e}", exc_info=True)
            self.error.emit(str(e))


# 创建单例实例
_instance = None


def get_watermark_remover() -> GeminiWatermarkRemover:
    """获取水印移除器单例"""
    global _instance
    if _instance is None:
        _instance = GeminiWatermarkRemover()
    return _instance
