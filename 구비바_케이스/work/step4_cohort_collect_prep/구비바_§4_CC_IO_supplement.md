# §4 I/O Redesign — Operational Supplement from Cowork

CC의 v2 설계(D primary + A fallback + C probe)에 대한 실전 보충.
Cowork이 discovery pass에서 실제로 겪은 것 기반.

---

## 1. Option D (Blob download) — 실증 완료

이번 세션에서 `gubiba_cohort_enriched_v2.csv` (80KB, 506행)를 Blob download로 반출했다. 작동한다.

**실행 코드 (검증 완료):**
```javascript
const blob = new Blob([window._finalCSV], { type: 'text/csv;charset=utf-8' });
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'gubiba_30d_full.csv';  // 영문명 필수
document.body.appendChild(a);
a.click();
document.body.removeChild(a);
URL.revokeObjectURL(url);
```

**주의사항 (실전에서 발생한 문제):**
- 한글 파일명(`구비바_§4_cohort_enriched_v2.csv`)으로 시도 → 사용자가 Downloads에서 못 찾음. 영문명으로 재시도 후 성공.
- 브라우저 다운로드 확인 팝업이 뜨는 경우 있음. 사용자가 "확인"을 눌러야 실제 저장됨.
- `pickup_downloads.ps1`에 "파일 미발견 시 30s 대기 후 재탐색" 로직 권장.

**BOM 포함 UTF-8 (한글 CSV용):**
```javascript
const BOM = '﻿';
const blob = new Blob([BOM + csvString], { type: 'text/csv;charset=utf-8' });
```

---

## 2. Option A (micro-chunk fallback) — 실측 제한치

JS tool output truncation 실측:
- 약 1.2KB 전후에서 잘림 (예측 불가, 안전마진 필요)
- compact array format (`[name,cid8,pk,av,fol,c1,c1s]`) 기준 ~10건/flush가 안전
- full CSV format 기준 ~5건/flush

**getNext() 설계 시:**
- 호출마다 `window._flushIndex`를 증분하는 방식이 안정적
- 호출 결과를 Cowork이 append → 파일시스템에 누적 → 끝나면 병합
- 500건 기준 50~100회 루프. 각 호출에 2-3초 소요 → 총 2.5~5분

---

## 3. Option C (cookie bridge) — 금지

SOFTC.ONE은 Vercel checkpoint 사용. 특징:
- JS challenge 기반. 단순 cookie 전달로는 비브라우저 요청 차단됨.
- `mcp__workspace__web_fetch` (서버사이드 fetch)로 시도 → checkpoint HTML만 반환, 데이터 없음.
- `curl`도 동일하게 차단될 가능성 높음.

**결론:** 쿠키/세션값을 브라우저 밖으로 반출하지 않는다. 테스트 목적으로도
브라우저 세션 값을 CLI, 로그, 프롬프트, 산출물에 복사하지 않는다.

허용 경로는 두 개뿐이다:
- 브라우저 컨텍스트 안에서 `fetch(..., { credentials: 'include' })` 실행
- Blob download로 수집 결과만 반출

이 원칙은 secret persistence 금지선과 일치한다.

---

## 4. SOFTC.ONE RSC 파싱 — 필드명 보정

핸드오프 프롬프트의 regex 패턴에 누락된 필드가 있다.

**랭킹 페이지:** 핸드오프 기재 대로 `peakViewers`, `avgViewers` 사용.

**상세 페이지:** 필드명이 다르다. 핸드오프의 `peakViewers`/`avgViewers` 대신:
- `maxLiveViews` = peak viewers (시계열, 주간 단위)
- `avgLiveViews` = avg viewers (시계열, 주간 단위)
- `airTime` = stream hours (시계열)
- `followerCount` = follower (최신값은 마지막 매치)
- `maxFollowerCount`, `startFollowerCount`, `endFollowerCount` = follower 변동

**상세 페이지 추출 regex (검증 완료):**
```javascript
// 주간 시계열 (24 data points = 6개월)
const maxLV = [...html.matchAll(/\\"maxLiveViews\\":(\d+)/g)].map(m => parseInt(m[1]));
const avgLV = [...html.matchAll(/\\"avgLiveViews\\":(\d+)/g)].map(m => parseInt(m[1]));
const airT  = [...html.matchAll(/\\"airTime\\":(\d+)/g)].map(m => parseInt(m[1]));

// follower (마지막 매치 = 최신값)
const fol = [...html.matchAll(/\\"followerCount\\":(\d+)/g)];
const follower = fol.length > 0 ? parseInt(fol[fol.length - 1][1]) : null;

// 카테고리별 viewership (핸드오프 기재와 동일, 정상 작동)
const catM = [...html.matchAll(/\\"category\\":\\"([^\\]+)\\",\\"sumLiveViews\\":\d+,\\"viewership\\":(\d+)/g)];
```

**주의:** 시계열 데이터가 RSC payload에서 2번 반복되는 경우 있음 (서버/클라이언트 hydration). `slice(0, Math.ceil(length/2))`로 중복 제거 필요.

---

## 5. 수집 정책 실측

506건 enrichment 결과:
- 2 workers × 2s delay → 429/403 제로. 전부 성공.
- 3 workers × 1.5s delay (~2 req/s)가 안전 상한.
- 랭킹 페이지 간: 2-3s delay (20 pages, 에러 없음)
- 총 소요시간: ~25분 (스캔 5분 + enrichment 20분)
- 30일 데이터도 동일 구조. 집계 윈도우 전환은 UI 버튼 클릭 후 페이지 리로드.

---

## 6. 30일 집계 윈도우 전환

7일 → 30일 전환 방법 (미검증, 탐색만 완료):
- 카테고리 랭킹 페이지에서 "지난 7일" 버튼 → "지난 30일" 클릭
- URL 파라미터가 변경되는지 또는 클라이언트 사이드 state인지 확인 필요
- RSC payload 구조는 동일할 것으로 예상 (동일 컴포넌트, 다른 데이터)
- CC 첫 동작: `diagnoseDOM()`에서 현재 집계 윈도우 + 전환 버튼 위치 확인

---

## 7. needmorefal 프로토타입 데이터

`data/needmorefal_proto_data.json`에 20명 실측 데이터 저장 완료.
- 24주 주간 avgLiveViews 시계열 포함
- 프로토타입 `dummyData.chart` 배열에 직접 매핑 가능
- 이 데이터는 §4 파이프라인과 별개. 프로토타입 UI 작업 시 참조.
