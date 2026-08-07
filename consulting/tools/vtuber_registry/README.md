# Korean VTuber Registry Tools

로컬에 이미 존재하는 소프트콘 버추얼 census와 치지직 프로필·시계열을
영업 필터와 분리된 중립 레지스트리로 이관한다.

## Boundary

- `bootstrap`은 네트워크에 접근하지 않는다.
- 계정 정본 키는 `platform + platform_account_id`다.
- `afreeca`는 `soop`, `naverchzzk`는 `chzzk`로 정규화한다.
- 이름 일치만으로 서로 다른 플랫폼의 페르소나를 병합하지 않는다.
- 기존 `outreach.status`와 `solo`는 정본 판정에 사용하지 않는다.

## Run

저장소 루트에서:

```powershell
python -m consulting.tools.vtuber_registry bootstrap
```

검증:

```powershell
python -m consulting.tools.vtuber_registry validate consulting/runs/vtuber_registry_20260805/20_normalized/accounts.ndjson --record-type account
```

참조 무결성 감사:

```powershell
python -m consulting.tools.vtuber_registry audit consulting/runs/vtuber_registry_20260805
```

공식 조직 출처를 검토한 뒤 명시적인 증거표를 적용하려면 다음을 실행해요.

```powershell
python -m consulting.tools.vtuber_registry enrich-organizations consulting/runs/vtuber_registry_20260805
```

이 명령은 네트워크나 로그인 세션을 사용하지 않아요. 코드에 검토해 넣은 공식 URL만
출처 원장에 추가하고, 정확히 한 persona에만 대응하는 이름만 affiliation으로 만들어요.
SOOP 공식 핸들과 소프트콘 `cid`가 다른 사례는 자동 병합하지 않고
`official_account_candidates.csv`에 남겨요.

검토한 공식 SOOP 계정 11건을 공개 프로필 증거와 함께 원장에 반영하려면 다음을 실행해요.

```powershell
python -m consulting.tools.vtuber_registry reconcile-soop consulting/runs/vtuber_registry_20260805
```

이 명령은 AKAIV와 이세계아이돌 공식 명단이 직접 가리키는 SOOP 계정을 생성하고,
교차 플랫폼 신원이 충분히 입증되지 않은 동명이인은 병합하지 않아요.

공식 조직·그룹 페이지가 직접 연결한 YouTube 채널 시드를 반영하려면 다음을 실행해요.

```powershell
python -m consulting.tools.vtuber_registry enrich-youtube-seeds consulting/runs/vtuber_registry_20260805
```

검색 결과만으로 채널을 확정하지 않고, 공식 페이지의 직접 링크와 YouTube 고정 채널 ID를
함께 확인한 계정만 기존 페르소나에 연결해요.

현재 커버리지와 남은 모집단 공백을 다시 계산하려면 다음을 실행해요.

```powershell
python -m consulting.tools.vtuber_registry coverage consulting/runs/vtuber_registry_20260805
```

이 명령은 `50_coverage/unresolved_population.md`, `coverage_status.json`,
`run_manifest_post_enrichment.json`을 생성해요.

고정된 100건 QA 표본의 CHZZK 공개 프로필 근거를 수집하려면 다음을 실행해요.

```powershell
python -m consulting.tools.vtuber_registry qa-public-profiles consulting/runs/vtuber_registry_20260805
```

이 명령은 로그인 없이 CHZZK 공개 프로필만 조회하고,
`40_review/manual_qa_public_evidence_100.csv`에 이름 일치와 명시적 버튜버 신호를 기록해요.
SOOP·CIME의 불명확한 `cid`는 자동으로 공식 URL로 변환하지 않아요.

공개 프로필 근거에서 빈 이름만 채우고 실제 이름 변경은 검토 큐로 보내려면 다음을 실행해요.

```powershell
python -m consulting.tools.vtuber_registry qa-apply-evidence consulting/runs/vtuber_registry_20260805
```
