"""
PDF页码校验工具 - 配置文件

集中管理应用配置参数。
"""

import os

# 文件上传配置
class FileConfig:
    """文件上传相关配置"""
    
    # 最大文件大小 (字节)
    # 可以根据服务器性能调整
    # 1GB = 1024 * 1024 * 1024 = 1073741824 bytes
    # 500MB = 500 * 1024 * 1024 = 524288000 bytes
    # 100MB = 100 * 1024 * 1024 = 104857600 bytes
    
    # 预设大小选项
    MAX_FILE_SIZE_OPTIONS = {
        '50MB': 50 * 1024 * 1024,
        '100MB': 100 * 1024 * 1024,
        '200MB': 200 * 1024 * 1024,
        '500MB': 500 * 1024 * 1024,
        '1GB': 1024 * 1024 * 1024,
        '2GB': 2 * 1024 * 1024 * 1024,
        '5GB': 5 * 1024 * 1024 * 1024,
        '无限制': None  # 设置为None表示无限制
    }
    
    # 默认最大文件大小 (500MB)
    DEFAULT_MAX_FILE_SIZE = None
    
    # 从环境变量读取配置，如果没有设置则使用默认值
    MAX_FILE_SIZE = os.environ.get('PDF_MAX_FILE_SIZE', DEFAULT_MAX_FILE_SIZE)
    
    # 如果环境变量设置为数字，则转换为整数
    if isinstance(MAX_FILE_SIZE, str):
        if MAX_FILE_SIZE.isdigit():
            MAX_FILE_SIZE = int(MAX_FILE_SIZE)
        elif MAX_FILE_SIZE.upper() == 'NONE':
            MAX_FILE_SIZE = None
    
    # 上传文件夹
    UPLOAD_FOLDER = os.environ.get('PDF_UPLOAD_FOLDER', 'uploads')
    
    # 允许的文件类型
    ALLOWED_EXTENSIONS = {'.pdf'}

# 应用配置
class AppConfig:
    """应用相关配置"""
    
    # 密钥
    SECRET_KEY = os.environ.get('PDF_SECRET_KEY', 'pdf-validator-secret-key-2024')
    
    # 调试模式
    DEBUG = os.environ.get('PDF_DEBUG', 'True').lower() == 'true'
    
    # 主机和端口
    HOST = os.environ.get('PDF_HOST', '127.0.0.1')
    PORT = int(os.environ.get('PDF_PORT', 5000))

# OCR配置
class OCRConfig:
    """OCR相关配置"""
    
    # Tesseract路径
    # 如果您在安装Tesseract时没有将其添加到系统PATH，请在此处指定其可执行文件的完整路径。
    # Windows下的常见默认路径: 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    # macOS/Linux下如果通过包管理器安装，通常不需要设置，设为None即可。
    # 请根据您的实际安装位置修改下面的路径。
    TESSERACT_PATH = os.environ.get('TESSERACT_PATH', 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe')
    
    # 图像DPI
    DEFAULT_DPI = int(os.environ.get('PDF_DPI', 100))
    
    # OCR语言
    OCR_LANGUAGE = os.environ.get('PDF_OCR_LANGUAGE', 'eng')

    # --- 废弃：旧的粗略区域识别配置 ---
    # 为提高准确性，以下配置已由更精确的设置取代。
    # 建议迁移到下方的"精准区域识别配置"。
    # 页眉区域高度占页面总高度的百分比 (例如 0.15 代表 15%)
    # HEADER_HEIGHT_PERCENT = float(os.environ.get('PDF_HEADER_PERCENT', 0.15))

    # 页脚区域高度占页面总高度的百分比 (此配置已废弃)
    FOOTER_HEIGHT_PERCENT = float(os.environ.get('PDF_FOOTER_PERCENT', 0.10))

    # --- 新增：精准区域识别配置 ---
    # 通过定义一个更小的矩形区域来提高页码识别的准确性，避免无关文本的干扰。
    # 坐标系以页面左上角为原点 (0,0)，所有值均为0到1之间的小数，代表百分比。

    # 水平范围：从页面左侧 X% 处开始，持续 W% 的宽度。
    # 例如，要识别页面底部中心区域的页码，可设置 X_START=0.4, WIDTH=0.2。
    CROP_X_START_PERCENT = float(os.environ.get('PDF_CROP_X_START', 0.40))  # 从左侧40%处开始
    CROP_WIDTH_PERCENT = float(os.environ.get('PDF_CROP_WIDTH', 0.20))      # 裁剪区域宽度为页面总宽度的20%

    # 页脚垂直范围：从页面底部向上 Y% 处开始，持续 H% 的高度。
    # 例如，要识别最底部的10%区域，可以设置 Y_START_FROM_BOTTOM=0.0, HEIGHT=0.1。
    FOOTER_CROP_Y_START_FROM_BOTTOM_PERCENT = float(os.environ.get('PDF_FOOTER_Y_START', 0.03))  # 从最底部开始
    FOOTER_CROP_HEIGHT_PERCENT = float(os.environ.get('PDF_FOOTER_HEIGHT', 0.08))              # 裁剪区域高度为页面总高度的10%
    
    # --- 新增：可视化调试 ---
    # 是否保存用于调试的裁剪图片
    DEBUG_SAVE_CROPPED_IMAGES = os.environ.get('PDF_DEBUG_CROPS', 'True').lower() == 'true'

    # 调试图片保存路径
    DEBUG_IMAGE_PATH = 'debug_crops'

# 日志配置
class LogConfig:
    """日志相关配置"""
    
    # 日志级别
    LOG_LEVEL = os.environ.get('PDF_LOG_LEVEL', 'INFO')
    
    # 日志格式
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 日志文件
    LOG_FILE = os.environ.get('PDF_LOG_FILE', None)

def get_max_file_size():
    """
    获取最大文件大小设置
    
    Returns:
        int or None: 最大文件大小（字节），None表示无限制
    """
    return FileConfig.MAX_FILE_SIZE

def format_file_size(size_bytes):
    """
    格式化文件大小显示
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小字符串
    """
    if size_bytes is None:
        return "无限制"
    
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def print_config():
    """
    打印当前配置信息
    """
    print("📋 当前配置:")
    print(f"   最大文件大小: {format_file_size(get_max_file_size())}")
    print(f"   上传文件夹: {FileConfig.UPLOAD_FOLDER}")
    print(f"   调试模式: {AppConfig.DEBUG}")
    print(f"   主机: {AppConfig.HOST}")
    print(f"   端口: {AppConfig.PORT}")
    print(f"   OCR DPI: {OCRConfig.DEFAULT_DPI}")
    print(f"   OCR 语言: {OCRConfig.OCR_LANGUAGE}") 