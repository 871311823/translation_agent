import os
import re
import json
from glob import glob
from pathlib import Path

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

# 保存上传的文件名（用于下载时命名）
uploaded_filename = None

# 标志：是否正在加载配置（防止 endpoint.change 覆盖模型名）
is_loading_config = False


def huanik(
    endpoint: str,
    base: str,
    model: str,
    api_key: str,
    choice: str,
    endpoint2: str,
    base2: str,
    model2: str,
    api_key2: str,
    source_lang: str,
    target_lang: str,
    source_text: str,
    country: str,
    max_tokens: int,
    temperature: int,
    rpm: int,
):
    if not source_text or source_lang == target_lang:
        raise gr.Error(
            "请检查内容或选项是否正确输入。"
        )

    try:
        model_load(endpoint, base, model, api_key, temperature, rpm)
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "Not Found" in error_msg:
            raise gr.Error(f"API端点配置错误 (404): 请检查基础URL和模型名称是否正确。错误详情: {e}") from e
        elif "401" in error_msg or "Unauthorized" in error_msg:
            raise gr.Error(f"API密钥无效 (401): 请检查API密钥是否正确。错误详情: {e}") from e
        else:
            raise gr.Error(f"模型加载失败: {e}") from e

    source_text = re.sub(r"(?m)^\s*$\n?", "", source_text)

    if choice:
        init_translation, reflect_translation, final_translation = (
            translator_sec(
                endpoint2=endpoint2,
                base2=base2,
                model2=model2,
                api_key2=api_key2,
                source_lang=source_lang,
                target_lang=target_lang,
                source_text=source_text,
                country=country,
                max_tokens=max_tokens,
            )
        )

    else:
        init_translation, reflect_translation, final_translation = translator(
            source_lang=source_lang,
            target_lang=target_lang,
            source_text=source_text,
            country=country,
            max_tokens=max_tokens,
        )

    final_diff = gr.HighlightedText(
        diff_texts(init_translation, final_translation),
        label="翻译差异对比",
        combine_adjacent=True,
        show_legend=True,
        visible=True,
        color_map={"removed": "red", "added": "green"},
    )
    
    # 翻译成功后自动保存配置
    save_config(
        endpoint, model, api_key, base,
        endpoint2, model2, api_key2, base2,
        source_lang, target_lang, country,
        max_tokens, temperature, rpm, choice
    )

    return init_translation, reflect_translation, final_translation, final_diff


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
            "api_key": api_key,  # 注意：密码字段也会保存
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
        return gr.update(value=f"✅ 配置已保存到: {CONFIG_FILE}", visible=True)
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
                # 如果值为空字符串、None 或不存在，使用默认值
                # 否则返回实际值（包括自定义模型名如 gemini-3-flash-preview）
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
    # 返回默认值
    is_loading_config = False
    return (
        "OpenAI", "gpt-4o", "", gr.update(value="", visible=False),
        "OpenAI", "gpt-4o", "", gr.update(value="", visible=False),
        "Chinese", "English", "United States",
        1000, 0.3, 60, False,
        gr.update(value="使用默认配置（未找到历史配置）", visible=True),
        gr.update(visible=False),
    )


def update_model(endpoint, current_model=None):
    """更新模型名，但保留已设置的自定义模型名"""
    global is_loading_config
    
    endpoint_model_map = {
        "Groq": "llama3-70b-8192",
        "OpenAI": "gpt-4o",
        "TogetherAI": "Qwen/Qwen2-72B-Instruct",
        "Ollama": "llama3",
        "CUSTOM": "",
    }
    
    default_model = endpoint_model_map.get(endpoint, "")
    
    # 如果正在加载配置，不更新模型名（保持加载的值）
    if is_loading_config:
        model_update = gr.update()  # 不更新，保持当前值
    # 如果当前模型名存在且不是默认值，保留它（说明是用户自定义的模型名）
    elif current_model and current_model.strip() and current_model != default_model:
        # 保留自定义模型名（如 gemini-3-flash-preview）
        model_update = gr.update()  # 不更新，保持当前值
    else:
        # 使用默认模型名（仅在用户主动更改端点时）
        model_update = gr.update(value=default_model)
    
    if endpoint == "CUSTOM":
        base = gr.update(visible=True, placeholder="例如: http://localhost:11434 或 http://api.example.com (会自动添加/v1后缀)")
    else:
        base = gr.update(visible=False)
    
    return model_update, base


def read_doc(path):
    global uploaded_filename
    
    if not path:
        raise gr.Error("文件路径为空，请重新上传文件。")
    
    # 处理文件路径，支持 Gradio 文件对象
    if isinstance(path, str):
        file_path = path
    else:
        # Gradio 上传的文件对象
        file_path = path.name if hasattr(path, 'name') else str(path)
    
    if not file_path or not os.path.exists(file_path):
        raise gr.Error("文件不存在，请重新上传文件。")
    
    # 保存原始文件名（用于下载时命名）
    original_filename = os.path.basename(file_path)
    # 提取文件名（不含扩展名）并转换为英文名（简单处理：移除特殊字符，保留字母数字和连字符）
    name_without_ext = os.path.splitext(original_filename)[0]
    # 将中文等非ASCII字符转换为拼音或使用通用名称，这里简化处理为 "translated"
    # 如果文件名已经是英文，则保留；否则使用 "translated"
    english_name = re.sub(r'[^\w\-]', '_', name_without_ext)
    if not english_name or not re.match(r'^[a-zA-Z]', english_name):
        english_name = "translated"
    uploaded_filename = english_name
    
    # 安全地提取文件扩展名
    if "." not in os.path.basename(file_path):
        raise gr.Error("文件没有扩展名，无法识别文件类型。")
    
    file_type = os.path.splitext(file_path)[1][1:].lower()  # 移除点号并转为小写
    print(f"文件类型: {file_type}, 保存的文件名: {uploaded_filename}")
    
    if file_type in ["pdf", "txt", "py", "docx", "json", "cpp", "md"]:
        if file_type == "pdf":
            content = extract_pdf(file_path)
        elif file_type == "docx":
            content = extract_docx(file_path)
        else:
            content = extract_text(file_path)
        return re.sub(r"(?m)^\s*$\n?", "", content)
    else:
        raise gr.Error(f"抱歉，不支持该文件类型: {file_type}")


def enable_sec(choice):
    if choice:
        return gr.update(visible=True)
    else:
        return gr.update(visible=False)


def update_menu(visible):
    return not visible, gr.update(visible=not visible)


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


def export_txt(translation_text):
    """导出翻译结果为txt文件"""
    global uploaded_filename
    
    if not translation_text:
        return gr.update(visible=False)
    
    # 清理和格式化翻译内容，使其适合小说网站阅读
    cleaned_text = clean_translation_for_novel(translation_text)
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    # 使用上传的文件名（如果存在），否则使用默认名称
    if uploaded_filename:
        filename = f"{uploaded_filename}.txt"
    else:
        base_count = len(glob(os.path.join(output_dir, "*.txt")))
        filename = f"translated_{base_count:06d}.txt"
    
    file_path = os.path.join(output_dir, filename)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
        return gr.update(value=file_path, visible=True, label="📥 下载翻译结果")
    except Exception as e:
        print(f"导出文件时出错: {e}")
        return gr.update(visible=False)


def switch(source_lang, source_text, target_lang, output_final):
    if output_final:
        return (
            gr.update(value=target_lang),
            gr.update(value=output_final),
            gr.update(value=source_lang),
            gr.update(value=source_text),
        )
    else:
        return (
            gr.update(value=target_lang),
            gr.update(value=source_text),
            gr.update(value=source_lang),
            gr.update(value=""),
        )


def close_btn_show():
    return gr.update(visible=False), gr.update(visible=True)


def close_btn_hide(output_diff):
    if output_diff:
        return gr.update(visible=True), gr.update(visible=False)
    else:
        return gr.update(visible=False), gr.update(visible=True)


TITLE = """
    <div style="display: inline-flex;">
        <div style="margin-left: 6px; font-size:32px; color: #6366f1"><b>翻译助手</b> WebUI</div>
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
    /* 结果区域美化 */
    #result_panel {
        border: 1px solid #2f3350;
        border-radius: 10px;
        padding: 12px;
        background-color: #0d0f1a;
        box-shadow: 0 6px 16px rgba(0,0,0,0.35);
    }
    #result_panel .tab-nav {
        margin-bottom: 6px;
    }
    #result_panel textarea {
        min-height: 260px;
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
                placeholder="例如: http://localhost:11434 或 http://api.example.com (会自动添加/v1后缀)"
            )
            with gr.Column(visible=False) as AddEndpoint:
                endpoint2 = gr.Dropdown(
                    label="额外端点",
                    choices=[
                        "OpenAI",
                        "Groq",
                        "TogetherAI",
                        "Ollama",
                        "CUSTOM",
                    ],
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
                    placeholder="例如: http://localhost:11434 或 http://api.example.com (会自动添加/v1后缀)"
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
            switch_btn = gr.Button(value="🔄️")
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

        with gr.Column(scale=4, elem_id="result_panel"):
            gr.Markdown("### 结果区域")
            source_text = gr.Textbox(
                label="源文本",
                value="",
                lines=12,
            )
            with gr.Tab("最终翻译"):
                output_final = gr.Textbox(
                    label="最终翻译", lines=14
                )
            with gr.Tab("初始翻译"):
                output_init = gr.Textbox(
                    label="初始翻译", lines=14
                )
            with gr.Tab("反思建议"):
                output_reflect = gr.Textbox(
                    label="反思建议", lines=14
                )
            with gr.Tab("差异对比"):
                output_diff = gr.HighlightedText(visible=False)
    with gr.Row():
        submit = gr.Button(value="翻译")
        upload = gr.UploadButton(label="上传文件", file_types=["text"])
        export = gr.DownloadButton(label="📥 下载翻译结果", visible=False)
        clear = gr.ClearButton(
            [source_text, output_init, output_reflect, output_final]
        )
        close = gr.Button(value="停止", visible=False)

    switch_btn.click(
        fn=switch,
        inputs=[source_lang, source_text, target_lang, output_final],
        outputs=[source_lang, source_text, target_lang, output_final],
    )

    menu_btn.click(
        fn=update_menu, inputs=visible, outputs=[visible, menubar], js=JS
    )
    # 页面加载时自动加载配置（必须在 endpoint.change 之前）
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
    
    endpoint.change(fn=update_model, inputs=[endpoint, model], outputs=[model, base])

    choice.select(fn=enable_sec, inputs=[choice], outputs=[AddEndpoint])
    endpoint2.change(
        fn=update_model, inputs=[endpoint2, model2], outputs=[model2, base2]
    )
    
    # 保存配置按钮
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

    start_ta = submit.click(
        fn=huanik,
        inputs=[
            endpoint,
            base,
            model,
            api_key,
            choice,
            endpoint2,
            base2,
            model2,
            api_key2,
            source_lang,
            target_lang,
            source_text,
            country,
            max_tokens,
            temperature,
            rpm,
        ],
        outputs=[output_init, output_reflect, output_final, output_diff],
    )
    upload.upload(fn=read_doc, inputs=upload, outputs=source_text)
    
    # 绑定下载功能到最终翻译结果
    def update_download_button(final_translation):
        """更新下载按钮的可见性和文件路径"""
        if final_translation:
            return export_txt(final_translation)
        return gr.update(visible=False)
    
    output_final.change(fn=update_download_button, inputs=output_final, outputs=[export])

    submit.click(fn=close_btn_show, outputs=[clear, close])
    output_diff.change(
        fn=close_btn_hide, inputs=output_diff, outputs=[clear, close]
    )
    close.click(fn=None, cancels=start_ta)

if __name__ == "__main__":
    import os
    import sys
    # 禁用 API 信息生成以避免 gradio-client bug
    os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
    try:
        demo.queue(api_open=False).launch(server_name="0.0.0.0", server_port=7860, show_api=False, share=True, inbrowser=False)
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error during launch: {e}")
        print("Trying alternative launch method...")
        # 尝试不使用 queue 和 share
        try:
            demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False, share=False, inbrowser=False)
        except Exception as e2:
            print(f"Alternative launch also failed: {e2}")
            sys.exit(1)
