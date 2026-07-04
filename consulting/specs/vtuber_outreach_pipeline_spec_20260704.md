# 버튜버 콜드메일 타겟 리스트업 파이프라인 스펙 v0.1

- type: spec (CC 기획 → Codex 구현 proposal)
- date: 2026-07-04
- 목적: 치지직 개인세 버튜버 중 비즈니스 메일 공개 채널을 발견·검증·지표화하여, 1:1 개별 작성 콜드메일 초안 큐를 생성한다.
- 근거 문서: `reviews/coldmail_vtuber_research_20260704.md` (방법론/법규/생태계), `_WORKING_CONTEXT/site_runbooks/CHZZK_RUNBOOK.md`, `COLLECTION_TOOLKIT.md`
- 원칙: 공개 데이터만. 발송은 전 건 operator 수동. 자동 발송 기능은 이 파이프라인에 존재하지 않는다.

---

## 0. 검증된 사실 (2026-07-04 프로브, 각 1회)

| Surface | 상태 | 반환 필드 |
|---|---|---|
| `api.chzzk.naver.com/service/v1/search/channels?keyword=&offset=&size=` | **working, 무인증** | channelId, channelName, channelDescription(짧은 bio), followerCount, openLive, verifiedMark |
| `api.chzzk.naver.com/service/v1/channels/{channelId}` | **working, 무인증** | 위 + channelType, subscriptionAvailability, adMonetizationAvailability, paidProductSaleAllowed |

기존 검증 루트 (재사용):
- CHZZK 프로필 API — CHZZK_RUNBOOK working
- 소프트콘 뷰어십 시계열 — `tools/collector/` config-driven (nodriver, 323 대상 검증) / HTTP 클라이언트는 WAF 100% 차단 (툴킷 §1, 반복 금지)
- LLM gate 패턴 — corpus 파이프라인 skip-gate 교훈: 과도 필터링 주의 (DL 관련 SESSION_NOTE 2026-06-23)

## 1. 스테이지 설계

```
S1 Discovery → S2 Enrich → S3 Classify → S4 Filter → S5 Email → S6 Metrics → S7 Compose → [operator 검토·발송]
```

| # | 스테이지 | 방법 | 도구/경로 | 미해결 |
|---|---|---|---|---|
| S1 | 버튜버 후보 발견 | (a) 검색 API 키워드 스윕: 버튜버, 버추얼, Vtuber, V튜버, 버미육, 신인 버튜버 등 + 페이지네이션 (b) 소프트콘 버튜버 카테고리 랭킹 | (a) HTTP (WAF 없음 확인) (b) 기존 collector | 치지직 버튜버 카테고리/라이브 목록 API 미탐색 — Codex 확장 과제 |
| S2 | 프로필 보강 | 채널 상세 API, 후보 전건 | HTTP, ~1 req/s | — |
| S3 | 버튜버/개인세 판별 | 1차 휴리스틱(이름·bio 패턴) + 소속사 블랙리스트(스텔라이브, 미츄, 버츄얼 유니온, 허니즈 등 — 별도 YAML 유지) + 경계 케이스만 LLM 판정 | 로컬 + LLM gate | 소속사 리스트 초기 시드 작성 필요 |
| S4 | 세그먼트 라벨링 (필터 아님 — 2026-07-04 operator 방향) | `rookie(<150)` / `growth(150~10,000)` / `large(>10,000)` 전원 수집·라벨. 발송 우선순위: growth(비교 진단 템플릿 A) → rookie 중 이메일 보유자(액셀러레이션 템플릿 B). 파일럿 실측: bio 이메일 공개율 growth 22% vs rookie 2% | 로컬 | 활동성 신호는 소프트콘 최근 30일 방송 이력으로 (S6과 통합) |
| S5 | 이메일 추출 | channelDescription regex (`[\w.+-]+@[\w-]+\.[\w.]+`) | 로컬 | **짧은 bio에 없는 경우 다수 예상.** 채널 소개 전문 surface(웹 소개 탭) endpoint 미탐색 — Codex 과제. 외부 링크(트위터 bio, 리트리) 2차 추출은 v0.2 |
| S6 | 지표 스냅샷 | 소프트콘에서 평균 시청자/방송시간 30d~1y → 버튜버 코호트 내 percentile 계산 → 훅 수치(강점 1 + 병목 1) 생성 | 기존 collector (nodriver) | CollectDirective — **operator 승인 게이트** |
| S7 | 초안 생성 | 리서치 노트 §4 템플릿 v2에 채널별 수치 삽입 → 검토 큐 (md 파일) | 로컬/LLM | 발송·팔로업 기록은 operator가 수행 후 파이프라인에 회귀 입력 |

## 2. 데이터 스키마 (NDJSON, append-only)

```json
{
  "channel_id": "str", "channel_name": "str",
  "follower_count": 0, "description": "str",
  "vtuber": {"value": true, "method": "heuristic|llm", "confidence": "high|low"},
  "solo": {"value": true, "matched_agency": null},
  "email": {"value": "str|null", "source": "bio|intro_page", "seen_at": "iso8601"},
  "activity": {"open_live_seen": false, "last_broadcast": "iso8601|null", "source": "softcon|api"},
  "metrics": {"avg_viewers_30d": null, "cohort_percentile": null, "bottleneck": null},
  "outreach": {"status": "candidate|qualified|drafted|sent|replied|opted_out|excluded", "sent_at": null, "followup_at": null, "opted_out_at": null}
}
```

- `opted_out`은 영구 상태. 어떤 재수집·재초안 대상에도 포함 금지.
- 이메일은 **공개 표기된 값만** 저장. 추정·조합 생성 금지.
- flush: 매 항목 append (행동계약 §12.4). progress 파일로 resume.

## 3. 에이전트 팀 구성

### 구현 (Codex 핸드오프, git 관리)
| 역할 | 담당 | 산출 |
|---|---|---|
| Scout | S1 keyword sweep 모듈 | `tools/outreach/scout.py` (가칭) |
| Enricher | S2 상세 조회 | 동일 패키지 |
| Classifier | S3 휴리스틱+블랙리스트+LLM 경계판정 | `agencies.yaml` + gate |
| Extractor | S5 regex + intro surface 탐색 | — |
| Metrics | S6 softcon 연계 | 기존 collector config 재사용 |
| Composer | S7 초안 큐 생성 | `outbox/` md 파일 |

### 세션 실행 (CC, operator 승인 후 파일럿)
- 파일럿 범위 제안: 키워드 6개 × 페이지네이션 → 후보 ~300 → S2~S5까지 (HTTP만, 소프트콘 제외) → "이메일 공개 개인세 버튜버" 수율 측정.
- 예상 요청량: 검색 ~30회 + 상세 ~300회, ~1 req/s, 총 ~6분. CC bash 안전 한도(7분) 내 배치 분할.
- S6(소프트콘)은 파일럿 결과 보고 후 별도 CollectDirective로.

## 4. 경계

- 공개 API, 무인증, 예의 속도(~1 req/s). 쿠키/토큰/스크린샷 저장 없음.
- 이메일 발송 기능 없음 — 파이프라인 산출물은 "operator 검토 큐"가 종점.
- 콜드메일 자체의 법적 설계는 리서치 노트 §2 (관행 노선: 1:1 개별 작성, 팔로업 1회, 거부 즉시 영구 제외 — operator 확정 2026-07-04).
- 수율이 낮으면(이메일 공개 <5%) 외부 링크 2차 추출(v0.2)을 별도 승인으로 검토.

## 5. 파일럿 결과 (2026-07-04 실행, operator 승인)

산출물: `runs/vtuber_outreach_pilot_20260704/` (raw/enriched NDJSON + summary 2종)

| 경로 | 결과 | 판정 |
|---|---|---|
| 채널명 키워드 검색 (S1c) | 73 유니크 중 64개가 팔로워 <150 (초소형 편향), 밴드 내 9, bio 이메일 2 | **보조로 강등** — 타겟 볼륨존 버튜버는 채널명에 키워드가 없음 |
| 라이브 검색 단발 스냅샷 | 8 유니크 (점심 시간대), 밴드 내 5, bio 이메일 1 | 시간대 의존 심함 — 단발로는 부족, 피크 시간 폴링 누적 필요 |
| 카테고리 API | `categories/ETC/virtual/lives` 등 3개 shape 모두 빈 배열. 버튜버는 게임/토크 등 콘텐츠 카테고리로 방송 — **"버추얼 카테고리" 발견 경로는 성립 안 함** | 폐기 |
| 라이브 태그 | live 객체에 `tags` 존재, 버튜버들이 "버츄얼" 등 태그 사용 | 폴링 누적의 판별 신호로 사용 |

핵심 수율: **qualified(개인세·밴드 내) 14명 중 bio 이메일 3명 (~21%)**. 발송 대상 50명 확보에 qualified ~250명 필요.

**S1 재설계 (v0.3 — 파일럿-2 실측 반영, `runs/.../pilot2_softcon_route.md`)**:
1. **발견 주력 = 치지직 라이브검색 폴링 누적** — 저녁 피크(20~24시) 스윕을 수일 누적, 태그/제목 버튜버 신호로 필터. **개인세 소형/신인(팔로워 수백~수천)이 여기서만 잡힘.**
2. **소프트콘 버추얼 랭킹은 발견 소스에서 강등** — top 300이 전원 팔로워 1만+ 기성/소속사라 타겟 밴드(150~10k)를 못 덮음. 대신 (a) 발견된 cid의 **지표 보강(S6)** 소스로 사용(소형까지 커버 확인), (b) 태그 필터의 소속사명을 S3 블랙리스트로.
3. S3 블랙리스트 확장: 소프트콘 태그(스텔라이브/이세계아이돌/에스더/아카이브/허니즈) + 소속사 이메일 도메인(pixelnetwork.co.kr, sandboxnetwork.net, enchantenter.co.kr, gysent.com, listella.tv).
4. 이메일 수율: 치지직 bio 이메일이 밴드 내에선 ~21%(파일럿-1). "소개 전문" surface 추가 탐색은 v0.2 과제.
5. 브라우저 제약: Claude Chrome 확장은 chzzk.naver.com 접근 정책 차단(치지직 웹 UI는 Codex/Cowork). **소프트콘은 사용자 인증 세션이면 Chrome MCP로 접근 가능**(checkpoint operator 1회 통과 필요).

## 6. 검증 루프

```
1. S1 스윕 → verify: 후보 수 및 중복률 리포트
2. S3 분류 → verify: 샘플 30건 수동 라벨과 일치율 ≥90%
3. S5 추출 → verify: 이메일 수율 + 오탐(비즈니스 아닌 메일) 수동 확인
4. S7 초안 → verify: 무작위 3건 operator 검토 통과
```
