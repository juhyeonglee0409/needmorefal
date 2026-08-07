# 대한민국 버튜버 레지스트리 로컬 부트스트랩 보고서

- 상태: `completed_local_bootstrap_unreviewed`
- 생성: 2026-08-05T23:08:46+0900
- 외부 네트워크 접근: 없음
- secret 저장: 없음

## 결과

| 항목 | 건수 |
|---|---:|
| 소프트콘 플랫폼 원본 | 7,489 |
| 주간 시계열 입력 | 7,472 |
| 정규화 계정 | 8,193 |
| 임시 페르소나 | 8,193 |
| 관측 레코드 | 241,689 |
| 조직 시드 | 12 |
| 리뷰 항목 | 800 |

## 플랫폼

| 플랫폼 | 계정 |
|---|---:|
| chzzk | 7,907 |
| cime | 177 |
| soop | 109 |

## 조인 감사

- 주간 시계열 직접 플랫폼 연결: 6,768
- 32자리 ID 형태로 치지직 판정: 704
- 플랫폼 미해결: 0
- 소프트콘 원본에 있으나 주간 시계열이 없는 계정: 721
- 치지직 프로필 조인: 7,201
- 프로필 전용 추가 계정: 0

## 리뷰 큐

| 사유 | 건수 |
|---|---:|
| `agency_domain_requires_organization_mapping` | 11 |
| `cross_platform_same_name_no_auto_merge` | 60 |
| `organization_seed_requires_official_source` | 12 |
| `platform_inferred_from_chzzk_id_shape` | 704 |
| `public_name_changed_between_sources` | 13 |

## 판정

플랫폼 키는 `platform + platform_account_id`로 분리되어 SOOP·CIME·치지직 ID가 섞이지 않는다.
같은 이름의 타 플랫폼 계정은 자동 병합하지 않았고 리뷰 큐로만 보냈다.
현재 persona는 계정당 하나의 임시 개체이므로, 공식 교차링크 검증 후 병합해야 실제 인원 수가 된다.

## 다음 게이트

1. `manual_qa_sample_100.csv` 100건 수동 대조
2. 704개 치지직 ID형 추론 계정의 공개 프로필 보강
3. SOOP 109·CIME 177계정의 공식 계정 ID와 프로필 연결 검증
4. 조직 시드에 공식 출처를 붙인 뒤 affiliation 생성
