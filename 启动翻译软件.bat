@echo off
chcp 65001 >nul
title Translation Agent Pro - 桌面版

echo ======================================================================
echo 🚀 Translation Agent Pro - 专业批量翻译桌面软件
echo    Professional Desktop Translation Software
echo ======================================================================
echo.

echo 📋 软件特性:
echo • 🔧 API配置与连接测试
echo • 📁 智能文件夹扫描与管理
echo • 🚀 多文件并发翻译 (最大10个并发)
echo • 📊 实时翻译进度监控
echo • 💾 自动结果保存与命名
echo • 🎯 反思式翻译工作流
echo.

echo 🌐 正在启动桌面软件...
echo ----------------------------------------------------------------------
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查核心依赖
echo 🔍 检查依赖包...
python -c "import openai, tiktoken, docx, pymupdf" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  缺少必要的依赖包，正在尝试安装...
    echo 如果安装失败，请手动运行: pip install -r requirements.txt
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败，请手动安装依赖包
        echo 运行命令: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

REM 启动软件
echo ✅ 正在启动桌面应用程序...
python translation_agent_gui.py

pause