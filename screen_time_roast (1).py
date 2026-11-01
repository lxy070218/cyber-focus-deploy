#!/usr/bin/env python3
"""
任务02：调用兼容 OpenAI 格式的多模态大模型 API，
读取手机屏幕使用时间截图，让"毒舌时间管理教练"嘲讽用户熬夜刷短视频。
默认对接华为云 MaaS；API 调用失败时输出兜底文案，绝不把异常抛给前端。

用法:
    export API_KEY="你的华为云 MaaS API Key"
    python3 screen_time_roast.py <图片路径>

可选环境变量:
    API_KEY            (必填) 大模型 API Key
    MAAS_API_KEY       (备选) API_KEY 未设置时使用
    VL_BASE_URL        (可选) OpenAI 兼容端点，默认华为云 MaaS
    VL_MODEL           (可选) 模型名，默认 deepseek-v4-flash
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://api.modelarts-maas.com/v1"
DEFAULT_MODEL = "deepseek-v4-flash"
PROMPT = (
    "你是一个毒舌的时间管理教练，请根据这张屏幕使用时间截图，"
    "用不超过50字嘲讽一下用户熬夜刷短视频的行为。"
)
FALLBACK = "AI教练暂时离线，但说真的——别刷了，快去睡。"


def get_api_key():
    return os.environ.get("API_KEY") or os.environ.get("MAAS_API_KEY")


def image_to_data_uri(path):
    if not os.path.isfile(path):
        sys.exit(f"错误：图片不存在：{path}")
    mime, _ = mimetypes.guess_type(path)
    if not mime or not mime.startswith("image/"):
        mime = "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def call_vl_model(image_path, prompt, base_url, model, api_key, timeout=30):
    if not api_key:
        raise RuntimeError("未配置 API_KEY / MAAS_API_KEY 环境变量")
    data_uri = image_to_data_uri(image_path)
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_text(result):
    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return json.dumps(result, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="毒舌时间管理教练：嘲讽熬夜刷短视频")
    parser.add_argument("image", help="手机屏幕使用时间截图路径")
    parser.add_argument("--prompt", default=PROMPT, help="自定义 prompt")
    parser.add_argument("--model", default=os.environ.get("VL_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.environ.get("VL_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--timeout", type=float, default=30.0, help="请求超时秒数")
    args = parser.parse_args()

    api_key = get_api_key()
    try:
        result = call_vl_model(args.image, args.prompt, args.base_url, args.model, api_key, args.timeout)
        print(extract_text(result))
    except Exception as e:
        print(f"API调用失败：{e}", file=sys.stderr)
        print(FALLBACK)


if __name__ == "__main__":
    main()
