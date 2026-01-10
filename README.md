# 🖼️ Image Toolbox 图片工具箱

[English](docs/readme.en.md) | 中文

一个简洁易用的图片处理工具，支持图片拼接、批量压缩和尺寸统一，基于 PySide6 + Fluent Design 构建。

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.8+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 功能

### 🔗 图片拼接
- 拖拽添加图片，支持拖拽排序
- 水平/垂直拼接方向
- 多种对齐方式：居中、边缘对齐、等比例缩放
- 可选缩放比例
- 智能处理透明背景

### 🗜️ 图片压缩
- 批量压缩处理
- 自定义缩放比例和输出质量
- 支持输出格式转换（JPEG/PNG/WEBP）
- 实时显示压缩比例

### 📐 尺寸统一
- 将多张不同尺寸的图片统一调整为相同分辨率
- 支持两种统一模式：
  - **最大尺寸模式**：所有图片调整为最大图片的尺寸
  - **最小尺寸模式**：所有图片调整为最小图片的尺寸
- 等比例缩放，保持图片比例不变形
- 支持输出质量调节和格式转换
- 批量处理，提高工作效率

### ✂️ 图片分割
- 将单张图片按指定行列数分割成多个图片块
- 支持自定义宽度等分数（1-20）和高度等分数（1-20）
- 智能处理边界情况，确保完整分割
- 支持输出格式转换（JPEG/PNG/WEBP）
- 自动创建专用文件夹存放分割结果，文件夹命名格式：`原文件名_split_宽x高`
- 自动生成有序的文件名（如：image_split_1_1.jpg）

### ✨ Gemini 水印移除
- 自动移除 Gemini AI 生成图片右下角的水印
- 支持批量处理，提高工作效率
- 可调节输出质量（1-100），平衡文件大小和质量
- 支持输出格式转换（JPEG/PNG/WEBP）
- 自动检测图片尺寸，选择合适的水印移除策略
- 智能文件验证，自动跳过无效图片文件
- 实现原理来源 [journey-ad/gemini-watermark-remover](https://github.com/journey-ad/gemini-watermark-remover)

### 📁 支持格式
PNG, JPG, JPEG, BMP, WEBP

## 🚀 快速开始

```bash
# 克隆项目
git clone git@github.com:ZichengCao/Image-Toolbox.git
cd image-toolbox

# 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 🔧 系统要求

- Python 3.9+
- Windows / macOS / Linux

## 📄 许可证

MIT License
