# 🖼️ Image Toolbox

[中文](../README.md) | English

A simple and user-friendly image processing tool that supports image stitching, batch compression, and size unification, built with PySide6 + Fluent Design.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.8+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### 🔗 Image Stitching
- Drag and drop to add images with drag-to-reorder support
- Horizontal/vertical stitching directions
- Multiple alignment options: center, edge alignment, proportional scaling
- Optional scaling ratio
- Smart transparent background handling

### 🗜️ Image Compression
- Batch compression processing
- Custom scaling ratio and output quality
- Output format conversion support (JPEG/PNG/WEBP)
- Real-time compression ratio display

### 📐 Size Unification
- Unify multiple images of different sizes to the same resolution
- Two unification modes supported:
  - **Maximum Size Mode**: Resize all images to the largest image's dimensions
  - **Minimum Size Mode**: Resize all images to the smallest image's dimensions
- Proportional scaling to maintain aspect ratio
- Output quality adjustment and format conversion support
- Batch processing for improved efficiency

### ✂️ Image Splitting
- Split a single image into multiple blocks by specified rows and columns
- Support custom width divisions (1-20) and height divisions (1-20)
- Smart boundary handling to ensure complete splitting
- Output format conversion support (JPEG/PNG/WEBP)
- Auto-create dedicated folder for split results, folder naming format: `original_filename_split_widthxheight`
- Auto-generate ordered filenames (e.g., image_split_1_1.jpg)

### ✨ Gemini Watermark Removal
- Automatically remove watermarks from Gemini AI generated images
- Batch processing support for improved efficiency
- Adjustable output quality (1-100) to balance file size and quality
- Output format conversion support (JPEG/PNG/WEBP)
- Auto-detect image dimensions and select appropriate watermark removal strategy
- Smart file validation with automatic skipping of invalid image files
- Implementation Rationale Source [journey-ad/gemini-watermark-remover](https://github.com/journey-ad/gemini-watermark-remover)
- 
### 📁 Supported Formats
PNG, JPG, JPEG, BMP, WEBP

## 🚀 Quick Start

```bash
# Clone the repository
git clone git@github.com:ZichengCao/Image-Toolbox.git
cd image-toolbox

# Create virtual environment (recommended)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## 🔧 System Requirements

- Python 3.9+
- Windows / macOS / Linux

## 📄 License

MIT License