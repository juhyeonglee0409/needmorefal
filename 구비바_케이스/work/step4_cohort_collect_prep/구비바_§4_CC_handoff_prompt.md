# 구비바 §4 — CC Handoff Prompt

## Context

Hosea가 SOFTC.ONE에서 구비바 §4 코호트 데이터를 브라우저 기반으로 수집했다. 이 패스는 **발견 + 파이프라인 검증**이었고, 다음이 확인됐다:

- SOFTC.ONE 구조 (카테고리 랭킹, 상세 페이지, RSC payload)
- 종합 게임(치지직, 공백 있음) vs 종합게임(SOOP, 공백 없음) 구분
- is_general_game 분류 규칙 (unknown=0으로 검증 완료)
- enrichment 파이프라인 (ranking scan → filter → detail fetch → classify)

**한계:** 현재 데이터는 **7일 집계**. 분석용 코호트로는 부적합 (주간 변동이 크고, 방송 안 한 주에는 peak=0). 30일 이상 집계로 재수집 필요.

---

## Files in D:\Gunsmith_Mailbox\reports\

| File | Description |
|---|---|
| `gubiba_cohort_enriched_v2.csv` | 7일 집계 enriched 데이터. 506ch, peak 10-50, 21 columns. **파이프라인 검증용. 분석용 아님.** |
| `구비바_§4_case_params_v1.json` | 수집 파라미터. category, peak band, classification rules, budgets 포함. |
| `구비바_§4_cohort_enriched_all.csv` | 이전 세션 산출물 (64ch, peak 74-296). superseded. |
| `구비바_§4_Charles_진단결과_20260614.md` | Charles 진단 결과. SOFTC.ONE 페이지 구조 상세. |
| `구비바_§4_inspect_memo_20260614.md` | Hosea Chrome 탐색 결과. |
| `구비바_§4_Arthur_ExecutionProtocol_v2_FILLED_20260614.json` | 실행 프로토콜 (이전 버전, LoL 기준. 참고만). |

---

## 구비바 기본 정보

- platform: naverchzzk (치지직)
- channelId: 269edc95873a1ec9fc534851c0783d1f
- raw_max: 148 (치지직 대시보드 동접 최고치. 전체 기간 historical peak.)
- softcone 7d peak: 27 (수집 시점 소프트콘 7일 집계 peak)
- followers: 724
- primary category: talk 49.6%
- tag: 버추얼

**raw_max vs softcone peak 구분이 중요하다.** raw_max=148은 채널 역대 최고 동접. softcone peak=27은 특정 7일 윈도우의 최고 동접. 두 지표는 별개이며, peak band 설계 시 어느 것 기준인지 명시해야 한다.

---

## Task 1: case_params 보정

`구비바_§4_case_params_v1.json`에 다음을 반영:

1. **raw_max 정의 추가**: raw_max=148이 "치지직 대시보드 역대 최고 동접"임을 명시. softcone peak(집계 윈도우 종속)와 구분.
2. **tasks 배열 정리**: 현재 tasks는 이전 LoL 기준 잔재가 섞여 있음. 실제 실행된 작업(종합 게임 카테고리, 치지직 전용, peak 10-50 enrichment)으로 교체.
3. **aggregation_window**: "7d" → 본 수집 시 30d로 변경 예정임을 기록.

---

## Task 2: 7일 데이터 검증 (파이프라인 확인용)

`gubiba_cohort_enriched_v2.csv` 검증 스크립트:

- row count: 506 expected (505 data rows + header — wc -l reports 506 due to no trailing newline)
- null check: follower, category_1, is_general_game에 null/빈값 있는지
- peak range: 모든 peak_viewers가 10-50 범위 내인지
- platform: 전부 naverchzzk인지
- is_general_game 분포: true=235, false=271, unknown=0
- gg_reason 분포: gg_primary=76, multi_game=149, gg_secondary=10, talk_primary=77, single_game_dominant=52, single_game_or_non_game=142
- exclude_reason: 현재 미적용 (빈값). exclude 로직은 별도 적용 필요.
- duplicate check: channelId 중복 여부

---

## Task 3: 30일 수집 자동화 스크립트

### SOFTC.ONE 구조

**카테고리 랭킹 페이지:**
- URL: `https://viewership.softc.one/category/%EC%A2%85%ED%95%A9%20%EA%B2%8C%EC%9E%84/ranking`
- Next.js App Router (RSC). 서버 렌더링.
- 페이지당 100채널. 페이지 파라미터는 URL이 아닌 클라이언트 사이드 네비게이션.
- 집계 윈도우 전환: UI 버튼 ("지난 7일" → "지난 30일" → "지난 90일")
- 제공 컬럼: rank, name, platform, channelId, stream_hours, peak_viewers, avg_viewers, viewership

**상세 페이지:**
- URL: `https://viewership.softc.one/channel/naverchzzk/{channelId}`
- RSC payload 내 escaped JSON에서 추출:
  - Follower: `/FollowerCount\\":(\d+)/g` (마지막 매치 사용 — 최신값)
  - Category: `/\\"category\\":\\"([^\\]+)\\",\\"sumLiveViews\\":\d+,\\"viewership\\":(\d+)/g`

### 자동화 요구사항

브라우저 컨텍스트(Chrome 인증 세션)에서 실행하는 단일 JS 스크립트. Vercel checkpoint를 우회하려면 인증된 브라우저의 fetch()를 사용해야 한다 (외부 HTTP 클라이언트로는 차단됨).

**파이프라인:**
1. 랭킹 스캔: 30일 집계 페이지 순회 → 전체 채널 목록 수집
2. 대역 필터: peak 10-50 (또는 조정된 band) 필터링
3. enrichment: 3 parallel workers, 1.5s delay, staggered starts
4. 분류: classifyGG() 적용
5. **점진적 반출**: 50건마다 compact chunk를 JS tool output으로 추출 → 파일에 append. 끝에 80KB 한 번에 빼려다 막힌 게 이번 최대 병목이었음.

### 분류 규칙 (검증 완료)

```javascript
function classifyGG(row) {
  const c1 = (row.category_1 || '').trim();
  const c1s = parseFloat(row.category_1_share) || 0;
  const c2 = (row.category_2 || '').trim();
  const c2s = parseFloat(row.category_2_share) || 0;
  const c3 = (row.category_3 || '').trim();
  const c3s = parseFloat(row.category_3_share) || 0;
  
  if (!c1) return { is_gg: 'unknown', reason: 'no_category_data' };
  if (c1 === '종합 게임' || c1 === '종합게임') return { is_gg: 'true', reason: 'gg_primary' };
  if (c1.toLowerCase() === 'talk' && c1s >= 50) return { is_gg: 'false', reason: 'talk_primary' };
  if (c1s >= 80) return { is_gg: 'false', reason: 'single_game_dominant' };
  
  const nonTalkCats = [[c1, c1s], [c2, c2s], [c3, c3s]].filter(([n, s]) => 
    n && n.toLowerCase() !== 'talk' && n !== '그림/아트' && n !== '먹방' && s >= 15);
  if (nonTalkCats.length >= 2) return { is_gg: 'true', reason: 'multi_game' };
  if ((c2 === '종합 게임' || c2 === '종합게임') && c2s >= 15) return { is_gg: 'true', reason: 'gg_secondary' };
  
  return { is_gg: 'false', reason: 'single_game_or_non_game' };
}
```

### Polite 수집 정책

- 랭킹 페이지 간: 2-3s delay
- 상세 페이지 간: 1.5-2s delay per worker
- 차단(429/403) 시: 즉시 후퇴, 30s 대기 후 재시도 1회, 실패 시 중단
- 동시 워커: 최대 3

---

## Task 4: 분석 산출물 (30일 데이터 확보 후)

1. `cohort_final_main_general_game.csv` — is_general_game=true만 추출, exclude_reason 적용
2. `cohort_robustness_table.csv` — peak band별, 분류 사유별 분포표
3. `cohort_enrichment_absence_inventory.csv` — follower null, category null 등 결측 목록

---

## Lessons from Discovery Pass

1. **7일 ≠ 분석용.** 방송 안 한 주면 peak=0. 30일이 최소 윈도우.
2. **종합 게임 카테고리 ≠ 종합 게임 스트리머.** 46.5%만 true. 분류 필수.
3. **raw_max ≠ softcone peak.** 별개 지표. band 설계 시 명시 필수.
4. **RSC payload 파싱은 안정적.** FollowerCount, category 정규식 506/506 성공.
5. **Rate limit 문제 없음.** 2워커 × 2s delay로 506건 전부 에러 없이 완주. 429/403 한 번도 안 떴음. 3워커 × 1.5s (~2 req/s)가 안전한 상한.

---

## I/O Architecture Problem (최대 병목)

이번 최대 병목은 rate limit이 아니라 **I/O 경로 설계 문제**였다.

**수집은 됐다.** 브라우저 JS가 SOFTC.ONE을 fetch하고, RSC를 파싱하고, 결과를 메모리에 쌓는 것까지 문제 없었다.

**반출에서 막혔다.** 80KB CSV가 브라우저 메모리에 완성됐는데, 파일시스템으로 꺼내는 정식 경로가 없었다:
- JS 실행 도구 output: "결과 미리보기"용이지 대용량 반출용이 아님. ~1.2KB에서 truncate.
- blob download → Downloads 폴더: Codex 작업 영역(D:\Codex_Workspace) 밖이라 자동으로 잡을 수 없음.
- clipboard: 브라우저 포커스/제스처 정책에 걸림. 자동화에서 불안정.
- base64: 원본보다 33% 커져서 제한에 더 잘 걸림.

**원인:** 수집 설계에 "flush to file" 단계가 없었다. 브라우저 콘솔 안에서 완성품을 만든 뒤 꺼내려 해서, 창고에 화물을 쌓았는데 화물차 출입구가 없었던 것.

**다음 패스의 I/O 설계 (택 1):**

```
A. 점진적 flush: 수집하면서 20-50건마다 즉시 파일 저장 (JS tool output 제한 이내)
B. Codex/Playwright 직접 fetch: 브라우저 밖에서 수집 + CSV 직접 작성
C. 역할 분리: 브라우저는 인증 세션만 제공, 반출은 로컬 스크립트가 담당
```

B 또는 C가 가능하면 가장 깔끔하지만, Vercel checkpoint가 비브라우저 요청을 차단하므로 인증 세션 공유 방법이 필요. A는 현재 도구 제약 내에서 가장 확실한 해결책.
