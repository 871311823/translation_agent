# Translation Agent - 智能翻译助手

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Gradio](https://img.shields.io/badge/Gradio-WebUI-orange.svg)](https://gradio.app/)

**基于大语言模型的反思式翻译系统 | Agentic Translation with Reflection Workflow**

[English](#english-version) | [中文](#中文版本)

</div>

---

## 中文版本

### 📋 项目简介

**Translation Agent** 是一个基于大语言模型（LLM）的智能翻译系统，采用**反思式工作流（Reflection Workflow）**来提升翻译质量。与传统机器翻译不同，它通过"翻译→反思→改进"的三阶段流程，让 LLM 自己评估和改进翻译结果。

### ✨ 核心特性

- 🔄 **反思式工作流**：三阶段翻译流程（初始翻译 → 反思评估 → 改进翻译）
- 🎨 **高度可定制**：支持风格、术语、地域变体等精细控制
- 🌍 **多 LLM 支持**：OpenAI、Groq、TogetherAI、Ollama、自定义端点
- 🖥️ **友好的 WebUI**：基于 Gradio 的图形界面，支持文件上传
- 💾 **配置自动保存**：页面刷新时自动回填历史配置
- 📄 **多格式支持**：PDF、DOCX、TXT、Markdown 等
- 🔍 **差异对比**：可视化显示翻译前后的改进

### 🎯 工作原理

```
源文本
  ↓
[阶段1] 初始翻译 (Initial Translation)
  ↓
初始翻译结果
  ↓
[阶段2] 反思评估 (Reflection)
  ↓  
改进建议
  ↓
[阶段3] 改进翻译 (Improved Translation)
  ↓
最终翻译结果
```

### 🚀 快速开始

#### 方式一：使用在线 WebUI

直接访问已部署的服务：**http://47.109.82.94:7860**

#### 方式二：本地安装

**前置要求：**
- Python 3.9+
- Poetry 包管理器

**安装步骤：**

```bash
# 1. 克隆项目
git clone https://github.com/871311823/translation_agent.git
cd translation_agent

# 2. 安装 Poetry（如果未安装）
pip install poetry

# 3. 安装依赖
poetry install --with app

# 4. 配置 API Key
cp .env.sample .env
# 编辑 .env 文件，添加你的 API Key

# 5. 启动 WebUI
poetry run python app/app.py
```

访问 `http://localhost:7860` 即可使用。

#### 方式三：Python API

```python
import translation_agent as ta

# 基本使用
translation = ta.translate(
    source_lang="Chinese",
    target_lang="English", 
    source_text="你好，世界！",
    country="United States"
)

print(translation)
```

### 📖 使用指南

#### WebUI 界面功能

1. **API 配置**
   - 选择 API 端点（OpenAI、Groq、TogetherAI、Ollama、CUSTOM）
   - 输入 API 密钥
   - 自定义模型名称
   - 配置基础 URL（CUSTOM 端点）

2. **翻译设置**
   - 源语言 / 目标语言
   - 地区变体（如：美国英语、墨西哥西班牙语）
   - 高级选项：Token 数、温度、请求频率

3. **翻译操作**
   - 直接输入文本
   - 上传文件（PDF、DOCX、TXT 等）
   - 查看三阶段翻译结果
   - 下载翻译结果

4. **配置管理**
   - 点击"💾 保存配置"保存当前设置
   - 页面刷新时自动加载历史配置
   - 翻译成功后自动保存配置

#### 支持的 API 端点

| 端点 | 说明 | 默认模型 |
|------|------|----------|
| OpenAI | OpenAI 官方 API | gpt-4o |
| Groq | Groq 高速推理 | llama3-70b-8192 |
| TogetherAI | Together AI 平台 | Qwen/Qwen2-72B-Instruct |
| Ollama | 本地 Ollama 服务 | llama3 |
| CUSTOM | 自定义 OpenAI 兼容端点 | 自定义 |

**CUSTOM 端点使用：**
- 支持任何 OpenAI 兼容的 API
- 自动添加 `/v1` 后缀
- 示例：输入 `http://localhost:11434` → 自动转换为 `http://localhost:11434/v1`

### 🎨 核心优势

#### 1. 反思式工作流

传统翻译系统一次性输出结果，而 Translation Agent 采用三阶段流程：

- **初始翻译**：快速生成初步翻译
- **反思评估**：从准确性、流畅性、风格、术语四个维度评估
- **改进翻译**：根据反思建议优化翻译

这种方法类似于人类翻译的"初译→审校→定稿"流程，显著提升翻译质量。

#### 2. 四维度评估体系

- **准确性（Accuracy）**：纠正增译、误译、漏译
- **流畅性（Fluency）**：语法、拼写、标点正确性
- **风格（Style）**：匹配源文本风格和文化背景
- **术语（Terminology）**：术语一致性和领域特定用语

#### 3. 高度可定制

通过提示词可以精确控制：
- 翻译风格（正式/非正式）
- 术语表（确保关键术语翻译一致）
- 地域变体（如：拉丁美洲西班牙语 vs 西班牙西班牙语）
- 目标受众（技术文档、营销文案、法律文件等）

### 📊 使用场景

- ✅ **专业文档翻译**：技术文档、学术论文、法律合同
- ✅ **多语言内容创作**：营销文案、产品说明、用户手册
- ✅ **批量翻译处理**：支持长文本和文件批量上传
- ✅ **翻译质量评估**：可查看反思过程，了解改进点
- ✅ **术语一致性**：通过术语表确保专业术语翻译统一

### 🏗️ 项目结构

```
translation-agent/
├── src/translation_agent/
│   ├── utils.py          # 核心翻译逻辑（三阶段工作流）
│   └── __init__.py
├── app/
│   ├── app.py            # Gradio WebUI 界面
│   ├── process.py        # 处理逻辑
│   ├── patch.py          # LLM 端点配置
│   └── user_config.json  # 用户配置（自动生成）
├── examples/
│   ├── example_script.py # Python API 使用示例
│   └── sample-texts/     # 示例文本
├── deploy.sh             # Linux 部署脚本
├── deploy.ps1            # Windows 部署脚本
└── pyproject.toml        # 项目依赖配置
```

### 🔧 高级功能

#### 长文本智能分块

系统自动处理长文本：
- 智能计算分块大小
- 保持上下文连贯性
- 使用 `<TRANSLATE_THIS>` 标记当前翻译块

#### 速率限制

自动控制 API 调用频率，避免超过速率限制：
```python
@rate_limit(lambda: RPM)
def get_completion(...):
    # 自动控制调用频率
```

#### 配置持久化

- 配置自动保存到 `app/user_config.json`
- 页面刷新时自动加载
- 支持导出/导入配置

### 🚢 部署指南

#### Docker 部署（推荐）

```bash
# 构建镜像
docker build -t translation-agent .

# 运行容器
docker run -d -p 7860:7860 \
  -e OPENAI_API_KEY=your-key \
  translation-agent
```

#### Linux 服务器部署

使用提供的部署脚本：

```bash
# 赋予执行权限
chmod +x deploy.sh

# 执行部署（默认部署到 47.109.82.94）
./deploy.sh [服务器IP] [部署目录]

# 启动服务
ssh root@服务器IP
systemctl start translation-agent
systemctl enable translation-agent  # 开机自启
```

#### Windows 部署

```powershell
# 执行 PowerShell 部署脚本
.\deploy.ps1 -ServerIP "your-server-ip"
```

### 📝 配置文件说明

**`.env` 文件：**
```bash
# OpenAI API Key（必需）
OPENAI_API_KEY="your-openai-api-key"

# 可选：其他 API Keys
GROQ_API_KEY="your-groq-api-key"
TOGETHER_API_KEY="your-together-api-key"
```

**`user_config.json` 文件（自动生成）：**
```json
{
  "endpoint": "CUSTOM",
  "model": "gemini-3-flash-preview",
  "api_key": "your-api-key",
  "base": "http://your-api-endpoint",
  "source_lang": "Chinese",
  "target_lang": "English",
  "country": "United States",
  "max_tokens": 1000,
  "temperature": 0.3,
  "rpm": 60
}
```

### 🔍 故障排查

#### 服务无法启动

```bash
# 查看服务状态
systemctl status translation-agent

# 查看日志
journalctl -u translation-agent -f

# 手动测试
cd /opt/translation-agent
poetry run python app/app.py
```

#### API 调用失败

- 检查 API Key 是否正确
- 检查网络连接
- 检查 API 端点 URL 格式
- 查看速率限制设置

#### 端口被占用

```bash
# 查看端口占用
netstat -tulpn | grep 7860

# 停止占用进程
kill <PID>
```

### 📚 相关研究

- *ChatGPT MT: Competitive for High- (but not Low-) Resource Languages*, Robinson et al. (2023)
- *How to Design Translation Prompts for ChatGPT: An Empirical Study*, Gao et al. (2023)
- *Beyond Human Translation: Harnessing Multi-Agent Collaboration for Translating Ultra-Long Literary Texts*, Wu et al. (2024)

### 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 📄 许可证

本项目采用 **MIT 许可证**。详见 [LICENSE](LICENSE) 文件。

### 🙏 致谢

本项目基于 [Andrew Ng 的 Translation Agent](https://github.com/andrewyng/translation-agent) 进行改进和扩展。

---

## English Version

### 📋 Overview

**Translation Agent** is an intelligent translation system based on Large Language Models (LLM), using a **Reflection Workflow** to improve translation quality. Unlike traditional machine translation, it uses a three-stage process: "Translate → Reflect → Improve" to let the LLM evaluate and enhance its own translations.

### ✨ Key Features

- 🔄 **Reflection Workflow**: Three-stage translation process (Initial → Reflection → Improved)
- 🎨 **Highly Customizable**: Fine control over style, terminology, regional variants
- 🌍 **Multi-LLM Support**: OpenAI, Groq, TogetherAI, Ollama, Custom endpoints
- 🖥️ **User-Friendly WebUI**: Gradio-based interface with file upload support
- 💾 **Auto-Save Configuration**: Automatically restore settings on page refresh
- 📄 **Multiple Formats**: PDF, DOCX, TXT, Markdown, etc.
- 🔍 **Diff Comparison**: Visual display of translation improvements

### 🚀 Quick Start

#### Option 1: Use Online WebUI

Visit the deployed service: **http://47.109.82.94:7860**

#### Option 2: Local Installation

**Requirements:**
- Python 3.9+
- Poetry package manager

**Installation:**

```bash
# 1. Clone the repository
git clone https://github.com/871311823/translation_agent.git
cd translation_agent

# 2. Install Poetry (if not installed)
pip install poetry

# 3. Install dependencies
poetry install --with app

# 4. Configure API Key
cp .env.sample .env
# Edit .env file and add your API key

# 5. Start WebUI
poetry run python app/app.py
```

Visit `http://localhost:7860` to use.

#### Option 3: Python API

```python
import translation_agent as ta

# Basic usage
translation = ta.translate(
    source_lang="Chinese",
    target_lang="English",
    source_text="你好，世界！",
    country="United States"
)

print(translation)
```

### 📖 Usage Guide

#### WebUI Features

1. **API Configuration**
   - Select API endpoint (OpenAI, Groq, TogetherAI, Ollama, CUSTOM)
   - Enter API key
   - Customize model name
   - Configure base URL (for CUSTOM endpoint)

2. **Translation Settings**
   - Source / Target language
   - Regional variant (e.g., US English, Mexican Spanish)
   - Advanced options: Token count, temperature, request rate

3. **Translation Operations**
   - Direct text input
   - File upload (PDF, DOCX, TXT, etc.)
   - View three-stage translation results
   - Download translation results

4. **Configuration Management**
   - Click "💾 Save Config" to save current settings
   - Auto-load saved configuration on page refresh
   - Auto-save after successful translation

### 🎨 Core Advantages

#### 1. Reflection Workflow

Traditional translation systems output results in one pass, while Translation Agent uses a three-stage process:

- **Initial Translation**: Quick generation of preliminary translation
- **Reflection**: Evaluate from four dimensions: accuracy, fluency, style, terminology
- **Improved Translation**: Optimize based on reflection suggestions

This approach mimics the human translation process of "draft → review → finalize", significantly improving translation quality.

#### 2. Four-Dimensional Evaluation

- **Accuracy**: Correct additions, mistranslations, omissions
- **Fluency**: Grammar, spelling, punctuation correctness
- **Style**: Match source text style and cultural context
- **Terminology**: Consistency and domain-specific terms

### 📊 Use Cases

- ✅ **Professional Document Translation**: Technical docs, academic papers, legal contracts
- ✅ **Multilingual Content Creation**: Marketing copy, product descriptions, user manuals
- ✅ **Batch Translation**: Support for long texts and batch file uploads
- ✅ **Translation Quality Assessment**: View reflection process to understand improvements
- ✅ **Terminology Consistency**: Use glossaries to ensure consistent professional terms

### 🚢 Deployment Guide

#### Docker Deployment (Recommended)

```bash
# Build image
docker build -t translation-agent .

# Run container
docker run -d -p 7860:7860 \
  -e OPENAI_API_KEY=your-key \
  translation-agent
```

#### Linux Server Deployment

Use the provided deployment script:

```bash
# Grant execute permission
chmod +x deploy.sh

# Execute deployment (default to 47.109.82.94)
./deploy.sh [ServerIP] [DeployDir]

# Start service
ssh root@ServerIP
systemctl start translation-agent
systemctl enable translation-agent  # Auto-start on boot
```

### 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) file for details.

### 🙏 Acknowledgments

This project is based on and extends [Andrew Ng's Translation Agent](https://github.com/andrewyng/translation-agent).

---

<div align="center">

**Made with ❤️ by the Translation Agent Team**

[Report Bug](https://github.com/871311823/translation_agent/issues) · [Request Feature](https://github.com/871311823/translation_agent/issues)

</div>
