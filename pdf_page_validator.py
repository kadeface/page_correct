"""
PDF文档页码校验工具

该工具用于验证PDF文档的页码是否正确，包括：
1. 建立实际页序
2. 识别每一页的页码
3. 检查页码是否符合页序
4. 输出实际页序与识别页码的对应表

作者: PDF Page Validator
版本: 1.0.0
"""

import os
import sys
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import numpy as np
import re
import pandas as pd
from typing import List, Dict, Tuple, Optional
import logging
from pathlib import Path
from pytesseract import TesseractNotFoundError
import io
from config import OCRConfig
import base64

# 解决 DecompressionBombError
# 通过将 MAX_IMAGE_PIXELS 设置为 None，可以禁用 Pillow 的图像大小限制，
# 从而允许处理从高分辨率PDF页面生成的大尺寸图像。
Image.MAX_IMAGE_PIXELS = None


class PDFPageValidator:
    """
    PDF页码校验器
    
    用于验证PDF文档中页码的正确性和连续性。
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        初始化PDF页码校验器
        
        Args:
            tesseract_path: Tesseract OCR引擎的安装路径，如果为None则使用系统默认路径
            
        Raises:
            TesseractNotFoundError: 当Tesseract未安装或路径不正确时抛出
        """
        self.logger = self._setup_logging()
        
        # 配置Tesseract
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # 验证Tesseract是否可用
        try:
            pytesseract.get_tesseract_version()
            self.logger.info("Tesseract OCR引擎初始化成功")
        except TesseractNotFoundError:
            self.logger.error("Tesseract OCR 引擎未找到。请确保它已安装并位于系统 PATH 中，或通过 TESSERACT_PATH 配置指定其路径。")
            raise RuntimeError(
                "Tesseract OCR 引擎未找到或未正确配置。\n\n"
                "请根据您的操作系统完成安装：\n"
                "  - Windows: 访问 https://github.com/UB-Mannheim/tesseract/wiki 下载并安装。\n"
                "  - macOS: 运行 `brew install tesseract`。\n"
                "  - Linux: 运行 `sudo apt-get install tesseract-ocr`。\n\n"
                "安装后请重启本应用。"
            )
        except Exception as e:
            self.logger.error(f"Tesseract OCR引擎初始化时发生未知错误: {e}")
            raise e

        # 如果启用了调试模式，则创建用于保存裁剪图片的目录
        if OCRConfig.DEBUG_SAVE_CROPPED_IMAGES:
            os.makedirs(OCRConfig.DEBUG_IMAGE_PATH, exist_ok=True)
            self.logger.info(f"可视化调试已开启，裁剪后的图片将保存到 '{OCRConfig.DEBUG_IMAGE_PATH}' 目录。")
    
    def _setup_logging(self) -> logging.Logger:
        """
        设置日志记录器
        
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        logger = logging.getLogger('PDFPageValidator')
        logger.setLevel(logging.INFO)
        
        # 防止日志消息向上传播到根记录器，避免重复记录
        logger.propagate = False
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def extract_page_number(self, image: Image.Image, crop_areas: List[Tuple[int, int, int, int]], page_index: int) -> Tuple[Optional[int], Optional[Image.Image]]:
        """
        从页面图像的指定区域中提取页码，并返回识别到的图片。

        Args:
            image: 完整的页面图像。
            crop_areas: 一个包含多个区域元组的列表，格式为 (left, top, right, bottom)。
            page_index: 当前页码索引，用于调试文件名。

        Returns:
            Tuple[Optional[int], Optional[Image.Image]]: 提取到的页码和对应的裁剪图片。
        """
        try:
            for i, area in enumerate(crop_areas):
                # 裁剪出指定区域进行识别
                cropped_image = image.crop(area)
                
                # 如果开启了可视化调试，则保存裁剪的图片
                if OCRConfig.DEBUG_SAVE_CROPPED_IMAGES:
                    area_name = 'footer' if i == 0 else 'header' # 根据扫描顺序命名
                    debug_filename = os.path.join(OCRConfig.DEBUG_IMAGE_PATH, f"page_{page_index + 1}_{area_name}.png")
                    cropped_image.save(debug_filename)
                
                # 转换为灰度图像以提高识别率
                gray = cropped_image.convert('L')
                
                # 使用Tesseract进行OCR识别
                text = pytesseract.image_to_string(gray, lang='eng', config='--psm 6')
                
                # 使用正则表达式查找页码
                patterns = [
                    r'\b(\d+)\b',        # 纯数字, 例如: 3
                    r'Page\s*(\d+)',     # "Page 1"
                    r'P\.\s*(\d+)',      # "P. 1"
                    r'-\s*(\d+)\s*-',    # "- 1 -"
                    r'\.\s*(\d+)\s*\.',  # ". 3 ." (新添加的规则)
                    r'(\d+)\s*/\s*\d+'   # "1 / 10"
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        # 找到第一个匹配的数字就立刻返回
                        page_num = int(matches[0])
                        self.logger.debug(f"在区域 {i+1} 中识别到页码: {page_num}")
                        return page_num, cropped_image
            
            self.logger.warning("在所有指定区域中都未能识别到页码")
            return None, None
            
        except Exception as e:
            self.logger.error(f"在区域页码识别过程中失败: {e}", exc_info=True)
            return None, None
    
    def validate_page_numbers(self, pdf_path: str, dpi: int = 300) -> Dict:
        """
        验证PDF文档的页码，采用逐页处理以优化内存使用。
        
        Args:
            pdf_path: PDF文件路径
            dpi: 图像分辨率，默认300
            
        Returns:
            Dict: 包含验证结果的字典。
        """
        try:
            self.logger.info(f"开始验证PDF文档: {pdf_path} (采用内存优化模式)")
            
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            actual_sequence = list(range(1, total_pages + 1))
            detected_numbers = []
            validation_results = []

            for i in range(total_pages):
                page = doc.load_page(i)
                
                # 渲染当前页为图像
                mat = fitz.Matrix(dpi/72, dpi/72)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                width, height = image.size

                # --- 使用精准配置计算页脚裁剪区域 ---
                x_start = int(width * OCRConfig.CROP_X_START_PERCENT)
                crop_width = int(width * OCRConfig.CROP_WIDTH_PERCENT)
                
                footer_y_start = int(height * (1 - OCRConfig.FOOTER_CROP_HEIGHT_PERCENT - OCRConfig.FOOTER_CROP_Y_START_FROM_BOTTOM_PERCENT))
                footer_height = int(height * OCRConfig.FOOTER_CROP_HEIGHT_PERCENT)

                left, top = x_start, footer_y_start
                right, bottom = x_start + crop_width, footer_y_start + footer_height

                regions_to_scan = [(left, top, right, bottom)]

                page_num, cropped_img = self.extract_page_number(image, crop_areas=regions_to_scan, page_index=i)
                detected_numbers.append(page_num)
                self.logger.info(f"第 {i + 1}/{total_pages} 页检测到页码: {page_num}")

                # 将裁剪的图片转换为Base64
                cropped_img_b64 = None
                if cropped_img:
                    buffered = io.BytesIO()
                    cropped_img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    cropped_img_b64 = f"data:image/png;base64,{img_str}"

                validation_results.append({
                    'page_index': i,
                    'actual_number': actual_sequence[i],
                    'detected_number': page_num,
                    'is_valid': actual_sequence[i] == page_num,
                    'cropped_image_b64': cropped_img_b64
                })

            doc.close()

            # 重新计算统计数据
            correct_pages_count = sum(1 for r in validation_results if r['is_valid'])
            issues = [f"第 {r['page_index'] + 1} 页: 期望页码 {r['actual_number']}, 检测到页码 {r['detected_number']}" for r in validation_results if not r['is_valid']]
            
            success_rate = (correct_pages_count / total_pages) * 100 if total_pages > 0 else 0

            result = {
                'total_pages': total_pages,
                'correct_pages': correct_pages_count,
                'error_pages': total_pages - correct_pages_count,
                'validation_results': validation_results,
                'issues': issues,
                'success_rate': success_rate
            }
            
            self.logger.info(f"验证完成，成功率: {result['success_rate']:.2f}%")
            return result
            
        except Exception as e:
            self.logger.error(f"PDF验证失败: {e}", exc_info=True)
            raise
    
    def generate_report(self, validation_result: Dict, output_path: str = None) -> str:
        """
        生成验证报告
        
        Args:
            validation_result: 验证结果字典
            output_path: 输出文件路径，如果为None则返回报告内容
            
        Returns:
            str: 报告内容或文件路径
        """
        try:
            # 创建DataFrame用于输出
            df = pd.DataFrame(validation_result['validation_results'])
            
            # 生成报告内容
            report_lines = [
                "=" * 60,
                "PDF页码验证报告",
                "=" * 60,
                f"总页数: {validation_result['total_pages']}",
                f"验证成功率: {validation_result['success_rate']:.2f}%",
                "",
                "详细结果:",
                "-" * 40
            ]
            
            # 添加详细结果
            for result in validation_result['validation_results']:
                status = "✓" if result['is_valid'] else "✗"
                report_lines.append(
                    f"第 {result['page_index'] + 1:2d} 页: "
                    f"期望 {result['actual_number']:2d}, "
                    f"检测 {result['detected_number'] or 'N/A':2s} {status}"
                )
            
            if validation_result['issues']:
                report_lines.extend([
                    "",
                    "发现的问题:",
                    "-" * 20
                ])
                for issue in validation_result['issues']:
                    report_lines.append(f"• {issue}")
            
            report_content = "\n".join(report_lines)
            
            # 如果指定了输出路径，保存到文件
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                # 同时保存CSV格式的详细数据
                csv_path = output_path.replace('.txt', '.csv')
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
                self.logger.info(f"报告已保存到: {output_path}")
                self.logger.info(f"详细数据已保存到: {csv_path}")
                return output_path
            
            return report_content
            
        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")
            raise


def main():
    """
    主函数 - 命令行接口
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF页码验证工具')
    parser.add_argument('pdf_path', help='PDF文件路径')
    parser.add_argument('-o', '--output', help='输出报告文件路径')
    parser.add_argument('--tesseract-path', help='Tesseract安装路径')
    parser.add_argument('--dpi', type=int, default=300, help='图像分辨率')
    
    args = parser.parse_args()
    
    try:
        # 创建验证器
        validator = PDFPageValidator(args.tesseract_path)
        
        # 执行验证
        result = validator.validate_page_numbers(args.pdf_path, args.dpi)
        
        # 生成报告
        if args.output:
            report_path = validator.generate_report(result, args.output)
            print(f"验证完成，报告已保存到: {report_path}")
        else:
            report_content = validator.generate_report(result)
            print(report_content)
            
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 