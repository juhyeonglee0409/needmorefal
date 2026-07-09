# -*- coding: utf-8 -*-
"""크몽 썸네일 v3 — gemini-3-pro-image 원샷 생성 (한글 타이포 포함, 분업 없음)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "consulting"))
from tools.vertex_client import vertex_image  # noqa: E402

HERE = Path(__file__).parent
REF = HERE.parent / "thumbnail1.png"

PROMPT = """레퍼런스 이미지와 동일한 디자인 언어로 크몽 서비스 썸네일을 새로 만들어줘. 4:3 비율.

디자인 언어 (레퍼런스 유지):
- 매우 어두운 네이비 배경 (#0a0e15), 은은한 비네트
- 네온 그린 (#37f383) 단일 강조색, 흰색/회색 보조
- 좌측: 대형 한글 헤드라인 (자간 좁은 굵은 고딕), 일부 단어만 네온 그린
- 우측: 다크 UI 패널 — RANK / CHANNEL / AVG VIEWER 컬럼의 랭킹 테이블,
  "내 채널" 행 하나만 네온 그린 테두리 + 그린 도트로 하이라이트,
  패널 하단에 우상향 스파크라인 차트 (마지막 점만 그린 글로우)
- 하단: 가로로 긴 네온 그린 아웃라인 박스 버튼
- 플랫한 모던 SaaS 대시보드 감성, 벡터 스타일, 사진/인물/캐릭터 없음

텍스트 (모든 한글은 정확히 이대로, 오탈자 절대 금지):
- 좌상단 로고 (모노스페이스): needmorefal  ("fal" 부분만 그린)
- 좌측 헤드라인 3줄:
  제 채널,        ("채널"만 그린)
  성장 중         ("성장"만 그린)
  인 거 맞죠?
- 헤드라인 아래 서브 카피 (회색, 작게): 치지직 버튜버 전수 7,400개 채널과 비교
- 우측 랭킹 테이블: 헤더 RANK | CHANNEL | AVG VIEWER
  행들: 01 채널A 1,286 / 02 채널B 1,143 / 03 채널C 1,032 / ··· /
  [그린 하이라이트 행] 27 내 채널 ● 612 / 28 채널D 598 / 29 채널E 543 / ···
  테이블 아래 작은 라벨: AVG VIEWER TREND + 스파크라인
- 하단 그린 아웃라인 버튼 안 텍스트 (크고 굵게, 그린): 버튜버 채널 컨설팅
- 좌하단 마이크로 카피 (모노스페이스, 회백색): DATA READING REPORT

고해상도, 선명한 텍스트 엣지, 전문적인 마감."""

out = vertex_image(PROMPT, str(HERE / "thumbnail_v3.png"),
                   model="gemini-3-pro-image", aspect_ratio="4:3",
                   reference_images=[str(REF)])
print("saved:", out)
