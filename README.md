# PDF页码校验工具

一个专业的PDF文档页码验证工具，支持自动识别和校验PDF文档中的页码正确性。

## 功能特性

- 🔍 **智能页码识别**: 使用OCR技术自动识别PDF页面中的页码
- 📄 **详细验证报告**: 生成包含页码对照表的详细验证报告
- 🎨 **现代化界面**: 基于Apple设计语言的简洁美观界面
- 📱 **响应式设计**: 支持桌面和移动设备
- ⚡ **高性能处理**: 优化的PDF处理算法
- 📁 **批量处理**: 支持多个PDF文件批量验证

## 安装要求

### 系统要求
- Python 3.8+
- Tesseract OCR引擎

### 安装Tesseract

#### Windows
1. 下载并安装 [Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
2. 将安装路径添加到系统环境变量

#### macOS
```bash
brew install tesseract
```

#### Ubuntu/Debian
```bash
sudo apt-get install tesseract-ocr
```

### 安装Python依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行使用

```bash
# 基本使用
python pdf_page_validator.py document.pdf

# 指定输出文件
python pdf_page_validator.py document.pdf -o report.txt

# 指定Tesseract路径
python pdf_page_validator.py document.pdf --tesseract-path "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### Web界面使用

1. 启动Web服务器：
```bash
python app.py
```

2. 打开浏览器访问：`http://localhost:5000`

3. 拖拽或选择PDF文件进行验证

## 输出格式

### 验证报告示例 

## 技术架构

### 核心组件

1. **PDF解析器**: 使用PyMuPDF提取页面图像
2. **OCR引擎**: 使用Tesseract进行文字识别
3. **页码识别器**: 正则表达式匹配页码格式
4. **验证引擎**: 对比实际页序与识别页码
5. **报告生成器**: 生成详细验证报告

### 支持的页码格式

- 纯数字页码 (1, 2, 3...)
- 中文页码 (第1页, 第2页...)
- 英文页码 (Page 1, Page 2...)
- 分数格式 (1/10, 2/10...)

## 配置选项

### 环境变量

- `TESSERACT_PATH`: Tesseract安装路径
- `PDF_DPI`: PDF图像提取分辨率 (默认: 300)

### 命令行参数

- `--dpi`: 设置图像分辨率
- `--tesseract-path`: 指定Tesseract路径
- `-o, --output`: 指定输出文件路径

## 故障排除

### 常见问题

1. **Tesseract未找到**
   - 确保Tesseract已正确安装
   - 检查环境变量设置
   - 使用`--tesseract-path`参数指定路径

2. **页码识别不准确**
   - 提高PDF图像质量
   - 增加DPI设置
   - 检查页码格式是否支持

3. **处理速度慢**
   - 降低DPI设置
   - 使用更快的硬件
   - 优化PDF文件大小

## 开发指南

### 项目结构

```
pdf_page_validator/
├── pdf_page_validator.py    # 核心验证逻辑
├── app.py                   # Web应用
├── templates/
│   └── index.html          # Web界面
├── static/                 # 静态资源
├── uploads/                # 上传文件目录
├── requirements.txt        # Python依赖
└── README.md              # 项目文档
```

### 扩展功能

1. **添加新的页码格式支持**
2. **实现批量处理功能**
3. **添加更多输出格式**
4. **集成云存储服务**

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持基本PDF页码验证
- 提供命令行和Web界面
- 生成详细验证报告