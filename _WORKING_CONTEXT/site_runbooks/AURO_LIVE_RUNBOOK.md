# AURO.LIVE Runbook

Last verified: 2026-06-15
Status: partial
Scope: 스트리머 팔로워 랭킹 수집 (needmorefal 카드 게임 데이터)

## Quick Read

- auro.live는 SvelteKit 앱. `__data.json` API 엔드포인트로 structured data 접근 가능.
- Codex sandbox proxy에서 403 차단됨 — Chrome JS fetch route 사용.
- Cloudflare 없음, robots 허용, 별도 gate 없음 (Charles 확인).
- 50 entries/page, 1.5s delay로 안정 수집 실측.

## Working Routes

| Route | Status | Use For | Notes |
|---|---|---|---|
| Chrome JS fetch (`__data.json`) | **working** | 팔로워 랭킹 전체 수집 | SvelteKit devalue format. Cowork/Chrome에서만 동작. |

## URL / Data Surfaces

| Surface | Pattern | Data | Caveat |
|---|---|---|---|
| 팔로워 랭킹 | `auro.live/follower?page={n}` | 50 entries/page, rank 1-11000+ | `__data.json` 엔드포인트로 접근. SvelteKit devalue format 파싱 필요. |

## Failure Modes

| Signal | Meaning | Action |
|---|---|---|
| Sandbox proxy 403 (Tunnel Forbidden) | Codex/CLI 환경 네트워크 제한 | Chrome browser JS fetch route로 전환. bash curl/httpx 사용 불가. |

## Collection Defaults

- **속도**: ~1.5s delay between requests 안정 실측.
- **페이지**: 50 entries/page. 11,000 entries = 220 pages.
- **secret/raw 금지**: 쿠키, auth 토큰 저장 금지.

## Related Decisions

없음. auro.live 관련 decision log 엔트리 미작성. 운영 기록은 SESSION_NOTE Cowork 섹션 참조.

## Proven Runs

| Date | Case/Step | Result | Artifact |
|---|---|---|---|
| 2026-06-15 | needmorefal 카드 rank 수집 | 11,000 entries, 0 errors, 0 duplicates | `Gunsmith_Mailbox/reports/auro_rank_1_11000.json` |

## Open Risks

- **Step 2 enrichment 미진행**: SOFTC.ONE에서 peak/avgViewers/chart 보강 필요하나 operator 보류.
- **devalue format 파싱**: SvelteKit `__data.json`은 JSON이 아닌 devalue format. 파서가 별도 필요하며, 형식 변경 시 깨질 수 있음.
- **sandbox 제한 지속 여부**: 향후 CLI에서 auro.live 직접 접근 가능해지면 route 재검토.
