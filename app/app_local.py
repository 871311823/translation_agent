import os
import re
import json
import threading
import sys
from glob import glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional
import time

# 添加当前目录到 Python 路径，以便导入 process 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import gradio as gr
from process import (
    diff_texts,
    extract_docx,
    extract_pdf,
    extract_text,
    model_load,
    translator,
    translator_sec,
)

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "user_config.json")

# 全局变量
translation_tasks = {}  # 存储翻译任务状态
task_counter = 0
MAX_CONCURRENT_TASKS = 5  # 最大并发数

# 标志：是否正在加载配置
is_loading_config = False


class TranslationTask:
    """翻译任务类"""
    def __init__(self, task_id: str, filename: str, content: str):
        self.task_id = task_id
        self.filename = filename
        self.content = content
        self.status = "等待中"  # 等待中, 翻译中, 已完成, 失败
        self.progress = 0
        self.init_translation = ""
        self.reflect_translation = ""
        self.final_translation = ""
        self.error_message = ""
        self.start_time = None
        self.end_time = None


def save_config(
    endpoint, model, api_key, base,
    endpoint2, model2, api_key2, base2,
    source_lang, target_lang, country,
    max_tokens, temperature, rpm, choice
):
    """保存配置到本地文件"""
    try:
        config = {
            "endpoint": endpoint,
            "model": model,
            "api_key": api_key,
            "base": base,
            "endpoint2": endpoint2,
            "model2": model2,
            "api_key2": api_key2,
            "base2": base2,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "country": country,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "rpm": rpm,
            "choice": choice,
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return gr.update(value="✅ 配置已保存", visible=True)
    except Exception as e:
        return gr.update(value=f"❌ 保存失败: {e}", visible=True)


def load_config():
    """从本地文件加载配置"""
    global is_loading_config
    is_loading_config = True
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)

            def cfg(key, default):
                val = config.get(key)
                if val is None or val == "":
                    return default
                return val

            endpoint_val = cfg("endpoint", "OpenAI")
            endpoint2_val = cfg("endpoint2", "OpenAI")
            choice_val = cfg("choice", False)
            
            result = (
                endpoint_val,
                cfg("model", "gpt-4o"),
                cfg("api_key", ""),
                gr.update(value=cfg("base", ""), visible=(endpoint_val == "CUSTOM")),
                endpoint2_val,
                cfg("model2", "gpt-4o"),
                cfg("api_key2", ""),
                gr.update(value=cfg("base2", ""), visible=(endpoint2_val == "CUSTOM")),
                cfg("source_lang", "Chinese"),
                cfg("target_lang", "English"),
                cfg("country", "United States"),
                cfg("max_tokens", 1000),
                cfg("temperature", 0.3),
                cfg("rpm", 60),
                choice_val,
                gr.update(value="✅ 已自动加载历史配置", visible=True),
                gr.update(visible=choice_val),
            )
            is_loading_config = False
            return result
    except Exception as e:
        print(f"加载配置时出错: {e}")
        is_loading_config = False
        pass
    
    is_loading_config = False
    return (
        "OpenAI", "gpt-4o", "", gr.update(value="", visible=False),
        "OpenAI", "gpt-4o", "", gr.update(value="", visible=False),
        "Chinese", "English", "United States",
        1000, 0.3, 60, False,
        gr.update(value="使用默认配置", visible=True),
        gr.update(visible=False),
    )


def update_model(endpoint, current_model=None):
    """更新模型名"""
    global is_loading_config
    
    endpoint_model_map = {
        "Groq": "llama3-70b-8192",
        "OpenAI": "gpt-4o",
        "TogetherAI": "Qwen/Qwen2-72B-Instruct",
        "Ollama": "llama3",
        "CUSTOM": "",
    }
    
    default_model = endpoint_model_map.get(endpoint, "")
    
    if is_loading_config:
        model_update = gr.update()
    elif current_model and current_model.strip() and current_model != default_model:
        model_update = gr.update()
    else:
        model_update = gr.update(value=default_model)
    
    if endpoint == "CUSTOM":
        base = gr.update(visible=True, placeholder="例如: http://localhost:11434")
    else:
        base = gr.update(visible=False)
    
    return model_update, base


def read_uploaded_files(files: List) -> List[Tuple[str, str]]:
    """读取上传的文件并返回文件名和内容"""
    file_contents = []
    
    if not files:
        return file_contents
    
    for file in files:
        try:
            if isinstance(file, str):
                file_path = file
            else:
                file_path = file.name if hasattr(file, 'name') else str(file)
            
            if not file_path or not os.path.exists(file_path):
                continue
            
            # 获取原始文件名
            original_filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(original_filename)[0]
            
            # 提取文件扩展名
            if "." not in os.path.basename(file_path):
                continue
            
            file_type = os.path.splitext(file_path)[1][1:].lower()
            
            if file_type in ["pdf", "txt", "py", "docx", "json", "cpp", "md"]:
                if file_type == "pdf":
                    content = extract_pdf(file_path)
                elif file_type == "docx":
                    content = extract_docx(file_path)
                else:
                    content = extract_text(file_path)
                
                # 清理内容
                content = re.sub(r"(?m)^\s*$\n?", "", content)
                if content.strip():
                    file_contents.append((name_without_ext, content))
                    
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")
            continue
    
    return file_contents


def translate_single_file(
    task: TranslationTask,
    endpoint: str, base: str, model: str, api_key: str,
    choice: bool, endpoint2: str, base2: str, model2: str, api_key2: str,
    source_lang: str, target_lang: str, country: str,
    max_tokens: int, temperature: int, rpm: int
) -> TranslationTask:
    """翻译单个文件"""
    try:
        task.status = "翻译中"
        task.start_time = time.time()
        task.progress = 10
        
        # 加载模型
        model_load(endpoint, base, model, api_key, temperature, rpm)
        task.progress = 20
        
        # 执行翻译
        if choice:
            init_translation, reflect_translation, final_translation = translator_sec(
                endpoint2=endpoint2,
                base2=base2,
                model2=model2,
                api_key2=api_key2,
                source_lang=source_lang,
                target_lang=target_lang,
                source_text=task.content,
                country=country,
                max_tokens=max_tokens,
            )
        else:
            init_translation, reflect_translation, final_translation = translator(
                source_lang=source_lang,
                target_lang=target_lang,
                source_text=task.content,
                country=country,
                max_tokens=max_tokens,
            )
        
        task.init_translation = init_translation
        task.reflect_translation = reflect_translation
        task.final_translation = final_translation
        task.progress = 100
        task.status = "已完成"
        task.end_time = time.time()
        
    except Exception as e:
        task.status = "失败"
        task.error_message = str(e)
        task.progress = 0
        task.end_time = time.time()
    
    return task


def start_batch_translation(
    files,
    output_folder: str,
    endpoint: str, base: str, model: str, api_key: str,
    choice: bool, endpoint2: str, base2: str, model2: str, api_key2: str,
    source_lang: str, target_lang: str, country: str,
    max_tokens: int, temperature: int, rpm: int
):
    """开始批量翻译"""
    global translation_tasks, task_counter
    
    if not files:
        return "❌ 请先上传文件", gr.update(), gr.update()
    
    if not output_folder or not os.path.exists(output_folder):
        # 尝试创建输出文件夹
        try:
            os.makedirs(output_folder, exist_ok=True)
        except:
            return "❌ 请选择有效的输出文件夹", gr.update(), gr.update()
    
    if not source_lang or not target_lang or source_lang == target_lang:
        return "❌ 请检查源语言和目标语言设置", gr.update(), gr.update()
    
    # 读取文件内容
    file_contents = read_uploaded_files(files)
    if not file_contents:
        return "❌ 没有找到可处理的文件内容", gr.update(), gr.update()
    
    # 创建翻译任务
    tasks = []
    for filename, content in file_contents:
        task_counter += 1
        task_id = f"task_{task_counter}"
        task = TranslationTask(task_id, filename, content)
        translation_tasks[task_id] = task
        tasks.append(task)
    
    # 保存配置
    save_config(
        endpoint, model, api_key, base,
        endpoint2, model2, api_key2, base2,
        source_lang, target_lang, country,
        max_tokens, temperature, rpm, choice
    )
    
    # 启动后台翻译线程
    def run_translations():
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TASKS) as executor:
            future_to_task = {
                executor.submit(
                    translate_single_file,
                    task,
                    endpoint, base, model, api_key,
                    choice, endpoint2, base2, model2, api_key2,
                    source_lang, target_lang, country,
                    max_tokens, temperature, rpm
                ): task for task in tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    completed_task = future.result()
                    # 保存翻译结果到文件
                    if completed_task.status == "已完成":
                        save_translation_to_file(completed_task, output_folder)
                except Exception as e:
                    task.status = "失败"
                    task.error_message = str(e)
    
    # 在后台线程中运行翻译
    threading.Thread(target=run_translations, daemon=True).start()
    
    status_msg = f"✅ 已开始翻译 {len(tasks)} 个文件，最大并发数: {MAX_CONCURRENT_TASKS}"
    return status_msg, update_progress_display(), gr.update(visible=True)


def clean_translation_for_novel(translation_text):
    """清理翻译内容，使其适合小说网站阅读
    
    移除AI生成的提示性文字，优化格式
    """
    if not translation_text:
        return ""
    
    # 需要移除的提示性短语列表（中英文）
    ai_markers = [
        "翻译如下：", "翻译如下:", "翻译：", "翻译:",
        "正文如下：", "正文如下:", "正文：", "正文:",
        "Translation:", "Translation as follows:", "TRANSLATION:", "TRANSLATION",
        "Here is the translation:", "Here's the translation:",
        "The translation is:", "Translated text:",
        "以下是翻译：", "以下是翻译:", "以下为翻译：", "以下为翻译:",
        "译文如下：", "译文如下:", "译文：", "译文:",
        "英文翻译：", "英文翻译:", "英译：", "英译:",
        "中文翻译：", "中文翻译:", "中译：", "中译:",
    ]
    
    lines = translation_text.strip().split('\n')
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # 跳过空行（但保留用于段落分隔）
        if not line_stripped:
            cleaned_lines.append('')
            continue
        
        # 检查是否是AI提示性文字（通常在开头几行）
        if i < 3:  # 只检查前3行
            is_marker = False
            for marker in ai_markers:
                if line_stripped.startswith(marker) or line_stripped == marker:
                    is_marker = True
                    print(f"[格式清理] 移除AI标记: {line_stripped}")
                    break
            
            if is_marker:
                continue  # 跳过这一行
        
        # 保留这一行
        cleaned_lines.append(line)
    
    # 重新组合文本
    cleaned_text = '\n'.join(cleaned_lines)
    
    # 移除开头的多余空行
    cleaned_text = cleaned_text.lstrip('\n')
    
    # 确保段落之间有适当的空行（小说格式）
    # 将多个连续空行压缩为最多2个空行
    import re
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    # 移除行尾空格
    cleaned_text = '\n'.join(line.rstrip() for line in cleaned_text.split('\n'))
    
    print(f"[格式清理] 完成，原始长度: {len(translation_text)}, 清理后长度: {len(cleaned_text)}")
    
    return cleaned_text


def save_translation_to_file(task: TranslationTask, output_folder: str):
    """保存翻译结果到文件 - 只输出最终翻译内容"""
    try:
        output_filename = f"{task.filename}_translated.txt"
        output_path = os.path.join(output_folder, output_filename)
        
        # 清理和格式化翻译内容，使其适合小说网站阅读
        cleaned_content = clean_translation_for_novel(task.final_translation)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_content)
        
        print(f"翻译结果已保存到: {output_path}")
        
    except Exception as e:
        print(f"保存文件时出错: {e}")
        task.status = "保存失败"
        task.error_message = f"保存文件时出错: {e}"


def update_progress_display():
    """更新进度显示"""
    if not translation_tasks:
        return gr.update(value="暂无翻译任务", visible=False)
    
    progress_html = """
    <div style="font-family: monospace; background: #f5f5f5; padding: 15px; border-radius: 8px;">
        <h3 style="margin-top: 0; color: #333;">📊 翻译进度</h3>
    """
    
    completed_count = 0
    total_count = len(translation_tasks)
    
    for task_id, task in translation_tasks.items():
        status_color = {
            "等待中": "#ffa500",
            "翻译中": "#007bff", 
            "已完成": "#28a745",
            "失败": "#dc3545",
            "保存失败": "#dc3545"
        }.get(task.status, "#6c757d")
        
        if task.status == "已完成":
            completed_count += 1
        
        # 计算耗时
        elapsed_time = ""
        if task.start_time:
            if task.end_time:
                elapsed = task.end_time - task.start_time
                elapsed_time = f" ({elapsed:.1f}s)"
            else:
                elapsed = time.time() - task.start_time
                elapsed_time = f" ({elapsed:.1f}s)"
        
        progress_html += f"""
        <div style="margin: 8px 0; padding: 8px; background: white; border-radius: 4px; border-left: 4px solid {status_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: bold;">{task.filename}</span>
                <span style="color: {status_color}; font-weight: bold;">{task.status}{elapsed_time}</span>
            </div>
            <div style="margin-top: 4px;">
                <div style="background: #e9ecef; height: 6px; border-radius: 3px; overflow: hidden;">
                    <div style="background: {status_color}; height: 100%; width: {task.progress}%; transition: width 0.3s;"></div>
                </div>
                <small style="color: #666;">进度: {task.progress}%</small>
            </div>
            {f'<div style="color: #dc3545; font-size: 12px; margin-top: 4px;">错误: {task.error_message}</div>' if task.error_message else ''}
        </div>
        """
    
    progress_html += f"""
        <div style="margin-top: 15px; padding: 10px; background: #e3f2fd; border-radius: 4px;">
            <strong>总体进度: {completed_count}/{total_count} 已完成</strong>
        </div>
    </div>
    """
    
    return gr.update(value=progress_html, visible=True)


def clear_all_tasks():
    """清空所有任务"""
    global translation_tasks
    translation_tasks.clear()
    return "✅ 已清空所有任务", gr.update(visible=False)


def enable_sec(choice):
    if choice:
        return gr.update(visible=True)
    else:
        return gr.update(visible=False)


def update_menu(visible):
    return not visible, gr.update(visible=not visible)


TITLE = """
    <div style="display: inline-flex;">
        <div style="margin-left: 6px; font-size:32px; color: #6366f1"><b>翻译助手</b> 本地批量版</div>
    </div>
"""

CSS = """
    h1 {
        text-align: center;
        display: block;
        height: 10vh;
        align-content: center;
    }
    footer {
        visibility: hidden;
    }
    .menu_btn {
        width: 48px;
        height: 48px;
        max-width: 48px;
        min-width: 48px;
        padding: 0px;
        background-color: transparent;
        border: none;
        cursor: pointer;
        position: relative;
        box-shadow: none;
    }
    .menu_btn::before,
    .menu_btn::after {
        content: '';
        position: absolute;
        width: 30px;
        height: 3px;
        background-color: #4f46e5;
        transition: transform 0.3s ease;
    }
    .menu_btn::before {
        top: 12px;
        box-shadow: 0 8px 0 #6366f1;
    }
    .menu_btn::after {
        bottom: 16px;
    }
    .menu_btn.active::before {
        transform: translateY(8px) rotate(45deg);
        box-shadow: none;
    }
    .menu_btn.active::after {
        transform: translateY(-8px) rotate(-45deg);
    }
    .lang {
        max-width: 100px;
        min-width: 100px;
    }
    .progress-container {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        background: #f9f9f9;
    }
"""

JS = """
    function () {
        const menu_btn = document.getElementById('menu');
        menu_btn.classList.toggle('active');
    }
"""

with gr.Blocks(theme="soft", css=CSS, fill_height=True) as demo:
    with gr.Row():
        visible = gr.State(value=True)
        menu_btn = gr.Button(
            value="", elem_classes="menu_btn", elem_id="menu", size="sm"
        )
        gr.HTML(TITLE)
    
    with gr.Row():
        with gr.Column(scale=1) as menubar:
            endpoint = gr.Dropdown(
                label="API端点",
                choices=["OpenAI", "Groq", "TogetherAI", "Ollama", "CUSTOM"],
                value="OpenAI",
            )
            choice = gr.Checkbox(
                label="额外端点",
                info="用于反思步骤的额外端点",
            )
            model = gr.Textbox(
                label="模型",
                value="gpt-4o",
            )
            api_key = gr.Textbox(
                label="API密钥",
                type="password",
            )
            base = gr.Textbox(
                label="基础URL", 
                visible=False,
                placeholder="例如: http://localhost:11434"
            )
            
            with gr.Column(visible=False) as AddEndpoint:
                endpoint2 = gr.Dropdown(
                    label="额外端点",
                    choices=["OpenAI", "Groq", "TogetherAI", "Ollama", "CUSTOM"],
                    value="OpenAI",
                )
                model2 = gr.Textbox(
                    label="模型",
                    value="gpt-4o",
                )
                api_key2 = gr.Textbox(
                    label="API密钥",
                    type="password",
                )
                base2 = gr.Textbox(
                    label="基础URL", 
                    visible=False,
                    placeholder="例如: http://localhost:11434"
                )
            
            with gr.Row():
                source_lang = gr.Textbox(
                    label="源语言",
                    value="Chinese",
                    elem_classes="lang",
                )
                target_lang = gr.Textbox(
                    label="目标语言",
                    value="English",
                    elem_classes="lang",
                )
            
            country = gr.Textbox(
                label="地区", value="United States", max_lines=1
            )
            
            with gr.Accordion("高级选项", open=False):
                max_tokens = gr.Slider(
                    label="每块最大Token数",
                    minimum=512,
                    maximum=2046,
                    value=1000,
                    step=8,
                )
                temperature = gr.Slider(
                    label="温度",
                    minimum=0,
                    maximum=1.0,
                    value=0.3,
                    step=0.1,
                )
                rpm = gr.Slider(
                    label="每分钟请求数",
                    minimum=1,
                    maximum=1000,
                    value=60,
                    step=1,
                )
            
            save_config_btn = gr.Button(value="💾 保存配置", variant="secondary", size="sm")
            config_status = gr.Textbox(
                label="配置状态", 
                visible=True, 
                interactive=False,
                value="配置将自动保存到本地文件",
                lines=1
            )

        with gr.Column(scale=4):
            gr.Markdown("### 📁 批量翻译")
            
            with gr.Row():
                files_upload = gr.File(
                    label="📤 上传多个文件",
                    file_count="multiple",
                    file_types=["text", ".pdf", ".docx", ".txt", ".md", ".py", ".json", ".cpp"]
                )
                output_folder = gr.Textbox(
                    label="📂 输出文件夹",
                    placeholder="选择保存翻译结果的文件夹路径",
                    value=os.path.expanduser("~/Desktop/translations")
                )
            
            with gr.Row():
                start_btn = gr.Button(value="🚀 开始批量翻译", variant="primary", size="lg")
                clear_btn = gr.Button(value="🗑️ 清空任务", variant="secondary")
            
            status_display = gr.Textbox(
                label="状态",
                value="请上传文件并选择输出文件夹",
                interactive=False,
                lines=2
            )
            
            progress_display = gr.HTML(
                value="",
                visible=False,
                elem_classes="progress-container"
            )
    
    # 页面加载时自动加载配置
    demo.load(
        fn=load_config,
        outputs=[
            endpoint, model, api_key, base,
            endpoint2, model2, api_key2, base2,
            source_lang, target_lang, country,
            max_tokens, temperature, rpm, choice,
            config_status, AddEndpoint
        ]
    )
    
    menu_btn.click(
        fn=update_menu, inputs=visible, outputs=[visible, menubar], js=JS
    )
    
    endpoint.change(fn=update_model, inputs=[endpoint, model], outputs=[model, base])
    choice.select(fn=enable_sec, inputs=[choice], outputs=[AddEndpoint])
    endpoint2.change(fn=update_model, inputs=[endpoint2, model2], outputs=[model2, base2])
    
    save_config_btn.click(
        fn=save_config,
        inputs=[
            endpoint, model, api_key, base,
            endpoint2, model2, api_key2, base2,
            source_lang, target_lang, country,
            max_tokens, temperature, rpm, choice
        ],
        outputs=[config_status]
    )
    
    start_btn.click(
        fn=start_batch_translation,
        inputs=[
            files_upload, output_folder,
            endpoint, base, model, api_key,
            choice, endpoint2, base2, model2, api_key2,
            source_lang, target_lang, country,
            max_tokens, temperature, rpm
        ],
        outputs=[status_display, progress_display, progress_display]
    )
    
    clear_btn.click(
        fn=clear_all_tasks,
        outputs=[status_display, progress_display]
    )
    
    # 定时更新进度显示
    demo.load(
        fn=lambda: None,
        every=2,  # 每2秒更新一次
    ).then(
        fn=update_progress_display,
        outputs=[progress_display]
    )


if __name__ == "__main__":
    import os
    import sys
    
    # 禁用 API 信息生成
    os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
    
    # 创建默认输出文件夹
    default_output = os.path.expanduser("~/Desktop/translations")
    os.makedirs(default_output, exist_ok=True)
    
    try:
        demo.queue(api_open=False).launch(
            server_name="127.0.0.1", 
            server_port=7861, 
            share=False, 
            inbrowser=True
        )
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error during launch: {e}")
        print("Trying alternative launch method...")
        try:
            demo.launch(
                server_name="127.0.0.1", 
                server_port=7861, 
                share=False, 
                inbrowser=True
            )
        except Exception as e2:
            print(f"Alternative launch also failed: {e2}")
            sys.exit(1)