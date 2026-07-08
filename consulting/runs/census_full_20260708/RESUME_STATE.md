# 전수 확장 수집 — 재개 상태 (2026-07-08 오후 중단)

## 진행
- 랭킹 재수확: 오늘자 버추얼 랭킹 98p → 전체 7,405채널 ID 확보
- 수집 대상: 7,405 − 이미보유 1,081 = 6,392채널
- **완료: cursor 528 / 6,392** (part_a: 527채널 저장, 평균 94.8주, 오류 0)
- 중단 사유: 누적 일일 WAF 예산 소진 → fetch 429 (15분 냉각 미해제)

## 재개 방법 (익일 권장)
1. Chrome 소프트콘 세션에서 fetch 프로브 200 확인
2. 브라우저 window._census 살아있으면: `window._censusRun(2500)` (cursor 528부터 자동 재개)
   - 세션 죽었으면: 랭킹 재수확부터 재실행 or part_a의 채널ID를 already-have에 추가 후 재구성
3. ~500채널마다 `window._censusDownload('census_full_part_X.ndjson', from, to)` → parts/로 이동
4. 하루 ~1,500채널 이하로 분할 (runbook 누적 예산 행 참조)

## 조립 (전체 수집 후)
- parts/*.ndjson → resample_weekly (assemble.py) → census_full_weekly.ndjson
- 세그먼트는 시계열 내장 maxFollowerCount로 직접 산출 (rookie<150/growth<10k/large)
- 백테스트: `python -m tools.backtest.run --input census_full_weekly.ndjson`
- 궤적매칭: `python -m tools.trajectory.validate --input census_full_weekly.ndjson` (중간 체급 미확정 해소 목표)
