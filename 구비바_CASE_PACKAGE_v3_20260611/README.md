# 구비바 CASE PACKAGE v3

**생성일:** 2026-06-11  
**목적:** 구비바 케이스의 사람용 정본, machine-readable 산출물, 원자료, 작업 산출물, 방법론 기준 문서를 한 패키지로 정리한다.

## 먼저 볼 파일

1. `구비바_CASE_DOSSIER_v3.md` — 사람용 통합 정본
2. `machine/구비바_project_v3.json` — 최신 project 레지스터
3. `machine/구비바_CaseResult_v3_stub.json` — CaseResult stub
4. `data/cohort/specs/` — §4 코호트 수집 준비 자료

## 현재 상태

- §1 정체성: 완료
- §2 데이터 정합성: 통과
- §3 측정 보정: 통과, 노방종 0일
- §4 코호트: spec 준비, 수집 전
- §5 진단: 대기
- CaseResult: stub
- PortfolioRow: not_ready
- PublicDemoRow: blocked

## 폴더 구조

```text
machine/        JSON/CSV 정본. 자동화·Bridge·QA용.
data/           방송통계, 코호트 데이터, 코호트 spec.
deliverables/   클라이언트 전달물. 현재는 대기.
source_inputs/  입력자료와 원자료. 기본 red/private.
references/     MASTER/방법론 기준 문서.
work/           Step0/Step1/migration 중간 산출물.
archive/        이전 패키지 zip과 백업.
```

## 운영 원칙

- 사람이 읽는 흐름은 `구비바_CASE_DOSSIER_v3.md`에 통합한다.
- JSON/CSV/원자료/로그는 분리한다.
- archive는 추적용이며 최신 판단의 기준은 아니다.
- 구비바 케이스는 현재 공개 사례가 아니라 private validation case이다.

## 다음 작업

1. §4 Charles 진단 재개
2. Arthur ExecutionProtocol 보강
3. 코호트 수집 및 robustness table 생성
4. §5 6단계 진단
5. CaseResult partial 승격
