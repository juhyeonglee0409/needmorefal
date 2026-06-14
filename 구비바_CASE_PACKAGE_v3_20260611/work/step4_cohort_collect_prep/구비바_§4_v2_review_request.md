# §4 v2 Script Review Request — Full-History Field Test Results

> **From**: Cowork (Hosea)
> **To**: CC → 검토 후 Codex용 구현 프롬프트 생성
> **Date**: 2026-06-15
> **Subject**: collect_30d_browser.js — full-history 실측 결과 반영 검토

---

## 1. 실측 결과 요약

SOFTC.ONE 종합 게임 카테고리에서 custom date range (2024-01-01 ~ 2026-06-15)를 설정하고 페이지를 리로드했다. 결과:

### 작동 확인
- **URL 파라미터**: `?startDateTime=2023-12-31T15:00:00.000Z&endDateTime=2026-06-15T14:59:59.999Z`
- 페이지 리로드 시 서버가 해당 기간의 집계 데이터를 반환.
- 달력 UI에서 custom range 선택 → 적용 → URL 자동 갱신 → 리로드 필요.

### 데이터 변화
| 항목 | 7일 | Full-history |
|------|-----|-------------|
| 자누 방송시간 | 29.7h | 3,692.3h |
| 자누 뷰어십 | 129,063 | 12,529,248 |
| 랭킹 순서 | 주간 기준 | 누적 뷰어십 기준 (재정렬됨) |
| totalCount | 10,000 | 10,000 (플랫폼 캡) |

### Peak 10-50 밴드 분포 (RSC 프리로드 2,000채널 기준)
| Sub-band | Count |
|----------|-------|
| 10-15 | 228 |
| 16-20 | 195 |
| 21-25 | 146 |
| 26-30 | 110 |
| 31-35 | 98 |
| 36-40 | 66 |
| 41-45 | 59 |
| 46-50 | 63 |
| **합계** | **965** |

- 7일 윈도우: 506채널. Full-history: 첫 2,000채널에서만 965. 전체 10,000 중 추정 3,000-5,000+.

---

## 2. 핵심 발견: RSC 필드명 이원화

**이건 스크립트에 직접 영향을 주는 변경이다.**

| 컨텍스트 | peak 필드 | avg 필드 | 비고 |
|---------|----------|---------|------|
| 랭킹 페이지 — 프리셋 기간 (7일/30일) | `peakViewers` | `avgViewers` | 기존 핸드오프 기재 |
| 랭킹 페이지 — custom date range | `maxLiveViews` | `avgLiveViews` | **신규 발견** |
| 상세 페이지 — 항상 | `maxLiveViews` | `avgLiveViews` | IO supplement §4에 기재 |

즉 **랭킹 페이지 RSC에서도 custom range 모드일 때 필드명이 바뀐다.**

v2의 `scanCurrentPage()` (L132-176)는 DOM positional parsing을 쓰므로 직접적 파싱 에러는 안 나지만, RSC 직접 파싱으로 전환하면 이 이원화를 반드시 처리해야 한다.

---

## 3. RSC 프리로드 2,000채널 — 효율화 기회

Full-history 모드에서 **한 번의 페이지 로드에 RSC payload가 2,000채널 데이터를 포함**한다.
- 현재 v2 flow: DOM 100건/페이지 × 100페이지 = 100번 페이지 이동 + scanCurrentPage()
- RSC 직접 파싱 시: **20배 적은 페이지 이동**으로 동일 커버리지

검토 포인트:
- Phase 1을 "DOM scan" → "RSC parse + DOM fallback"으로 전환하는 것이 안전한가?
- RSC payload의 channelId 필드명 확인 필요 (7일에서는 `channelId`, full-history에서 아직 미확인 — `chzzkId`일 수 있음)
- 2,000 단위로 잘리는 경계를 처리하는 방법?

---

## 4. v2 스크립트 검토 항목

### 4-A. CONFIG 확장 (L24-36)
```
현재:
  downloadPrefix: 'gubiba_30d'

필요:
  dateRange: { start: null, end: null },  // ISO string or null (= preset)
  downloadPrefix: dynamic (기간 기반)
```
- "30d"라는 이름이 full-history와 맞지 않음.
- CONFIG에 날짜 범위를 넣고, downloadPrefix를 동적으로 생성할 것.

### 4-B. scanCurrentPage() — DOM positional 한계 (L132-176)
```javascript
// 현재: nums[2] = peak, nums[3] = avg
// 위험: full-history에서 column 순서가 바뀌었을 수 있음
```
- 실측에서 컬럼 순서 변경 미관찰 (최고 시청자/평균 시청자 위치 동일).
- 하지만 DOM 파싱 + RSC 파싱 병행이 안전. diagnoseDOM()에서 컬럼 헤더를 읽어 자동 매핑하면 이상적.

### 4-C. RSC 직접 파싱 함수 신규 (미구현)
```javascript
// 제안: scanFromRSC() — 페이지 HTML에서 RSC payload 직접 추출
// 2,000채널/로드 → Phase 1 소요시간: 5분 → 30초
function scanFromRSC() {
  var html = document.documentElement.innerHTML;
  // maxLiveViews || peakViewers — 이원화 대응
  var peaks = [...html.matchAll(/\\"(maxLiveViews|peakViewers)\\":(\d+)/g)];
  // ... channelId, name, viewership도 동일 패턴 추출
  // hydration dedup 적용
}
```

### 4-D. diagnoseDOM() — 집계 윈도우 감지 (L473-508)
```javascript
// 현재: "지난 7일/30일" 버튼만 탐지
// full-history에서는 프리셋 버튼이 아닌 custom range 표시
// "2024. 01. 01 – 2026. 06. 15" 텍스트가 필터 영역에 표시됨
```
- custom range 감지 로직 추가 필요.
- `26.06.15 까지` 같은 텍스트도 파싱 가능.

### 4-E. 볼륨 스케일링
| 항목 | 7일 | Full-history |
|------|-----|-------------|
| 스캔 대상 | ~10,000 | ~10,000 |
| Peak 10-50 필터 후 | 506 | 3,000-5,000+ |
| Enrichment 시간 (3w×1.5s) | ~25분 | ~50분-2시간 |
| CSV 크기 | ~80KB | ~500KB-1MB |
| 시계열 JSONL | ~150KB | ~1-3MB |

- Blob download: 1MB도 문제없음.
- getNext() fallback: 5000건 × 8건/호출 = 625회 루프 (10-20분). 여전히 viable.
- enrichment 중 abort + resume 필요성 증가. 현재 abort()는 있지만 resume 없음.

### 4-F. verify_cohort_v2.js (별도 파일)
- 7일 기준 하드코딩 없음 (이전 세션에서 이미 제거 확인). 구조 검증만 수행하므로 수정 불요.
- 단, full-history에서는 `is_general_game: unknown` 비율이 달라질 수 있음. 모니터링 필요.

---

## 5. CC에게 요청하는 산출물

1. **v2 스크립트 변경점 목록** (동의/수정/거부 판정)
2. **Codex용 구현 프롬프트** — 위 검토 결과를 바탕으로, Codex가 v2 스크립트를 v3로 업데이트할 수 있는 구체적 지시서

구현 프롬프트에 포함할 것:
- 변경 대상 파일 경로 (절대경로)
- 함수별 변경 내용 (추가/수정/삭제)
- 테스트 기준 (diagnoseDOM() 출력 예시 등)
- full-history URL 파라미터 자동 설정 로직 여부 (수동 전환 vs 자동)

---

## 6. 참조 파일

| 파일 | 위치 | 용도 |
|------|------|------|
| collect_30d_browser.js | `data/cohort/scripts/` | 검토 대상 |
| verify_cohort_v2.js | `data/cohort/scripts/` | 검증 스크립트 |
| 구비바_§4_CC_IO_supplement.md | `work/step4_cohort_collect_prep/` | 이전 보충 (필드명 보정 포함) |
| 구비바_§4_CC_handoff_prompt.md | `work/step4_cohort_collect_prep/` | 최초 핸드오프 |
| needmorefal_proto_data.json | `data/` | 프로토타입 실측 데이터 |

모든 경로는 `D:\Codex_Workspace\Streamer Consulting Project\구비바_CASE_PACKAGE_v3_20260611\` 기준.
