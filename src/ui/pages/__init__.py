#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI页面模块
"""

from .image_stitcher_page import ImageStitcherPage
from .image_compress_page import ImageCompressPage
from .image_resize_page import ImageResizePage
from .image_grid_split_page import ImageGridSplitPage
from .image_crop_page import ImageCropPage
from .image_gemini_watermark_page import ImageGeminiWatermarkPage

__all__ = [
    'ImageStitcherPage',
    'ImageCompressPage',
    'ImageResizePage',
    'ImageGridSplitPage',
    'ImageCropPage',
    'ImageGeminiWatermarkPage'
]