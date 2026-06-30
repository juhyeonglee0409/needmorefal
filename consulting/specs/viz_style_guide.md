# 시각화 스타일 가이드 v2

> 이 문서는 스트리머 컨설팅 보고서의 모든 시각화에 적용되는 디자인 표준이다.
> 컨설팅 보고서 베스트 프랙티스(McKinsey/Bain 레퍼런스) + 기존 보고서 톤을 기반으로 도출.
> needmorefal.com 브랜드는 참조 수준이며, 보고서 메인 팔레트에는 적용하지 않는다.

---

## 1. 디자인 원칙

1. **액션 타이틀**: 모든 차트에 결론 문장을 제목으로 붙인다. "코호트 분포"가 아니라 "구비바는 잔류율 상위 14%에 위치한다"
2. **최소 장식**: 그리드라인, 테두리, 장식을 최소화. 데이터 잉크 비율을 최대화
3. **일관된 색상 매핑**: 같은 의미에 같은 색. SUBJECT는 항상 teal, 코호트는 항상 slate gray
4. **라이트 테마 기본**: 클라이언트 보고서는 화이트 베이스가 기본. 다크 테마는 웹 대시보드 전용 옵션
5. **한글 우선**: 모든 라벨, 축 이름, 범례를 한글로

---

## 2. 컬러 팔레트

### 2.1 시맨틱 컬러 (역할별 고정)

> 개인 브랜드 디자인 토큰(design_tokens.md) 기반. 트리니티(캔버스·teal·amber) 준수.
> 따뜻함은 배경이 아니라 잉크가 운반한다.

| 역할 | 색상 | 토큰 출처 | 용도 |
|---|---|---|---|
| **SUBJECT** (분석 대상) | `#3A5F78` | teal-600 | 대상 채널. 항상 가장 눈에 띄는 색 |
| **SUBJECT 강조** | `#2D4A5E` | teal-800 (surface-teal) | 표 헤더, 결론 강조 배경 |
| **코호트 중앙** | `#9B9590` | neutral-400 | 비교군 중앙값/평균 기준선 |
| **코호트 분포** | `#E8E4DF` | neutral-200 | 분포 영역, 박스플롯 fill |
| **강점/상승** | `#01682D` | success-700 | 긍정 지표, 상승 트렌드 |
| **약점/하락** | `#A8292F` | error-700 | 부정 지표, 하락 트렌드 |
| **경고/주의** | `#A43112` | warning-700 | 경보 하한, 주의 구간 |
| **핵심 수치** | `#C4834D` | amber-500 (primary) | 핵심 숫자 강조. **희소하게** (차트당 1~2회) |
| **중립/보조1** | `#6B6560` | neutral-500 | 보조 데이터 계열 |
| **보조2** | `#708DA1` | teal-400 | 제2비교군 (같은 teal 계열 내 톤 변화) |
| **보조3** | `#A8693A` | amber-600 | 제3비교군 (겸업 등, amber 계열) |

### 2.2 배경 & 텍스트

| 요소 | 색상 | 토큰 출처 |
|---|---|---|
| 차트 배경 | `#FFFFFF` | white (인쇄 캔버스, 불변 조항 9) |
| 차트 영역 | `#FBF7F1` | neutral-50 (웜 오프화이트) |
| 축/틱 텍스트 | `#6B6560` | neutral-500 |
| 제목 텍스트 | `#1B1711` | neutral-900 (웜 다크) |
| 부제/출처 | `#9B9590` | neutral-400 |
| 그리드라인 | `#E8E4DF` | neutral-200 (0.6 alpha) |
| 헤어라인/보더 | `#D4D0C8` | neutral-300 |

### 2.3 순차(Sequential) 팔레트 — 단일 변수 강도

```
teal 계열: #1E3545 → #2D4A5E → #3A5F78 → #708DA1 → #99AEBD → #DBE4EA
```

### 2.4 코호트 티어별 (김달수 전용)

| 티어 | 색상 | 토큰 출처 |
|---|---|---|
| Tier A (LoL Top 100) | `#A8693A` | amber-600 |
| Tier B (Legacy 126ch) | `#708DA1` | teal-400 |
| Tier C (Scale 1,317ch) | `#9B9590` | neutral-400 |
| SUBJECT | `#3A5F78` | teal-600 |

### 2.5 amber 예산 규칙

> design_print.md: "앰버 예산: 문서당 ≤3회"
> 차트 내 amber-500(`#C4834D`)은 핵심 수치 1~2개에만. 변화율 박스나 결론 수치에 사용.
> amber를 데이터 계열 전체에 깔지 않는다.

### 2.6 다크 테마 (웹 대시보드 전용, 선택사항)

> 클라이언트 보고서에는 사용하지 않는다 (불변 조항 9).
> 필요 시 ink 세트(#1A1A1A/#222222/#333333) + 동일 teal/amber를 사용.

---

## 3. 타이포그래피

### 3.1 폰트 스택

| 용도 | 폰트 | 대체 |
|---|---|---|
| 차트 제목 (액션 타이틀) | Pretendard | Noto Sans KR, sans-serif |
| 축 라벨 / 범례 / 데이터 라벨 | Pretendard | Noto Sans KR |
| 수치 / 모노 | JetBrains Mono | Fira Code, monospace |

### 3.2 크기 규격

| 요소 | 크기 (px 기준, 300dpi PNG) | 비고 |
|---|---|---|
| 액션 타이틀 | 16px, bold | 차트 상단 좌측 정렬 |
| 부제 / 출처 | 10px | 차트 하단, muted 색상 |
| 축 라벨 | 11px | |
| 틱 라벨 | 10px | |
| 데이터 라벨 | 10px, mono | 핵심 포인트에만 표시 |
| 범례 | 10px | 차트 내부 또는 상단 |

### 3.3 matplotlib 폰트 설정

```python
# 한글 폰트 설정 — 환경에 따라 경로 조정
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Pretendard 우선, 없으면 Noto Sans KR
for font_name in ['Pretendard', 'Noto Sans KR', 'NanumGothic']:
    fonts = fm.findSystemFonts()
    if any(font_name.lower().replace(' ', '') in f.lower() for f in fonts):
        plt.rcParams['font.family'] = font_name
        break
plt.rcParams['axes.unicode_minus'] = False
```

---

## 4. rcParams 프리셋

### 4.1 보고서 테마 (기본)

```python
REPORT_THEME = {
    # 배경 — 인쇄 캔버스 white, 차트 영역 웜 오프화이트
    'figure.facecolor': '#FFFFFF',
    'axes.facecolor': '#FBF7F1',       # neutral-50
    'savefig.facecolor': '#FFFFFF',

    # 텍스트 — 웜 다크 (neutral 계열)
    'text.color': '#1B1711',            # neutral-900
    'axes.labelcolor': '#6B6560',       # neutral-500
    'xtick.color': '#6B6560',           # neutral-500
    'ytick.color': '#6B6560',           # neutral-500

    # 그리드 — 웜 그레이
    'axes.grid': True,
    'grid.color': '#E8E4DF',            # neutral-200
    'grid.alpha': 0.6,
    'grid.linewidth': 0.5,
    'axes.axisbelow': True,

    # 스파인
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.spines.left': True,
    'axes.spines.bottom': True,
    'axes.edgecolor': '#D4D0C8',        # neutral-300
    'axes.linewidth': 0.5,

    # 폰트
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.titlepad': 16,
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,

    # 레이아웃
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'figure.figsize': (10, 6),
    'figure.constrained_layout.use': True,

    # 범례
    'legend.frameon': False,
    'legend.labelcolor': '#6B6560',     # neutral-500

    # 라인
    'lines.linewidth': 2.0,
    'lines.markersize': 6,
}
```

### 4.2 시맨틱 컬러 딕셔너리

```python
COLORS = {
    'subject': '#3A5F78',      # teal-600 — 분석 대상
    'subject_deep': '#2D4A5E', # teal-800 — 표 헤더, 강조 배경
    'cohort_mid': '#9B9590',   # neutral-400 — 코호트 중앙
    'cohort_fill': '#E8E4DF',  # neutral-200 — 코호트 분포 영역
    'positive': '#01682D',     # success-700 — 상승/강점
    'negative': '#A8292F',     # error-700 — 하락/약점
    'warning': '#A43112',      # warning-700 — 경고
    'highlight': '#C4834D',    # amber-500 (primary) — 핵심 수치. 희소하게
    'neutral': '#6B6560',      # neutral-500 — 보조
    'aux2': '#708DA1',         # teal-400 — 보조2
    'aux3': '#A8693A',         # amber-600 — 보조3
    'tier_a': '#A8693A',       # amber-600 — 김달수 Tier A
    'tier_b': '#708DA1',       # teal-400 — 김달수 Tier B
    'tier_c': '#9B9590',       # neutral-400 — 김달수 Tier C
}
```

### 4.3 적용 함수

```python
import matplotlib.pyplot as plt

def apply_theme():
    """보고서 테마 적용. 라이트 베이스가 기본."""
    plt.rcParams.update(REPORT_THEME)
    return COLORS
```

---

## 5. 차트 타입별 가이드

### 5.1 시계열 (성장 추세, §3.4)

- **타입**: 라인 차트
- **SUBJECT 라인**: teal (subject), linewidth=2.5, marker='o', markersize=5
- **코호트 중앙선**: cohort_mid 색, linewidth=1.5, linestyle='--'
- **코호트 분포 밴드**: cohort_fill 색, alpha=0.15, fill_between(p25, p75)
- **dip 구간 강조**: warning 색 수직 span, alpha=0.1
- **X축**: 분기('24Q1, '24Q2, ...) 또는 월(2024-02, ...)
- **Y축**: 지표명 + 단위 ("평균 시청자 (명)")
- **액션 타이틀 예**: "2년간 평균시청자 +57% 성장, 채팅 참여 +201% 급증"

### 5.2 포지셔닝 (4축, §3.1)

- **타입**: 레이더 차트 또는 2x2 매트릭스
- **레이더**: SUBJECT는 teal (subject) fill(alpha=0.2) + 실선, 코호트 중앙은 gray fill(alpha=0.1) + 점선
- **2x2 매트릭스**: X축=팔로워 규모, Y축=잔류율. SUBJECT를 큰 마커로 강조
- **축 라벨**: 각 축에 "상위 N%" 또는 실제값 병기

### 5.3 코호트 분포 (벤치마크)

- **타입**: 수평 바 차트 또는 박스플롯
- **SUBJECT 위치를 화살표/마커로 표시**
- **코호트 바**: cohort_fill 색
- **SUBJECT 마커**: teal (subject), 삼각형 또는 다이아몬드
- **백분위 주석**: "상위 14%", "하위 9%" 등을 직접 차트에 기재

### 5.4 산점도 (방송량 vs 시청자, §5.2)

- **타입**: 스캐터
- **코호트 점**: cohort_mid 색, alpha=0.3, size=20
- **SUBJECT 점**: teal (subject), size=100, edgecolor='white'(다크) 또는 edgecolor='black'(라이트), zorder=10
- **추세선**: neutral 색, linestyle='--', linewidth=1
- **상관계수 주석**: 차트 우상단, mono 폰트, "r = −0.315"

### 5.5 그룹 바 차트 (팔로워 밴드별 확률, §5.3)

- **타입**: 수직 바
- **현재 구간 바**: warning 색 테두리로 강조
- **목표 구간 바**: subject 색으로 강조
- **나머지**: neutral 색
- **변곡점 구간에 주석**: "→ 83%" 등 핵심 수치 직접 표기

### 5.6 효율 감쇠 곡선 (§4.2)

- **타입**: 라인 + 산점
- **X축**: 팔로워 구간 (로그 스케일 권장)
- **Y축**: peak/follower 또는 avg/follower
- **SUBJECT 현재 위치**: teal (subject) 마커
- **목표 구간 표시**: 반투명 수직 밴드 + 라벨

### 5.7 파이/도넛 (일상 vs 스파이크, §3.5) — 비권장

- 파이 차트는 가급적 사용하지 않는다. 비율 비교가 필요하면 수평 누적 바로 대체
- 부득이한 경우: 최대 3 세그먼트, 라벨을 차트 내부에 직접 배치

---

## 6. 레이아웃 규칙

### 6.1 차트 구조

```
┌─────────────────────────────────────────┐
│  액션 타이틀 (볼드, 제목 색상)            │
│  부제 (출처/기간, muted 색상)            │
├─────────────────────────────────────────┤
│                                         │
│             차트 영역                    │
│                                         │
│   ● SUBJECT  ── 코호트 중앙  ░ 분포     │  ← 범례 (차트 내부 상단)
│                                         │
├─────────────────────────────────────────┤
│  출처: Softcon 뷰어십 / n=323채널        │  ← 하단 주석
│  기준: 2026-06 / 단정등급: 확실          │
└─────────────────────────────────────────┘
```

### 6.2 여백

- 차트 주변 최소 여백: 좌 60px, 우 20px, 상 60px (제목 공간), 하 50px (축+출처)
- constrained_layout 사용 시 자동 조정됨

### 6.3 출력 사양

| 용도 | 포맷 | 해상도 | 크기 |
|---|---|---|---|
| 웹/HTML 보고서 | PNG | 150 dpi | 1500×900 px |
| 인쇄/docx | PNG | 300 dpi | 3000×1800 px |
| 인터랙티브 | HTML (Plotly) | — | 반응형 |
| 프레젠테이션 | PNG | 200 dpi | 1920×1080 px |

---

## 7. 접근성

- 색상만으로 구분하지 않는다: 선 패턴(실선/점선/파선), 마커 모양, 라벨을 병용
- SUBJECT는 항상 가장 굵은 선 + 채워진 마커
- 코호트는 점선 + 빈 마커
- 텍스트 대비비: WCAG AA 이상 (다크 배경 위 #b8b8c4 = 약 7:1)

---

## 8. 파일 명명 규칙

```
{case}_{section}_{chart_type}_{date}.png

예시:
gubiba_s3_growth_trend_20260617.png
gubiba_s3_4axis_radar_20260617.png
gubiba_s5_broadcast_vs_viewers_scatter_20260617.png
kimdalsu_s3_cohort_position_20260617.png
```

---

## 9. 보고서별 차트 목록

### 9.1 구비바 1부 (§1-§6)

| § | 차트 | 타입 | 핵심 메시지 |
|---|---|---|---|
| §3.1 | 4축 포지셔닝 | 레이더 또는 2x2 | 중하위 체급 + 최상위 잔류율 |
| §3.4 | 성장 추세 (2년) | 멀티라인 시계열 | avg +57%, 채팅 +201% |
| §3.5 | 일상 vs 스파이크 | 누적 바 또는 히스토그램 | 일상 94.2%가 본체 |
| §4.2 | 효율 감쇠 곡선 | 라인+산점 | 구간마다 효율 ~40% 하락 |
| §5.1 | 겸업 비교 | 그룹 바 | 겸업 avg 13 > only 8 |
| §5.2 | 방송량 vs 시청자 | 산점도 | r = −0.315, 더 많이 ≠ 더 좋게 |
| §5.3 | 팔로워 밴드별 확률 | 그룹 바 | 1,500 변곡점: 28% → 83% |

### 9.2 김달수 v3 (§2-§4)

| § | 차트 | 타입 | 핵심 메시지 |
|---|---|---|---|
| §3 | 4축 포지셔닝 | 레이더 또는 2x2 | 최소 팔로워 + 극단 방송량 + 최저 잔류율 |
| §3 | 코호트 3-Tier 분포 | 박스플롯 | A/B/C 각 층에서의 위치 |
| §4 | 효율-체급 관계 | 산점도+회귀 | 팔로워↑ → 효율↓ |

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-06-17 | v1 | 초안 작성. needmorefal.com CSS + 컨설팅 레퍼런스 + 기존 보고서 분석 기반 |
| 2026-06-17 | v2 | 라이트 테마 기본으로 전환. 다크+네온그린 → 화이트+teal. needmorefal.com은 참조만 |
