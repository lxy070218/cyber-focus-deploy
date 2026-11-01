#!/usr/bin/env python3
"""
专注力评语服务：三层降级策略生成每日评语。

generate_comment(stats, image_path):
  第 1 层：调用华为云 MaaS 大模型（OpenAI 兼容格式），模型 deepseek-v4-flash，超时 3 秒。
  第 2 层：第 1 层任意异常（断网、超时、报错）→ 从 5 条毒舌 + 5 条温柔中随机返回一条。
  第 3 层：第 2 层也异常 → 固定兜底文案，绝不把异常抛给前端。

环境变量:
    API_KEY       (必填) 华为云 MaaS API Key
    MAAS_API_KEY  (备选) API_KEY 未设置时使用
    MAAS_BASE_URL (可选) 默认 https://api.modelarts-maas.com/v1
    MAAS_MODEL    (可选) 默认 deepseek-v4-flash
"""

import base64
import json
import mimetypes
import os
import random
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://api.modelarts-maas.com/v1"
DEFAULT_MODEL = "deepseek-v4-flash"
LLM_TIMEOUT = 3

FALLBACK_COMMENT = "今天也辛苦啦，明天继续加油。"

SASSY_COMMENTS = [
    "凌晨还在刷手机，你是和时间有仇吗？",
    "专注5分钟，分心50次，你的意志力是漏勺做的吧。",
    "熬夜冠军非你莫属，黑眼圈都快掉地上了。",
    "说好的再刷5分钟，结果刷到天亮，骗自己挺在行的。",
    "手机比你亲妈还亲，它没你不行，你没它活不了。",
]

GENTLE_COMMENTS = [
    "今天辛苦啦，虽然有点分心，但已经在努力了，明天会更好。",
    "专注不容易，能坚持下来就很棒了，给自己一个拥抱吧。",
    "累了就早点休息，明天醒来又是全新的一天。",
    "每一次专注都是进步，别太苛责自己，慢慢来。",
    "今天也谢谢自己的努力，好好睡一觉，明天继续。",
]


def _get_api_key():
    return os.environ.get("API_KEY") or os.environ.get("MAAS_API_KEY")


def _build_prompt(stats):
    minutes = stats.get("today_minutes", 0)
    distraction = stats.get("distraction_count", 0)
    return (
        "你是一个专注力教练。用户今天专注了 "
        f"{minutes} 分钟，分心 {distraction} 次。"
        "请用一句不超过 30 字的话给出鼓励或建议，不要使用 Markdown。"
    )


def _image_to_data_uri(path):
    if not path or not os.path.isfile(path):
        return None
    mime, _ = mimetypes.guess_type(path)
    if not mime or not mime.startswith("image/"):
        mime = "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _call_llm(stats, image_path):
    """第 1 层：调用大模型。成功返回非空文本，失败抛异常。"""
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("未配置 API_KEY / MAAS_API_KEY 环境变量")

    base_url = os.environ.get("MAAS_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = os.environ.get("MAAS_MODEL", DEFAULT_MODEL)

    content = [{"type": "text", "text": _build_prompt(stats)}]
    data_uri = _image_to_data_uri(image_path)
    if data_uri:
        content.append({"type": "image_url", "image_url": {"url": data_uri}})

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 100,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base_url + "/chat/completions", data=body, headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=LLM_TIMEOUT) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    text = result["choices"][0]["message"]["content"].strip()
    if not text:
        raise RuntimeError("大模型返回空内容")
    return text


def _local_random_comment():
    """第 2 层：从 5 条毒舌 + 5 条温柔中随机返回一条。"""
    return random.choice(SASSY_COMMENTS + GENTLE_COMMENTS)


def generate_comment(stats: dict, image_path=None) -> str:
    """生成每日评语，三层降级，绝不向外抛异常。"""
    try:
        return _call_llm(stats, image_path)
    except Exception:
        print("API调用失败，已触发第2层本地规则降级")
        try:
            return _local_random_comment()
        except Exception:
            return FALLBACK_COMMENT


if __name__ == "__main__":
    stats = {"today_minutes": 25, "distraction_count": 3}
    here = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(here, "..", "sample_screen_time.png")
    image_path = image_path if os.path.isfile(image_path) else None

    print("=== 测试1：默认配置（华为云 MaaS） ===")
    print("stats:", stats, "| image:", image_path)
    print("评语:", generate_comment(stats, image_path))
    print()

    print("=== 测试2：模拟断网（不可达端点 192.0.2.1） ===")
    os.environ["MAAS_BASE_URL"] = "http://192.0.2.1:80/v1"
    print("评语:", generate_comment(stats, image_path))
    del os.environ["MAAS_BASE_URL"]
    print()

    print("=== 测试3：第二层也异常（random 被 monkey-patch 破坏）→ 第三层兜底 ===")
    random.choice = lambda pool: (_ for _ in ()).throw(RuntimeError("随机失败"))
    print("评语:", generate_comment(stats, image_path))
