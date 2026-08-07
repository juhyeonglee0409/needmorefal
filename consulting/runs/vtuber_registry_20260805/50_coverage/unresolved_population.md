# 미해결 모집단과 커버리지 현황

- 상태: `in_progress_manual_qa_and_platform_expansion_pending`
- 생성: 2026-08-05T23:52:06+0900
- 로그인 세션 사용: 없음
- 외부 연락: 없음

## 현재 원장

| 항목 | 건수 |
|---|---:|
| sources | 57 |
| personas | 8,203 |
| accounts | 8,217 |
| organizations | 16 |
| affiliations | 39 |
| reviews | 828 |

| 플랫폼 | 계정 |
|---|---:|
| chzzk | 7,907 |
| cime | 177 |
| soop | 120 |
| youtube | 13 |

조직 시드 12곳은 공식 출처 검증을 마쳤고, 버츄얼 유니온 공식 회원사 4곳을 추가했어요.
공식 소속과 이름이 정확히 하나의 기존 persona에 대응한 39건만
affiliation으로 물질화했어요.

## 열린 검토 항목

| 사유 | 건수 |
|---|---:|
| `agency_domain_requires_organization_mapping` | 5 |
| `cross_platform_same_name_no_auto_merge` | 60 |
| `official_roster_name_not_exact_unique` | 9 |
| `official_soop_cross_platform_identity_ambiguous` | 1 |
| `platform_inferred_from_chzzk_id_shape` | 704 |
| `public_name_changed_between_sources` | 13 |
| `public_name_changed_since_qa_sample` | 1 |

## 알려진 커버리지 공백

- `softcon_soop_official_handle_gap`: 0건. Official ISEGYE IDOL SOOP handles absent from the Softcon seed.
- `softcon_cid_not_official_soop_handle`: 0건. AKAIV official SOOP handles require identity reconciliation; Softcon cid is not assumed to be the handle.
- `youtube_independent_population_not_systematically_discovered`: 규모 미산정. 13 official-linked YouTube seed accounts are present, but YouTube-only and independent YouTube-primary Korean VTubers remain outside the current population frame.
- `manual_qa_incomplete`: 100건. The stratified 100-account manual QA sheet is not yet closed.

## 수동 QA

- 표본: 100건
- 완료: 0건
- 미완료: 100건

공개 프로필 사전 검증은 CHZZK 98건을 완료했어요.
기존 이름이 있던 87건 중
86건이 일치했고, 1건은
이름 변경 검토 큐로 보냈어요. 빈 이름 11건은 현재 공개 이름으로 채웠어요.
프로필 텍스트에 버튜버 표현이 명시된 것은 3건뿐이므로,
텍스트 신호가 없는 계정은 자동 확정하지 않았어요.

따라서 현재 원장은 CHZZK·SOOP·CIME의 강한 출발점이지만, 아직 대한민국 활동 버튜버
‘전원’ 원장이라고 부를 단계는 아니에요. 다음 모집단 확장은 YouTube-only/YouTube-primary
계정 발견과 공식 SOOP 계정 후보 11건의 식별 병합이에요.
