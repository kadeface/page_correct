"""
PDF页码校验工具 - Web应用

提供基于Flask的Web界面，用于PDF文档页码验证。

作者: PDF Page Validator
版本: 1.0.1
"""

import os
import sys
import tempfile
from datetime import datetime
import logging
from pytesseract import TesseractNotFoundError

# 检查Flask是否已安装
try:
    from flask import Flask, render_template, request, jsonify, send_file
    from werkzeug.utils import secure_filename
except ImportError as e:
    print(f"❌ 缺少必要的依赖: {e}")
    print("请运行以下命令安装依赖:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# 导入配置和核心逻辑
try:
    from config import AppConfig, FileConfig, LogConfig, OCRConfig, format_file_size
    from pdf_page_validator import PDFPageValidator
except ImportError as e:
    print(f"❌ 无法导入模块: {e}")
    print("请确保所有项目文件都存在且依赖已正确安装。")
    sys.exit(1)

# 初始化Flask应用
app = Flask(__name__)

# 从配置文件加载配置
app.config['MAX_CONTENT_LENGTH'] = FileConfig.MAX_FILE_SIZE
app.config['UPLOAD_FOLDER'] = FileConfig.UPLOAD_FOLDER
app.config['SECRET_KEY'] = AppConfig.SECRET_KEY

# 确保必要的目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=LogConfig.LOG_LEVEL,
    format=LogConfig.LOG_FORMAT,
    filename=LogConfig.LOG_FILE
)
logger = logging.getLogger(__name__)

# 全局验证器实例
validator = None

def get_validator():
    """
    获取PDF验证器实例
    
    Returns:
        PDFPageValidator: 验证器实例
        
    Raises:
        Exception: 当验证器初始化失败时抛出
    """
    global validator
    if validator is None:
        try:
            validator = PDFPageValidator(tesseract_path=OCRConfig.TESSERACT_PATH)
            logger.info("PDF验证器初始化成功")
        except TesseractNotFoundError as e:
            logger.error(f"Tesseract OCR 引擎未找到: {e}", exc_info=True)
            raise Exception(f"验证器初始化失败: {str(e)}")
        except Exception as e:
            logger.error(f"初始化验证器失败: {e}")
            raise Exception(f"验证器初始化失败: {str(e)}")
    return validator

@app.route('/favicon.ico')
def favicon():
    """
    处理浏览器图标请求
    
    Returns:
        Response: 返回一个空响应，防止404错误
    """
    return '', 204

@app.route('/')
def index():
    """
    主页路由
    
    Returns:
        str: 渲染的HTML页面
    """
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    文件上传处理
    
    Returns:
        dict: JSON响应，包含处理结果
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件', 'code': 'NO_FILE'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件', 'code': 'NO_FILE'}), 400
        
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in FileConfig.ALLOWED_EXTENSIONS:
            return jsonify({
                'error': f'只支持以下文件格式: {", ".join(FileConfig.ALLOWED_EXTENSIONS)}',
                'code': 'INVALID_FORMAT'
            }), 400
        
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        if app.config['MAX_CONTENT_LENGTH'] and file_size > app.config['MAX_CONTENT_LENGTH']:
            max_size_formatted = format_file_size(app.config['MAX_CONTENT_LENGTH'])
            return jsonify({
                'error': f'文件大小超过限制 ({max_size_formatted})',
                'code': 'FILE_TOO_LARGE',
                'max_size': max_size_formatted
            }), 413
        
        logger.info(f"开始处理文件: {file.filename} (大小: {format_file_size(file_size)})")
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        file.save(filepath)
        logger.info(f"文件已保存: {filepath}")
        
        validator_instance = get_validator()
        result = validator_instance.validate_page_numbers(filepath, dpi=OCRConfig.DEFAULT_DPI)
        logger.info(f"验证完成: {file.filename}")
        
    except TesseractNotFoundError as e:
        logger.error(f"Tesseract OCR 引擎未找到: {e}", exc_info=True)
        return jsonify({
            'error': f'OCR引擎配置错误: 请确保Tesseract已正确安装并添加到系统PATH。错误详情: {e}',
            'code': 'TESSERACT_NOT_FOUND'
        }), 500
    except Exception as e:
        logger.error(f"处理文件时出现未预期的错误: {e}", exc_info=True)
        # 在调试模式下，将完整的错误信息返回给前端
        if app.debug:
            import traceback
            tb_str = traceback.format_exc()
            return jsonify({
                'error': '服务器内部发生未知错误。',
                'traceback': tb_str,
                'code': 'INTERNAL_ERROR'
            }), 500
        
        return jsonify({'error': '服务器内部错误', 'code': 'INTERNAL_ERROR'}), 500
    finally:
        if 'filepath' in locals() and os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.info(f"临时文件已清理: {filepath}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")

    result['filename'] = file.filename
    result['upload_time'] = datetime.now().isoformat()
    result['file_size'] = format_file_size(file_size)
    
    return jsonify(result)

@app.route('/download-report', methods=['POST'])
def download_report():
    try:
        data = request.get_json()
        if not data or 'report_content' not in data:
            return jsonify({'error': '没有提供报告数据', 'code': 'NO_DATA'}), 400
        
        report_content = data['report_content']
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(report_content)
            temp_path = f.name
        
        filename = f"PDF页码验证报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        logger.info(f"生成报告文件: {filename}")
        
        return send_file(temp_path, as_attachment=True, download_name=filename, mimetype='text/plain')
        
    except Exception as e:
        logger.error(f"生成报告时出错: {e}", exc_info=True)
        return jsonify({'error': '生成报告失败', 'code': 'REPORT_ERROR'}), 500

@app.route('/config')
def get_config_endpoint():
    """
    获取应用配置信息
    
    Returns:
        dict: 配置信息
    """
    return jsonify({
        'max_file_size': app.config['MAX_CONTENT_LENGTH'],
        'max_file_size_formatted': format_file_size(app.config['MAX_CONTENT_LENGTH']),
        'version': '1.0.1'
    })

@app.errorhandler(413)
def too_large(e):
    max_size_formatted = format_file_size(app.config["MAX_CONTENT_LENGTH"])
    return jsonify({'error': f'文件大小超过限制 ({max_size_formatted})', 'code': 'FILE_TOO_LARGE'}), 413

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"内部服务器错误: {e}", exc_info=True)
    return jsonify({'error': '服务器内部错误', 'code': 'INTERNAL_ERROR'}), 500

# 移除了 if __name__ == '__main__' 代码块
# 启动逻辑现在由 start.py 负责 