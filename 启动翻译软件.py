#!/usr/bin/env python3
"""
Translation Agent Pro 桌面版启动脚本
Desktop Translation Agent Launcher
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 70)
    print("🚀 Translation Agent Pro - 专业批量翻译桌面软件")
    print("   Professional Desktop Translation Software")
    print("=" * 70)
    
    print("\n📋 软件特性:")
    print("• 🔧 API配置与连接测试")
    print("• 📁 智能文件夹扫描与管理")
    print("• 🚀 多文件并发翻译 (最大10个并发)")
    print("• 📊 实时翻译进度监控")
    print("• 💾 自动结果保存与命名")
    print("• 🎯 反思式翻译工作流")
    
    print(f"\n🌐 正在启动桌面应用程序...")
    print("-" * 70)
    
    try:
        # 启动桌面应用
        from translation_agent_gui import main as gui_main
        gui_main()
        
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        print("\n🔧 请确保以下文件存在:")
        print("• translation_agent_gui.py")
        print("• app/process.py")
        print("• app/patch.py")
        print("• src/translation_agent/utils.py")
        
        input("\n按回车键退出...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        input("\n按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()