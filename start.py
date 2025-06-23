"""
PDF页码校验工具 - 启动脚本

该脚本用于启动Web应用。
所有配置请在 config.py 文件中修改。
"""

import sys

def main():
    """
    主启动函数
    """
    try:
        # 导入应用和配置
        from app import app
        from config import AppConfig, print_config

        # 打印欢迎信息和当前配置
        print("🚀 PDF页码校验工具 - Web服务器")
        print("=" * 50)
        print_config()
        print("-" * 50)
        
        print(f"🌐 服务器正在启动...")
        print(f"📱 访问地址: http://{AppConfig.HOST}:{AppConfig.PORT}")
        print("⏹️  按 Ctrl+C 停止服务器")
        print("-" * 50)

        # 启动Web服务器
        app.run(
            debug=AppConfig.DEBUG, 
            host=AppConfig.HOST, 
            port=AppConfig.PORT
        )

    except ImportError as e:
        print(f"❌ 启动失败: 无法导入模块 - {e}")
        print("请确保所有项目文件完整，并已安装所有依赖。")
        print("运行 'pip install -r requirements.txt' 安装依赖。")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止。")
    except Exception as e:
        print(f"❌ 启动时发生未知错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 