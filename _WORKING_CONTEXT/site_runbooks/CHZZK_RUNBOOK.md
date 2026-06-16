# CHZZK Runbook

Last verified: 2026-06-15
Status: partial
Scope: 치지직 스트리머 프로필/채널 데이터 (upstream identity/source)

## Quick Read

- chzzk.naver.com은 수집 대상 사이트가 아니라 upstream identity source.
- Charles/Arthur에서 검증된 공개 API surface가 있음.
- 사이트 자체보다 channelId 기반 프로필 조회 용도.

## Working Routes

| Route | Status | Use For | Notes |
|---|---|---|---|
| 공개 프로필 API | **working** | 채널명/프로필 이미지/상태 조회 | Charles ScoutReport에서 usable endpoint로 분류됨 |

## URL / Data Surfaces

| Surface | Pattern | Data | Caveat |
|---|---|---|---|
| 채널 프로필 | `chzzk.naver.com/api/channels/{channelId}` 계열 | 채널명, 프로필, 팔로워 수, 방송 상태 | 공개 API. 인증 불필요. |

## Failure Modes

| Signal | Meaning | Action |
|---|---|---|
| 403/401 on profile endpoint | 비공개 채널 또는 API 변경 | absence 기록. 재시도 불필요. |

## Collection Defaults

- **속도**: 공개 API이므로 별도 rate 제약 미실측. 일반적 예의 수준 유지.
- **secret/raw 금지**: 쿠키, auth 토큰 저장 금지.

## Related Decisions

| Decision ID | Date | Summary |
|---|---|---|
| DL_TOOLING_20260613_020 | 2026-06-13 | DLG-001 I2 real-artifact offline smoke (CHZZK CollectionResult → Pearson) |
| DL_TOOLING_20260611_016 | 2026-06-11 | Charles browser probe contract promotion (CHZZK endpoint 분류의 근거) |

## Proven Runs

| Date | Case/Step | Result | Artifact |
|---|---|---|---|
| 2026-06-13 | DLG-001 I2 offline smoke | CHZZK CollectionResult → Pearson store 검증 | `_tmp/i2/store/` (DL_020) |

## Open Risks

- **API 안정성 미검증**: 공개 API 경로가 문서화되지 않은 내부 API일 수 있음. 변경 시 깨질 위험.
- **rate limit 미실측**: 대량 수집 시 rate limit 여부 확인 안 됨.
- **방송 기록/시계열 endpoint 미탐색**: 프로필 조회만 검증. 방송 기록이나 시청자 통계 API는 별도 탐색 필요.
