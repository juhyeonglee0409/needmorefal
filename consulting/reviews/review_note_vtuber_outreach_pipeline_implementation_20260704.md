# 버튜버 콜드메일 타겟 파이프라인 제안 검토 메모 (Implementation Review)

- type: review_note
- date: 2026-07-04
- surface: CC
- source_spec: `specs/vtuber_outreach_pipeline_spec_20260704.md`
- owner: Codex (implementation review)

CC 제안(spec v0.1 / v0.3 보강)을 구현 관점으로 검토한 결과, 다음 항목은 현재 인프라 상태에서 이견이 있다.

## 1) 경로(엔드포인트) 정합성 이슈

제안 스펙은 CHZZK `api.chzzk.naver.com/service/v1/search/channels` 및 `/service/v1/channels/{channelId}` 사용을 가정한다.  
그러나 `CHZZK_RUNBOOK.md`의 정식 Working Surface는 `chzzk.naver.com/api/channels/{channelId}` 계열로 한정되어 있고, 검색 API는 공식 working route로 등록되어 있지 않다.  

요구사항: v1 탐색 경로를 수용할지, 아니면 런북 정식 경로 중심 설계로 제한할지 사전 합의 필요.

근거:
- `consulting/_WORKING_CONTEXT/site_runbooks/CHZZK_RUNBOOK.md` Working Routes/Surface 정의는 `api/channels/{channelId}`뿐.

## 2) LLM 의존 단계는 기존 수집 스택으로 즉시 구현 불가

제안의 S3(`heuristic + LLM 경계판정`) 및 S7(`초안 큐 생성`)은 LLM 모듈 사용을 전제한다.  
현재 `consulting/tools/collector/`는 HTTP/API/DOM 수집 및 추출 중심이고, LLM 클라이언트/래퍼/프롬프트 라우팅이 존재하지 않는다.

요구사항:
- S3/S7를 기존 수집기(노력 최소 수정)로 분리하거나,
- 별도 outreach 모듈에서 LLM 의존 계층을 새로 도입해야 함.

근거:
- `consulting/tools/collector/`에서 `dom_eval`, `api_json`, `http_engine`, `nodriver_engine`만 확인됨.
- `Get-ChildItem consulting/tools`에서 `outreach` 폴더가 존재하지 않음.

## 3) 출력 스키마/형식 불일치

제안 스키마는 `NDJSON append-only`를 기본 산출로 명시한다.  
현재 `tools/collector`는 대상별 CSV를 생성하고, manifest JSON + progress/error NDJSON(진행/상태 기록) 형태로 출력한다.  

요구사항:
- NDJSON 기반 pipeline output(`channel` 단위 append) 설계를 별도 구현하거나,
- spec에 현재 collector의 파일 구조(CSV+매니페스트) 반영 후 downstream를 설계해야 함.

근거:
- `consulting/tools/collector/collector.py`의 기본 출력은 `write_csv`.
- `consulting/tools/collector/config.py` 기본 `output_file_pattern="{channelId}.csv"`.
- `consulting/tools/collector/tracking.py`는 progress NDJSON을 사용하지만 결과 자체는 per-target CSV.

## 4) SOFTC.ONE 연동은 별도 게이트/승인 조건이 선결

제안은 S6에서 소프트콘 기반 지표 보강을 가정하지만, 현 환경에서 소프트콘은 브라우저/프로필 제약이 강하다.
- Vercel WAF로 HTTP 클라이언트 경로가 차단됨(`COLLECTION_TOOLKIT.md`, `SOFTC_ONE_RUNBOOK.md`).
- 노드river/Playwright 경로 모두 프로필·checkpoint 이슈가 존재하며, fresh profile 실패 사례가 문서화됨.

요구사항:
- S6를 바로 실행하지 말고 `operator` 승인된 탐색/브라우징 경로 및 profile 준비 상태를 사전에 분리 체크.
- `tools/collector` 범용 경로와 소프트콘 지표 수집 경로의 실행 계약을 분리.

근거:
- `SOFTC_ONE_RUNBOOK.md`/`COLLECTION_TOOLKIT.md`의 WAF, checkpoint, fresh profile 실패 리스크.

## 5) 권장 액션

1. spec에 v0.1/v0.3를 통합해, 구현-바인딩 가능한 최소 스펙(collector-compatible layer)과 향후 고도화 레이어(LLM + outreach)로 분리.
2. S1~S3는 `collector` 기반으로 우선 실행 가능한 버전으로 고정, output contract는 실측 형식(CSV/manifest/progress) 기준으로 정식화.
3. LLM 경로는 별도 모듈(예: `consulting/tools/outreach`)로 설계 후 CC 실행 요청 단계로 이동.
4. CHZZK는 런북 정식 경로 우선 사용과 검색 경로 fallback 정책을 문서에 명시.
