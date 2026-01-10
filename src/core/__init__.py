# Core Processing Logic

from .gemini_watermark_remover import (
    GeminiWatermarkRemover,
    GeminiWatermarkThread,
    get_watermark_remover,
    WatermarkConfig,
    detect_watermark_config,
    calculate_watermark_position,
)

__all__ = [
    'GeminiWatermarkRemover',
    'GeminiWatermarkThread',
    'get_watermark_remover',
    'WatermarkConfig',
    'detect_watermark_config',
    'calculate_watermark_position',
]