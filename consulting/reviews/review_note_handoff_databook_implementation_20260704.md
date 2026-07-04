# SESSION_NOTE 핸드오프 데이터북 proposal 구현 검토 메모

- type: review_note
- date: 2026-07-04
- source_proposal: `consulting/reviews/proposal_handoff_databook_20260704.md`
- owner: Codex implementation review

CC proposal은 방향성상 수용 가능하다. 다만 구현 관점에서 아래 조정이 필요하다.

## 1. 기존 SESSION_NOTE 물리 archive는 이번 변경에서 제외

proposal은 `SESSION_NOTE_archive_~20260704.md` 형태의 동결 파일을 제안한다.

이견:
- 현재 `SESSION_NOTE.md`와 `12_CONTINUITY_CONTRACT.md`에 이미 uncommitted 변경이 있다.
- 파일 rename/copy는 대형 공유 문서에 새 충돌면을 만든다.
- “역변환 없음 / 전방 적용” 원칙이면 기존 파일을 그대로 legacy archive로 남기는 것이 더 작고 안전하다.

구현 방침:
- `SESSION_NOTE.md`는 legacy read-only archive로 문서화한다.
- 신규 handoff만 `_WORKING_CONTEXT/handoffs/`에 작성한다.
- 물리 rename/copy는 별도 operator 요청이 있을 때만 한다.

## 2. 파일명은 Windows-safe 정렬 형식으로 고정

proposal의 예시는 `2026-07-04T1730-CC.md`라서 Windows-safe이다. 이를 명시 규칙으로 고정한다.

구현 방침:
- 파일명: `YYYY-MM-DDTHHMM-<Surface>.md`
- 파일명에는 colon(`:`)을 쓰지 않는다.
- 같은 surface가 같은 분에 2건을 쓰면 `-02`, `-03` suffix를 붙인다.

## 3. frontmatter 파서는 stdlib 최소 구현

이견:
- outreach의 YAML 유사 파서는 list-only 특화라 handoff frontmatter에 재사용하기 부적절하다.
- 새 PyYAML 의존성을 넣기에는 CI/로컬 마찰이 크다.

구현 방침:
- `consulting.tools.ops` 안에 frontmatter 최소 파서를 둔다.
- 지원 타입은 문자열 scalar와 한 줄 배열(`[a, b]`)로 제한한다.
- lint가 허용 스키마와 상태값을 검증한다.

## 4. INDEX 생성은 명시 스크립트 + CI check

이견:
- Codex/CC/Cowork 공통 “세션 종료 훅”은 현재 신뢰할 실행면이 없다.

구현 방침:
- `status_board.py`가 `_WORKING_CONTEXT/handoffs/INDEX.md`를 생성한다.
- CI에서는 `--check`로 INDEX가 최신인지 검증한다.
- 세션 종료 시 표준 절차는 “handoff 파일 작성 → index 생성/check”로 둔다.

## 5. 진행 판정

이 조정안으로 구현 진행 가능하다.

남는 경계:
- 기존 `SESSION_NOTE.md` 본문을 즉시 압축하거나 이동하지 않는다.
- 결정 로그는 operator 승인 근거가 있는 workflow 변경으로 `DL_CONTEXT_*`에 기록한다.
