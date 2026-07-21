from __future__ import annotations

import json
from typing import Any, Literal

try:
    from .config import (
        LLM_BASE_URL,
        LLM_EXTRACT_MODEL,
        LLM_GATE_MODEL,
        LLM_MODEL,
        LLM_PROVIDER,
        VERTEX_LOCATION,
        VERTEX_MODEL,
        VERTEX_PROJECT,
        anthropic_api_key,
        configured_anthropic_model,
        openai_api_key,
    )
except ImportError:  # pragma: no cover - direct script execution fallback.
    from config import (
        LLM_BASE_URL,
        LLM_EXTRACT_MODEL,
        LLM_GATE_MODEL,
        LLM_MODEL,
        LLM_PROVIDER,
        VERTEX_LOCATION,
        VERTEX_MODEL,
        VERTEX_PROJECT,
        anthropic_api_key,
        configured_anthropic_model,
        openai_api_key,
    )


Provider = Literal["openai", "anthropic"]


def llm_complete(
    *,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 800,
    provider: str | None = None,
    response_format: Literal["json_object"] | None = "json_object",
    model_override: str | None = None,
) -> str:
    selected = (provider or LLM_PROVIDER).lower()
    if selected == "openai":
        return openai_complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            response_format=response_format,
            model_override=model_override,
        )
    if selected == "anthropic":
        return anthropic_complete(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=max_tokens, model_override=model_override)
    if selected == "vertex":
        return vertex_complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            response_format=response_format,
            model_override=model_override,
        )
    raise RuntimeError(f"unsupported LLM_PROVIDER: {selected}")


def llm_json_object(*, system_prompt: str, user_prompt: str, max_tokens: int = 800, provider: str | None = None, model_override: str | None = None) -> dict[str, Any]:
    text = llm_complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        provider=provider,
        response_format="json_object",
        model_override=model_override,
    )
    parsed = json.loads(extract_json_object(text))
    if not isinstance(parsed, dict):
        raise ValueError("LLM response is not a JSON object")
    return parsed


def llm_json_array(*, system_prompt: str, user_prompt: str, max_tokens: int = 1600, provider: str | None = None, model_override: str | None = None) -> list[Any]:
    text = llm_complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        provider=provider,
        response_format=None,
        model_override=model_override,
    )
    parsed = json.loads(extract_json_array(text))
    if not isinstance(parsed, list):
        raise ValueError("LLM response is not a JSON array")
    return parsed


def openai_complete(
    *,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    response_format: Literal["json_object"] | None,
    model_override: str | None = None,
) -> str:
    api_key = openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise RuntimeError("openai package is not installed") from exc

    client_kwargs: dict[str, Any] = {"api_key": api_key}
    if LLM_BASE_URL:
        client_kwargs["base_url"] = LLM_BASE_URL
    client = OpenAI(**client_kwargs)
    kwargs: dict[str, Any] = {
        "model": model_override or LLM_MODEL,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if response_format:
        kwargs["response_format"] = {"type": response_format}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


def anthropic_complete(*, system_prompt: str, user_prompt: str, max_tokens: int, model_override: str | None = None) -> str:
    api_key = anthropic_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is missing")
    try:
        import anthropic  # type: ignore
    except ImportError as exc:
        raise RuntimeError("anthropic package is not installed") from exc

    client = anthropic.Anthropic(api_key=api_key)
    model = model_override or configured_anthropic_model()
    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    # claude-sonnet-5 이후 temperature 폐기 — 구세대 모델에만 전달
    if not (model.startswith("claude-sonnet-5") or model.startswith("claude-opus-4-8") or model.startswith("claude-fable")):
        kwargs["temperature"] = 0
    if system_prompt:
        kwargs["system"] = system_prompt
    message = client.messages.create(**kwargs)
    return "".join(block.text for block in message.content if getattr(block, "type", None) == "text")


def vertex_complete(
    *,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    response_format: Literal["json_object"] | None = "json_object",
    model_override: str | None = None,
) -> str:
    """Vertex AI 경유 Gemini 호출 — GCP 프로젝트 결제(Free Trial 크레딧 적용).

    인증: ADC. 최초 1회 `gcloud auth application-default login` 필요.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("google-genai package is not installed") from exc

    client = genai.Client(vertexai=True, project=VERTEX_PROJECT, location=VERTEX_LOCATION)
    config = types.GenerateContentConfig(
        temperature=0,
        max_output_tokens=max_tokens,
        system_instruction=system_prompt or None,
        response_mime_type="application/json" if response_format == "json_object" else None,
    )
    response = client.models.generate_content(
        model=model_override or VERTEX_MODEL,
        contents=user_prompt,
        config=config,
    )
    return response.text or ""


def extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found")
    return text[start : end + 1]


def extract_json_array(text: str) -> str:
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON array found")
    return text[start : end + 1]
