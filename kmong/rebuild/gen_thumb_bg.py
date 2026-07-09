# -*- coding: utf-8 -*-
"""크몽 썸네일 v2 배경 생성 — 기존 이미지 문법 계승 (Gemini via Vertex).

한글 타이포는 HTML 오버레이로 얹으므로 배경에는 텍스트 금지 (영문 마이크로 라벨만 허용).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "consulting"))
from tools.vertex_client import vertex_image  # noqa: E402

HERE = Path(__file__).parent
REF = HERE.parent / "thumbnail1.png"

PROMPT = """Recreate the visual style of the reference image as a BACKGROUND-ONLY design, 4:3 aspect.

Keep from the reference:
- Very dark navy background (#0a0e15), subtle vignette
- Neon green (#37f383) as the single accent color, white/gray for secondary
- Right side: a clean dark UI panel (rounded corners, thin border) showing a ranking table with columns RANK / CHANNEL / AVG VIEWER, 6-7 rows of placeholder bars (no readable channel names, use soft gray horizontal bars as fake text), one row highlighted with a neon green outline and a green dot
- Below the table inside the panel: a small ascending sparkline chart in gray with the last point glowing neon green, labeled tiny "TREND" in English
- Flat, modern SaaS dashboard aesthetic, crisp vector look, no photorealism, no people, no characters

Change from the reference:
- REMOVE all large Korean headline text: the entire LEFT 55% of the canvas must be empty dark background (just the vignette), reserved for text overlay later
- REMOVE the bottom green outlined button/bar completely: bottom 18% must be empty dark background
- No Korean characters anywhere. Only tiny English UI micro-labels (RANK, CHANNEL, AVG VIEWER, TREND) are allowed
- Add a very subtle dot-grid texture in the empty left area, barely visible

High resolution, sharp edges, professional."""

out = vertex_image(PROMPT, str(HERE / "thumb_bg_v2.png"), aspect_ratio="4:3",
                   reference_images=[str(REF)])
print("saved:", out)
