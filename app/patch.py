import os
import time
from functools import wraps
from threading import Lock
from typing import Optional, Union

import gradio as gr
import openai
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import translation_agent.utils as utils


RPM = 60
MODEL = ""
TEMPERATURE = 0.3
# Hide js_mode in UI now, update in plan.
JS_MODE = False
ENDPOINT = ""


# Add your LLMs here
def model_load(
    endpoint: str,
    base_url: str,
    model: str,
    api_key: Optional[str] = None,
    temperature: float = TEMPERATURE,
    rpm: int = RPM,
    js_mode: bool = JS_MODE,
):
    global client, RPM, MODEL, TEMPERATURE, JS_MODE, ENDPOINT
    ENDPOINT = endpoint
    RPM = rpm
    MODEL = model
    TEMPERATURE = temperature
    JS_MODE = js_mode

    if endpoint == "OpenAI":
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    elif endpoint == "Groq":
        client = openai.OpenAI(
            api_key=api_key if api_key else os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        )
    elif endpoint == "TogetherAI":
        client = openai.OpenAI(
            api_key=api_key if api_key else os.getenv("TOGETHER_API_KEY"),
            base_url="https://api.together.xyz/v1",
        )
    elif endpoint == "CUSTOM":
        if not base_url:
            raise ValueError("CUSTOM端点需要提供基础URL")
        if not api_key:
            raise ValueError("CUSTOM端点需要提供API密钥")
        # 确保base_url以/v1结尾（OpenAI兼容格式）
        base_url = base_url.strip()
        if not base_url.endswith("/v1"):
            if base_url.endswith("/"):
                base_url = base_url + "v1"
            else:
                base_url = base_url + "/v1"
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
    elif endpoint == "Ollama":
        client = openai.OpenAI(
            api_key="ollama", base_url="http://localhost:11434/v1"
        )
    else:
        client = openai.OpenAI(
            api_key=api_key if api_key else os.getenv("OPENAI_API_KEY")
        )


def rate_limit(get_max_per_minute):
    def decorator(func):
        lock = Lock()
        last_called = [0.0]

        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                max_per_minute = get_max_per_minute()
                min_interval = 60.0 / max_per_minute
                elapsed = time.time() - last_called[0]
                left_to_wait = min_interval - elapsed

                if left_to_wait > 0:
                    time.sleep(left_to_wait)

                ret = func(*args, **kwargs)
                last_called[0] = time.time()
                return ret

        return wrapper

    return decorator


@rate_limit(lambda: RPM)
def get_completion(
    prompt: str,
    system_message: str = "You are a helpful assistant.",
    model: str = "gpt-4-turbo",
    temperature: float = 0.3,
    json_mode: bool = False,
) -> Union[str, dict]:
    """
        Generate a completion using the OpenAI API with reasonable timeout control.

    Args:
        prompt (str): The user's prompt or query.
        system_message (str, optional): The system message to set the context for the assistant.
            Defaults to "You are a helpful assistant.".
        model (str, optional): The name of the OpenAI model to use for generating the completion.
            Defaults to "gpt-4-turbo".
        temperature (float, optional): The sampling temperature for controlling the randomness of the generated text.
            Defaults to 0.3.
        json_mode (bool, optional): Whether to return the response in JSON format.
            Defaults to False.

    Returns:
        Union[str, dict]: The generated completion.
            If json_mode is True, returns the complete API response as a dictionary.
            If json_mode is False, returns the generated text as a string.
    """

    model = MODEL
    temperature = TEMPERATURE
    json_mode = JS_MODE

    # 设置合理的超时时间：根据提示长度调整，但不要过于严格
    prompt_length = len(prompt)
    if prompt_length < 2000:
        timeout_seconds = 300  # 短提示5分钟
    elif prompt_length < 8000:
        timeout_seconds = 600  # 中等提示10分钟
    else:
        timeout_seconds = 900  # 长提示15分钟

    if json_mode:
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                top_p=1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                timeout=timeout_seconds  # 添加超时控制
            )
            if not response.choices or len(response.choices) == 0:
                raise gr.Error("API返回空响应: 模型未返回任何内容")
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                raise gr.Error(f"API请求超时 ({timeout_seconds//60}分钟): 请检查网络连接或尝试减少文本长度。错误详情: {e}") from e
            elif "404" in error_msg or "Not Found" in error_msg:
                raise gr.Error(f"API端点或模型不存在 (404): 请检查基础URL和模型名称是否正确。错误详情: {e}") from e
            elif "401" in error_msg or "Unauthorized" in error_msg:
                raise gr.Error(f"API密钥无效 (401): 请检查API密钥是否正确。错误详情: {e}") from e
            elif "429" in error_msg:
                raise gr.Error(f"请求过于频繁 (429): 请稍后再试或降低请求频率。错误详情: {e}") from e
            elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                raise gr.Error(f"服务器错误 ({error_msg}): API服务器暂时不可用，请稍后重试。") from e
            else:
                raise gr.Error(f"发生意外错误: {e}") from e
    else:
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                top_p=1,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                timeout=timeout_seconds  # 添加超时控制
            )
            if not response.choices or len(response.choices) == 0:
                raise gr.Error("API返回空响应: 模型未返回任何内容")
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                raise gr.Error(f"API请求超时 ({timeout_seconds//60}分钟): 请检查网络连接或尝试减少文本长度。错误详情: {e}") from e
            elif "404" in error_msg or "Not Found" in error_msg:
                raise gr.Error(f"API端点或模型不存在 (404): 请检查基础URL和模型名称是否正确。错误详情: {e}") from e
            elif "401" in error_msg or "Unauthorized" in error_msg:
                raise gr.Error(f"API密钥无效 (401): 请检查API密钥是否正确。错误详情: {e}") from e
            elif "429" in error_msg:
                raise gr.Error(f"请求过于频繁 (429): 请稍后再试或降低请求频率。错误详情: {e}") from e
            elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                raise gr.Error(f"服务器错误 ({error_msg}): API服务器暂时不可用，请稍后重试。") from e
            else:
                raise gr.Error(f"发生意外错误: {e}") from e


utils.get_completion = get_completion

one_chunk_initial_translation = utils.one_chunk_initial_translation
one_chunk_reflect_on_translation = utils.one_chunk_reflect_on_translation
one_chunk_improve_translation = utils.one_chunk_improve_translation
one_chunk_translate_text = utils.one_chunk_translate_text
num_tokens_in_string = utils.num_tokens_in_string
multichunk_initial_translation = utils.multichunk_initial_translation
multichunk_reflect_on_translation = utils.multichunk_reflect_on_translation
multichunk_improve_translation = utils.multichunk_improve_translation
multichunk_translation = utils.multichunk_translation
calculate_chunk_size = utils.calculate_chunk_size
