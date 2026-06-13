# 구비바 CASE DOSSIER v3

**패키지 생성일:** 2026-06-11  
**위상:** private validation case / Deep-Dive in progress  
**기준 체계:** MASTER v2 M7.1 + 스트리머 채널진단 방법론 v3 draft  
**공개경계 기본값:** 🔴 red/private

---

## 0. 먼저 읽을 것

이 파일은 구비바 케이스의 **사람용 통합 정본**이다.  
세부 JSON/CSV/원자료는 각 하위 폴더에 분리되어 있다.

권장 열람 순서:

1. `README.md`
2. `구비바_CASE_DOSSIER_v3.md`
3. `machine/구비바_project_v3.json`
4. `source_inputs/current_analysis/구비바_§1_입력자료_v3.md`
5. `source_inputs/current_analysis/구비바_§6§7§9_진입자료.md`
6. `data/cohort/specs/구비바_§4_코호트_방법론_v2_20260610.md`

---

## 1. 현재 상태 요약

| 영역 | 상태 | 메모 |
|---|---|---|
| §1 정체성 추출 | 완료 | 5차 디스코드 면담 기반, 본인 발화·본인 확인 자료 |
| §2 데이터 정합성 | 통과 | 1년 일별 방송 통계 존재 |
| §3 측정 보정 | 통과 | 노방종 0일, 보정 미적용 통과 |
| §4 코호트 구축 | 대기/다음 단계 | 주 코호트=종합게임, 보조 코호트=버추얼 |
| §5 6단계 진단 | 대기 | §4 final cohort 이후 진행 |
| §6 목표 트레이드오프 | 진입자료 있음 | 본 분석 전 |
| §7 콘텐츠 채널 효과 | 진입자료 있음 | O17 쇼츠 결과 확인 필요 |
| §8 XGPS | 미진행 | §5 이후 입력 패키지 필요 |
| §9 산출물 설계 | 진입자료 있음 | 최종 리포트 작성 금지, 전달설계 우선 |
| CaseResult | stub | `machine/구비바_CaseResult_v3_stub.json` |
| PortfolioRow | not_ready | §4/§5 미완료 |
| PublicDemoRow | blocked | 실제 발화·도네·자기정의·MCN 정보 식별/민감 |

---

## 2. 케이스 한 줄 현재 정의

구비바 케이스는 **정체성은 강하게 잡혔지만, 코호트 위치와 성장 병목 진단은 아직 닫히지 않은 private Deep-Dive 케이스**다.

핵심 정체성은 다음 축으로 요약된다.

> 동네 누나·여동생 톤의 “광대 + 샌드백”을 본인 의도로 깔고, 시청자가 이를 “멘헤라 꾸숭이” 계열로 받아들이는 종합게임 힐링 채널.

단, 위 문장은 클라이언트 내부 분석용 표현이며 외부 공개용으로 직접 쓰지 않는다.

---

## 3. 본인명시 / 통합해석 구분

이 케이스의 수집 재료는 디스코드 면담 기반이므로, 현재 수집된 주요 재료는 **본인 발화 기반**으로 처리한다.

다만 다음 구분을 유지한다.

| 층위 | 설명 | 상태 |
|---|---|---|
| 구성 재료 | 매력 의심, 도네 자기검열, “전업 같은 취미” 자기정의 등 본인이 말한 재료 | 본인 발화 기반 |
| 통합 구조 | 위 재료들을 “자기 가치 평가 낮춤”이라는 동일 뿌리로 묶는 분석 | 분석가 통합 해석 |
| 다음 확인 | 산출물 전달 후 본인이 이 통합 구조를 수용/교정하는지 확인 | pending client response |

canonical 값:

```json
{
  "components_source": "self_statement",
  "synthesis_status": "analyst_synthesis_pending_client_response",
  "interpretation_status": "open_claim",
  "claim_level": "L4_intervention_candidate",
  "disclosure_tag": "red"
}
```

---

## 4. 핵심 Claim / Open / Action

### 4.1 확정에 가까운 Claim

- §1 정체성은 본인 의도와 시청자 수용 사이의 격차가 작다는 방향으로 강하게 정리됨.
- 본인 자발 어휘가 풍부하고, 정체성 표지로 활용 가능함.
- 노방종/장시간 보정은 구비바 케이스에서 큰 왜곡 요인으로 보이지 않음.

### 4.2 강한 통합해석이지만 전달 후 반응 확인이 필요한 Claim

- 매력 의심, 도네 자기검열, “전업 같은 취미” 자기정의 격차는 동일한 자기 가치 평가 낮춤 구조에서 나오는 것으로 보임.
- 이 통합해석은 핵심 O13이며, 최종 리포트 본문에서 단정형으로 던지기보다 토론 배틀/반응 검증형으로 설계해야 함.

### 4.3 Open

- O4: §4 코호트 finalization 필요.
- O13: 통합진단 전달설계 및 산출물 전달 후 반응 확인 필요.
- O17: 쇼츠 1개 수행 여부 확인 필요.
- §5: 6단계 진단 미완료.
- §8: XGPS 미진행.

### 4.4 다음 Action

1. §4 Charles 진단 재개
2. Arthur ExecutionProtocol 보강
3. 종합게임 주 코호트 + 버추얼 보조 코호트 수집
4. cohort_final.csv / robustness table 생성
5. §5 6단계 진단
6. CaseResult를 stub → partial로 승격

---

## 5. §4 코호트 구축 상태

결정:

- 주 코호트: 치지직 종합게임 스트리머
- 보조 코호트: 치지직 버추얼 스트리머

현재 포함된 spec:

- `data/cohort/specs/구비바_§4_cohort_spec_v2_20260610.json`
- `data/cohort/specs/구비바_§4_코호트_방법론_v2_20260610.md`
- `data/cohort/specs/구비바_§4_column_contract_v2_20260610.csv`
- `data/cohort/specs/구비바_§4_Charles_진단요청_v2_20260610.md`
- `data/cohort/specs/구비바_§4_Arthur_ExecutionProtocol_v2_TEMPLATE_20260610.json`

아직 없음:

- `cohort_final.csv`
- `cohort_robustness_table.csv`

---

## 6. 폴더별 역할

```text
구비바_CASE_PACKAGE_v3_20260611/
  README.md                       # 패키지 사용법
  구비바_CASE_DOSSIER_v3.md         # 사람용 통합 정본
  MANIFEST.json                    # 파일 목록/해시

  machine/                         # 기계용 정본 JSON/CSV
  data/                            # 통계·코호트 데이터
  deliverables/                    # 클라이언트 전달물, 현재는 대기
  source_inputs/                   # 입력자료/원자료
  references/                      # 방법론/마스터 기준 문서
  work/                            # 중간 작업 산출물
  archive/                         # 이전 패키지/백업
```

---

## 7. 공개경계

구비바 케이스는 현재 기본적으로 🔴 red/private이다.

공개 금지:

- 실제 디스코드 면담 발화 원문
- 본인 고유 어휘의 식별 가능한 조합
- 도네/수입/자기정의 관련 구체 발화
- MCN명 및 추천 맥락
- O13 통합진단 전달문
- 산출물 전달 후 반응 로그

부분공개 가능 후보:

- “종합게임 주 코호트 + 버추얼 보조 코호트”라는 방법론적 구조
- “본인 발화 기반 재료와 분석가 통합해석을 분리한다”는 일반 원칙
- “실행 미이행을 실패가 아니라 장벽 데이터로 기록한다”는 일반 원칙

---

## 8. 현재 기준 정본 파일

| 유형 | 파일 |
|---|---|
| project | `machine/구비바_project_v3.json` |
| CaseResult | `machine/구비바_CaseResult_v3_stub.json` |
| EvidencePackage | `machine/구비바_EvidencePackage_v3_initial.json` |
| AbsenceInventory | `machine/구비바_AbsenceInventory_v3_initial.json` |
| DisclosureLog | `machine/구비바_DisclosureLog_v3_initial.json` |
| Validation row | `machine/구비바_ValidationCaseRegistryRow_v3.json` |
| 원자료 | `source_inputs/original_raw/` |
| 현재 분석자료 | `source_inputs/current_analysis/` |
| 코호트 spec | `data/cohort/specs/` |

---

## 9. 다음 작업 체크리스트

- [ ] O17 쇼츠 결과 확인
- [ ] §4 Charles 공개 데이터 경로 진단
- [ ] Arthur ExecutionProtocol 실제 source URL로 보강
- [ ] 주/보조 코호트 수집
- [ ] 팔로워 매칭
- [ ] cohort_final.csv 생성
- [ ] robustness table 생성
- [ ] §5 6단계 진단
- [ ] O13 전달 설계 작성
- [ ] CaseResult partial 승격
- [ ] 클라이언트 전달물 초안 작성

