from __future__ import annotations

import base64
import json
import urllib.request
from typing import Any

try:
    from .config import anthropic_api_key, openai_api_key
except ImportError:
    from config import anthropic_api_key, openai_api_key

PREFILTER_MODEL = "gpt-4o-mini"
EXTRACT_MODEL = "gpt-4o"

PREFILTER_PROMPT = (
    "이 이미지에 AI/LLM 프롬프트 텍스트, ChatGPT 대화 스크린샷, "
    "또는 복사 가능한 프롬프트가 포함되어 있는가? "
    'JSON으로만 응답: {"has_prompt": true/false}'
)

EXTRACT_PROMPT = """이 이미지에서 AI/LLM 프롬프트 텍스트를 추출하라.

규칙:
- UI 요소(버튼, 메뉴, 타임스탬프, 좋아요, 프로필)는 제외
- 프롬프트 본문만 추출
- 여러 프롬프트가 있으면 ---로 구분
- 프롬프트가 없으면 빈 문자열 반환

추출된 프롬프트 텍스트만 출력하라. 설명 없이."""


def _download_image(url: str, timeout: int = 15) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        if "png" in content_type:
            media_type = "image/png"
        elif "webp" in content_type:
            media_type = "image/webp"
        elif "gif" in content_type:
            media_type = "image/gif"
        else:
            media_type = "image/jpeg"
    return data, media_type


def _openai_vision_call(image_data: bytes, media_type: str, prompt: str, *, model: str, max_tokens: int = 300, detail: str = "auto") -> str:
    api_key = openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise RuntimeError("openai package is not installed") from exc

    client = OpenAI(api_key=api_key)
    b64 = base64.b64encode(image_data).decode("ascii")
    data_url = f"data:{media_type};base64,{b64}"
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url, "detail": detail}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return response.choices[0].message.content or ""


def _anthropic_vision_call(image_data: bytes, media_type: str, prompt: str, *, model: str, max_tokens: int = 2000) -> str:
    api_key = anthropic_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is missing")
    try:
        import anthropic  # type: ignore
    except ImportError as exc:
        raise RuntimeError("anthropic package is not installed") from exc

    client = anthropic.Anthropic(api_key=api_key)
    b64 = base64.b64encode(image_data).decode("ascii")
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": b64},
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return "".join(block.text for block in message.content if getattr(block, "type", None) == "text")


def prefilter_image(image_url: str) -> bool:
    try:
        data, media_type = _download_image(image_url)
    except Exception:
        return False
    if len(data) < 10_000:
        return False
    try:
        result = _openai_vision_call(data, media_type, PREFILTER_PROMPT, model=PREFILTER_MODEL, max_tokens=80, detail="low")
        parsed = json.loads(result[result.find("{"):result.rfind("}") + 1])
        return bool(parsed.get("has_prompt"))
    except Exception:
        return False


def extract_prompt_from_image(image_url: str) -> str:
    data, media_type = _download_image(image_url)
    result = _openai_vision_call(data, media_type, EXTRACT_PROMPT, model=EXTRACT_MODEL, max_tokens=2000, detail="high")
    return result.strip()


def ocr_threads_images(image_urls: list[str], *, max_images: int = 10) -> list[str]:
    extracted: list[str] = []
    checked = 0
    for url in image_urls:
        if checked >= max_images:
            break
        checked += 1
        if prefilter_image(url):
            try:
                text = extract_prompt_from_image(url)
                if text and len(text) > 20:
                    extracted.append(text)
            except Exception:
                continue
    return extracted
