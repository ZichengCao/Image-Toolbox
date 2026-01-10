#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理核心逻辑
"""

import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from PIL import Image
from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition

logger = logging.getLogger('ImageStitcher.image_processor')


def convert_to_rgb(img: Image.Image) -> Image.Image:
    """将图片转换为 RGB 格式
    
    Args:
        img: PIL Image 对象
        
    Returns:
        转换后的 RGB 格式图片
    """
    if img.mode in ('RGBA', 'LA', 'P'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        if img.mode == 'RGBA':
            bg.paste(img, mask=img.split()[3])
        else:
            bg.paste(img)
        return bg
    return img


def get_output_format(original_format: Optional[str], output_format: Optional[str]) -> str:
    """确定输出格式
    
    Args:
        original_format: 原始格式
        output_format: 指定的输出格式
        
    Returns:
        最终的输出格式
    """
    if original_format == 'JPG':
        original_format = 'JPEG'
    return output_format or original_format or 'JPEG'


def get_file_extension(format_name: str) -> str:
    """根据格式名称获取文件扩展名
    
    Args:
        format_name: 格式名称
        
    Returns:
        文件扩展名
    """
    ext_map = {
        'JPEG': '.jpg',
        'PNG': '.png',
        'WEBP': '.webp'
    }
    return ext_map.get(format_name, '.jpg')


class ResizeThread(QThread):
    """尺寸统一线程"""
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(list)
    error = Signal(str)
    overwrite_request = Signal(str)

    def __init__(
        self,
        image_files: List[str],
        output_dir: str,
        resize_mode: str = "max",
        quality: int = 95,
        output_format: Optional[str] = None
    ):
        super().__init__()
        self.image_files = image_files
        self.output_dir = output_dir
        self.resize_mode = resize_mode
        self.quality = quality
        self.output_format = output_format
        self.target_width: Optional[int] = None
        self.target_height: Optional[int] = None
        
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.overwrite_allowed = True
        self.waiting_for_response = False

    def set_custom_size(self, width: int, height: int) -> None:
        """设置自定义尺寸"""
        self.target_width = width
        self.target_height = height

    def set_overwrite_allowed(self, allowed: bool) -> None:
        """设置是否允许覆盖文件"""
        self.mutex.lock()
        self.overwrite_allowed = allowed
        if self.waiting_for_response:
            self.wait_condition.wakeAll()
        self.mutex.unlock()

    def run(self) -> None:
        try:
            results: List[Dict[str, Any]] = []
            total = len(self.image_files)
            
            self.status.emit("分析图片尺寸...")
            images_info = []
            for filepath in self.image_files:
                with Image.open(filepath) as img:
                    images_info.append({
                        'path': filepath,
                        'width': img.width,
                        'height': img.height
                    })
            
            if self.resize_mode == "max":
                target_width = max(info['width'] for info in images_info)
                target_height = max(info['height'] for info in images_info)
            elif self.resize_mode == "min":
                target_width = min(info['width'] for info in images_info)
                target_height = min(info['height'] for info in images_info)
            else:
                target_width = self.target_width or 800
                target_height = self.target_height or 600
            
            self.progress.emit(10)
            
            for i, info in enumerate(images_info):
                self.status.emit(f"处理 {i+1}/{total}: {os.path.basename(info['path'])}")
                
                with Image.open(info['path']) as img:
                    original_size = os.path.getsize(info['path'])
                    
                    img_resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    
                    original_format = img.format or os.path.splitext(info['path'])[1][1:].upper()
                    out_format = get_output_format(original_format, self.output_format)
                    
                    filename = os.path.basename(info['path'])
                    name, _ = os.path.splitext(filename)
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    ext = get_file_extension(out_format)
                    output_path = os.path.join(self.output_dir, f"{name}_resized_{timestamp}{ext}")
                    
                    if os.path.exists(output_path):
                        self.mutex.lock()
                        self.waiting_for_response = True
                        self.overwrite_request.emit(output_path)
                        self.wait_condition.wait(self.mutex)
                        self.waiting_for_response = False
                        self.mutex.unlock()
                        if not self.overwrite_allowed:
                            continue
                    
                    if out_format == 'JPEG':
                        img_resized = convert_to_rgb(img_resized)
                        img_resized.save(output_path, 'JPEG', quality=self.quality, optimize=True)
                    elif out_format == 'PNG':
                        img_resized.save(output_path, 'PNG', optimize=True)
                    elif out_format == 'WEBP':
                        img_resized.save(output_path, 'WEBP', quality=self.quality)
                    else:
                        img_resized.save(output_path, quality=self.quality)
                    
                    new_size = os.path.getsize(output_path)
                    results.append({
                        'input': info['path'],
                        'output': output_path,
                        'original_size': f"{info['width']}x{info['height']}",
                        'new_size': f"{target_width}x{target_height}",
                        'file_size': new_size
                    })
                    
                    self.progress.emit(10 + int((i + 1) / total * 90))
            
            self.finished.emit(results)
            
        except Exception as e:
            logger.error(f"ResizeThread error: {e}", exc_info=True)
            self.error.emit(str(e))


class CompressThread(QThread):
    """图片压缩线程"""
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(list)
    error = Signal(str)
    overwrite_request = Signal(str)

    def __init__(
        self,
        image_files: List[str],
        output_dir: str,
        scale: int = 80,
        quality: int = 80,
        output_format: Optional[str] = None
    ):
        super().__init__()
        self.image_files = image_files
        self.output_dir = output_dir
        self.scale = scale
        self.quality = quality
        self.output_format = output_format
        
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.overwrite_allowed = True
        self.waiting_for_response = False

    def set_overwrite_allowed(self, allowed: bool) -> None:
        """设置是否允许覆盖文件"""
        self.mutex.lock()
        self.overwrite_allowed = allowed
        if self.waiting_for_response:
            self.wait_condition.wakeAll()
        self.mutex.unlock()

    def run(self) -> None:
        try:
            results: List[Dict[str, Any]] = []
            total = len(self.image_files)
            
            for i, filepath in enumerate(self.image_files):
                self.status.emit(f"正在处理 {i+1}/{total}: {os.path.basename(filepath)}")
                
                with Image.open(filepath) as img:
                    original_size = os.path.getsize(filepath)
                    
                    if self.scale < 100:
                        new_width = int(img.width * self.scale / 100)
                        new_height = int(img.height * self.scale / 100)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    original_format = img.format or os.path.splitext(filepath)[1][1:].upper()
                    out_format = get_output_format(original_format, self.output_format)
                    
                    filename = os.path.basename(filepath)
                    name, _ = os.path.splitext(filename)
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    ext = get_file_extension(out_format)
                    output_path = os.path.join(self.output_dir, f"{name}_compressed_{timestamp}{ext}")
                    
                    if os.path.exists(output_path):
                        self.mutex.lock()
                        self.waiting_for_response = True
                        self.overwrite_request.emit(output_path)
                        self.wait_condition.wait(self.mutex)
                        self.waiting_for_response = False
                        self.mutex.unlock()
                        if not self.overwrite_allowed:
                            continue
                    
                    if out_format == 'JPEG':
                        img = convert_to_rgb(img)
                        img.save(output_path, 'JPEG', quality=self.quality, optimize=True)
                    elif out_format == 'PNG':
                        img.save(output_path, 'PNG', optimize=True)
                    elif out_format == 'WEBP':
                        img.save(output_path, 'WEBP', quality=self.quality)
                    else:
                        img.save(output_path, quality=self.quality)
                    
                    new_size = os.path.getsize(output_path)
                    results.append({
                        'input': filepath,
                        'output': output_path,
                        'original_size': original_size,
                        'new_size': new_size,
                        'ratio': (1 - new_size / original_size) * 100 if original_size > 0 else 0
                    })
                    
                    self.progress.emit(int((i + 1) / total * 100))
            
            self.finished.emit(results)
            
        except Exception as e:
            logger.error(f"CompressThread error: {e}", exc_info=True)
            self.error.emit(str(e))


class StitchThread(QThread):
    """图片拼接线程"""
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(str)
    error = Signal(str)
    overwrite_request = Signal(str)

    def __init__(
        self,
        image_files: List[str],
        compress_enabled: bool = True,
        scale: int = 80,
        output_dir: Optional[str] = None,
        output_name: Optional[str] = None,
        is_horizontal: bool = True,
        align_mode: str = "center"
    ):
        super().__init__()
        self.image_files = image_files
        self.compress_enabled = compress_enabled
        self.scale = scale
        self.output_dir = output_dir
        self.output_name = output_name
        self.is_horizontal = is_horizontal
        self.align_mode = align_mode
        
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.overwrite_allowed = True
        self.waiting_for_response = False

    def set_overwrite_allowed(self, allowed: bool) -> None:
        """设置是否允许覆盖文件"""
        self.mutex.lock()
        self.overwrite_allowed = allowed
        if self.waiting_for_response:
            self.wait_condition.wakeAll()
        self.mutex.unlock()

    def run(self) -> None:
        try:
            self.status.emit("正在加载图片...")
            self.progress.emit(10)

            images = []
            formats = set()
            for filepath in self.image_files:
                with Image.open(filepath) as img:
                    images.append(img.copy())
                    formats.add(img.format)

            self.progress.emit(30)
            self.status.emit("正在计算尺寸...")

            if len(formats) > 1:
                output_format = "JPEG"
                has_transparency = False
            else:
                output_format = list(formats)[0]
                has_transparency = any(
                    img.mode in ('RGBA', 'LA') or
                    (img.mode == 'P' and 'transparency' in img.info)
                    for img in images
                )

            canvas_size = self._calculate_canvas_size(images)

            self.progress.emit(50)
            self.status.emit("正在拼接图片...")

            if has_transparency and output_format == "PNG":
                result = Image.new('RGBA', canvas_size, (0, 0, 0, 0))
            else:
                result = Image.new('RGB', canvas_size, (255, 255, 255))

            self._stitch_images(images, result, canvas_size)

            self.progress.emit(90)
            self.status.emit("正在保存文件...")

            output_path = self._save_result(result, output_format)

            self.progress.emit(100)
            self.finished.emit(output_path)

        except Exception as e:
            logger.error(f"StitchThread error: {e}", exc_info=True)
            self.error.emit(str(e))

    def _calculate_canvas_size(self, images: List[Image.Image]) -> tuple:
        """计算画布尺寸"""
        if self.is_horizontal:
            if self.align_mode in ["等比例放大到同一尺寸", "等比例缩小到同一尺寸"]:
                if self.align_mode == "等比例放大到同一尺寸":
                    target_height = max(img.height for img in images)
                else:
                    target_height = min(img.height for img in images)
                
                if self.compress_enabled:
                    scale = self.scale / 100
                    target_height = int(target_height * scale)
                
                total_width = 0
                for img in images:
                    aspect_ratio = img.width / img.height
                    scaled_width = int(target_height * aspect_ratio)
                    total_width += scaled_width
                
                return (total_width, target_height)
            else:
                max_height = max(img.height for img in images)
                total_width = sum(img.width for img in images)
                
                if self.compress_enabled:
                    scale = self.scale / 100
                    max_height = int(max_height * scale)
                    total_width = int(total_width * scale)
                
                return (total_width, max_height)
        else:
            if self.align_mode in ["等比例放大到同一尺寸", "等比例缩小到同一尺寸"]:
                if self.align_mode == "等比例放大到同一尺寸":
                    target_width = max(img.width for img in images)
                else:
                    target_width = min(img.width for img in images)
                
                if self.compress_enabled:
                    scale = self.scale / 100
                    target_width = int(target_width * scale)
                
                total_height = 0
                for img in images:
                    aspect_ratio = img.height / img.width
                    scaled_height = int(target_width * aspect_ratio)
                    total_height += scaled_height
                
                return (target_width, total_height)
            else:
                max_width = max(img.width for img in images)
                total_height = sum(img.height for img in images)
                
                if self.compress_enabled:
                    scale = self.scale / 100
                    max_width = int(max_width * scale)
                    total_height = int(total_height * scale)
                
                return (max_width, total_height)

    def _stitch_images(self, images: List[Image.Image], result: Image.Image, canvas_size: tuple) -> None:
        """拼接图片"""
        x_offset = 0
        y_offset = 0
        
        for i, img in enumerate(images):
            if self.compress_enabled:
                scale = self.scale / 100
                new_width = int(img.width * scale)
                new_height = int(img.height * scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            if self.is_horizontal and self.align_mode in ["等比例放大到同一尺寸", "等比例缩小到同一尺寸"]:
                target_height = canvas_size[1]
                aspect_ratio = img.width / img.height
                new_width = int(target_height * aspect_ratio)
                img = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
            elif not self.is_horizontal and self.align_mode in ["等比例放大到同一尺寸", "等比例缩小到同一尺寸"]:
                target_width = canvas_size[0]
                aspect_ratio = img.height / img.width
                new_height = int(target_width * aspect_ratio)
                img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)

            if result.mode == 'RGB' and img.mode in ('RGBA', 'LA', 'P'):
                if img.mode == 'P' and 'transparency' in img.info:
                    img = img.convert('RGBA')
                bg = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    bg.paste(img, mask=img.split()[3])
                else:
                    bg.paste(img)
                img = bg
            elif result.mode == 'RGBA' and img.mode == 'RGB':
                img = img.convert('RGBA')

            if self.is_horizontal:
                if self.align_mode in ["等比例放大到同一尺寸", "等比例缩小到同一尺寸"]:
                    result.paste(img, (x_offset, 0))
                else:
                    if self.align_mode == "顶部对齐":
                        y_pos = 0
                    elif self.align_mode == "底部对齐":
                        y_pos = canvas_size[1] - img.height
                    else:
                        y_pos = (canvas_size[1] - img.height) // 2
                    
                    result.paste(img, (x_offset, y_pos))
                
                x_offset += img.width
            else:
                if self.align_mode in ["等比例放大到同一尺寸", "等比例缩小到同一尺寸"]:
                    result.paste(img, (0, y_offset))
                else:
                    if self.align_mode == "左侧对齐":
                        x_pos = 0
                    elif self.align_mode == "右侧对齐":
                        x_pos = canvas_size[0] - img.width
                    else:
                        x_pos = (canvas_size[0] - img.width) // 2
                    
                    result.paste(img, (x_pos, y_offset))
                
                y_offset += img.height
                
            self.progress.emit(50 + int((i + 1) / len(images) * 30))

    def _save_result(self, result: Image.Image, output_format: str) -> Optional[str]:
        """保存结果"""
        if not self.output_dir:
            self.output_dir = os.path.dirname(self.image_files[0])

        if not self.output_name:
            first_name = os.path.splitext(os.path.basename(self.image_files[0]))[0]
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            self.output_name = f"{first_name}_stitched_{timestamp}"

        ext = ".png" if output_format == "PNG" else ".jpg"
        output_path = os.path.join(self.output_dir, self.output_name + ext)

        if os.path.exists(output_path):
            self.mutex.lock()
            self.waiting_for_response = True
            self.overwrite_request.emit(output_path)
            self.wait_condition.wait(self.mutex)
            self.waiting_for_response = False
            self.mutex.unlock()
            if not self.overwrite_allowed:
                return None

        if output_format == "JPEG":
            result = result.convert('RGB')
            result.save(output_path, "JPEG", quality=95)
        else:
            result.save(output_path, output_format)

        return output_path


class GridSplitThread(QThread):
    """图片等分线程"""
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(list)
    error = Signal(str)
    overwrite_request = Signal(str)

    def __init__(
        self,
        image_file: str,
        output_dir: str,
        x_splits: int = 2,
        y_splits: int = 2,
        quality: int = 95,
        output_format: Optional[str] = None
    ):
        super().__init__()
        self.image_file = image_file
        self.output_dir = output_dir
        self.x_splits = x_splits
        self.y_splits = y_splits
        self.quality = quality
        self.output_format = output_format
        
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.overwrite_allowed = True
        self.waiting_for_response = False

    def set_overwrite_allowed(self, allowed: bool) -> None:
        """设置是否允许覆盖文件"""
        self.mutex.lock()
        self.overwrite_allowed = allowed
        if self.waiting_for_response:
            self.wait_condition.wakeAll()
        self.mutex.unlock()

    def run(self) -> None:
        try:
            self.status.emit("正在加载图片...")
            self.progress.emit(10)
            
            with Image.open(self.image_file) as img:
                original_width = img.width
                original_height = img.height
                
                block_width = original_width // self.x_splits
                block_height = original_height // self.y_splits
                
                self.status.emit(f"开始等分 {self.x_splits}x{self.y_splits} = {self.x_splits * self.y_splits} 块...")
                self.progress.emit(20)
                
                results: List[Dict[str, Any]] = []
                total_blocks = self.x_splits * self.y_splits
                
                original_format = img.format or os.path.splitext(self.image_file)[1][1:].upper()
                out_format = get_output_format(original_format, self.output_format)
                
                filename = os.path.basename(self.image_file)
                name, _ = os.path.splitext(filename)
                
                split_folder_name = f"{name}_split_{self.x_splits}x{self.y_splits}"
                split_output_dir = os.path.join(self.output_dir, split_folder_name)
                
                if not os.path.exists(split_output_dir):
                    os.makedirs(split_output_dir)
                
                for y in range(self.y_splits):
                    for x in range(self.x_splits):
                        block_index = y * self.x_splits + x + 1
                        self.status.emit(f"处理第 {block_index}/{total_blocks} 块...")
                        
                        left = x * block_width
                        top = y * block_height
                        right = left + block_width
                        bottom = top + block_height
                        
                        if x == self.x_splits - 1:
                            right = original_width
                        if y == self.y_splits - 1:
                            bottom = original_height
                        
                        cropped_img = img.crop((left, top, right, bottom))
                        
                        ext = get_file_extension(out_format)
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                        output_filename = f"{name}_split_{timestamp}_{y+1}_{x+1}{ext}"
                        output_path = os.path.join(split_output_dir, output_filename)
                        
                        if os.path.exists(output_path):
                            self.mutex.lock()
                            self.waiting_for_response = True
                            self.overwrite_request.emit(output_path)
                            self.wait_condition.wait(self.mutex)
                            self.waiting_for_response = False
                            self.mutex.unlock()
                            if not self.overwrite_allowed:
                                continue
                        
                        if out_format == 'JPEG':
                            cropped_img = convert_to_rgb(cropped_img)
                            cropped_img.save(output_path, 'JPEG', quality=self.quality, optimize=True)
                        elif out_format == 'PNG':
                            cropped_img.save(output_path, 'PNG', optimize=True)
                        elif out_format == 'WEBP':
                            cropped_img.save(output_path, 'WEBP', quality=self.quality)
                        else:
                            cropped_img.save(output_path, quality=self.quality)
                        
                        results.append({
                            'input': self.image_file,
                            'output': output_path,
                            'output_folder': split_output_dir,
                            'position': f"第{y+1}行第{x+1}列",
                            'size': f"{cropped_img.width}x{cropped_img.height}",
                            'file_size': os.path.getsize(output_path)
                        })
                        
                        progress = 20 + int((block_index / total_blocks) * 70)
                        self.progress.emit(progress)
            
            self.progress.emit(100)
            self.finished.emit(results)
            
        except Exception as e:
            logger.error(f"GridSplitThread error: {e}", exc_info=True)
            self.error.emit(str(e))


class CropSplitThread(QThread):
    """自定义区域分割线程"""
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(list)
    error = Signal(str)
    overwrite_request = Signal(str)

    def __init__(
        self,
        image_file: str,
        output_dir: str,
        regions: List[Tuple[float, float, float, float]],
        quality: int = 95,
        output_format: Optional[str] = None
    ):
        super().__init__()
        self.image_file = image_file
        self.output_dir = output_dir
        self.regions = regions
        self.quality = quality
        self.output_format = output_format
        
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.overwrite_allowed = True
        self.waiting_for_response = False

    def set_overwrite_allowed(self, allowed: bool) -> None:
        """设置是否允许覆盖文件"""
        self.mutex.lock()
        self.overwrite_allowed = allowed
        if self.waiting_for_response:
            self.wait_condition.wakeAll()
        self.mutex.unlock()

    def run(self) -> None:
        try:
            self.status.emit("正在加载图片...")
            self.progress.emit(10)
            
            with Image.open(self.image_file) as img:
                original_width = img.width
                original_height = img.height
                
                self.status.emit(f"开始分割 {len(self.regions)} 个区域...")
                self.progress.emit(20)
                
                results: List[Dict[str, Any]] = []
                
                original_format = img.format or os.path.splitext(self.image_file)[1][1:].upper()
                out_format = get_output_format(original_format, self.output_format)
                
                filename = os.path.basename(self.image_file)
                name, _ = os.path.splitext(filename)
                
                split_folder_name = f"{name}_crop_{len(self.regions)}_regions"
                split_output_dir = os.path.join(self.output_dir, split_folder_name)
                
                if not os.path.exists(split_output_dir):
                    os.makedirs(split_output_dir)
                
                for i, (x, y, width, height) in enumerate(self.regions):
                    self.status.emit(f"处理第 {i+1}/{len(self.regions)} 个区域...")
                    
                    left = int(x * original_width)
                    top = int(y * original_height)
                    right = int((x + width) * original_width)
                    bottom = int((y + height) * original_height)
                    
                    cropped_img = img.crop((left, top, right, bottom))
                    
                    ext = get_file_extension(out_format)
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    output_filename = f"{name}_crop_{timestamp}_{i+1}{ext}"
                    output_path = os.path.join(split_output_dir, output_filename)
                    
                    if os.path.exists(output_path):
                        self.mutex.lock()
                        self.waiting_for_response = True
                        self.overwrite_request.emit(output_path)
                        self.wait_condition.wait(self.mutex)
                        self.waiting_for_response = False
                        self.mutex.unlock()
                        if not self.overwrite_allowed:
                            continue
                    
                    if out_format == 'JPEG':
                        cropped_img = convert_to_rgb(cropped_img)
                        cropped_img.save(output_path, 'JPEG', quality=self.quality, optimize=True)
                    elif out_format == 'PNG':
                        cropped_img.save(output_path, 'PNG', optimize=True)
                    elif out_format == 'WEBP':
                        cropped_img.save(output_path, 'WEBP', quality=self.quality)
                    else:
                        cropped_img.save(output_path, quality=self.quality)
                    
                    results.append({
                        'input': self.image_file,
                        'output': output_path,
                        'output_folder': split_output_dir,
                        'region': f"区域{i+1}",
                        'size': f"{cropped_img.width}x{cropped_img.height}",
                        'file_size': os.path.getsize(output_path)
                    })
                    
                    progress = 20 + int((i + 1) / len(self.regions) * 70)
                    self.progress.emit(progress)
            
            self.progress.emit(100)
            self.finished.emit(results)
            
        except Exception as e:
            logger.error(f"CropSplitThread error: {e}", exc_info=True)
            self.error.emit(str(e))
