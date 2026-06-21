# 구비바 CASE DOSSIER v3

**패키지 생성일:** 2026-06-11 (최종 갱신: 2026-06-21)  
**위상:** private validation case / Deep-Dive in progress  
**기준 체계:** MASTER v2 M7.1 + 스트리머 채널진단 방법론 v4 draft  
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
| §4 코호트 구축 | **완료** | T1 종합게임 184ch, T2 버추얼 196ch, 유니크 323ch, robustness R1-R7 |
| §5 6단계 진단 | **완료 (정본 v3)** | 코호트 방송기록 309ch/24,056건 수집, 6건 리뷰 반영 |
| §5/§6 576 VTuber 보조 진단 | **완료** | 576ch 3-layer(A50/B106/C420), 4강2약 구조 확인 |
| §6 목표 트레이드오프 | **완료 (정본 v2)** | 1만+200 불가 판정, 현실 목표 재설정, 수익 모델 교정 |
| §7 유튜브 타당성 | **완료** | 상위밴드 84ch 샘플, YT↔리텐션 무상관(r≈0), full_vod→clip 전환 권고 |
| §8 XGPS | **완료 (정본 v1)** | Layer A/C 42ch 4,482건. 2수렴·3발산 확인 |
| §9 산출물 설계 | **완료 (정본 v1)** | 6모듈 전달구조, O13 토론배틀 보조, 반응로그 템플릿 |
| CaseResult | **partial** | `machine/구비바_CaseResult_v3_partial.json` (§5~§9 반영) |
| PortfolioRow | not_ready | CaseResult partial 승격 후 |
| PublicDemoRow | blocked | 실제 발화·도네·자기정의·MCN 정보 식별/민감 |

---

## 2. 케이스 한 줄 현재 정의

구비바 케이스는 **§1~§9(정체성·위치·성장·트레이드오프·유튜브·XGPS·산출물설계)가 모두 닫혔고, CaseResult partial 승격과 전달 전 산출물 갱신만 남은 private Deep-Dive 케이스**다.

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

### 4.2 §5 진단에서 확정된 Claim

- 코호트 대비 현재 위치 우위: peak +26~28%, avg +28~40% (정적 비교, 동적 판단 불가).
- 잔류율 우위: avg 격차 > peak 격차 → 시청자가 머무르면서 성장.
- 4축 균형 성장: peak_median +18%, avg +16%, chat +18%, follower +51%.
- 효율 백분위(상위 25~30%)는 실력이 아닌 체급 소형에서 오는 구간 효과 — 통계적 착시.
- 저녁 시간대 성과 저조 확인, 단 카테고리 교란 미분리로 원인 미확정.
- 576 VTuber 보조 코호트: 4강2약 구조 (전환·피크·효율·방송시간 상위, 팔로워·리텐션 하위). B+C(526ch) 확장 시에도 동일 패턴.

### 4.3 §6 목표 트레이드오프에서 확정된 Claim

- 본인 목표(1만 팔로워 + 평청 200)는 코호트 관측 범위 밖. 두 방법(구간 중앙값, log-log 회귀) 모두 1만에서 avg 30 내외가 최선 추정. 평청 200 불가.
- 체급 상승 비용: 효율(peak/follower)은 구간마다 약 절반으로 하락 (500-1k 2.63% → 1k-3k 1.75% → 3k-5k 0.92%).
- 잔류율(0.712, 86.4%ile)의 절반은 “peak이 올라가야 할 만큼 안 올라감”에서 기인 — 체급 올리면 잔류율 자체의 의미가 달라짐.
- 현실 목표 권고: 1차 3,000 팔로워 / peak 35 / avg 21 / 잔류율 0.6 이상, 경보선 eff_peak 0.7% 이하.
- 수익 모델: 현재 체급 월 2~5만원, 1만 도달 시 월 30~60만원 (후원 + 광고 + 유튜브). 전업 전환 가능 수준(200만+)까지는 3만+ 팔로워 + 적극적 수익화 필요.

### 4.4 §7 유튜브 타당성에서 확정된 Claim

- 상위밴드(10k+) 84ch 중 92.9%가 유튜브 보유, 79.5% 활성 → 사실상 표준 인프라.
- 유튜브 구독자/업로드 빈도 ↔ 치지직 리텐션: 상관 없음 (r≈0). 유튜브는 도달(reach) 채널이지 리텐션 도구가 아니다.
- full_vod 전략은 잔류율 최하위(median 0.564). clip + highlight가 상위밴드 69.2%로 주류.
- 구비바 유튜브(@GOOBIBA02): 구독자 166명(하위 9.3%ile), 367개 풀VOD, 7개월 휴면.
- 권고: 유튜브 재시작 필요하나, 리텐션 개선(P0) 이후. 재시작 시 full_vod 폐기 → clip/highlight 전환.

### 4.5 §8 XGPS 교차검증에서 확인된 Claim

수렴 2건:
- 모든 체급에서 긴 방송 = 잔류율 하락 (r=-0.24~-0.37). 구비바의 감소가 가장 완만(-0.0115/h).
- 모든 체급에서 주말 시청자 소폭 우위 (+5~14%).

발산 3건:
- **방송길이→시청자 관계가 체급 의존.** 중소(LC)는 r=0.25(긴 방송=더 많은 시청자), 상위(LA)와 구비바는 r≈0(무상관). 구비바가 무상관인 이유: 월 102.9h(코호트 20배)로 방송시간의 한계수익 소진.
- **저녁 시간대 효과가 체급마다 반대.** 동체급(LC)에서 저녁=프라임타임(peak_z +0.33)인데, 구비바만 저녁 최저. 시간대 자체의 문제가 아닌 구비바 고유 요인(생활국면 정체기/카테고리 교란).
- **talk vs game이 구비바만 역전.** LA/LC 모두 game > talk. 구비바만 talk(pk 26) > game(pk 19) → 시청자가 게임이 아닌 스트리머 자체에 반응하는 구조.

### 4.6 강한 통합해석이지만 전달 후 반응 확인이 필요한 Claim

- 매력 의심, 도네 자기검열, “전업 같은 취미” 자기정의 격차는 동일한 자기 가치 평가 낮춤 구조에서 나오는 것으로 보임.
- 이 통합해석은 핵심 O13이며, 최종 리포트 본문에서 단정형으로 던지기보다 토론 배틀/반응 검증형으로 설계해야 함.

### 4.7 Open

- O13: 통합진단 전달설계 및 산출물 전달 후 반응 확인 필요.
- O17: 쇼츠 1개 수행 여부 확인 필요.

### 4.8 다음 Action

1. CaseResult를 stub → partial로 승격 (§5~§9 결과 반영)
2. 전달 전 산출물 갱신 (2부 종합 리포트 §8 반영, 1부 PDF 재생성, 보고가이드 v2)
3. 2부 보고가이드 본문 작성
4. 클라이언트 전달 → 산출물 반응 로그 기록

---

## 5. §4 코호트 구축 — 완료

| 항목 | 값 |
|---|---|
| T1 main_general_game | 184ch (final_include) |
| T2 aux_virtual | 196ch (final_include) |
| 유니크 합계 | 323ch (57ch 중복) |
| robustness | R1-R7 완료 |

spec 파일:

- `data/cohort/specs/구비바_§4_cohort_spec_v2_20260610.json`
- `data/cohort/specs/구비바_§4_코호트_방법론_v2_20260610.md`
- `data/cohort/specs/구비바_§4_column_contract_v2_20260610.csv`

final 데이터:

- `data/cohort/collected/cohort_final_main_general_game.csv`
- `data/cohort/collected/cohort_final_aux_virtual.csv`
- `data/cohort/collected/cohort_robustness_table.csv`

## 5-2. §5 6단계 진단 — 완료 (정본 v3)

| 항목 | 값 |
|---|---|
| 코호트 방송기록 | 309ch (T1=178, T2=139), 317 CSV, 24,056 broadcasts |
| 수집 도구 | nodriver (Vercel WAF 통과), 95.7% success rate |
| 구비바 데이터 | 585건 (2023.10~2026.06) |
| 14h+ 제외 | 코호트 603건, 구비바 0건 |
| 리뷰 | 6건 반영 완료 (효율구간효과, dip서술, 저녁미확정, 정적동적구분, chat품질주의, 수집실패패턴) |

정본 파일: `work/step5_diagnosis/구비바_§5_정본진단_20260615.md`

## 5-3. §5/§6 576 VTuber 보조 진단 — 완료

| 항목 | 값 |
|---|---|
| 코호트 | 576 VTuber (치지직 SOFTC.ONE 전수) |
| 관측 기간 | 45일 |
| 3-layer 구조 | A(상위 50), B(동체급 106), C(성장참조 420) |
| 구비바 Layer B 위치 | 전환 71.7%ile, 피크 75.9%ile, 효율 73.1%ile, 방송시간 62.7%ile, 팔로워 27.8%ile, 리텐션 25.0%ile |
| 판정 | 4강2약 (전환·피크·효율·방송시간 상위, 팔로워·리텐션 하위) |

정본 파일: `deliverables/gubiva_§5§6_576cohort_diagnosis_20260619.md`

## 5-4. §6 목표 트레이드오프 — 완료 (정본 v2)

| 항목 | 값 |
|---|---|
| 본인 목표 | 1만 팔로워 + 평청 200 |
| 판정 | 두 방법 모두 불가. 1만 도달 시 avg 30 내외가 최선 추정 |
| 현실 목표 권고 | 1차 3,000 fol / peak 35 / avg 21 |
| 경보선 | eff_peak 0.7% 이하 → 속 빈 성장 |
| 수익 모델 | 현재 월 2~5만원, 1만 시 월 30~60만원 |

정본 파일: `work/step6_tradeoff/구비바_§6_목표트레이드오프_20260616.md`

## 5-5. §7 유튜브 타당성 — 완료

| 항목 | 값 |
|---|---|
| 샘플 | 상위밴드 271ch 중 84ch (31%) |
| YT 보유율 | 92.9% (78/84) |
| YT↔리텐션 상관 | r≈0 (무상관) |
| full_vod 잔류율 | median 0.564 (최하위) |
| 구비바 YT | @GOOBIBA02, 구독 166, 풀VOD 367개, 7개월 휴면 |
| 권고 | 리텐션 30%+ 도달 후 유튜브 재시작, full_vod→clip/highlight 전환 |

정본 파일: `deliverables/gubiva_§7_youtube_feasibility_20260619.md`

## 5-6. §8 XGPS 교차검증 — 완료 (정본 v1)

| 항목 | 값 |
|---|---|
| Layer A | 19ch, 1,706건 (peak median 1,276) |
| Layer C | 23ch, 2,194건 (peak median 66) |
| 구비바 | 1ch, 582건 (peak median 19) |
| 수렴 | 2건: 잔류율×방송길이 감소, 주말 우위 |
| 발산 | 3건: 방송길이→시청자 체급 의존, 저녁 시간대 구비바 역전, talk>game 구비바 역전 |

핵심 발견: 구비바의 방송길이 무상관(r≈0)은 "상위 채널 포화 패턴"과 동일 → 월 102.9h의 한계수익 소진. 저녁 저조와 talk>game은 구비바 고유 요인.

정본 파일: `work/step8_xgps/구비바_§8_XGPS_교차검증_20260621.md`  
런노트: `work/step8_layer_ac_broadcasts/구비바_§8_layer_ac_broadcast_collection_run_20260620.md`

---

## 6. 폴더별 역할

```text
구비바_CASE_PACKAGE_v3_20260611/
  README.md                       # 패키지 사용법
  구비바_CASE_DOSSIER_v3.md         # 사람용 통합 정본
  MANIFEST.json                    # 파일 목록/해시

  machine/                         # 기계용 정본 JSON/CSV
  data/                            # 통계·코호트 데이터
  deliverables/                    # 클라이언트 전달물 (1부+2부 리포트, 차트, 보고가이드)
  source_inputs/                   # 입력자료/원자료
  references/                      # MASTER 프레임워크 (방법론은 프로젝트 루트 references/로 이동)
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
| 코호트 final | `data/cohort/collected/cohort_final_*.csv` |
| 코호트 robustness | `data/cohort/collected/cohort_robustness_table.csv` |
| 코호트 방송기록 | `data/cohort/collected/broadcast_samples/T1/, T2/` (317 CSV) |
| §5 정본진단 | `work/step5_diagnosis/구비바_§5_정본진단_20260615.md` (v3) |
| §5/§6 576 VTuber 진단 | `deliverables/gubiva_§5§6_576cohort_diagnosis_20260619.md` |
| §6 목표 트레이드오프 | `work/step6_tradeoff/구비바_§6_목표트레이드오프_20260616.md` (v2) |
| §7 유튜브 타당성 | `deliverables/gubiva_§7_youtube_feasibility_20260619.md` |
| §8 XGPS 교차검증 | `work/step8_xgps/구비바_§8_XGPS_교차검증_20260621.md` (v1) |
| §8 Layer A/C 방송기록 | `work/step8_layer_ac_broadcasts/` (42 CSV, 4,038건) |
| §9 산출물설계 | `work/step9_deliverable_design/구비바_§9_산출물설계_20260621.md` (v1) |
| O13 토론배틀 보조 | `deliverables/gubiva_O13_토론배틀보조_v1.md` |
| 산출물 반응 로그 | `deliverables/gubiva_산출물반응로그.csv` (빈 템플릿) |
| 1부 클라이언트 리포트 | `deliverables/gubiba_part1_client_report_v3_20260619.md` |
| 2부 종합 리포트 | `deliverables/gubiva_full_report_v3_20260619.md` |
| 언니채널 궤적매칭 | `deliverables/구비바_언니채널_궤적매칭_v2.md` |
| 보고가이드 합본 | `deliverables/gubiba_보고가이드_합본_v1.md` (1부 v2 + 2부 v1 통합) |
| CaseResult partial | `machine/구비바_CaseResult_v3_partial.json` |
| 구비바 방송요약 | `data/daily_stats/구비바_방송별_요약_586건_20260615.csv` |
| 방법론 정본 | `../references/스트리머_채널진단_방법론_v4_draft_20260620.md` (프로젝트 루트) |

---

## 9. 다음 작업 체크리스트

- [x] §4 코호트 구축 (T1 184ch, T2 196ch, robustness R1-R7)
- [x] 코호트 방송기록 수집 (nodriver 309/323ch, 24,056건)
- [x] §5 6단계 정본 진단 (v3, 6건 리뷰 반영)
- [x] §5/§6 576 VTuber 보조 진단 (3-layer, 4강2약)
- [x] §6 목표 트레이드오프 분석 (정본 v2, 수익 모델 교정)
- [x] §7 유튜브 타당성 분석 (상위밴드 84ch 샘플, r≈0)
- [x] §8 XGPS 데이터 수집 (Layer A/C 42/44 CSV, 4,038건)
- [x] §8 XGPS 교차검증 분석 (정본 v1, 2수렴 3발산)
- [x] 1부 클라이언트 리포트 초안 (v3)
- [x] 2부 종합 리포트 초안 (v3)
- [x] 언니채널 궤적매칭 v2
- [x] §9 산출물 설계 + O13 전달설계 (정본 v1, 토론배틀 보조 v1)
- [x] CaseResult partial 승격 (§5~§9 반영, partial.json 생성)
- [x] 2부 종합 리포트 §8 XGPS 반영 (v4, Phase 1~3 복구 + §8-b 추가)
- [x] 보고가이드 합본 v1 (1부 v2 + 2부 v1 → 단일 문서 통합)
- [ ] O17 쇼츠 결과 확인
- [ ] 1부 PDF/DOCX v3 재생성
- [ ] 차트 PNG v3 재생성
- [ ] 클라이언트 전달 → 반응 로그 기록

