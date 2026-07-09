# Vertex AI 접근 셋업 (Gemini via GCP)

`tools/vertex_client.py`로 Vertex AI 경유 Gemini를 호출한다. AI Studio API 키가 아니라
**GCP 프로젝트 결제**로 청구되므로 Free Trial 크레딧이 적용된다.

> **왜 Vertex인가:** AI Studio에서 발급한 Gemini 키는 *선불(prepay)* 지갑에 묶여 GCP Free Trial
> 크레딧이 적용되지 않는다(429 `prepayment credits depleted`). Vertex 경로는 프로젝트 결제 계정으로
> 직행하므로 크레딧이 그대로 차감된다.

## 1회 셋업

### ① google-genai 설치
```
pip install -r tools/requirements-llm.txt
```

### ② gcloud CLI 설치 (없으면)
```
winget install --id Google.CloudSDK --silent
```
설치 경로 예: `%LOCALAPPDATA%\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd`
(설치 직후 PATH에 안 잡히면 새 셸을 열거나 절대경로로 호출)

### ③ ADC 인증 (자격증명은 리포에 넣지 않는다)
```
gcloud auth application-default login      # 브라우저에서 계정 승인
gcloud config set project contextwins
```
자격증명은 머신 단위 파일(`%APPDATA%\gcloud\application_default_credentials.json`)에 저장된다.
**절대 커밋 금지.** 코드는 ADC를 자동으로 찾으므로 `.env`에 넣을 비밀이 없다.

### ④ Vertex AI API 활성화 + 결제 확인 (프로젝트당 1회)
```
https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=contextwins
https://console.cloud.google.com/billing/linkedaccount?project=contextwins
```
> 이 프로젝트(needmorefal)는 별도 GCP 프로젝트를 두지 않고, Vertex가 이미 활성화되고 Free Trial
> 결제가 붙은 **`contextwins` GCP 프로젝트를 공용으로 재사용**한다(기본값). ADC는 머신 단위라
> 같은 PC에서 그대로 통한다. 별도 프로젝트를 쓰려면 `VERTEX_PROJECT` 환경변수로 오버라이드하고,
> 그 프로젝트에서 ④를 다시 수행한다.

## 사용

```python
from tools.vertex_client import vertex_text, vertex_json, list_models

txt = vertex_text("한 줄로 요약해줘: ...")
obj = vertex_json('아래를 JSON으로 분류: {"label": "..."}', model="gemini-3.5-flash")
print(list_models())          # 이 프로젝트로 쓸 수 있는 gemini 모델
```

스모크 테스트:
```
cd consulting
python -m tools.vertex_client        # → OK (project=contextwins, ...): {'vertex': 'ok'}
```

환경변수(모두 선택, 셸 또는 프로세스 env로 지정):
```
VERTEX_PROJECT=contextwins
VERTEX_LOCATION=global
VERTEX_MODEL=gemini-2.5-flash
```

## 주의사항 (실측 기반)

1. **thinking 토큰이 출력 예산을 잠식한다.** `max_output_tokens`가 작으면(예: 800) Gemini가
   대부분을 thinking에 써버려 응답이 잘린다(`finish_reason=MAX_TOKENS` → 빈 텍스트). 그래서
   `vertex_client`의 기본 `max_tokens=4000`. 분류/태깅류는 이 값 이상 유지.
2. **프리뷰 모델은 쿼터가 낮다.** `gemini-3.1-pro-preview`는 429가 잦다(~0.2건/s). 대량 처리에는
   `gemini-3.5-flash`가 실용적(~2.9건/s). 대량 루프에는 지수 백오프를 직접 감쌀 것.
3. **Free Trial 만료: 2026-09-17.** 소멸 예정 크레딧이므로 비싼 모델을 아낄 이유가 없다.
4. **모델 조회:** `list_models()` 또는 `client.models.list()`로 접근 가능 모델 확인.
