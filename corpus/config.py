from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = Path(__file__).resolve().parent
DATA_DIR = TOOL_ROOT / "data"

_ENV_PATH = TOOL_ROOT / ".env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value
RAW_DIR = DATA_DIR / "raw"
GATED_DIR = DATA_DIR / "gated"
EXTRACTED_DIR = DATA_DIR / "extracted"
PROGRESS_PATH = DATA_DIR / "progress.ndjson"
ERRORS_PATH = DATA_DIR / "errors.ndjson"

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4.1-mini")
# Vertex AI (provider="vertex"): GCP 프로젝트 결제로 청구 — Free Trial 크레딧 적용됨.
# 인증은 ADC (gcloud auth application-default login).
VERTEX_PROJECT = os.environ.get("VERTEX_PROJECT", "contextwins")
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "global")
VERTEX_MODEL = os.environ.get("VERTEX_MODEL", "gemini-2.5-flash")
LLM_GATE_MODEL = os.environ.get("LLM_GATE_MODEL") or None
LLM_EXTRACT_MODEL = os.environ.get("LLM_EXTRACT_MODEL") or None
LLM_BASE_URL = os.environ.get("LLM_BASE_URL") or None
GOOGLE_CSE_KEY = os.environ.get("GOOGLE_CSE_KEY")
GOOGLE_CSE_CX = os.environ.get("GOOGLE_CSE_CX")
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")


GITHUB_SOURCES: dict[str, dict[str, object]] = {
    "E1": {
        "name": "f/awesome-chatgpt-prompts",
        "owner": "f",
        "repo": "awesome-chatgpt-prompts",
        "parser": "e1_act_sections",
        "target_models": ["chatgpt"],
    },
    "E2": {
        "name": "ai-boost/awesome-prompts",
        "owner": "ai-boost",
        "repo": "awesome-prompts",
        "parser": "file_per_prompt",
        "target_models": ["chatgpt", "generic"],
    },
    "E3": {
        "name": "promptslab/awesome-prompt-engineering",
        "owner": "promptslab",
        "repo": "awesome-prompt-engineering",
        "parser": "markdown_prompt_blocks",
        "target_models": ["generic"],
    },
    "E4": {
        "name": "aminblm/awesome-chatgpt-content-creation-prompts",
        "owner": "aminblm",
        "repo": "awesome-chatgpt-content-creation-prompts",
        "parser": "markdown_prompt_blocks",
        "target_models": ["chatgpt"],
    },
}


def github_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def openai_api_key() -> str | None:
    return os.environ.get("OPENAI_API_KEY")


def serper_api_key() -> str | None:
    return os.environ.get("SERPER_API_KEY")


def anthropic_api_key() -> str | None:
    return os.environ.get("ANTHROPIC_API_KEY")


def configured_anthropic_model() -> str:
    return os.environ.get("LLM_MODEL") or os.environ.get("ANTHROPIC_MODEL") or "claude-3-5-haiku-latest"


def google_cse_credentials() -> tuple[str, str]:
    if not GOOGLE_CSE_KEY:
        raise RuntimeError("GOOGLE_CSE_KEY is missing")
    if not GOOGLE_CSE_CX:
        raise RuntimeError("GOOGLE_CSE_CX is missing")
    return GOOGLE_CSE_KEY, GOOGLE_CSE_CX


def naver_credentials() -> tuple[str, str]:
    if not NAVER_CLIENT_ID:
        raise RuntimeError("NAVER_CLIENT_ID is missing")
    if not NAVER_CLIENT_SECRET:
        raise RuntimeError("NAVER_CLIENT_SECRET is missing")
    return NAVER_CLIENT_ID, NAVER_CLIENT_SECRET


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    GATED_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
