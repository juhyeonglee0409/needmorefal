# 대한민국 버튜버 전수 레지스트리 구축 프로토콜 v0.1

- 작성일: 2026-08-05
- 상태: `draft / operator review required`
- 적용 프로젝트: needmorefal Streamer Consulting
- 목적: 대한민국 버튜버 산업의 공개 활동자 모집단을 재현 가능하게 발견·검증·갱신하는 마스터 레지스트리 구축
- 현재 단계: 설계와 로컬 사전준비. 외부 수집, 로그인 세션 사용, 연락, 발송은 미승인·미실행

---

## 0. 결론부터

이 작업은 이름 목록을 만드는 일이 아니다. 다음 세 층을 분리해 구축한다.

1. **마스터 레지스트리**: 버튜버 페르소나, 플랫폼 계정, 조직, 소속 관계, 활동 상태, 근거
2. **관측 스냅샷**: 팔로워·방송 활동·시청 지표처럼 시간에 따라 바뀌는 값
3. **파생 뷰**: 기업세/개인세 시장 지도, 플랫폼별 현황, 컨설팅 잠재고객 등 목적별 결과물

기존 `tools/outreach/` 풀은 3번 중 ‘개인세 영업 후보’에 해당한다. 이를 마스터로 사용하면 기업세와 연락처 없는 개인세가 구조적으로 누락된다. 따라서 기존 자료는 중요한 입력으로 재사용하되, 새 레지스트리는 영업 여부와 무관한 중립 스키마로 만든다.

---

## 1. 이미 확보된 자산과 실제 출발점

### 1.1 재사용 가능한 자산

| 자산 | 규모/상태 | 이번 작업에서의 역할 |
|---|---:|---|
| `D:/Gunsmith_Mailbox/reports/softcon_virtual_census_20260704.ndjson` | 소프트콘 버추얼 7,489계정: 치지직 7,203·SOOP 109·CIME 177 | 플랫폼이 보존된 공통 모집단 주 시드 |
| `runs/census_full_20260708/census_full_weekly.ndjson` | 7,472채널, 최대 53주 시계열. 조립 과정에서 플랫폼 필드 소실 | 시계열 보강용. 단독 정체성 키로 사용 금지 |
| `runs/vtuber_outreach_pilot_20260704/census_pool.ndjson` | 7,204행, 치지직 프로필·bio·팔로워·분류 | 치지직 계정의 프로필 보강 |
| `runs/vtuber_outreach_pilot_20260704/softcon_chzzk_census_20260704.ndjson` | 7,203채널 | 이전 스냅샷과 구성 변화 비교 |
| `tools/outreach/chzzk.py` | 공개 검색·프로필 API 클라이언트 | 치지직 freshness 확인 모듈로 재사용 후보 |
| `tools/outreach/pool.py` | append-only NDJSON, progress flush | 레지스트리 이벤트 로그 설계 참고 |
| `tools/outreach/agencies.yaml` | 소속사명·도메인 보수적 시드 | 조직 발견 시드. 정본으로 사용하지 않음 |
| `site_runbooks/CHZZK_RUNBOOK.md` | 공개 surface와 실패 신호 기록 | 치지직 외부 실행 규칙 |
| `site_runbooks/SOFTC_ONE_RUNBOOK.md` | 버추얼 랭킹과 대량 시계열 수집 실적 | 기존 시드의 출처·한계 확인 |

### 1.2 현재 자산의 한계

- 7월 4일 소프트콘 원본에는 치지직·SOOP·CIME가 함께 있고 `platform + cid`가 보존되어 있다.
- 7,472 시계열 조립본은 플랫폼을 버리고 `channel_id`만 남겼다. 7월 4일 원본과 6,768개 ID가 직접 연결되며, 미연결 704개는 모두 치지직형 32자리 16진 ID다. 새 레지스트리는 시계열 조립본의 `channel_id`를 플랫폼 독립 키로 사용하지 않는다.
- 2026-07-08 스냅샷이므로 신규 데뷔·졸업·이동을 반영하려면 freshness 확인이 필요하다.
- `solo.value`는 영업 필터용 이진값이라 기업세·매니지먼트형·크루형을 충분히 표현하지 못한다.
- `channel_id`는 플랫폼 계정 식별자이지 버튜버 페르소나 식별자가 아니다.
- 한 페르소나의 치지직·SOOP·YouTube 계정이 아직 하나의 개체로 연결되어 있지 않다.
- YouTube-only, SOOP-only, 기타 플랫폼 중심 버튜버는 별도 발견이 필요하다.

### 1.3 출발 원칙

```text
소프트콘 7,489계정 = 치지직·SOOP·CIME를 포함한 가장 큰 검증된 시드
계정 정본 키 = softcon platform + cid
7,472 시계열 = 플랫폼을 복구한 뒤에만 계정에 연결
마스터의 단위 = 채널이 아니라 공개 버튜버 페르소나
플랫폼 계정 = 페르소나에 연결되는 별도 개체
영업 적합성 = 마스터 확정 후 생성하는 파생값
```

---

## 2. 모집단 정의

### 2.1 기본 정의안

> 기준일 현재, 한국어권 시청자를 주요 대상으로 하며, 지속적인 가상 캐릭터 정체성을 사용해 공개 콘텐츠를 제공하는 페르소나.

국적·거주지는 공개 활동만으로 정확히 확인하기 어렵고 산업 분석에도 불필요한 경우가 많다. 따라서 기본 모집단은 **대한민국 국적자**가 아니라 **한국 버튜버 시장 활동자**로 정의한다.

### 2.2 포함 기준

아래 A와 B를 모두 충족하면 포함한다.

#### A. 한국 시장 신호

다음 중 하나 이상이 확인되어야 한다.

- 한국어가 주 활동 언어다.
- 치지직·SOOP 등 한국 시장 플랫폼이 주 활동면이다.
- 공식 프로필이 한국 시청자를 주 대상으로 명시한다.
- 한국 기업·크루·프로젝트의 공식 탤런트다.

#### B. 버튜버 정체성 신호

다음 중 하나 이상이 확인되어야 한다.

- 본인 또는 소속사가 버튜버·버추얼 스트리머로 명시한다.
- Live2D·3D·PNG 등 지속적인 가상 페르소나로 방송 또는 영상을 제작한다.
- 플랫폼의 버추얼 태그·카테고리에 반복적으로 관측된다.
- 여러 공개 콘텐츠에서 동일한 가상 정체성을 주된 출연자로 사용한다.

### 2.3 표현 형식 분류

PNG 사용자를 자의적으로 제외하지 않는다. 표현 방식과 활동 정체성을 분리한다.

```text
representation_mode:
  live2d
  three_d
  png
  vr_avatar
  mixed_virtual
  unknown
```

### 2.4 활동 상태

최근 방송 한 번만으로 활동/비활동을 이분화하지 않는다.

| 코드 | 판정 기준 |
|---|---|
| `active_30d` | 최근 30일 내 공개 라이브·영상·공식 활동 존재 |
| `active_90d` | 31~90일 내 공개 활동 존재 |
| `hiatus_declared` | 본인·소속사가 휴식 또는 활동 중단을 공지 |
| `dormant_365d` | 91~365일 내 활동은 있으나 최근 90일 없음 |
| `inactive` | 365일 이상 활동 증거 없음 |
| `graduated` | 공식 졸업·활동 종료 공지 확인 |
| `predebut` | 데뷔 예정이 공식적으로 공개됨 |
| `unknown` | 근거 부족 |

‘현재 활동하는 전원’의 기본 집계는 `active_30d + active_90d`다. 휴식·졸업·데뷔 예정은 레지스트리에 보존하되 활성 모집단에서는 분리한다.

### 2.5 운영 형태

기업세/개인세를 단순 소속 여부로 자르지 않는다.

```text
operating_model:
  agency_ip_owned          # 기업이 IP를 소유·운영
  creator_owned_managed    # 창작자 소유 IP + 매니지먼트 계약
  independent_team         # 개인세이나 제작·운영 팀 존재
  independent_solo         # 실질적 1인 운영
  corporate_character      # 기업 홍보·서비스 캐릭터
  project_collective       # 프로젝트·크루 단위 활동
  unknown
```

대외 요약에서는 필요에 따라 `기업세 / 개인세 / 경계형 / 불명`으로 접어 보여주고, 마스터에는 세부 운영형을 유지한다.

### 2.6 제외 기준

- 실제 방송인의 일회성 아바타·필터 사용
- 방송 정체성이 아닌 단순 채널 마스코트
- 팬 계정, 클립 계정, 다시보기 전용 계정
- 공식 독립 페르소나가 없는 그룹 공용 계정
- 자동 생성 캐릭터 채널 중 지속적인 수행 주체가 확인되지 않는 경우
- 비공개 정보나 추정된 실연자 신원에 의존해야만 연결되는 경우

그룹 공용 계정은 `organization_account`로 보존할 수 있지만 페르소나 수에는 포함하지 않는다.

---

## 3. 조사 단위와 데이터 모델

### 3.1 개체 분리

| 개체 | 의미 | 기본 키 |
|---|---|---|
| `persona` | 시청자가 인식하는 버튜버 정체성 | 내부 `persona_id` |
| `account` | 치지직·SOOP·YouTube 등의 플랫폼 계정 | `platform + platform_account_id` |
| `organization` | 기업·레이블·크루·프로젝트 | 내부 `organization_id` |
| `affiliation` | 페르소나와 조직의 기간별 관계 | 내부 `affiliation_id` |
| `source` | 판정에 사용한 공개 근거 | 내부 `source_id` |
| `observation` | 특정 시점의 활동·수치 관측 | 내부 `observation_id` |

### 3.2 persona 최소 필드

```json
{
  "persona_id": "krvt_p_...",
  "display_name": "",
  "public_aliases": [],
  "market": "ko_KR",
  "market_evidence": [],
  "vtuber_status": "confirmed|probable|review|excluded",
  "representation_mode": "live2d|three_d|png|vr_avatar|mixed_virtual|unknown",
  "operating_model": "agency_ip_owned|creator_owned_managed|independent_team|independent_solo|corporate_character|project_collective|unknown",
  "activity_status": "active_30d|active_90d|hiatus_declared|dormant_365d|inactive|graduated|predebut|unknown",
  "first_seen_at": "",
  "last_verified_at": "",
  "review_status": "auto|manual_confirmed|manual_rejected|needs_review",
  "source_ids": []
}
```

### 3.3 account 최소 필드

```json
{
  "account_id": "krvt_a_...",
  "persona_id": "krvt_p_...|null",
  "platform": "chzzk|soop|youtube|twitch|x|other",
  "platform_account_id": "",
  "handle": "",
  "canonical_url": "",
  "account_role": "primary|secondary|archive|clips|group|unknown",
  "last_public_activity_at": "",
  "first_seen_at": "",
  "last_verified_at": "",
  "source_ids": []
}
```

### 3.4 affiliation 최소 필드

```json
{
  "affiliation_id": "krvt_f_...",
  "persona_id": "krvt_p_...",
  "organization_id": "krvt_o_...",
  "relationship": "talent|member|managed|partner|former|unknown",
  "start_at": null,
  "end_at": null,
  "status": "current|former|announced|unknown",
  "source_ids": []
}
```

### 3.5 source 최소 필드

```json
{
  "source_id": "krvt_s_...",
  "url": "",
  "source_tier": "P0|P1|P2|P3|P4",
  "publisher": "",
  "observed_at": "",
  "supports": ["market", "vtuber_identity", "account_link", "affiliation", "activity"],
  "note": "",
  "secret_values_stored": false
}
```

### 3.6 시간변동 값 분리

팔로워·구독자·평균 시청자·마지막 방송일을 persona나 account 본문에 계속 덮어쓰지 않는다. `observations.ndjson`에 시점별로 append하고, 최신값은 파생 뷰에서 계산한다.

### 3.7 아웃리치 데이터 분리

공개 비즈니스 메일, 접촉 여부, 거절 여부는 마스터 정체성 레지스트리와 분리한다.

```text
registry master -> prospecting view -> outreach state
```

`opted_out`은 기존 아웃리치 시스템의 영구 상태를 그대로 보존하며, 레지스트리 갱신 여부와 무관하게 재접촉 대상에서는 제외한다.

---

## 4. 출처 계층

| 등급 | 출처 | 사용 원칙 |
|---|---|---|
| `P0` | 본인·소속사 공식 공지/공식 프로필 | 이름·소속·졸업·계정 연결의 최우선 근거 |
| `P1` | 플랫폼 공개 프로필·API·공식 채널 메타데이터 | 계정 ID·활동·공개 수치의 주 근거 |
| `P2` | 공개 통계 서비스·공신력 있는 산업 데이터베이스 | 발견·시계열 보강. 정체성 판정은 P0/P1과 교차 |
| `P3` | 위키·팬 디렉터리·차트·커뮤니티 목록 | 후보 발견 전용. 단독 확정 금지 |
| `P4` | 합방·팔로우·이름 유사성 등 관계망 추론 | 리뷰 큐 생성 전용. 자동 병합 금지 |

최종 확정은 원칙적으로 `P0 1건` 또는 `P1 2건`을 요구한다. P2~P4만 있는 경우 `probable` 또는 `review`로 남긴다.

---

## 5. 발견 전략

### 5.1 트랙 A — 기존 소프트콘 다중 플랫폼 모집단 부트스트랩

목표: 플랫폼이 보존된 7,489계정 census를 정체성 주축으로 삼고, 7,472채널 시계열을 안전하게 연결한다.

1. 소프트콘 원본의 `naverchzzk / afreeca / cime`를 각각 `chzzk / soop / cime` 정규 코드로 매핑한다.
2. `platform + cid`로 account를 생성하고 7,472 시계열 파일을 observation으로 분해한다.
3. 7,204 치지직 프로필 풀은 `chzzk + channel_id`로만 조인한다.
4. 7월 4일/8일 스냅샷 차이를 구성 변화로 기록한다.
5. 기존 `solo`·`outreach.status`는 마스터 판정에 사용하지 않고 원출처 보조값으로만 보존한다.
6. 미조인·이름 변경·중복·삭제 채널을 리뷰 큐로 분리한다.

이 단계는 전부 로컬에서 실행할 수 있으며 외부 접근이 필요 없다.

### 5.2 트랙 B — 기업세 조직 전수조사

목표: 사람을 검색하기 전에 조직을 전부 열거하고 공식 로스터를 내려받는다.

1. 기존 `agencies.yaml`, 치지직 시드의 소속 신호, 산업자료에서 조직 후보를 만든다.
2. 기업·레이블·크루·프로젝트를 구분한다.
3. 각 조직 공식 홈페이지·공식 SNS의 현재/과거 로스터를 확인한다.
4. 기수, 데뷔일, 졸업일, IP 소유형태가 공개된 경우 기록한다.
5. 그룹 공용 계정과 개별 페르소나 계정을 분리한다.

기업세 완성도는 `발견된 조직 중 공식 로스터 검증 완료 비율`로 측정한다.

### 5.3 트랙 C — SOOP 활동자 발견

SOOP의 1차 발견축은 별도 라이브 폴링이 아니라 **소프트콘 버추얼 랭킹의 `afreeca` 플랫폼 행**이다. 2026-07-04 원본에서 109계정이 확인되어 있다. 소프트콘 스냅샷을 갱신할 때마다 `afreeca -> soop`으로 정규화하고, SOOP 공식 프로필은 이름·활동 상태·공식 링크 보강에 사용한다.

사전 Scout에서 먼저 확인할 것:

- 버추얼 카테고리·태그·랭킹의 공개 surface
- 플랫폼 계정의 안정적 ID
- 페이지네이션과 최대 노출 범위
- 프로필과 최근 활동일 확인 경로
- 429·로그인·체크포인트 등 경계 신호

소프트콘에 아직 잡히지 않는 신생·초소형 SOOP 장기꼬리가 의심될 때만 평일/주말 라이브 스냅샷을 보조 발견축으로 추가한다. 한 번의 SOOP 랭킹 캡처를 전수로 간주하지 않는다.

### 5.4 트랙 D — YouTube 계정 보강

YouTube는 ‘버튜버 전체’ 카테고리를 제공하지 않으므로 검색만으로 전수조사할 수 없다. 다음 순서를 사용한다.

1. 치지직·SOOP·기업세 공식 프로필에 연결된 YouTube 채널을 우선 수집한다.
2. 알려진 채널 ID는 `channels.list` 배치로 메타데이터를 보강한다.
3. 공식 채널의 추천 채널·설명 링크·합방 크레딧으로 관계망을 확장한다.
4. 검색 API는 YouTube-only 장기꼬리 발견에만 사용한다.
5. 키워드×기간×정렬 방식별 결과 중복과 신규 수율을 기록한다.

검색 결과의 `totalResults`를 모집단 크기로 사용하지 않는다. 검색은 발견면이지 정본이 아니다.

### 5.5 트랙 E — 관계망 확장

확정된 페르소나마다 아래 공개 연결을 후보로 추가한다.

- 합방 상대
- 같은 기수·크루·서버·대회 참가자
- 공식 추천 채널
- 커버곡·콘서트·대회 크레딧
- 프로필에 직접 연결된 다른 플랫폼 계정

관계망에서 발견된 후보는 자동 확정하지 않고 `P4 -> review`로 들어간다.

### 5.6 트랙 F — 공개 제보와 정정

장기적으로는 본인·소속사·시청자가 다음 내용을 제보할 수 있는 폼이 필요하다.

- 신규 등록
- 계정 연결
- 소속 변경
- 휴식·졸업 상태
- 잘못된 병합·분리 요청

제보는 증거 URL을 필수로 받고, 자동 반영하지 않는다.

---

## 6. 동일인·중복 제거 규칙

### 6.1 자동 병합 허용

아래와 같은 명시적 연결만 자동 병합할 수 있다.

- 공식 프로필이 다른 플랫폼 계정을 직접 링크한다.
- 소속사 공식 로스터가 동일 페르소나의 계정을 함께 표기한다.
- 플랫폼 이전 공지에서 이전·신규 계정을 직접 연결한다.

### 6.2 수동 검토 후 병합

다음은 강한 보조신호이나 단독 자동 병합은 금지한다.

- 동일한 고유 캐릭터명과 이미지
- 동일한 공식 비즈니스 메일
- 동일한 Linktree 계정
- 여러 콘텐츠에서 상호 계정 연결을 반복 언급

### 6.3 병합 금지

- 이름이 같다는 이유만으로 병합
- 목소리·말투·그림체 유사성으로 병합
- 팬 위키의 전생 정보만으로 병합
- 비공개 실연자 신원을 추정해 병합
- 계정 삭제 후 등장한 새 페르소나를 임의 연결

전생·환생 연결은 당사자나 공식 조직이 공개적으로 연결한 경우에만 `public_alias` 또는 관계 레코드로 기록한다.

### 6.4 병합 확신도

```text
link_confidence:
  explicit       # 공식 직접 링크
  corroborated   # 독립된 강한 공개 근거 2개 이상 + 수동 검토
  tentative      # 가능성만 있음, 마스터 병합 안 함
  rejected
```

---

## 7. 단계별 실행 프로토콜

각 단계는 `작업 -> verify` 쌍으로 닫는다.

### P0. 목적·경계 동결

**입력**

- 본 문서
- 조사 목적: 산업 지도/분석 모집단/영업 기반

**작업**

- 모집단 정의, 기준일, 활동 기간, 포함 플랫폼, 외부 공개 여부를 확정한다.
- 기본안은 ‘한국어권 시장 + 최근 90일 + 전 플랫폼 + 내부 레지스트리’다.

**verify**

- 20개 경계 사례를 만들어 포함/제외 판정이 일관적인지 확인한다.

**산출물**

- `00_scope/scope_decision.yaml`
- `00_scope/boundary_cases.csv`

**중단 조건**

- 국적 기준과 시장 기준이 혼재함
- PNG·기업 캐릭터·하이브리드 방송인의 포함 기준이 미정

### P1. 스키마 동결과 로컬 변환기 준비

**작업**

- persona/account/organization/affiliation/source/observation 스키마를 JSON Schema로 고정한다.
- append-only 이벤트와 최신 materialized view를 분리한다.
- deterministic ID 생성 규칙을 정한다.

**verify**

- 샘플 30건이 스키마를 통과한다.
- 같은 입력을 두 번 넣어도 같은 ID가 생성된다.
- 이름 변경이 새 페르소나를 만들지 않는다.

**산출물**

- `specs/korean_vtuber_registry_schema_v0_1.json`
- `tools/vtuber_registry/` 로컬 변환·검증 모듈

**중단 조건**

- 플랫폼 계정 ID와 persona ID가 혼용됨
- 수치가 시점 없이 덮어써짐

### P2. 소프트콘 7,489 다중 플랫폼 로컬 부트스트랩

**작업**

- 플랫폼 보존 7,489계정 census를 `platform + cid`로 이관한다.
- 7,472 시계열과 7,204 치지직 프로필을 플랫폼 안전 키로 조인한다.
- 프로필·시계열·출처를 새 스키마로 변환한다.
- 기존 이진 `solo` 판정은 임시 참고값으로만 이관한다.

**verify**

- 입력 7,489계정의 손실 0건
- 중복 platform key 0건
- 조인 실패와 이름 충돌 전건 리뷰 큐 기록
- 무작위 100건 원본 대조

**산출물**

- `10_bootstrap/platform_accounts.ndjson`
- `10_bootstrap/platform_observations.ndjson`
- `40_review/platform_join_review.ndjson`
- `50_coverage/bootstrap_report.md`

### P3. 조직 레지스트리 구축

**작업**

- 조직 후보를 수집하고 공식 로스터를 검증한다.
- 현재·과거 소속과 운영형을 분리한다.

**verify**

- 조직마다 공식 출처 1개 이상
- 탤런트 수와 로스터 수의 차이 기록
- 무소속으로 분류된 대형 채널을 역검수

**산출물**

- `organizations.ndjson`
- `affiliations.ndjson`
- `40_review/affiliation_review.ndjson`

### P4. 플랫폼별 Scout

**작업**

- SOOP, YouTube, 필요시 기타 플랫폼에 대해 각각 1회의 좁은 공개 surface 진단을 수행한다.
- URL, ID, 페이지네이션, 활동일, 경계 신호, 예상 요청량을 기록한다.

**verify**

- 샘플 응답에서 안정적 ID 확인
- raw secret·cookie·token 저장 0건
- 전체 예상 시간과 배치 크기 계산

**산출물**

- 플랫폼별 ScoutReport 또는 동등한 run note
- 사이트 runbook patch candidate

**승인 게이트**

- 외부 Scout는 플랫폼별 operator 승인 후 실행한다.
- 로그인 세션이 필요하면 별도 명시 승인을 받는다.

### P5. 소규모 파일럿

**작업**

- 플랫폼별 100~300개 후보만 수집한다.
- 자동 분류와 수동 정답표를 비교한다.

**verify**

- 버튜버 포함 precision 97% 이상
- 계정 병합 precision 99% 이상
- 활동 상태 일치율 95% 이상
- boundary/error/timeout이 progress 로그에 남음

**중단 조건**

- 플랫폼 ID가 불안정함
- 오탐 기준 미달
- 429·challenge 이후 정상 범위 내 복구가 되지 않음
- 예상 시간 또는 요청량이 승인 범위를 초과함

### P6. 본 수집

**작업**

- 승인된 배치 크기로 순차 수집한다.
- 매 항목 또는 소배치마다 append·flush한다.
- resume cursor와 manifest를 유지한다.

**verify**

- 배치마다 건수·신규율·중복률·오류율을 보고한다.
- 1% 이상 오류 배치는 원인 확인 전 다음 배치로 확대하지 않는다.
- 429·checkpoint·로그인 경계 신호가 나오면 해당 경로를 중단하고 기록한다.

**산출물**

- `10_inputs/` 정규화된 공개 사실
- `20_normalized/` 개체별 append-only 데이터
- `run_manifest.json`
- `progress.ndjson`

### P7. 개체 연결과 수동 리뷰

**작업**

- 명시적 공식 링크를 우선 병합한다.
- 이름·메일·링크 중복 후보는 리뷰 큐로 보낸다.

**verify**

- 무작위 병합 100건 대조
- 모든 병합에 source_id 존재
- tentative 후보는 persona 수에서 임의 합산하지 않음

### P8. 활동 상태·운영형 확정

**작업**

- 기준일 기준 마지막 공개 활동을 계산한다.
- operating_model과 affiliation을 확정한다.

**verify**

- 기업세 표본 50, 개인세 표본 50 수동 대조
- 졸업·휴식은 공식 공지 우선
- 불명 값을 억지로 개인세에 넣지 않음

### P9. 커버리지 감사

**작업**

- 독립된 소스 간 중복과 신규 발견률을 측정한다.
- 플랫폼·조직·규모대별 누락 위험을 따로 평가한다.

**verify**

- 신규 소스/회차를 추가했을 때 활성 페르소나 신규율 기록
- 세 회차 연속 신규율 0.5% 미만이면 1차 포화 판정
- 플랫폼별 무작위 표본에서 누락률 측정
- 기업 공식 로스터의 레지스트리 포함률 측정

**산출물**

- `50_coverage/coverage_report.md`
- `50_coverage/source_overlap.csv`
- `50_coverage/unresolved_population.md`

### P10. 릴리스와 유지보수

**작업**

- 기준일이 명시된 내부 버전을 생성한다.
- 외부 공개본은 별도 승인 후 필요한 필드만 내보낸다.

**verify**

- 비공개 실연자 신원·secret·개인 연락처 추정값 0건
- 모든 레코드에 last_verified_at 존재
- 공개 주장과 coverage report가 일치

**표현 규칙**

`대한민국 버튜버 전원` 대신 다음처럼 쓴다.

> 2026-XX-XX 기준, 정의된 활동 조건을 충족하며 공개적으로 확인 가능한 한국어권 버튜버 레지스트리

---

## 8. 품질관리 지표

### 8.1 정확도

| 지표 | 파일럿 통과선 |
|---|---:|
| 버튜버 포함 precision | ≥ 97% |
| 계정-페르소나 병합 precision | ≥ 99% |
| 활동 상태 일치율 | ≥ 95% |
| 소속 관계 precision | ≥ 98% |
| platform key 중복 | 0건 |
| 근거 없는 확정 레코드 | 0건 |

### 8.2 완전성

완전성은 단일 백분율 하나로 주장하지 않는다.

- 플랫폼별 발견 수
- 조직 공식 로스터 포함률
- 소스별 신규 수율
- 장기꼬리 규모대별 표본 누락률
- unresolved·review·unknown 비율
- 최근 30/90일 활동일 확인률

### 8.3 포획-재포획 추정

치지직·SOOP·YouTube처럼 독립에 가까운 발견 집합의 중복을 이용해 미관측 모집단을 추정할 수 있다. 다만 플랫폼 간 활동 확률이 독립이 아니므로 절대값이 아니라 **누락 위험의 방향성 지표**로만 사용한다.

### 8.4 신규 발견 포화

```text
new_yield = 이번 회차 신규 확정 활성 페르소나 / 직전 마스터 활성 페르소나
```

동일한 시간대만 반복해서 포화로 오인하지 않도록 플랫폼·요일·시간대를 분리한다.

---

## 9. 실행 디렉터리 제안

실제 착수 시 새 run을 만들고 기존 자산을 덮어쓰지 않는다.

```text
consulting/runs/vtuber_registry_20260805/
  00_scope/
  10_bootstrap/
  10_inputs/
  20_normalized/
  30_entity_resolution/
  40_review/
  50_coverage/
  60_exports/
  run_manifest.json
  progress.ndjson
  README.md
```

정본 후보:

```text
personas.ndjson
accounts.ndjson
organizations.ndjson
affiliations.ndjson
sources.ndjson
observations.ndjson
review_queue.ndjson
```

최신 조회용 CSV·SQLite·대시보드 데이터는 위 append-only 파일에서 재생성하는 파생물로 둔다.

---

## 10. 외부 실행 전 사전 체크리스트

### 범위

- [ ] 한국 시장 기준 확정
- [ ] 최근 90일 활성 기준 확정
- [ ] PNG·하이브리드·기업 캐릭터 기준 확정
- [ ] 포함 플랫폼과 기준일 확정
- [ ] 내부 전용/외부 공개 범위 확정

### 데이터

- [ ] 기존 7,489 플랫폼 census와 7,472 시계열 파일 해시·행 수 기록
- [ ] 기존 7,204 프로필 풀 해시와 행 수 기록
- [ ] 변환 전 원본 read-only 유지
- [ ] deterministic ID 테스트
- [ ] schema validator 준비
- [ ] append/resume/progress 테스트

### 수집

- [ ] 플랫폼별 공개 surface 확인
- [ ] 대상 수 × 요청 간격 × 평균 응답시간으로 예상 시간 계산
- [ ] 실행 환경 hard timeout의 70% 이하로 배치 분할
- [ ] HTTP 15초, 브라우저 로드 30초 등 개별 timeout 설정
- [ ] 오류 시 skip+log, 전체 중단 여부 구분
- [ ] 429/checkpoint/login 신호의 stop rule 설정
- [ ] 플랫폼별 operator 승인 확인

### 정보 경계

- [ ] 공개 데이터만 사용
- [ ] 비공개 실연자 신원 추적 금지
- [ ] 전생 자동 연결 금지
- [ ] cookie/token/auth 값 저장 금지
- [ ] 추정 이메일 생성 금지
- [ ] 연락·발송 기능 비활성
- [ ] 공개 export는 별도 승인

### QA

- [ ] 경계 사례 20건 정답표
- [ ] 파일럿 표본 100~300건
- [ ] 병합 검수 표본 100건
- [ ] 조직 로스터 검수표
- [ ] source overlap과 신규 수율 계산기
- [ ] coverage report 템플릿

---

## 11. 첫 착수 순서

외부 수집 전까지의 로컬 착수 순서는 아래로 고정한다.

1. 본 프로토콜의 P0 기본안을 operator가 확정한다.
2. JSON Schema와 ID 규칙을 구현한다.
3. 소프트콘 7,489 플랫폼 계정 + 7,472 시계열 + 7,204 치지직 프로필의 로컬 무손실 조인기를 만든다.
4. 100건 수동 대조와 조인 충돌 보고서를 낸다.
5. 조직 레지스트리의 빈 스키마와 기존 agency seed 변환기를 만든다.
6. 그 결과를 보고 SOOP Scout 1회 범위를 승인받는다.
7. SOOP 파일럿 통과 후 본 수집 여부를 결정한다.
8. YouTube는 알려진 계정 연결 보강부터 시작하고 검색은 마지막에 사용한다.

### 착수 완료의 정의

다음 상태가 되어야 ‘수집 준비 완료’다.

- 모집단 경계 확정
- 스키마 validator 통과
- 소프트콘 7,489 다중 플랫폼 계정 무손실 이관
- 중복/병합 리뷰 큐 작동
- 플랫폼별 요청량·시간·중단 조건 계산 완료
- 외부 실행과 연락 기능이 분리됨

---

## 12. 현재 operator 결정이 필요한 항목

권장 기본값을 먼저 제시한다.

| 결정 | 권장 기본값 | 영향 |
|---|---|---|
| 대한민국의 의미 | 한국어권 시장 활동자 | 국적·거주지 추정 없이 산업 모집단 구성 가능 |
| 활성 기준 | 최근 90일 | 휴방이 긴 개인세의 과도한 누락 방지 |
| PNG 버튜버 | 포함, 표현형 별도 라벨 | 소형 개인세 장기꼬리 보존 |
| 기업 홍보 캐릭터 | 포함하되 `corporate_character` 분리 | 산업 전체 지도와 창작자 시장을 동시에 유지 |
| 하이브리드 얼굴/버추얼 | 지속적 가상 페르소나가 있으면 포함 | 일회성 필터 사용자는 제외 |
| 전생 연결 | 공식 자기공개만 연결 | 신원추정·오병합 방지 |
| 레지스트리 용도 | 내부 정본 우선 | 공개본은 coverage·필드 검토 후 별도 생성 |
| 실제 수집 | 플랫폼별 승인 게이트 | 범위와 요청량을 확인한 뒤 실행 |

이 기본값이 승인되면 P1~P3의 로컬 작업은 외부 접속 없이 바로 착수할 수 있다. P4 이후의 외부 Scout·수집은 별도 승인 대상으로 유지한다.
