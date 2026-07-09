"""Vertex AI (Gemini) access helper — 스트리머 컨설팅 도구 공용.

GCP 프로젝트 결제로 청구되므로 Free Trial 크레딧이 적용된다(AI Studio 선불 키와 다름).
인증은 ADC(gcloud): 최초 1회 `gcloud auth application-default login`. 자세한 셋업은
tools/VERTEX_SETUP.md 참조.

의존성: google-genai (tools/requirements-llm.txt). 없으면 호출 시 안내 예외.

사용:
    from tools.vertex_client import vertex_text, vertex_json
    txt = vertex_text("한 줄 요약해줘: ...")
    obj = vertex_json('아래를 JSON으로: {"label": ...}', model="gemini-3.5-flash")

환경변수(모두 선택):
    VERTEX_PROJECT   기본 "contextwins" (Vertex 활성화 + Free Trial 결제가 붙은 GCP 프로젝트)
    VERTEX_LOCATION  기본 "global"
    VERTEX_MODEL     기본 "gemini-2.5-flash"
"""
from __future__ import annotations

import json
import os
from typing import Any

# GCP 프로젝트 id. 기본값은 Vertex가 활성화되고 Free Trial 크레딧이 붙은 프로젝트.
# 다른 프로젝트를 쓰려면 VERTEX_PROJECT 환경변수로 오버라이드.
DEFAULT_PROJECT = os.environ.get("VERTEX_PROJECT", "contextwins")
DEFAULT_LOCATION = os.environ.get("VERTEX_LOCATION", "global")
DEFAULT_MODEL = os.environ.get("VERTEX_MODEL", "gemini-2.5-flash")

# 실측 교훈: thinking 토큰이 max_output_tokens를 잠식한다. 800으로 두면 응답이 잘려
# 빈 텍스트가 나온다(finish_reason=MAX_TOKENS). 태깅/분류류는 4000 이상 권장.
DEFAULT_MAX_TOKENS = 4000

_client = None


def _get_client():
    """genai Vertex 클라이언트 (프로세스 1회 생성)."""
    global _client
    if _client is None:
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "google-genai가 설치되지 않았습니다. "
                "`pip install -r tools/requirements-llm.txt` 후 재시도하세요."
            ) from exc
        _client = genai.Client(
            vertexai=True, project=DEFAULT_PROJECT, location=DEFAULT_LOCATION
        )
    return _client


def vertex_text(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.0,
    as_json: bool = False,
) -> str:
    """Vertex Gemini 호출 → 응답 텍스트.

    as_json=True면 response_mime_type을 application/json으로 지정한다.
    인증 실패 시 google 예외가 그대로 올라온다(ADC 미설정 등) — VERTEX_SETUP.md 참조.
    """
    from google.genai import types

    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        system_instruction=system or None,
        response_mime_type="application/json" if as_json else None,
    )
    resp = client.models.generate_content(
        model=model or DEFAULT_MODEL, contents=prompt, config=config
    )
    return resp.text or ""


def vertex_json(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.0,
) -> Any:
    """vertex_text(as_json=True) + JSON 파싱. 모델이 앞뒤 텍스트를 붙여도 최외곽
    {..} 또는 [..]를 추출해 파싱한다."""
    text = vertex_text(
        prompt,
        system=system,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        as_json=True,
    )
    return json.loads(_extract_json(text))


def _extract_json(text: str) -> str:
    s_obj, s_arr = text.find("{"), text.find("[")
    starts = [i for i in (s_obj, s_arr) if i != -1]
    if not starts:
        raise ValueError(f"응답에서 JSON을 찾지 못함: {text[:200]!r}")
    start = min(starts)
    close = "}" if text[start] == "{" else "]"
    end = text.rfind(close)
    if end <= start:
        raise ValueError(f"JSON 종료 괄호 없음: {text[:200]!r}")
    return text[start : end + 1]


def list_models(name_filter: str = "gemini") -> list[str]:
    """이 프로젝트로 호출 가능한 모델 id 목록 (기본 gemini 계열만)."""
    client = _get_client()
    out = []
    for m in client.models.list():
        short = (m.name or "").split("/")[-1]
        if name_filter.lower() in short.lower():
            out.append(short)
    return sorted(out)


if __name__ == "__main__":  # 스모크 테스트: python -m tools.vertex_client
    import sys

    try:
        r = vertex_json('Return exactly this JSON and nothing else: {"vertex": "ok"}')
        print(f"OK (project={DEFAULT_PROJECT}, model={DEFAULT_MODEL}):", r)
    except Exception as e:  # noqa: BLE001
        print("FAIL:", type(e).__name__, str(e)[:300])
        sys.exit(1)
