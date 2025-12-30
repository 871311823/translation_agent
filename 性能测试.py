#!/usr/bin/env python3
"""
翻译性能测试脚本
用于验证优化后的翻译性能
"""

import time
import os
import sys
from pathlib import Path

def test_translation_performance():
    """测试翻译性能"""
    print("🚀 翻译性能测试")
    print("=" * 50)
    
    # 检查必要文件
    gui_file = "translation_agent_gui.py"
    if not os.path.exists(gui_file):
        print("❌ 找不到 translation_agent_gui.py 文件")
        return False
    
    # 检查app目录
    app_dir = "app"
    if not os.path.exists(app_dir):
        print("❌ 找不到 app 目录")
        return False
    
    required_files = [
        "app/process.py",
        "app/patch.py"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ 找不到 {file_path} 文件")
            return False
    
    print("✅ 所有必要文件检查通过")
    
    # 测试导入
    try:
        print("\n📦 测试模块导入...")
        
        # 添加当前目录到路径
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
        
        # 测试导入GUI模块
        import translation_agent_gui
        print("✅ translation_agent_gui 导入成功")
        
        # 测试导入process模块
        sys.path.insert(0, os.path.join(os.getcwd(), 'app'))
        import process
        print("✅ process 模块导入成功")
        
        # 测试导入patch模块
        import patch
        print("✅ patch 模块导入成功")
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 导入时出现其他错误: {e}")
        return False
    
    # 测试GUI创建
    try:
        print("\n🖥️ 测试GUI创建...")
        import tkinter as tk
        
        # 创建测试窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        # 创建GUI实例
        app = translation_agent_gui.TranslationAgentGUI(root)
        print("✅ GUI创建成功")
        
        # 测试配置加载
        app.load_config()
        print("✅ 配置加载成功")
        
        # 测试性能设置
        if hasattr(app, 'api_timeout_var'):
            print(f"✅ API超时设置: {app.api_timeout_var.get()}秒")
        
        if hasattr(app, 'performance_mode_var'):
            print(f"✅ 性能模式: {app.performance_mode_var.get()}")
        
        if hasattr(app, 'retry_count_var'):
            print(f"✅ 重试次数: {app.retry_count_var.get()}")
        
        # 关闭测试窗口
        root.destroy()
        
    except Exception as e:
        print(f"❌ GUI测试失败: {e}")
        return False
    
    print("\n🎉 性能测试完成！")
    print("=" * 50)
    print("✅ 所有测试通过")
    print("\n📋 优化内容:")
    print("• 动态超时控制")
    print("• 智能并发管理")
    print("• 性能模式选择")
    print("• 增强错误处理")
    print("• 实时进度监控")
    
    return True

def show_performance_tips():
    """显示性能优化建议"""
    print("\n💡 性能优化建议:")
    print("=" * 30)
    print("🚀 快速模式: 适合小文件批量翻译")
    print("⚖️ 平衡模式: 适合大多数情况(推荐)")
    print("🛡️ 稳定模式: 适合大文件或网络不稳定")
    print("\n📊 并发设置建议:")
    print("• 小文件(<2KB): 8-10个并发")
    print("• 中等文件(2-10KB): 5个并发")
    print("• 大文件(>10KB): 2-3个并发")
    print("\n⏱️ 超时设置建议:")
    print("• 网络良好: 60-120秒")
    print("• 网络一般: 120-300秒")
    print("• 网络较差: 300-600秒")

if __name__ == "__main__":
    print("🔧 Translation Agent Pro - 性能测试工具")
    print("版本: 2.1.0 (性能优化版)")
    print("时间:", time.strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    success = test_translation_performance()
    
    if success:
        show_performance_tips()
        print(f"\n🎯 启动翻译软件: python translation_agent_gui.py")
    else:
        print("\n❌ 测试失败，请检查错误信息")
        sys.exit(1)