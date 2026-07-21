from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from .config import LLM_PROVIDER, ERRORS_PATH, PROGRESS_PATH
    from .io_utils import append_error, append_ndjson, append_progress, load_progress_keys, read_ndjson
    from .llm_client import llm_json_object
    from .schemas import normalized_from_dict, record_to_dict
except ImportError:  # pragma: no cover - direct script execution fallback.
    from config import LLM_PROVIDER, ERRORS_PATH, PROGRESS_PATH
    from io_utils import append_error, append_ndjson, append_progress, load_progress_keys, read_ndjson
    from llm_client import llm_json_object
    from schemas import normalized_from_dict, record_to_dict


# ─────────────────────────────────────────────────────────────────────────────
# 표면 신호 정규식 — TILLER v0.7 F층 코드북 (TILLER_Framework_v0_7_0.md §2) 기준.
# 공통 원칙: EN은 단어 경계 필수, BERTH는 부정 표지 필수, BEARING은 대화 이력 지시만,
# HEADING은 어휘 우연 일치(framework 등) 배제.
# ─────────────────────────────────────────────────────────────────────────────

# HEADING — 서두(400자)의 관점·역할 선언 (F층 §2.3)
_ROLE_RE = re.compile(
    r"너는|당신은|(?:나|저)는|역할|"
    r"\byou are\b|\bact as\b|\bi want you to\b|\bi am\b|\brole\b",
    re.I,
)
_FRAME_RE = re.compile(
    r"프레임(?!워크)|관점에서|맥락|배경|상황(?:을|은|:)\s*|"
    r"\bframe\b|\bframing\b|\bscenario\b|\bgiven that\b|\bin the context of\b|\bcontext:",
    re.I,
)

# BERTH — 부정 표지가 붙은 제약 (F층 §2.4). 부정 표지 필수:
# 긍정적 절차 지시(step-by-step, 단계별)는 BERTH가 아니라 SOUNDING 신호.
_CATEGORY_RE = re.compile(
    r"제외|금지|빼고|빼\s*줘|말고|언급하지\s*마|하지\s*마|하지\s*않|다루지\s*마|"
    r"[이가]\s*아닌|[와과]는\s*다른|"
    r"\bdo not\b|\bdon'?t\b|\bnever\b|\bexclude\b|\bavoid\b|\bwithout mentioning\b|\bno mention\b",
    re.I,
)
_METHOD_RE = re.compile(
    r"단순한?\s*\S{1,12}[이가]?\s*아니라|나열하지\s*말|요약(?:만)?\s*하지\s*말|하지\s*말고|"
    r"식으로\s*(?:하|쓰)지\s*마|"
    r"\bnot just\b|\bdon'?t just\b|\binstead of\b|\brather than\b|"
    r"\bavoid (?:listing|summariz\w*|bullet)",
    re.I,
)

# BEARING — 대화 이력 지시만 (F층 §2.5). 외부 대상 지시(previous studies 등) 배제.
_OUTPUT_RE = re.compile(
    r"위(?:의|에서)?\s*(?:\d|결과|답변|출력|분석|내용)|앞(?:의|서)?\s*(?:결과|답변|출력)|"
    r"위에서\s*네가|네가\s*[\w가-힣]{0,10}한\s*(?:결과|내용|답변|출력)|"
    r"\bprevious (?:answer|response|output|result|step)s?\b|"
    r"\babove (?:result|answer|output|response)s?\b|"
    r"\byour (?:previous|last|earlier) (?:answer|response|output|analysis)\b",
    re.I,
)
_EXPERIENCE_RE = re.compile(
    r"아까\s*네가|방금\s*네가|네가\s*(?:검색|시도|겪|찾)|"
    r"\bas you (?:did|experienced|saw)\b|\byou (?:tried|attempted|encountered) (?:earlier|before)\b",
    re.I,
)
_FAILURE_RE = re.compile(
    r"못\s*찾은|아까\s*(?:못|실패)|실패한\s*(?:것|소스|검색|시도|부분)|네가\s*실패|깨진\s*(?:링크|url)|"
    r"\bwhat went wrong\b|\bfailed (?:attempt|search|source)s?\b|"
    r"\byou (?:failed|missed|couldn'?t find)\b",
    re.I,
)

# SLACK — 필터 완화 지시 (F층 §2.6). 단어 경계 필수 (draw/strawberry 오탐 방지).
_INCLUDE_RE = re.compile(
    r"빠짐없이|전부\s*포함|모두\s*포함|하나도\s*빼지\s*말|관련\s*없어\s*보이는\s*것도|"
    r"\binclude all\b|\binclude everything\b|\bdon'?t filter\b|\bdo not filter\b|\bleave nothing out\b",
    re.I,
)
_RAW_RE = re.compile(
    r"있는\s*그대로|원문\s*그대로|가공하지\s*마|해석\s*없이|검열하지|여과\s*없이|"
    r"\braw\s+(?:output|form|state|text|data)\b|\bin\s+raw\b|\bkeep\s+it\s+raw\b|"
    r"\bunfiltered\b|\bverbatim\b|\bas[- ]is\b",
    re.I,
)  # 'raw' 단독 금지 — "8K RAW", "RAW photo" 등 사진 용어·형식 명사는 지시가 아님

# CHANNEL — 판단 범주 신호와 타이브레이크 (F층 §2.1)
_CH2_RE = re.compile(
    r"\bcompare\b|\bversus\b|\bvs\b|\bchoose between\b|\bpros and cons\b|\ba/b\b|"
    r"비교(?!적)|대조|장단점|장점과\s*단점|중\s*선택|중에서\s*골라|어느\s*쪽|차이점|"
    r"인지[\s\S]{0,30}?인지",  # "X인지 Y인지 판단해" 이항 분기
    re.I,
)
# "뒷받침/교정/무관/조건적 지지로 분류", "친구/코치/멘토 3가지" — 슬래시 나열 + 범주화 큐 = Ch3
_CH3_SLASH_RE = re.compile(
    r"(?:[\w가-힣]{1,20}/){2,}[\w가-힣]{1,20}[\s\S]{0,25}?"
    r"(?:분류|구분|나누|나눠|categori[sz]e|classify|\d\s*가지|[한두세네]\s*가지|유형|종류|스타일|중)",
    re.I,
)
# "개념 부족, 실수, 오해 중 어디에" — 쉼표 나열 3+개 + '중' = Ch3
_CH3_COMMA_RE = re.compile(r"(?:[^,\n]{1,20},){2,}\s*[^,\n]{1,15}?\s*중(?:\s|에서|에|인지)")
# 리스트 마커가 판단 범주이려면 범주화 큐 필수 — 요구사항·제약·구성요소 리스트는 분기가 아님
_CATEGORY_CUE_RE = re.compile(
    r"분류|범주|카테고리|유형|종류|로\s*나[눠누]|중에서|각각|\d\s*가지|[한두세네]\s*가지|"
    r"\bcategor(?:y|ies|i[sz]e)|\bclassify\b|\btypes?\b|\beach of\b",
    re.I,
)
_CH4_RE = re.compile(
    r"\bbrainstorm\b|\bgenerate ideas\b|\bmultiple options\b|\ball possible\b|"
    r"가능한\s*모든|아이디어를\s*내|브레인스톰|여러\s*가지|최대한\s*많이",
    re.I,
)
# 타이브레이크 2: 순차 작업 마커 — 리스트가 단계이면 CHANNEL이 아니라 SOUNDING 신호
_SEQ_STEP_RE = re.compile(
    r"1\s*단계|첫\s*(?:번째\s*)?단계|\bstep\s*1\b|순서(?:로|대로)|차례(?:로|대로)|"
    r"먼저[\s\S]{0,100}?(?:그\s*다음|그리고\s*나서|이후)|첫째[\s\S]{0,150}?둘째",
    re.I,
)
# 타이브레이크 1: 출력 형식·구성요소 나열 — 포맷 리스트는 분기가 아님
_FORMAT_LIST_RE = re.compile(
    r"형식|포맷|양식|목차|구성(?:으로|은|:)|다음(?:을|과\s*같은|\s*항목)?[을를]?\s*포함(?:해|하)|"
    r"\bformat\b|\bstructure:|\binclude the following\b|\bfollowing (?:sections|elements|fields)\b",
    re.I,
)

# SOUNDING — 동사 체인 신호 (F층 §2.2)
# KR 지시 동사: 활용형 lookahead 필수 — 명사 속 어근("분석 보고서")은 동사가 아님.
_KR_INSTRUCTION_VERBS = re.compile(
    r"(?:분석|설명|평가|비교|분류|요약|추출|정리|작성|수정|변환|검토|판단|"
    r"나열|생성|제안|추천|구분|해석|번역|계산|측정|진단|예측|최적화|"
    r"정의|도출|제시|산출|조사|탐색|선별|가공|검증|확인|추적|점검)(?=\s*(?:하|해|한|할|합|했))"
)
_EN_INSTRUCTION_VERBS = re.compile(
    r"\b(analy[sz]e|explain|evaluate|compare|classify|summari[sz]e|rewrite|extract|rank)\b",
    re.I,
)
# 체인 커넥터: 순차 의존 표지만 — "위해서/대해서/관해서/통해서" 등 비순차 '해서'는 배제.
_KR_CHAIN_CONNECTORS = re.compile(
    r"한\s*다음|하고\s*나서|한\s*후에?|(?<![위대관의통])해서|(?<![위대의통])하여|한\s*뒤에?|"
    r"먼저[\s\S]{0,100}?(?:그\s*다음|그리고|이후)|"
    r"첫째[\s\S]{0,150}?둘째|1단계[\s\S]{0,150}?2단계|\bstep\s*\d"
)
# So4 메타 신호: 대상이 모델 자신의 출력·추론일 때만 (외부 텍스트 점검은 So4 아님).
_KR_DEPTH_SIGNALS = re.compile(
    r"되돌아보|자가\s*점검|스스로\s*검토|"
    r"네\s*(?:답변?|추론|판단|결과)[을를]?\s*(?:다시|점검|검토|비판)|"
    r"출력[을를]?\s*(?:다시\s*)?검토|결과[를을]?\s*비판|재검토|"
    r"추론\s*과정[\s\S]{0,10}?(?:점검|오류|검토)|틀렸을\s*경우|오류가\s*있(?:는지|으면)"
)
_EN_DEPTH_SIGNALS = re.compile(
    r"self[- ]check|critique your|revise your reasoning|double[- ]check your|"
    r"(?:review|check|verify) your (?:own\s+)?(?:answer|reasoning|output|work)",
    re.I,
)


def tag_file(
    input_path: Path,
    output_path: Path,
    *,
    mode: str = "null",
    progress_path: Path = PROGRESS_PATH,
    errors_path: Path = ERRORS_PATH,
) -> int:
    progress = load_progress_keys(progress_path)
    written = 0
    for row in read_ndjson(input_path):
        record = normalized_from_dict(row)
        key = ("L3", "", record.content_id)
        if key in progress:
            continue
        try:
            if mode == "heuristic":
                record.tiller = heuristic_tiller(record.body)
            elif mode == "llm":
                record.tiller = llm_tiller(record.body)
            elif mode == "anthropic":
                record.tiller = anthropic_tiller(record.body)
            elif mode == "null":
                record.tiller = None
            else:
                raise ValueError(f"unknown tag mode: {mode}")
            append_ndjson(output_path, record_to_dict(record))
            append_progress(progress_path, "L3", "", record.content_id)
            progress.add(key)
            written += 1
        except Exception as exc:  # noqa: BLE001 - keep failed records with tiller null.
            append_error(errors_path, "L3", "", type(exc).__name__, content_id=record.content_id, detail=str(exc))
            record.tiller = None
            append_ndjson(output_path, record_to_dict(record))
            append_progress(progress_path, "L3", "", record.content_id, status="error_null_tiller")
            progress.add(key)
            written += 1
    return written


def heuristic_tiller(body: str) -> dict[str, Any]:
    channel, ch_reason = infer_channel_with_reason(body)
    sounding, so_reason = infer_sounding_with_reason(body)
    heading, heading_reason = _infer_heading(body)
    berth, berth_reason = _infer_berth(body)
    bearing, bearing_reason = _infer_bearing(body)
    slack, slack_reason = _infer_slack(body)
    return {
        "channel": channel,
        "channel_reason": ch_reason,
        "sounding": sounding,
        "sounding_reason": so_reason,
        "heading": heading,
        "heading_reason": heading_reason,
        "berth": berth,
        "berth_reason": berth_reason,
        "bearing": bearing,
        "bearing_reason": bearing_reason,
        "slack": slack,
        "slack_reason": slack_reason,
    }


def _infer_heading(body: str) -> tuple[str | None, str]:
    head = body[:400]
    has_role = bool(_ROLE_RE.search(head))
    has_frame = bool(_FRAME_RE.search(head))
    if has_role and has_frame:
        return "Both", "role + frame declaration in opening"
    if has_role:
        return "Role", "role declaration in opening"
    if has_frame:
        return "Frame", "frame/context declaration in opening"
    return None, "no heading declaration in opening"


def _infer_berth(body: str) -> tuple[str | None, str]:
    has_method = bool(_METHOD_RE.search(body))
    has_category = bool(_CATEGORY_RE.search(body)) and not (
        has_method and not _CATEGORY_RE.search(_METHOD_RE.sub(" ", body))
    )
    if has_category and has_method:
        return "Both", "negated content + negated method signals"
    if has_category:
        return "Category", "negation-marked content exclusion"
    if has_method:
        return "Method", "negation-marked method exclusion"
    return None, "no negation-marked constraint"


def _infer_bearing(body: str) -> tuple[str | None, str]:
    has_failure = bool(_FAILURE_RE.search(body))
    has_experience = bool(_EXPERIENCE_RE.search(body))
    has_output = bool(_OUTPUT_RE.search(body))
    if has_failure:
        return "Failure", "prior failure/absence reference"
    if has_experience:
        return "Experience", "prior model-action reference"
    if has_output:
        return "Output", "prior output reference"
    return None, "no dialogue-history reference"


def _infer_slack(body: str) -> tuple[str | None, str]:
    has_raw = bool(_RAW_RE.search(body))
    has_include = bool(_INCLUDE_RE.search(body))
    if has_raw:
        return "Raw", "raw/verbatim/unprocessed signal (word-bounded)"
    if has_include:
        return "Include", "include-all / filter-relaxation signal"
    return None, "no filter-relaxation signal"


def infer_channel_with_reason(body: str) -> tuple[int, str]:
    """CHANNEL 판정 + 근거. F층 §2.1: 판단 범주의 나열만 분기로 센다.

    판정 순서: Ch3(명시 나열) → Ch2(이항) → Ch4(열린 분기).
    Ch3를 먼저 보는 이유: 'A vs B' 항목을 포함한 3+ 범주 리스트에서
    이항 신호가 다항 나열을 선점하지 않도록.
    """
    m = _CH3_SLASH_RE.search(body)
    if m:
        return 3, f"ch=3 slash-enumerated categories: '{m.group(0).strip()[:40]}'"
    m = _CH3_COMMA_RE.search(body)
    if m:
        return 3, f"ch=3 comma-enumerated + '중': '{m.group(0).strip()[:40]}'"

    list_markers = len(re.findall(r"(^|\n)\s*(?:[-*–—•]|\d+\.)\s+", body))
    kr_numbered = len(re.findall(r"(?:^|\n)\s*(?:[①②③④⑤⑥⑦⑧⑨⑩]|\d+\))\s*", body))
    if list_markers >= 3 or kr_numbered >= 3:
        if _SEQ_STEP_RE.search(body):
            # 타이브레이크 2: 순차 작업 나열은 CHANNEL이 아니라 SOUNDING 신호
            pass
        elif _FORMAT_LIST_RE.search(body):
            # 타이브레이크 1: 출력 형식·구성요소 나열은 분기가 아님
            pass
        elif _CATEGORY_CUE_RE.search(body):
            # 범주화 큐가 있을 때만 분기 — 요구사항·제약 리스트 배제
            return 3, f"ch=3 category-list markers={list_markers + kr_numbered} with cue"

    m = _CH2_RE.search(body)
    if m:
        return 2, f"ch=2 binary-judgment signal: '{m.group(0).strip()[:40]}'"

    m = _CH4_RE.search(body)
    if m:
        return 4, f"ch=4 open-branch signal: '{m.group(0).strip()}'"

    if list_markers >= 3 or kr_numbered >= 3:
        return 1, "ch=1 list markers present but no category cue / tie-break applied"
    return 1, "ch=1 no branch signal"


def infer_channel(body: str) -> int:
    return infer_channel_with_reason(body)[0]


def infer_sounding_with_reason(body: str) -> tuple[int, str]:
    """SOUNDING 판정 + 근거. F층 §2.2: 의존 체인의 길이로 센다 (어휘 종류 수 아님)."""
    lowered = body.lower()

    # So4: 자기 출력·추론 대상 메타 신호
    kr_depth = _KR_DEPTH_SIGNALS.search(body)
    en_depth = _EN_DEPTH_SIGNALS.search(body)
    if kr_depth or en_depth:
        sig = (kr_depth or en_depth).group(0).strip()
        return 4, f"so=4 self-directed meta signal: '{sig}'"

    kr_verbs = list(dict.fromkeys(_KR_INSTRUCTION_VERBS.findall(body)))
    en_verbs = list(dict.fromkeys(m.group(0).lower() for m in _EN_INSTRUCTION_VERBS.finditer(body)))
    verb_count = len(kr_verbs) + len(en_verbs)
    chain_count = len(_KR_CHAIN_CONNECTORS.findall(body))

    parts = []
    if kr_verbs:
        parts.append(f"kr_verbs:[{','.join(kr_verbs[:5])}]")
    if en_verbs:
        parts.append(f"en_verbs:[{','.join(en_verbs[:5])}]")
    if chain_count:
        parts.append(f"chains:{chain_count}")
    detail = " ".join(parts) if parts else "no verb/chain signal"

    # So3: 3단 이상 체인 (동사 3+와 체인 표지 동반, 또는 체인 표지 2+)
    if chain_count >= 2 or (verb_count >= 3 and chain_count >= 1):
        return 3, f"so=3 {detail}"
    # So2: 2단 체인 또는 파생 지시 동사 복수 또는 step-by-step
    if chain_count >= 1 or verb_count >= 2 or "step by step" in lowered or "단계별" in body:
        return 2, f"so=2 {detail}"
    if verb_count == 1:
        return 1, f"so=1 single verb {detail}"
    return 1, f"so=1 {detail}"


def infer_sounding(body: str) -> int:
    return infer_sounding_with_reason(body)[0]


# ─────────────────────────────────────────────────────────────────────────────
# LLM 태깅 — F층 코드북 이식 (v0.6.3까지는 축 이름·값 범위만 제공 → κ 저하 원인)
# ─────────────────────────────────────────────────────────────────────────────

def anthropic_tiller(body: str) -> dict[str, Any]:
    parsed = llm_json_object(
        system_prompt="",
        user_prompt=build_tiller_prompt(body),
        max_tokens=800,
        provider="anthropic",
    )
    parsed = normalize_tiller(parsed)
    validate_tiller(parsed)
    return parsed


def llm_tiller(body: str) -> dict[str, Any]:
    provider = LLM_PROVIDER.lower()
    if provider == "openai":
        return openai_tiller(body)
    if provider == "anthropic":
        return anthropic_tiller(body)
    raise RuntimeError(f"unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def openai_tiller(body: str) -> dict[str, Any]:
    parsed = llm_json_object(
        system_prompt="",
        user_prompt=build_tiller_prompt(body),
        max_tokens=800,
        provider="openai",
    )
    parsed = normalize_tiller(parsed)
    validate_tiller(parsed)
    return parsed


def build_tiller_prompt(body: str) -> str:
    return f"""당신은 TILLER v0.7 F층 코드북에 따라 프롬프트 표본을 태깅하는 주석자다.
아래 정의와 판정 규칙만 근거로 판정한다. 발화 표면에서 관찰되는 형태만 태깅하고, 효과나 의도의 추정은 하지 않는다.
표본은 한국어·영어·혼합일 수 있으며 규칙은 언어 무관하게 적용한다.

[CHANNEL — 판단의 분기 수 (1~4)]
정의: 발화가 명시적으로 나열한 '판단 범주'(출력이 선택·분류·비교될 후보)의 수.
- 1: 범주 나열 없음. 예: "X를 설명해"
- 2: 두 범주. 예: "X인지 Y인지 판단해", "장점과 단점을 정리해"
- 3: 셋 이상 범주 명시 나열. 예: "경제/문화/제도 요인으로 분류하고 근거 제시"
- 4: 범주 수를 모델에 위임하며 범주 미명시. 예: "가능한 해석을 모두 도출해"
타이브레이크 1 (포맷 리스트 배제): 출력 형식·구성요소의 나열은 분기가 아니다.
  "1) 제목 2) 본문 3) 해시태그 형식으로 써줘" → 1 (출력 구성이지 판단 범주가 아님).
타이브레이크 2 (순차 작업 배제): 순차 연결된 작업 나열("먼저 A, 그 다음 B", "1단계… 2단계…")은
  CHANNEL이 아니라 SOUNDING 신호다.
병렬 독립 과업("요약해줘. 그리고 번역도 해줘")은 분기가 아니다 → 1.

[SOUNDING — 추론의 깊이 (1~4)]
정의: 순차 의존 관계로 연결된 지시 동사 체인의 길이. 뒤 동사가 앞 동사의 출력을 입력으로 받을 때만 체인으로 센다.
- 1: 조회·서술 동사 1개(설명/나열/요약/번역 등) 또는 상호 독립인 병렬 동사들. 예: "X는 뭐야"
- 2: 파생 요구 동사 1개(추적/도출/진단/예측/검증/평가 — 입력에 잠재된 정보를 분석적 추론으로 끌어냄), 또는 2단 체인, 또는 "단계별로/step by step".
- 3: 3단 이상 체인 (순차 표지로 연결). 예: "추적하고 → 검증한 뒤 → 도출해"
- 4: 메타 동사 — 대상이 모델 '자신의 출력·추론 과정'일 때만. 예: "네 추론 과정에 오류가 있는지 점검해"
주의 1: 명사 속 어근("분석 보고서"의 '분석')은 지시 동사가 아니다. 명령·요청 서법의 동사만 센다.
주의 2: 외부 텍스트에 대한 점검("이 논문의 추론 오류를 점검해")은 4가 아니다 (대상이 외부 → 2~3).
주의 3: 동사 어휘의 개수가 아니라 의존 체인의 단계 수를 센다.
주의 4: **생성·창작 요청은 파생이 아니다.** "글/기획안/코드/프레젠테이션을 작성해줘·구성해줘·만들어줘"는
  산출물이 입력에 없어도 1이다. 기준은 "새 텍스트를 만드는가"가 아니라 "숨은 사실을 추론해야 하는가".
  앵커: "기획안을 작성해줘" → 1 / "이 업무 목록에서 자동화 우선순위를 도출해" → 2.
주의 5: **표면 명시 원칙.** 분석·판단이 생성의 암묵적 전제일 뿐이면 단계로 세지 않는다.
  "내 강점에 맞는(align with) 직업을 추천해줘" → 1 (분석 동사가 표면에 없음).
  판단·파생 동사가 표면에 명시된 경우만 체인 단계다: "A와 B를 비교해서 글을 써줘" → 2.
주의 6: **부연 연쇄는 체인이 아니다.** 조회·서술 동사만의 연쇄("5가지를 나열하고 각각 설명해")는
  부연이므로 1. 뒤 단계가 앞 단계의 '판단 결과'를 입력으로 받을 때만 체인이다:
  "5가지를 나열하고 그중 최적을 골라 근거를 설명해" → 2 ('골라'가 판단 개입).

[HEADING — 서두의 관점·역할 선언 (null/Frame/Role/Both)]
정의: 발화 서두(첫 문장 ~ 첫 단락)에 위치한 명시적 선언. 본문 중간의 언급은 HEADING이 아니다.
- Frame: 분석 렌즈·맥락 설정. "~의 관점에서", "상황: ~", "맥락은 ~"
- Role: 화자·청자 역할 선언. "나는 ~다", "너는 ~다", "Act as ~"
- Both: 둘 다 (한 문장 압축 포함. 예: "나는 LLM의 인식론적 위험을 연구하는 사람이야")
주의: 'framework', 'wireframe' 속의 frame 같은 어휘 우연 일치는 신호가 아니다. 실질적 선언 구문만.

[BERTH — 부정 표지가 붙은 제약 (null/Category/Method/Both)]
정의: 부정 표지(말고/제외/금지/않/하지 마/not/never/don't/avoid)가 붙은 명시적 제약. 부정 표지가 반드시 있어야 한다.
- Category: '다룰 주제·지식·소재'의 배제. "X 주제는 제외", "환각이나 사실 오류와는 다른 종류의"
- Method: '산출물의 표현·구성·형식·절차'의 배제. "단순 요약이 아니라", "나열하지 말고", "불릿 쓰지 마"
모드 경계 판정:
- 어휘·용어·톤의 배제("전문 용어는 피하고", "이 단어 금지")는 어떻게 말할지의 제약 → Method.
- 설명·부가 정보의 배제("설명 없이 답만", "부연하지 마")는 산출물 구성의 제약 → Method.
- 이미지 생성의 negative prompt("no logos, no text" 나열, negative_prompt 필드)는 묘사 소재의 배제 → Category.
- 구조 필드(JSON·목록) 속 부정도 유효하다 — 산문 지시일 필요 없음.
주의: 긍정적 절차 지시("단계별로 진행해", "step-by-step으로")는 BERTH가 아니다 → SOUNDING 신호로만 센다.

[BEARING — 이전 컨텍스트 지시 (null/Experience/Output/Failure)]
정의: 대화 이력의 특정 지점(이전 출력, 이전 행동, 이전 실패·부재)을 지시하는 표현.
- Output: 이전 출력 지시. "위에서 네가 분석한 결과를 기반으로", "위 2번 결과"
- Experience: 모델의 이전 행동 지시. "아까 네가 검색하면서 겪었잖아"
- Failure: 이전 실패·부재 지시. "아까 못 찾은 것, 깨진 URL"
주의: 외부 대상 지시("previous studies", "위 사진", "앞 장에서")는 BEARING이 아니다. 대화·출력 이력만.

[SLACK — 필터 완화 지시 (null/Include/Raw)]
정의: 모델의 기본 선별·가공 동작을 명시적으로 완화하는 지시.
- Include: 관련성 선별의 완화. "관련 없어 보이는 것도 포함해", "빠짐없이"
- Raw: 가공·편집의 억제. "있는 그대로", "해석 없이", "verbatim"
주의: 'draw' 속의 raw 같은 부분 문자열은 신호가 아니다. 출력 형식 지정("표로 정리해")은 SLACK이 아니다.

각 축의 값과 판정 근거(매칭된 표면 신호를 짧게 인용)를 JSON 객체 하나로만 출력한다.
해당 신호가 없으면 JSON null을 쓴다 (문자열 "null" 금지). 모드 값의 대소문자는 정확히:
Frame/Role/Both/Category/Method/Experience/Output/Failure/Include/Raw.

{{"channel": int, "channel_reason": "...", "sounding": int, "sounding_reason": "...", "heading": "Frame|Role|Both|null", "heading_reason": "...", "berth": "Category|Method|Both|null", "berth_reason": "...", "bearing": "Experience|Output|Failure|null", "bearing_reason": "...", "slack": "Include|Raw|null", "slack_reason": "..."}}

---
프롬프트 표본:
{body}
---"""


_CANON_MODES = {
    "frame": "Frame",
    "role": "Role",
    "both": "Both",
    "category": "Category",
    "method": "Method",
    "experience": "Experience",
    "output": "Output",
    "failure": "Failure",
    "include": "Include",
    "raw": "Raw",
}


def normalize_tiller(data: dict[str, Any]) -> dict[str, Any]:
    """LLM 출력 정규화: 'null' 문자열 → None, 모드 대소문자 → 정본, 등급 → int."""
    for key in ("channel", "sounding"):
        value = data.get(key)
        if value is not None:
            data[key] = int(value)
    for key in ("heading", "berth", "bearing", "slack"):
        value = data.get(key)
        if isinstance(value, str):
            stripped = value.strip().lower()
            if stripped in ("", "null", "none", "no", "n/a"):
                data[key] = None
            else:
                data[key] = _CANON_MODES.get(stripped, value)
    return data


def validate_tiller(data: dict[str, Any]) -> None:
    required = {
        "channel",
        "channel_reason",
        "sounding",
        "sounding_reason",
        "heading",
        "heading_reason",
        "berth",
        "berth_reason",
        "bearing",
        "bearing_reason",
        "slack",
        "slack_reason",
    }
    missing = required - set(data)
    if missing:
        raise ValueError(f"missing tiller fields: {sorted(missing)}")
    if int(data["channel"]) not in {1, 2, 3, 4}:
        raise ValueError("channel out of range")
    if int(data["sounding"]) not in {1, 2, 3, 4}:
        raise ValueError("sounding out of range")
    if data["heading"] not in {None, "Frame", "Role", "Both"}:
        raise ValueError("heading out of range")
    if data["berth"] not in {None, "Category", "Method", "Both"}:
        raise ValueError("berth out of range")
    if data["bearing"] not in {None, "Experience", "Output", "Failure"}:
        raise ValueError("bearing out of range")
    if data["slack"] not in {None, "Include", "Raw"}:
        raise ValueError("slack out of range")
