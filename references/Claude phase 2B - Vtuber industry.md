# DIAGNOSE 결과 — 버튜버 기술·제작 인프라

> **진단일:** 2026-06-30
> **Phase 1 수집:** 106개 팩트 → **Phase 2 보강 후 합계: 184개 팩트**
> **조사 관점:** 버튜버 활동에 필요한 기술 스택과 제작 파이프라인의 현실적 조건

---

## 범례

### 밀도 등급 (Axis 1: Source Density Hierarchy)

| 등급 | 출처 유형 | 밀도 근거 |
|------|-----------|-----------|
| A (최고) | 1차 출처 — 공식 문서, 제조사 발표, 법적 제출물, Wikipedia 인용 | 편집 최소. 구조 직접 노출 |
| B | 업계 전문 미디어 또는 검증된 커뮤니티 위키 | 전문 관찰자 기록. 관찰자 편향 존재 |
| C | 다수 출처 교차 확인된 시장 보고서·가격 정보 | 편집·선별·프레이밍 존재 |
| D | 단일 매체 보도 또는 제한적 검증 | 단일 관점 의존 |
| E (최저) | 커뮤니티 포럼·개인 블로그 | 원본 사실이 가공·평균화됨 |

### 고유성 태그 (Axis 2: Uniqueness Tag)

| 태그 | 정의 | 기준 |
|------|------|------|
| ★ (고유) | 해당 출처에서만 확인되는 관점·데이터·반례 | 동일 내용을 다른 출처에서 찾을 수 없음 |
| — (비고유) | 다른 출처와 중복되는 내용 | 동일 사실/관점이 다른 출처에도 존재 |

---

# Phase 2 본문

---

## 2a — 데이터 진단 (카운팅)

### 수집 범위 항목별 팩트 수

| 수집 범위 항목 | Phase 1 팩트 번호 | P1 수량 | Phase 2 보강 번호 | P2 추가 | 합계 | 판정 |
|---|---|---|---|---|---|---|
| 아바타 제작 파이프라인 (디자인→모델링→리깅) | #29–#32 | 4 | #107–#116 | 10 | **14** | ✅ 해소 |
| 제작 비용 구조 (일러스트·Live2D·3D·의상·추가) | #33–#47 | 15 | — | 0 | **15** | ✅ 충분 |
| 트래킹: 페이스 트래킹 | #48–#56 | 9 | #156–#166 (일부) | 5 | **14** | ✅ 충분 |
| 트래킹: 모션캡처 (상반신/전신) | #57–#62 | 6 | — | 0 | **6** | ⚠️ 경계선 |
| 트래킹: 핸드 트래킹 | #63–#65 | 3 | #117–#134 | 18 | **21** | ✅ 해소 |
| 방송 소프트웨어 | #66–#71 | 6 | — | 0 | **6** | ⚠️ 경계선 |
| 3D 라이브·콘서트 기술 | #72–#81 | 10 | #179–#184 (일부) | 3 | **13** | ✅ 충분 |
| AI 기술: AI VTuber | #82–#91 | 10 | #135–#136, #153 | 3 | **13** | ✅ 충분 |
| AI 기술: AI 음성 합성 | #92–#94 | 3 | #137–#147 | 11 | **14** | ✅ 해소 |
| AI 기술: AI 일러스트 논란 | #95–#98 | 4 | #148–#155 | 8 | **12** | ✅ 해소 |
| 버전 전환점: Live2D | #18–#28 | 11 | — | 0 | **11** | ✅ 충분 |
| 버전 전환점: 니지산지 모델 체계 | #99–#102 | 4 | #167–#173 | 7 | **11** | ✅ 해소 |
| 버전 전환점: iPhone 트래킹 도입·3D 전환 시점 | #8, #48–#51 (부분) | 4 | #156–#166, #174–#178 | 16 | **20** | ✅ 해소 |
| 시장 규모 | #103–#106 | 4 | — | 0 | **4** | 보조 항목 |
| 역사·기원 | #1–#17 | 17 | — | 0 | **17** | ✅ 충분 |

### 밀도 등급 분포 (Phase 1+2 합산, 184개)

| 등급 | Phase 1 (106개) | Phase 2 보강 (78개) | 합계 | 비율 |
|------|----------------|-------------------|------|------|
| A (1차 출처) | ~37개 (35%) | ~28개 (36%) | ~65개 | 35% |
| B (전문 미디어) | ~32개 (30%) | ~20개 (26%) | ~52개 | 28% |
| C (교차 확인) | ~26개 (25%) | ~15개 (19%) | ~41개 | 22% |
| D (단일 매체) | ~9개 (8%) | ~12개 (15%) | ~21개 | 12% |
| E (커뮤니티) | ~2개 (2%) | ~3개 (4%) | ~5개 | 3% |

A–B 비율이 63%로 양호하나, Phase 2 보강에서 D등급 비율이 15%로 상승한 점은 주의가 필요해요. 특히 핸드 트래킹(SlimeVR 크라우드펀딩 페이지, GitHub 이슈) 및 AI 일러스트 논란(뉴스 단일 보도) 영역에서 D등급이 집중되어 있어요.

### 고유성(★) 분포

**★ 집중 영역:**
- Live2D 세부 버전 기능 (#23, #25, #94)
- NexStage 콘서트 제작 실무 (#76, #77)
- PLAVE 공연 데이터 (#79, #80)
- Animaze 안티-AI 기능 (#69, #95)
- Neuro-sama LLM 사양 (#85, #91)
- Xsens 가격 인상 논란 (#60)
- Rokoko Coil Pro UWB 보정 (#62)
- iPhone 13 이후 TrueDepth 모캡 품질 변화 (#160) — Phase 2 추가
- SlimeVR 핑거 트래킹 본 구조 (#125) — Phase 2 추가
- GPT-SoVITS v2 RTF 벤치마크 (#143) — Phase 2 추가
- VLAST "Virtual Slate" 동기화 도구 (#182) — Phase 2 추가
- HYBE·YG PLUS의 VLAST 지분 투자 (#184) — Phase 2 추가

**★ 부재 영역:**
- 방송 소프트웨어 기능 비교 상세 (OBS 연동 방식 차이 등)
- 모션캡처 상반신/전신 영역의 VTuber 특화 사례
- Twitch·YouTube 플랫폼의 AI 아바타 공식 정책 (명문화된 1차 출처 미확인)

### 제외 항목 침투 점검

- "소프트웨어 사용법 튜토리얼" → Phase 1·2 모두 침투 없음. 기능·스펙 수준의 팩트만 기록됨.
- "개인 리뷰어 주관적 장비 평가" → Phase 1 #62 beforesandafters.com Rokoko 리뷰에서 일부 사용감이 포함되었으나 기술적 사실(UWB 보정)로 필터링됨. Phase 2에서 추가 침투 없음.

---

## 2b — 자기 진단

### 수집 전 목적
버튜버 활동에 필요한 기술 스택과 제작 파이프라인의 현실적 조건을 파악한다.

### 수집 후 목적 조정
변경 없음. 다만, 수집 결과를 보니 "현실적 조건"의 핵심은 **비용 구조보다 실제 워크플로우의 병목과 기술 선택 간 트레이드오프**에 있다는 점이 더 선명해졌다.

### 예상과 다른 점

1. **파이프라인 워크플로우의 팩트 부족 (Phase 1에서 4개 → Phase 2 보강으로 14개로 해소)**
   - 가격 정보는 넘치지만, "실제로 어떤 순서로 누가 무엇을 하는가"에 대한 구조적 사실이 의외로 부족했다. 출처들이 대부분 가격 가이드여서 프로세스 자체보다 결과물의 가격에만 초점을 맞춘 결과로 보인다.
   - Phase 2 보강에서 리거 개인 사이트(ShiraLive2D, typeou.dev, Fiverr)와 교육 플랫폼(Coloso)을 통해 해소했으나, 이들은 개별 리거의 자기 신고치이며 업계 표준은 아니다.

2. **핸드 트래킹 기술 다양성 (Phase 1에서 3개 → Phase 2 보강으로 21개로 해소)**
   - Leap Motion 외에 VRChat Quest 핸드 트래킹, StretchSense 글러브, SlimeVR 핑거 트래킹 개발 현황, MediaPipe Hands까지 폭넓게 확보했다.
   - 다만 SlimeVR 핑거 트래킹은 아직 개발 중(#124)이어서 실사용 사례가 아닌 "계획" 수준이다.

3. **AI 음성 합성의 실적용 사례 부족 → 부분 해소**
   - TTS 엔진 목록을 넘어 GPT-SoVITS의 RTF 벤치마크(#143), Coqui XTTSv2의 200ms 미만 스트리밍(#146), Neuro-sama 재현 프로젝트의 파이프라인 구조(#147)까지 확보했다.
   - 그러나 Neuro-sama 이외에 AI TTS를 실제 라이브 방송에서 사용하는 구체적 VTuber 사례는 여전히 부족하다. CoeFont→Pictoria "Spinen" (#137)이 유일한 에이전시 레벨 사례이다.

4. **플랫폼(Twitch·YouTube) AI 아바타 공식 정책 — 미확인**
   - AI 생성 아바타를 직접 규율하는 명문 정책 조항을 1차 출처로 확인하지 못했다. 확인된 정책은 에이전시(홀로라이브·니지산지)의 팬워크/2차 창작 가이드라인 수준이다.

5. **홀로라이브 JP의 3D 데뷔 기준 — 미확인**
   - Cover Corporation이 3D 모델 제공 기준(구독자 수, 활동 기간 등)을 공식 발표한 1차 출처를 찾지 못했다. 홀로라이브 EN Myth의 3D 데뷔 타임라인은 확보했으나(#174–#177), JP 멤버의 기준은 확인 불가.

### 예상보다 두꺼운 영역

- **비용 구조 (15개)** — Phase 1에서 이미 충분. Cloud Animations, BuzzFlick, Viverse 등 가격 비교 사이트가 풍부하게 존재.
- **AI VTuber / Neuro-sama (13개)** — Wikipedia + Fandom + Grokipedia에서 A등급 출처가 풍부. 단일 주제로 가장 밀도 높은 팩트 보유.
- **핸드 트래킹 (Phase 2 보강 후 21개)** — 보강 과정에서 예상보다 다양한 기기·플랫폼 정보가 확보됨.

---

## 2c — 보강된 팩트 (#107~#184)

### 보강 대상 1: 아바타 제작 파이프라인 워크플로우

107. Live2D 리깅 커미션 워크플로우는 "일러스트 발주 → PSD 파츠/레이어 분리(커팅·클리닝) → 리깅 → 물리 설정 → 트래킹 테스트" 단계를 따른다.
     — 출처: ShiraLive2D (shiralive2d.com) | C | —

108. ShiraLive2D는 리깅 작업이 모델 사양에 따라 통상 2~4주 소요된다고 명시한다.
     — 출처: ShiraLive2D (shiralive2d.com) | C | —

109. Vtubermodel.com 작가는 캐릭터 디자인 승인 후 리깅이 2~3주 걸리며, 전체 작업은 수정 없을 경우 약 2~3개월 걸린다고 밝힌다.
     — 출처: vtubermodel.com | C | ★

110. Fiverr 리거 Yuki_ono는 스케치/콘셉트 1~2일, 베이스 컬러/커팅 2~4일, 리깅/물리 2~7일로 패키지·복잡도에 따라 총 5~15일이 걸린다고 명시한다.
     — 출처: Fiverr yuki_ono | C | ★

111. 리거 typeou는 2021년 중반부터 70개 이상의 풀바디 모델을 리깅했으며 통상 작업 기간이 10~20일이라고 밝힌다.
     — 출처: typeou.dev/comms | C | ★

112. ShiraLive2D는 일러스트(아트)는 일러스트레이터가, 리깅은 별도의 Live2D 애니메이터가 담당하는 별개 인력일 수 있다고 명시한다.
     — 출처: ShiraLive2D (shiralive2d.com) | C | —

113. Vtubermodel.com 작가는 혼자 모든 커미션을 작업하기 때문에 다른 프로젝트가 많으면 지연될 수 있다고 밝혀, 1인 올인원 작업 방식을 보여준다.
     — 출처: vtubermodel.com | C | ★

114. 3D VTuber 파이프라인은 "모델링 → UV 언래핑 → 텍스처링 → 리깅(아마추어/스키닝) → 블렌드셰이프(셰이프 키) 설정 → VRM/FBX 익스포트" 순서를 따른다.
     — 출처: yelzkizi.org | B | —

115. 3D VTuber 모델은 Blender에서 리깅·텍스처링 후 FBX로 익스포트해 Unity의 UniVRM 패키지로 VRM 변환하며, VRChat용은 폴리곤 7만 트라이앵글 미만으로 최적화된다.
     — 출처: yelzkizi.org | B | ★

116. 3D 캐릭터 모델러 Fusako는 VTuber·VRChat 아바타로 20개 이상의 모델을 제작했다고 밝힌다.
     — 출처: Coloso (coloso.global) | B | —

### 보강 대상 2: 핸드 트래킹 기술 상세

117. VRChat은 Meta Quest용 핸드(핑거) 트래킹을 2022년 10월 26일 오픈 베타로 출시하고 2022년 11월 3일 버전 2022.4.1에서 정식 공개했다.
     — 출처: VRChat Wiki / VRChat Docs | A | —

118. VRChat의 Quest 핸드 트래킹은 Quest Link(유선) 연결에서는 작동하지 않는다.
     — 출처: VRChat Docs (docs.vrchat.com) | A | ★

119. StretchSense Studio Glove는 단종(End of Life)되어 더 이상 판매되지 않는다.
     — 출처: StretchSense 공식 (stretchsense.com) | A | —

120. StretchSense Mocap Pro Studio 글러브는 16개 센서로 손과 손가락 동작을 캡처한다.
     — 출처: StretchSense (stretchsense.com/mocap-pro-studio-2) | A | —

121. StretchSense는 자사 글러브가 SteamVR, Unity, Unreal Engine, Xsens와 통합되며 게임·VR 크리에이터·애니메이터·VTuber·모캡에 활용된다고 설명한다.
     — 출처: StretchSense 공식 (stretchsense.com) | A | —

122. MOXI 모캡 슈트는 StretchSense Studio Gloves와 통합해 핑거·핸드 트래킹을 추가할 수 있다.
     — 출처: Knoxlabs (knoxlabs.com) | B | —

123. SlimeVR의 표준 Butterfly Tracker는 핑거 트래킹용으로 설계되지 않았으나, 모캡·VTubing용 핸드 트래커로는 작동할 수 있다.
     — 출처: Crowd Supply SlimeVR Q&A | D | —

124. SlimeVR는 오픈소스 핑거 트래킹용 "SlimeVR Gloves"를 개발 중이라고 밝힌다.
     — 출처: Crowd Supply SlimeVR Updates | D | ★

125. SlimeVR 소프트웨어 손가락 모델은 한 손당 15개 본(손가락당 3개), 양손 총 30개 본으로 구성되며 손가락당 1~3개 트래커/데이터 포인트를 지원하도록 설계됐다.
     — 출처: GitHub SlimeVR-Server Issue #1086 | D | ★

126. SlimeVR는 최대 20개 트래킹 포인트와 함께 핑거 트래킹·발가락 트래킹을 개발 중이라고 명시한다.
     — 출처: Crowd Supply SlimeVR | D | —

127. Ultraleap Leap Motion Controller 2는 2023년 7월 출시됐다.
     — 출처: alibaba.com electronics Q&A | D | —

128. Leap Motion Controller 2는 공식 데이터시트 기준 최대 110cm(43") 거리의 3D 인터랙티브 존, 160°×160° 최대 시야각, 뼈·관절 포함 27개 손 요소 추적, 최대 120Hz를 제공한다.
     — 출처: Ultraleap 공식 데이터시트 (robotshop.com 호스팅 PDF) | A | ★

129. Leap Motion Controller 2는 듀얼 1280×960 IR 카메라를 사용하며, Ultraleap은 자사 핸드 트래킹이 120FPS 이상적 조건에서 ≤15ms 엔드-투-엔드 지연으로 평가된다고 설명한다(데스크톱 근거리 트래킹 시 sub-10ms로도 보고됨).
     — 출처: Ultraleap Blog / alibaba.com electronics Q&A | B | ★

130. Ultraleap은 Leap Motion Controller 2가 Luppet, VSeeFace를 포함한 주요 VTubing 소프트웨어와 호환된다고 명시한다.
     — 출처: Amazon Ultraleap 제품 페이지 | B | —

131. Leap Motion Controller 2는 출시 당시 $140에 사전 예약을 받았으며 Ultraleap 공식 권장가는 $139.00이다.
     — 출처: Road to VR / LearnXR Blog | D | —

132. Google Research는 MediaPipe Hands가 머신러닝으로 단일 프레임에서 한 손당 21개 3D 키포인트를 추론하며 모바일에서 실시간 성능을 달성한다고 2019년 발표했다.
     — 출처: Google Research Blog | A | —

133. VTube Studio는 핸드 트래킹을 지원한다.
     — 출처: VTube Studio 공식 (denchisoft.com) | A | —

134. 웹캠 기반 트래킹(MediaPipe 등)은 iPhone ARKit 대비 사각 각도와 가변 조명에서 안정성이 크게 떨어지며 눈 추적 정확도가 빠르게 저하된다.
     — 출처: MoCap Online VTuber Guide | B | —

### 보강 대상 3: AI 음성 합성의 VTuber 실적용

135. Neuro-sama는 2022년 12월 19일 Twitch에 데뷔한 AI VTuber로, LLM과 텍스트-투-스피치 음성, Live2D 아바타를 결합해 작동한다.
     — 출처: Wikipedia "Neuro-sama" | A | —

136. Neuro-sama의 TTS 보이스는 Microsoft Azure의 "Ashley"(en-US-AshleyNeural)이며 25% 피치 업된다.
     — 출처: VTuber Fandom Wiki "Neuro-sama" | B | —

137. CoeFont는 2023년 4월 10일 Pictoria사의 AITuber "Spinen"에 자사 디지털 보이스가 채택됐다고 발표했다.
     — 출처: CoeFont Medium 블로그 | B | ★

138. VOICEVOX는 딥러닝 기반 AI 음성 합성 소프트웨어로 Windows·Mac·Linux에서 무료로 사용 가능하며 상업적 사용 시 크레딧 표기가 필요하다.
     — 출처: ondoku3.com | C | —

139. VOICEVOX는 2024년 1월 노래 음성 합성("Humming") 기능을 추가했다.
     — 출처: ondoku3.com | C | ★

140. CoeFont STUDIO는 YELLSTON사가 개발한 무료 TTS 합성기로 2021년 4월 23일 출시됐다.
     — 출처: Vocal Synth Fandom Wiki | B | —

141. GPT-SoVITS는 5초 음성 샘플로 제로샷 TTS를, 1분 학습 데이터로 퓨샷 파인튜닝을 제공한다.
     — 출처: GitHub RVC-Boss/GPT-SoVITS README | A | —

142. GPT-SoVITS는 영어·일본어·한국어·광둥어·중국어의 크로스-링구얼 추론을 지원한다.
     — 출처: GitHub RVC-Boss/GPT-SoVITS README | A | —

143. GPT-SoVITS v2 ProPlus의 RTF(추론 속도)는 4090에서 0.014로 측정되어 실시간보다 훨씬 빠르게 합성한다.
     — 출처: GitHub RVC-Boss/GPT-SoVITS | A | ★

144. VITS 논문 "Conditional Variational Autoencoder with Adversarial Learning for End-to-End Text-to-Speech"(Kim, Kong, Son)는 arXiv 2106.06103으로 2021년 6월 11일 공개됐으며, GPT-SoVITS·Piper 등 여러 VTuber 음성 도구의 기반이 된다.
     — 출처: Hugging Face Papers | A | —

145. RVC(Retrieval-based Voice Conversion)는 AICoverGen·Ultimate RVC 등 파이프라인을 통해 VTuber/챗봇/AI 어시스턴트에 노래 기능을 추가하는 데 사용된다.
     — 출처: GitHub SociallyIneptWeeb/AICoverGen | B | —

146. Coqui XTTSv2는 200ms 미만 지연으로 스트리밍할 수 있다.
     — 출처: PyPI coqui-tts | A | ★

147. Neuro-sama 재현 오픈소스 프로젝트(kimjammer/Neuro)는 RealtimeTTS와 CoquiTTS XTTSv2 모델을 사용하며 오디오를 가상 오디오 케이블로 VTube Studio에 전달해 립싱크를 처리한다.
     — 출처: GitHub kimjammer/Neuro | A | ★

### 보강 대상 4: AI 일러스트 활용 논란 상세

148. 홀로라이브와 니지산지의 팬워크 가이드라인은 2차 창작물이 제3자 권리를 침해하지 않을 것을 요청한다.
     — 출처: Ani Trendz 2022 | D | —

149. 홀로라이브의 2차 창작 가이드라인은 팬에게 "팬/취미 수준"으로 창작을 제한하고 "영리로 간주될 수 있는 목적"으로 사용하지 말 것을 요청한다.
     — 출처: Dexerto | D | —

150. 홀로라이브 EN의 Takanashi Kiara는 2022년 10월 5일 자신의 아트 해시태그에 AI 생성 아트를 게시하지 말 것을 요청했다.
     — 출처: Ani Trendz 2022 | D | —

151. 홀로라이브 EN의 Mori Calliope와 Gawr Gura도 자신들의 전용 해시태그에 AI 아트를 홍보하지 말 것을 요청했다.
     — 출처: Dexerto | D | —

152. NovelAI Diffusion(애니메이션 스타일 이미지 생성기)은 Danbooru로 학습된 Stable Diffusion 기반이며 2022년 10월 등장해 손으로 그린 작품과 구별이 어려운 이미지를 출력했다.
     — 출처: Ani Trendz 2022 | D | —

153. AI 기반 VTuber Neuro-sama는 홀로코스트 부정 등 부적절한 발언으로 2023년 초 일시적으로 Twitch 밴을 당했다.
     — 출처: AI Incident Database | B | —

154. VTuber Ironmouse는 2026년 5월 4일 라이브 방송에서 게임 Neverness to Everness가 생성형 AI를 사용했다는 논란이 일자 스폰서십을 종료한다고 발표했다.
     — 출처: Dexerto | D | —

155. YouTuber Kwebbelkop(Jordi van den Bussche)은 2023년 8월 자신의 채널을 "Kwebbelkop AI"라는 포토리얼리스틱 AI 아바타로 전환했다.
     — 출처: Columbia Law and Arts Journal | B | ★

### 보강 대상 5: iPhone ARKit 트래킹의 VTuber 생태계 도입 타임라인

156. Apple은 iPhone X를 2017년 11월 3일 출시했으며 Face ID와 TrueDepth 카메라 시스템을 도입했다.
     — 출처: face.camera 블로그 | B | —

157. TrueDepth 시스템은 LED로 3만 개 이상의 불규칙 적외선 점 격자를 투사해 밀리초 단위로 깊이를 기록한다.
     — 출처: Apple Fandom Wiki | B | —

158. ARKit은 얼굴 지오메트리를 52개 블렌드셰이프 계수(jawOpen, eyeBlinkLeft 등)로 매핑한다.
     — 출처: MoCap Online VTuber Guide | B | —

159. iPhone/iPad가 ARKit "PerfectSync" 페이스 트래킹 데이터를 보내려면 iOS/iPadOS 11.0 이상이 필요하다.
     — 출처: VRCFT Docs (docs.vrcft.io) | A | ★

160. iPhone 13 이후 TrueDepth 시스템은 도트 프로젝터 패턴이 변경되어 X~12 모델 대비 모캡 콘텐츠 제작에는 덜 이상적이라고 평가된다.
     — 출처: face.camera 블로그 | D | ★

161. VTube Studio는 iOS에서 Apple ARKit, Android에서 Alter Mocap4Face 프레임워크를 사용한다.
     — 출처: VTube Studio GitHub Wiki | A | —

162. VTube Studio는 FaceID가 있는 iPhone/iPad 또는 A12 Bionic 칩 이상의 기기를 ARKit 트래킹에 지원한다.
     — 출처: VTube Studio GitHub Wiki | A | —

163. VBridger는 Live2D 모델에 iPhone X ARKit 트래킹을 더 잘 활용하게 하는 VTube Studio 페이스 트래킹 플러그인이다.
     — 출처: Steam VBridger | A | —

164. VSeeFace는 iFacialMocap/FaceMotion3D/VTube Studio/MeowFace를 통해 퍼펙트 싱크를 지원하며, 아바타에 52개 ARKit 블렌드셰이프가 필요하다.
     — 출처: VSeeFace 공식 사이트 | A | —

165. iFacialMocap 지원이 추가되기 전 iPhone 트래킹 데이터를 받는 유일한 방법은 Waidayo 또는 iFacialMocap2VMC였다.
     — 출처: VSeeFace 공식 사이트 | A | ★

166. 전문 VTuber 아바타는 크로스플랫폼 호환성을 위해 52개 ARKit 블렌드셰이프 표준을 구현한다.
     — 출처: Threedium (threedium.io) | B | —

### 보강 대상 6: 홀로라이브·니지산지 2D↔3D 전환 타임라인

167. 니지산지의 Niji3D는 ANYCOLOR(당시 Ichikara)가 2018년 11월 9일 발표한 니지산지 앱 기능으로, iPhone X와 Apple ARKit로 표정·동작을 인식해 3D 모델에 투영한다.
     — 출처: NamuWiki "니지산지/3D" | B | —

168. Niji3D는 트래킹이 어려운 손 동작을 Oculus Rift의 Oculus Touch 컨트롤러와 센서로 처리한다.
     — 출처: NamuWiki "니지산지/3D" | B | ★

169. 니지산지는 Live2D와 전통적 풀바디 3D 모캡 외에 스튜디오 없이 3D 모델로 방송할 수 있는 "Niji 3D"를 지원한다.
     — 출처: VTuber Fandom Wiki "NIJISANJI" | B | —

170. 니지산지 앱은 iPhone X 페이스 모캡 기술로 Live2D 애니메이션 아바타 스트리밍을 가능하게 해, Kizuna AI에 쓰인 풀바디 3D 모캡보다 단순하고 저렴했다.
     — 출처: TV Tropes "Nijisanji" | B | —

171. 니지산지는 2022년 10월 1~2일 NIJIFes 2022에서 Hana Macchia가 첫 ex-ID 라이버로 3D 모델을 공개했다.
     — 출처: VTuber Fandom Wiki "NIJISANJI (main branch)" | B | ★

172. 니지산지 EN의 Elira Pendora는 2023년 1월 13일 3D 의상 데뷔를 시작했다.
     — 출처: Dexerto | D | —

173. 니지산지는 데뷔 후 라이버에게 2.0·3.0 브러시업을 제공하며 3D 모델 보유자는 3D 브러시업도 받을 수 있다.
     — 출처: VTuber Fandom Wiki "NIJISANJI" | B | —

174. 홀로라이브 English -Myth-(Mori Calliope, Takanashi Kiara, Ninomae Ina'nis, Gawr Gura, Watson Amelia)는 2020년 9월 데뷔했다.
     — 출처: Siliconera | D | —

175. 홀로라이브 EN Myth의 3D 모델은 2022년 3월 "hololive 3rd fes. Link Your Wish"에서 처음 공개됐으나 정식 3D 데뷔 스트림은 COVID-19로 지연됐다.
     — 출처: Dot Esports | D | —

176. 홀로라이브 EN Myth의 3D 모델 쇼케이스 릴레이는 2023년 2월 18일(Ina'nis)부터 시작해 3월 4일(PST) 합동 스트림으로 마무리됐으며 순서는 Ina → Kiara → Calli → Gura → Ame였다.
     — 출처: Hololive 공식 뉴스 (hololivepro.com) | A | ★

177. Gawr Gura는 2022년 3월 19일 "hololive 3rd fes. Link Your Wish" 1일차에 3D 모델을 데뷔했다.
     — 출처: VTuber Fandom Wiki "Gawr Gura" | B | —

178. 홀로라이브 EN -Council-은 2021년 8월 23일 데뷔했다.
     — 출처: Hololive Wiki | B | —

179. PLAVE는 한국 가상 아이돌 그룹으로 2023년 3월 데뷔했으며 Unreal Engine으로 렌더링된 디지털 휴먼이다.
     — 출처: Unreal Engine 공식 Spotlight | A | —

180. PLAVE의 다섯 멤버는 실제 인간 퍼포머가 모션 캡처 기술로 실시간 연기하며, AI가 아니다.
     — 출처: HTC Vive Blog | B | —

181. PLAVE 개발사 VLAST는 Unreal Engine의 Live Link 플러그인으로 모션 캡처 원시 데이터를 스트리밍하고 Take Recorder로 시퀀스를 캡처한다.
     — 출처: Unreal Engine 공식 Spotlight | A | ★

182. VLAST는 모션 캡처·오디오·Unreal Engine 녹화를 단일 워크플로우로 동기화하는 태블릿 앱 "Virtual Slate"를 개발했다.
     — 출처: Unreal Engine 공식 Spotlight | A | ★

183. PLAVE는 2024년 3월 9일 MBC "Show! Music Core"에서 "WAY 4 LUV"로 1위를 차지하며 주요 음악방송에서 1위를 한 첫 가상 아이돌이 됐다(종합 첫 음악방송 1위는 3월 6일 MBC M "Show Champion"이 선행).
     — 출처: Koreaboo / Seoulz | D | —

184. HYBE와 YG PLUS는 2024년 초 VLAST에 지분 투자를 했다.
     — 출처: Malay Mail | D | ★

---

## 고유성 재평가

| 팩트 # | 밀도 변경 | 근거 |
|--------|----------|------|
| #123 (SlimeVR Butterfly 핸드 트래킹) | D 유지 | Crowd Supply Q&A가 유일 출처이나, 제조사 직접 답변이므로 B 격상 고려. 단, 크라우드펀딩 특성상 제품 미확정이므로 D 유지 |
| #127 (Leap Motion 2 출시 시점) | D → B 격상 가능 | alibaba.com Q&A가 1차 출처는 아니지만, Ultraleap 공식 데이터시트(#128)에서 제품 존재 확인. Road to VR(#131)에서도 교차 확인됨 |
| #160 (iPhone 13 이후 모캡 품질) | D 유지, ★ 유지 | face.camera 블로그의 기술 분석으로 Apple 공식 발표가 아님. 고유한 관점이지만 검증 필요 |
| #167–#168 (Niji3D 도입일) | B 유지 | NamuWiki 출처. ANYCOLOR 공식 1차 발표로 추가 교차검증 권장 |

---

## 획득 불가 항목

아래 항목은 Phase 2 보강에서 검색했으나 출처가 있는 팩트로 확보하지 못한 것들이에요. Phase 3에서 gap으로 처리됩니다.

1. **홀로라이브 JP의 3D 데뷔 기준 (구독자 수, 활동 기간 임계값)**
   — Cover Corporation이 공식적으로 3D 모델 제공 기준을 명시한 1차 출처를 찾지 못했다. 커뮤니티에서는 "구독자 10만 명 이상 + 일정 활동 기간"이라는 추측이 있으나 출처 없는 해석이므로 수집 대상에서 제외.

2. **Twitch·YouTube의 AI 생성 VTuber 아바타 관련 명문 정책**
   — 플랫폼이 AI 생성 아바타를 직접 규율하는 정책 조항을 1차 출처(ToS, 커뮤니티 가이드라인)에서 확인하지 못했다. 확인된 것은 에이전시(홀로라이브·니지산지)의 팬워크 가이드라인 수준.

3. **Neuro-sama 외 AI TTS 실시간 라이브 방송 VTuber의 구체적 시청자 수·방송 시간 데이터**
   — CoeFont→Pictoria "Spinen" (#137) 외에 에이전시 레벨의 AI TTS 실사용 사례를 출처와 함께 확보하지 못했다. 인디 레벨의 개인 프로젝트는 GitHub에 다수 존재하나 방송 실적 데이터가 없다.

4. **VTube Studio의 초기 ARKit 지원 시작 시점 (정확한 버전·날짜)**
   — VTube Studio가 처음 iPhone ARKit을 지원하기 시작한 정확한 버전과 날짜를 1차 출처에서 확인하지 못했다. GitHub Wiki에는 현재 지원 사양만 기재.

5. **니지산지 JP Livers의 3D 모델 제공 시작 시점과 선정 기준**
   — 최초 3D 모델 제공 Liver가 누구인지, ANYCOLOR의 선정 기준이 무엇인지 공식 출처 미확인. Niji3D 기술 발표(2018년 11월)는 확인됐으나 실제 적용 시작 시점은 별도.

---

## 출처 조견표 (#1~#184)

### Phase 1 원본 (#1~#106)

| # | 팩트 요약 | 출처 | 밀도 | 고유성 |
|---|----------|------|------|--------|
| 1 | Kizuna AI 2016-11-29 YouTube 첫 업로드, "Virtual YouTuber" 용어 최초 사용 | Wikipedia "Kizuna AI" / "VTuber" | A | — |
| 2 | Kizuna AI 제작: Activ8 산하, 성우 카스가 노조미 | Wikipedia "Kizuna AI" | A | — |
| 3 | Kizuna AI 3D 모델: 디자인 En Morikura, 모델링 Tomitake, 감수 Tda | Wikipedia "Kizuna AI" | A | ★ |
| 4 | Kizuna AI 데뷔 10개월 만에 구독자 200만, 2021년까지 400만+ | Wikipedia "Kizuna AI" | A | — |
| 5 | FaceRig 2014년 Steam 출시, 웹캠 기반 라이브 아바타 최초 | Wikipedia "VTuber" | A | — |
| 6 | FaceRig 2015년 Live2D Inc. 협업, 2D 아바타 모듈 추가 | Wikipedia "VTuber" | A | — |
| 7 | ANYCOLOR(이치카라) 2017년 설립, 2018-02 니지산지 출범 | VTuber Wiki / TV Tropes | A | — |
| 8 | 니지산지: iPhone X 페이셜 모캡 + Live2D 자체 앱, 3D 풀바디보다 저비용 | TV Tropes / VTuber Wiki | B | — |
| 9 | 니지산지: 라이브 스트리밍 + Live2D 포맷 전환, 현대 VTuber 포맷 정립 | Wikipedia / VTuber Wiki | A | — |
| 10 | Cover Corp: 원래 AR/VR 회사, 2017년 Hololive 앱 출시 후 VTuber 전환 | Wikipedia "Hololive" | A | — |
| 11 | 토키노 소라 2017-09 데뷔, 홀로라이브 첫 번째 멤버 | Shapes.inc | B | — |
| 12 | 2018-05~07 활동 VTuber 2,000→4,000명 | Wikipedia "VTuber" | A | — |
| 13 | 2020년까지 전 세계 활동 VTuber 10,000명 초과 | Wikipedia "VTuber" | A | — |
| 14 | VShojo 2020-11 설립, 서구 최초 VTuber 에이전시 중 하나 | Wikipedia "VTuber" | A | — |
| 15 | Kizuna AI 2022-02-26 무기한 중단, 2025-02-26 복귀 | Kizuna AI Wiki | B | — |
| 16 | VShojo 2025년 운영 중단 | vchavcha.com | B | ★ |
| 17 | Twitch VTubing 2021년 전년비 467% 성장 (Amazon 데이터) | Wikipedia "VTuber" | A | ★ |
| 18 | Live2D 2010년 베타, 2013년 Cubism 1.0 릴리스 | Grokipedia | B | — |
| 19 | Cubism 2.0 2014년 출시, 다중 레이어 변형 도입 | Grokipedia | B | — |
| 20 | Cybernoids → Live2D Inc. 사명 변경 (2014년) | Grokipedia | B | ★ |
| 21 | Cubism 3.0 SDK 2017-06 튜토리얼 공개, 물리 시뮬레이션 정식 지원 | Live2D 공식 문서 | A | — |
| 22 | Cubism 4.0 SDK R1 2020-01 릴리스 | Live2D 공식 문서 | A | — |
| 23 | Cubism 4.2: Multiply Color, Screen Color, Blend Shapes 추가 | Live2D 공식 문서 | A | ★ |
| 24 | Cubism 5.0: 다크/라이트 테마, HiDPI, Motion-sync, 강화 Blend Shapes | Live2D 공식 문서 | A | — |
| 25 | Cubism 5.1.00 릴리스, 5.2에서 Parameter Controller 추가 | Live2D 공식 문서 | A | ★ |
| 26 | 2018년 Aniplex가 Live2D Inc. 지분 과반 인수, 영화 협업 발표 | Grokipedia | B | ★ |
| 27 | Live2D Creative Studio 2021년 극장판 《벨》 애니메이션 기여 | Grokipedia | B | ★ |
| 28 | Cubism Editor PRO 유료 구독, 무료 42일 PRO 트라이얼 후 FREE 전환 | Live2D 공식 | A | — |
| 29 | VTuber 아바타 제작 순서: 디자인→파츠 분리→리깅→물리→테스트 | ShiraLive2D / vtubermodelcommissions | C | — |
| 30 | Live2D 리깅 시 48개+ 파츠 레이어 분리 필요 (대칭 기준) | GrifNMore | C | ★ |
| 31 | 리깅 아티스트: 9방향 배열, 기본 표정 생성, 물리 설정 | GrifNMore | C | — |
| 32 | VRoid Studio: 무료 3D 아바타 제작 도구, 기본 애니메 스타일 | 다수 출처 | C | — |
| 33 | PNGTuber 비용: $40~$200 | Pixel Studios / BuzzFlick | C | — |
| 34 | 입문용 Live2D: $450~$1,450 (일러스트 $250~$700 + 리깅 $200~$750) | Cloud Animations | C | — |
| 35 | 중급 Live2D: $1,600~$3,300 (일러스트 $800~$1,500 + 리깅 $800~$1,800) | Cloud Animations | C | — |
| 36 | 프리미엄 Live2D (에이전시급): $3,500~$7,500 | Cloud Animations | C | — |
| 37 | 풀바디 Live2D 프로: $2,000~$5,000+, 2019년 $200~$1,000에서 급등 | BuzzFlick | C | — |
| 38 | 고도 디테일 Live2D (70° 회전, 다층 헤어 물리): ~$5,000 | Viverse | C | ★ |
| 39 | 입문용 3D: $1,300~$3,800 | Cloud Animations | C | — |
| 40 | 고급 3D (기업·모캡용): $5,000~$15,000+ | Cloud Animations | C | — |
| 41 | 3D 고급 애니메이션 (댄스 등) 추가: $1,000~$3,000 | Delta Animations | C | — |
| 42 | 역대 최고가 VTuber 모델: $15,000 초과 | ARwall / Cloud Animations | C | — |
| 43 | 상업 라이선스 추가: 기본 가격의 1.5~3배 | Cloud Animations | C | ★ |
| 44 | 러시 오더 수수료: 기본의 50%~200% 추가 | Cloud Animations / ShiraLive2D | C | — |
| 45 | 마이너 수정 1~3회 기본 포함, 메이저 수정 시간당 과금 | Cloud Animations | C | — |
| 46 | 의상 추가·시즌 업데이트: 아트+리깅 모두 필요, 가장 빈번한 반복 비용 | Viverse | C | — |
| 47 | 인기 아티스트 대기 목록: 최대 6개월 | Cloud Animations | C | ★ |
| 48 | iPhone TrueDepth: 30,000 IR 도트, 60fps, ARKit 52개 블렌드셰이프 | MoCap Online | B | — |
| 49 | ARKit 페이스 트래킹: iPhone X(2017) 이후 Face ID 탑재 전 모델 | MoCap Online | B | — |
| 50 | VTube Studio: 웹캠(OpenSeeFace) 또는 iPhone/Android 페이스 트래킹 | VTube Studio 공식 / Live3D | B | — |
| 51 | 2022년 VTube Studio NVIDIA RTX AI 가속 페이셜 모캡 업데이트 | Wikipedia "VTuber" | A | ★ |
| 52 | VBridger: VTube Studio + Live2D 전용, ARKit 데이터 증강·혼합·수정 | Steam "VBridger" | A | — |
| 53 | VBridger 입력 소스: iFacialMocap, FaceMotion3D, MeowFace, VTS, MediaPipe, NVIDIA | Steam "VBridger" | A | — |
| 54 | VSeeFace: 무료 VRM, Perfect Sync(52개 ARKit 블렌드셰이프) | VSeeFace 공식 | A | — |
| 55 | 웹캠 vs ARKit: 웹캠은 측면 각도·가변 조명에서 안정성 크게 열위 | MoCap Online | B | — |
| 56 | 니지산지 Livers: iPhone 모캡 + ANYCOLOR 리깅 + NIJISANJI 앱(비매품) | VTuber Wiki | B | — |
| 57 | 전신 트래킹 4단계: 페이스→VR+Vive Tracker→관성 슈트→슈트+광학 페이스 | MoCap Online | B | — |
| 58 | Rokoko Smartsuit Pro II: $2,500, 19 IMU, 가장 대중적 관성 풀바디 | MoCap Online / Rokoko | B | — |
| 59 | Perception Neuron Studio: $1,500, 17 센서 | MoCap Online | C | — |
| 60 | Xsens MVN Awinda: $5,000+, 2024년 구독료 $500~$800/월 인상 논란 | Rokoko 비교 | C | ★ |
| 61 | Rokoko Smartgloves: $695, Smartsuit Pro II와 결합 핑거 트래킹 | MoCap Online | B | — |
| 62 | Rokoko Coil Pro: UWB 기반 위치 보정, IMU 드리프트 감소 | beforesandafters.com | D | ★ |
| 63 | Leap Motion Controller: IR 광학 핸드 트래커, VSeeFace 등 지원 | VSeeFace / MoCap Online | B | — |
| 64 | 핸드 트래킹 액세서리: $100~$500 추가 비용 | Viverse | C | — |
| 65 | 니지산지 Niji 3D: 스튜디오 없이 3D 방송, 상반신+핸드 트래킹 제한 | VTuber Wiki | B | — |
| 66 | VTube Studio: 가장 널리 사용, iOS/Android/Steam, Live2D 전용 | Live3D / vtubermodelcommissions | B | — |
| 67 | VSeeFace: 무료 VRM, Windows 8+, VMC 프로토콜 | VSeeFace 공식 | A | — |
| 68 | VMagicMirror: Windows 전용 VRM, 키보드·마우스로 조작, 사운드 립싱크 | SaaSHub / Live3D | B | — |
| 69 | Animaze(구 FaceRig): 자체 렌더 엔진, 다포맷, 암호화 .avatar 역공학 방지 | GitHub Gist | B | ★ |
| 70 | OBS: 핵심 방송 백본, 게임 캡처·Spout2·가상 카메라 투명 배경 합성 | vtubermodelcommissions / VSeeFace | B | — |
| 71 | VTube Studio API: 서드파티 플러그인(VBridger 등) Live2D 모델 제어 | Steam "VBridger" | A | — |
| 72 | 홀로라이브 2020-01 토요스 PIT 첫 단독 3D 콘서트 "Nonstop Story", 23명 | Shapes.inc | B | — |
| 73 | 2024년 홀로라이브 EN "Mixed Reality Concert Series", AR·공간 컴퓨팅 | SkyQuestt | C | ★ |
| 74 | 니지산지 EN 2024-04-14 첫 AR 이벤트 "COLORS", 라이브 밴드+AR | NIJISANJI 공식 / VTuber Wiki | A | — |
| 75 | 니지산지 2024-12-31 오사카 "COUNTDOWN LIVE", 21명, 14,300엔 | vchavcha.com | B | ★ |
| 76 | NexStage: UE 기반 실시간 3D 콘서트, 5벌 프로 모캡 슈트, 미국 내 5인 스튜디오 3곳 | VTuber NewsDrop | D | ★ |
| 77 | NexStage: VTuber 팬이 실시간 모캡 난이도 인지 못함, 일본 외 기술 진입장벽 | VTuber NewsDrop | D | ★ |
| 78 | PLAVE: 만화 스타일 + 고정밀 3D 모캡, 음악·댄스 중심 | vchavcha.com | B | — |
| 79 | PLAVE 2025-08 아시아 투어, 서울 고척 스카이돔 앙코르 37,000명 | vchavcha.com | B | ★ |
| 80 | PLAVE 티켓 사전판매 피크 트래픽 530,000건, 대기 30,000명+ | vchavcha.com | B | ★ |
| 81 | Cover Corp 2025~2026 회계연도 holoEarth 33억엔 손실, 순손실 9.1억엔 | Wikipedia "Hololive" | A | ★ |
| 82 | Neuro-sama: 영국 Vedal 개발, 2022-12-19 Twitch 데뷔 | Wikipedia / Fandom | A | — |
| 83 | Neuro-sama 원형: 2018~2019 osu! 플레이용 신경망 | Wikipedia | A | — |
| 84 | Neuro-sama: LLM 핵심 엔진, Azure TTS "Ashley" 25% 피치 업 | Wikipedia / VTuber Wiki | A | — |
| 85 | Neuro-sama LLM: 2025 초 기준 2B 파라미터, q2_k 양자화 | Fandom Wiki | B | ★ |
| 86 | Neuro-sama 게임 AI: LLM과 별도, 컴퓨터 비전 80×60 그레이스케일 | Grokipedia | B | — |
| 87 | 2023년 초 Neuro-sama 홀로코스트 부정 발언 생성, 필터링 문제 | futureaiblog / Wikipedia | A | — |
| 88 | Neuro-sama 첫 커스텀 모델 2023-05-27, 디자인 Anny, 모델링 Otozuki Teru | Wikipedia | A | — |
| 89 | 2025-01-01 Neuro-sama Twitch 하이프 트레인 역대 최고 레벨 111 | Wikipedia / Fandom | A | — |
| 90 | 2026-01 기준 Neuro-sama ~100만 팔로워, Twitch 역대 3위 구독, VTuber 1위 | Wikipedia / Fandom | A | — |
| 91 | 2025-11-15 Neuro-sama 3D 모델 데뷔 스트림 | Wikipedia | A | ★ |
| 92 | Open-LLM-VTuber: sherpa-onnx, MeloTTS, GPTSoVITS, Bark 등 다양한 TTS | GitHub | A | — |
| 93 | GPTSoVITS 음성 클로닝으로 AI VTuber 음색 부여 | GitHub / ai-vtuber topic | B | — |
| 94 | Cubism 5.0 "Motion-sync": 오디오 기반 립싱크 베이킹 에디터 내 지원 | Live2D 공식 | A | ★ |
| 95 | Animaze 암호화 .avatar: AI 기반 역공학·무단 사용 방지 명시 | GitHub Gist (Animaze 코멘트) | B | ★ |
| 96 | 2026-05 NTE AI 배경 아트 발각, Ironmouse 스폰서십 해지, Shylily 방송 종료 | NTE Guide | B | — |
| 97 | Hotta Studio: AI 도구는 소수 배경·환경 에셋에 한정, 캐릭터·스토리는 인간 제작 | NTE Guide | B | — |
| 98 | VTuber 커뮤니티: AI 아바타 아트가 일러스트레이터·리거 생계 위협 비판 지속 | toolify.ai | D | — |
| 99 | 니지산지 2.0 브러시업: 움직임 확장+표정 추가, 2022년 이후 신규 기본 적용 | VTuber Wiki | B | — |
| 100 | 3.0 브러시업 2021년 시작, 새 표정·확장 움직임·토글, 추첨 배분 | VTuber Wiki | B | — |
| 101 | 2022-11 기준 니지산지 146명 2.0 브러시업 완료 | VTuber Wiki | B | — |
| 102 | 2024-03 기준 니지산지 3.0: JP 85 + ID 2 + KR 5 = 92명, EN 16명 | VTuber Wiki | B | — |
| 103 | 2024년 글로벌 VTuber 시장 $25.4억 | SkyQuestt | C | — |
| 104 | 2033년까지 $136.2억 전망, CAGR 20.5% | SkyQuestt | C | — |
| 105 | 2025-05 홀로라이브 88명 활동, YouTube 8,000만+ 구독 | Wikipedia "Hololive" | A | — |
| 106 | 2026-06 니지산지 196명 활동 (JP 151, ID 6, KR 11, EN 28), YouTube 6,000만+ | VTuber Wiki | B | — |

### Phase 2 보강 (#107~#184)

| # | 팩트 요약 | 출처 | 밀도 | 고유성 |
|---|----------|------|------|--------|
| 107 | Live2D 커미션 워크플로우: 일러스트→PSD 분리→리깅→물리→테스트 | ShiraLive2D | C | — |
| 108 | ShiraLive2D: 리깅 통상 2~4주 | ShiraLive2D | C | — |
| 109 | Vtubermodel.com: 리깅 2~3주, 전체 2~3개월 (수정 없을 시) | vtubermodel.com | C | ★ |
| 110 | Fiverr Yuki_ono: 스케치 1~2일, 컬러/커팅 2~4일, 리깅 2~7일, 총 5~15일 | Fiverr | C | ★ |
| 111 | typeou: 70+ 풀바디 리깅, 통상 10~20일 | typeou.dev | C | ★ |
| 112 | ShiraLive2D: 일러스트와 리깅 별도 인력 가능 | ShiraLive2D | C | — |
| 113 | Vtubermodel.com: 1인 올인원 작업 방식, 타 프로젝트 시 지연 | vtubermodel.com | C | ★ |
| 114 | 3D 파이프라인: 모델링→UV→텍스처링→리깅→블렌드셰이프→VRM/FBX 익스포트 | yelzkizi.org | B | — |
| 115 | 3D: Blender→FBX→Unity UniVRM→VRM, VRChat 7만 트라이앵글 미만 최적화 | yelzkizi.org | B | ★ |
| 116 | Fusako: VTuber·VRChat 아바타 20+ 제작 | Coloso | B | — |
| 117 | VRChat Quest 핸드 트래킹: 2022-10-26 오픈베타, 2022-11-03 정식 (v2022.4.1) | VRChat Wiki/Docs | A | — |
| 118 | VRChat Quest 핸드 트래킹: Quest Link(유선)에서 미작동 | VRChat Docs | A | ★ |
| 119 | StretchSense Studio Glove: 단종(EOL) | StretchSense 공식 | A | — |
| 120 | StretchSense Mocap Pro Studio: 16개 센서 | StretchSense 공식 | A | — |
| 121 | StretchSense: SteamVR·Unity·UE·Xsens 통합, VTuber·모캡 활용 명시 | StretchSense 공식 | A | — |
| 122 | MOXI 모캡 슈트: StretchSense Gloves 통합 핑거·핸드 트래킹 | Knoxlabs | B | — |
| 123 | SlimeVR Butterfly: 핑거용 미설계, 핸드 트래커로는 작동 | Crowd Supply Q&A | D | — |
| 124 | SlimeVR: 오픈소스 "SlimeVR Gloves" 핑거 트래킹 개발 중 | Crowd Supply Updates | D | ★ |
| 125 | SlimeVR 핑거 모델: 한 손 15본(×3), 양손 30본, 손가락당 1~3 데이터 포인트 | GitHub Issue #1086 | D | ★ |
| 126 | SlimeVR: 최대 20 트래킹 포인트, 핑거+발가락 트래킹 개발 중 | Crowd Supply | D | — |
| 127 | Leap Motion Controller 2: 2023-07 출시 | alibaba.com / Road to VR | D→B | — |
| 128 | Leap Motion 2: 110cm, 160°×160°, 27 손 요소, 최대 120Hz | Ultraleap 데이터시트 | A | ★ |
| 129 | Leap Motion 2: 듀얼 1280×960 IR, ≤15ms e2e 지연, 근거리 sub-10ms | Ultraleap Blog | B | ★ |
| 130 | Leap Motion 2: Luppet·VSeeFace VTubing 소프트웨어 호환 명시 | Amazon Ultraleap | B | — |
| 131 | Leap Motion 2: 출시가 $140, 권장가 $139 | Road to VR / LearnXR | D | — |
| 132 | MediaPipe Hands: 한 손당 21 3D 키포인트, 모바일 실시간 (2019) | Google Research Blog | A | — |
| 133 | VTube Studio: 핸드 트래킹 지원 | VTube Studio 공식 | A | — |
| 134 | 웹캠 vs ARKit: 웹캠은 사각 각도·가변 조명에서 안정성 크게 열위 | MoCap Online | B | — |
| 135 | Neuro-sama: LLM + TTS + Live2D, 2022-12-19 Twitch 데뷔 | Wikipedia | A | — |
| 136 | Neuro-sama TTS: Azure "Ashley" (en-US-AshleyNeural), 25% 피치 업 | Fandom Wiki | B | — |
| 137 | CoeFont 2023-04-10: Pictoria AITuber "Spinen"에 디지털 보이스 채택 | CoeFont Medium | B | ★ |
| 138 | VOICEVOX: 무료, Win/Mac/Linux, 상업 사용 시 크레딧 필요 | ondoku3.com | C | — |
| 139 | VOICEVOX 2024-01: 노래 합성 "Humming" 기능 추가 | ondoku3.com | C | ★ |
| 140 | CoeFont STUDIO: YELLSTON 개발, 무료 TTS, 2021-04-23 출시 | Vocal Synth Fandom | B | — |
| 141 | GPT-SoVITS: 5초 제로샷 TTS, 1분 퓨샷 파인튜닝 | GitHub README | A | — |
| 142 | GPT-SoVITS: 영어·일본어·한국어·광둥어·중국어 크로스-링구얼 | GitHub README | A | — |
| 143 | GPT-SoVITS v2 ProPlus: RTF 0.014 (4090), 실시간 대비 초고속 | GitHub | A | ★ |
| 144 | VITS 논문 (Kim et al.) 2021-06-11 arXiv, GPT-SoVITS·Piper 등 기반 | Hugging Face Papers | A | — |
| 145 | RVC: AICoverGen·Ultimate RVC, VTuber/챗봇 노래 기능 추가 | GitHub AICoverGen | B | — |
| 146 | Coqui XTTSv2: 200ms 미만 스트리밍 지연 | PyPI coqui-tts | A | ★ |
| 147 | Neuro-sama 재현 프로젝트: RealtimeTTS + XTTSv2 → 가상 오디오 → VTS 립싱크 | GitHub kimjammer/Neuro | A | ★ |
| 148 | 홀로라이브·니지산지 팬워크 가이드라인: 제3자 권리 침해 금지 | Ani Trendz | D | — |
| 149 | 홀로라이브 2차 창작 가이드라인: "팬/취미 수준", 영리 목적 금지 | Dexerto | D | — |
| 150 | Kiara 2022-10-05: 아트 해시태그에 AI 아트 게시 금지 요청 | Ani Trendz | D | — |
| 151 | Calliope·Gura: 전용 해시태그에 AI 아트 홍보 금지 요청 | Dexerto | D | — |
| 152 | NovelAI Diffusion: Danbooru 학습 SD 기반, 2022-10 등장 | Ani Trendz | D | — |
| 153 | Neuro-sama 2023년 초 Twitch 일시 밴 (홀로코스트 부정 발언) | AI Incident DB | B | — |
| 154 | Ironmouse 2026-05-04: NTE AI 사용 논란으로 스폰서십 종료 | Dexerto | D | — |
| 155 | Kwebbelkop 2023-08: "Kwebbelkop AI" 포토리얼 AI 아바타 전환 | Columbia Law & Arts | B | ★ |
| 156 | iPhone X 2017-11-03 출시, Face ID + TrueDepth 도입 | face.camera | B | — |
| 157 | TrueDepth: LED로 3만+ 불규칙 IR 점 투사, 밀리초 깊이 기록 | Apple Fandom Wiki | B | — |
| 158 | ARKit 52개 블렌드셰이프 계수 (jawOpen, eyeBlinkLeft 등) | MoCap Online | B | — |
| 159 | ARKit PerfectSync: iOS/iPadOS 11.0 이상 필요 | VRCFT Docs | A | ★ |
| 160 | iPhone 13 이후 TrueDepth 도트 프로젝터 패턴 변경, X~12 대비 모캡 덜 이상적 | face.camera | D | ★ |
| 161 | VTube Studio: iOS=ARKit, Android=Alter Mocap4Face | VTS GitHub Wiki | A | — |
| 162 | VTube Studio ARKit: FaceID 탑재 또는 A12 Bionic+ 기기 | VTS GitHub Wiki | A | — |
| 163 | VBridger: Live2D + iPhone X ARKit 플러그인 | Steam | A | — |
| 164 | VSeeFace: iFacialMocap 등 퍼펙트 싱크, 아바타에 52 블렌드셰이프 필요 | VSeeFace 공식 | A | — |
| 165 | VSeeFace: iFacialMocap 지원 전 Waidayo/iFacialMocap2VMC만 가능 | VSeeFace 공식 | A | ★ |
| 166 | 전문 VTuber 아바타: 52 ARKit 블렌드셰이프 표준 구현 | Threedium | B | — |
| 167 | Niji3D 2018-11-09 ANYCOLOR 발표, iPhone X + ARKit → 3D 모델 투영 | NamuWiki | B | — |
| 168 | Niji3D: 손 동작을 Oculus Touch 컨트롤러+센서로 처리 | NamuWiki | B | ★ |
| 169 | 니지산지: Live2D + 풀바디 3D + Niji 3D (스튜디오 불필요) 3종 지원 | VTuber Fandom | B | — |
| 170 | 니지산지 앱: iPhone X 모캡 + Live2D, Kizuna AI 풀바디 3D보다 저렴 | TV Tropes | B | — |
| 171 | NIJIFes 2022 (2022-10-01~02): Hana Macchia 첫 ex-ID 3D 공개 | VTuber Fandom | B | ★ |
| 172 | 니지산지 EN Elira Pendora 2023-01-13 3D 의상 데뷔 | Dexerto | D | — |
| 173 | 니지산지: 2.0·3.0 브러시업 + 3D 보유자 3D 브러시업 | VTuber Fandom | B | — |
| 174 | 홀로라이브 EN Myth (5명) 2020-09 데뷔 | Siliconera | D | — |
| 175 | Myth 3D: 2022-03 hololive 3rd fes. 첫 공개, 정식 데뷔 COVID로 지연 | Dot Esports | D | — |
| 176 | Myth 3D 릴레이: 2023-02-18(Ina)~03-04 합동, Ina→Kiara→Calli→Gura→Ame | Hololive 공식 뉴스 | A | ★ |
| 177 | Gura 3D: 2022-03-19 hololive 3rd fes. 1일차 | VTuber Fandom | B | — |
| 178 | 홀로라이브 EN Council 2021-08-23 데뷔 | Hololive Wiki | B | — |
| 179 | PLAVE 2023-03 데뷔, Unreal Engine 렌더링 디지털 휴먼 | UE 공식 Spotlight | A | — |
| 180 | PLAVE 5멤버: 실제 인간 퍼포머 + 모캡 실시간, AI 아님 | HTC Vive Blog | B | — |
| 181 | VLAST: UE Live Link → 모캡 스트리밍, Take Recorder → 시퀀스 캡처 | UE 공식 Spotlight | A | ★ |
| 182 | VLAST "Virtual Slate": 모캡·오디오·UE 녹화 동기화 태블릿 앱 | UE 공식 Spotlight | A | ★ |
| 183 | PLAVE 2024-03-09 MBC "Show! Music Core" 1위, 가상 아이돌 음방 첫 1위 | Koreaboo / Seoulz | D | — |
| 184 | HYBE·YG PLUS 2024년 초 VLAST 지분 투자 | Malay Mail | D | ★ |

---

## 주의사항 (Caveats)

1. **커미션 소요 시간 (#108~#111):** 개별 리거의 자기 신고치이며 업계 표준 평균이 아니다.
2. **AI 음성 지연 수치 (#143, #146):** 공식 릴리스 노트·체인지로그 기반이나, 풀 파이프라인(LLM 추론 + TTS + 오디오 전달) 지연은 별도이며 #147의 재현 프로젝트에서 ~500ms로 보고됨.
3. **VITS ↔ VOICEVOX 통념 정정:** VOICEVOX는 end-to-end VITS가 아니라 3개 DNN(duration·pitch·decode) 캐스케이드 파이프라인을 사용하므로 "VITS = VOICEVOX 기반"은 부정확하다. VITS의 실제 VTuber 적용처는 GPT-SoVITS·Piper 등이다.
4. **iPhone 13 이후 모캡 품질 (#160):** face.camera 블로그의 기술 분석이며 Apple 공식 발표가 아닌 teardown·실측 기반 주장이다.
5. **Niji3D 도입일 (#167~#168):** NamuWiki(한국어 위키) 출처. ANYCOLOR 공식 1차 발표로 교차검증 권장.
6. **AI 일러스트 논란 영역 (#148~#155):** D등급 출처(뉴스 단일 보도) 비율이 높다 (8개 중 6개가 D). 에이전시 공식 정책 원문보다 뉴스 보도를 통한 간접 확인에 의존하고 있으므로 인용 시 출처 등급 명시 필요.

---
---

# Phase 1 Original (원본 보존)

> 아래는 Phase 1 산출물의 원본 전문이며, 수정 없이 그대로 보존한다.

---

# 버튜버 기술·제작 인프라 팩트북

> 수집일: 2026-06-30 | 형식: 팩트 번호 매김 | 밀도 등급 A–E | 고유성 ★/—

---

## 밀도 등급 기준
- **A** = 1차 출처(공식 문서, 제조사 발표, 위키피디아 인용 포함)
- **B** = 업계 전문 미디어 또는 검증된 커뮤니티 위키
- **C** = 다수 출처 교차 확인된 시장 보고서·가격 정보
- **D** = 단일 매체 보도 또는 제한적 검증
- **E** = 커뮤니티 포럼·개인 블로그(사실 확인 가능한 항목만 포함)

## 고유성 태그
- **★** = 해당 팩트가 단일 출처에서만 확인된 고유 정보
- **—** = 복수 출처에서 교차 확인된 일반 정보

---

## A. 역사·기원·전환점

1. Kizuna AI는 2016년 11월 29일 YouTube 채널 "A.I.Channel"에 첫 동영상을 업로드했고, "Virtual YouTuber"라는 용어를 최초로 사용했다.
   — 출처: Wikipedia "Kizuna AI" / "VTuber" | A | —

2. Kizuna AI는 Activ8 산하 디지털 프로덕션이 제작했으며, 성우 카스가 노조미(春日望)가 음성을 담당했다.
   — 출처: Wikipedia "Kizuna AI" | A | —

3. Kizuna AI의 3D 모델은 캐릭터 디자인 En Morikura, 3D 모델링 Tomitake, 모델링 감수 Tda가 담당했다.
   — 출처: Wikipedia "Kizuna AI" | A | ★

4. Kizuna AI는 데뷔 10개월 만에 YouTube 구독자 200만 명을 돌파했으며, 2021년까지 3개 채널 합산 400만 명 이상을 유지했다.
   — 출처: Wikipedia "Kizuna AI" | A | —

5. 2014년 FaceRig이 Steam에서 출시되어 웹캠 기반 페이스 모션 캡처로 라이브 아바타를 가능하게 한 최초의 소프트웨어가 되었다.
   — 출처: Wikipedia "VTuber" | A | —

6. FaceRig은 2015년 Live2D Inc.와 협업하여 2D 아바타 모듈을 추가했다.
   — 출처: Wikipedia "VTuber" | A | —

7. ANYCOLOR(당시 이치카라)는 2017년에 설립되었고, 2018년 2월 니지산지(NIJISANJI)를 출범시켰다.
   — 출처: VTuber Wiki "NIJISANJI" / TV Tropes | A | —

8. 니지산지는 iPhone X의 페이셜 모션 캡처 기술과 Live2D 모델을 결합한 자체 앱을 통해 스트리밍하는 방식을 채택했으며, 이는 3D 풀바디 모션캡처보다 비용이 크게 낮았다.
   — 출처: TV Tropes "Nijisanji" / VTuber Wiki | B | —

9. 니지산지는 기존 편집 영상 중심이던 VTuber 형태를 라이브 스트리밍 + Live2D 형태로 전환시켜, 현대 VTuber 포맷을 정립한 것으로 평가된다.
   — 출처: Wikipedia "VTuber" / VTuber Wiki | A | —

10. Cover Corporation은 원래 AR/VR 소프트웨어 개발 회사였으나, 2017년 Hololive 앱을 출시하고 VTuber 사업으로 전환했다.
    — 출처: Wikipedia "Hololive Production" | A | —

11. 홀로라이브의 첫 번째 멤버 토키노 소라(Tokino Sora)는 2017년 9월에 데뷔했다.
    — 출처: Shapes.inc VTuber Timeline | B | —

12. 2018년 5월~7월 사이 활동 VTuber 수가 2,000명에서 4,000명으로 증가했다.
    — 출처: Wikipedia "VTuber" | A | —

13. 2020년까지 전 세계 활동 VTuber 수가 10,000명을 넘었다.
    — 출처: Wikipedia "VTuber" | A | —

14. VShojo는 2020년 11월에 설립되어, 서구 최초의 VTuber 에이전시 중 하나가 되었다.
    — 출처: Wikipedia "VTuber" | A | —

15. Kizuna AI는 2022년 2월 26일 무기한 활동 중단을 발표했으며, 정확히 3년 후인 2025년 2월 26일에 새 3D 모델과 함께 복귀했다.
    — 출처: Kizuna AI Wiki | B | —

16. 2025년 VShojo는 운영을 중단했다.
    — 출처: vchavcha.com 2025 VTuber Recap | B | ★

17. Twitch에서 VTubing 콘텐츠는 2021년에 전년 대비 467% 성장했다 (Amazon 제공 데이터).
    — 출처: Wikipedia "VTuber" | A | ★

---

## B. Live2D 버전 변천사

18. Live2D 기술은 2010년에 베타 출시되었으며, 첫 공식 버전(Cubism 1.0)은 2013년에 릴리스되었다.
    — 출처: Grokipedia "Live2D" | B | —

19. 2014년에 Live2D Cubism 2.0이 출시되어 다중 레이어 변형(multi-layer deformation) 기능이 도입되었다.
    — 출처: Grokipedia "Live2D" | B | —

20. 개발사 Cybernoids Co., Ltd.는 2014년에 Live2D Inc.로 사명을 변경했다.
    — 출처: Grokipedia "Live2D" | B | ★

21. Live2D Cubism 3.0 SDK는 2017년 6월에 튜토리얼이 공개되었으며, 물리 시뮬레이션(physics) 설정 기능이 정식 지원되었다.
    — 출처: Live2D 공식 문서 Editor Manual Update History 3 Series | A | —

22. Cubism 4.0 SDK R1은 2020년 1월에 릴리스되었다.
    — 출처: Live2D 공식 문서 SDK Tutorial Update History | A | —

23. Cubism 4.2에서 Multiply Color, Screen Color, Blend Shapes 기능이 추가되었다.
    — 출처: Live2D 공식 문서 Cubism Core Change History | A | ★

24. Cubism 5.0은 다크/라이트 테마 전환, HiDPI 디스플레이 지원, Motion-sync(모션 싱크) 기능, 강화된 Blend Shapes를 도입했다.
    — 출처: Live2D 공식 문서 Update History 5.0 Series | A | —

25. Cubism Editor 5.1.00 공식 릴리스가 이루어졌으며, 5.2 시리즈에서는 Parameter Controller, 오디오 트랙 볼륨 세부 표시 등이 추가되었다.
    — 출처: Live2D 공식 문서 Update History 5.2 / Release History | A | ★

26. 2018년 Aniplex가 Live2D Inc.의 지분 과반을 인수하고, Live2D 기술을 활용한 장편 애니메이션 영화 제작 협업을 발표했다.
    — 출처: Grokipedia "Live2D" | B | ★

27. Live2D Creative Studio는 2021년 극장판 애니메이션 《벨》(Belle, 호소다 마모루 감독)에서 캐릭터 애니메이션에 기여했다.
    — 출처: Grokipedia "Live2D" | B | ★

28. Live2D Cubism Editor PRO는 유료 구독 모델이며, 무료 버전은 42일 PRO 트라이얼 후 기능 제한 FREE 버전으로 전환된다.
    — 출처: Live2D 공식 사이트 | A | —

---

## C. 아바타 제작 파이프라인 및 비용 구조

### C-1. 파이프라인 개요

29. VTuber 아바타 제작은 일반적으로 캐릭터 디자인(일러스트) → 파츠 분리(PSD 레이어) → 리깅(Live2D 또는 3D) → 물리 설정 → 테스트 순서로 진행된다.
    — 출처: ShiraLive2D / vtubermodelcommissions.com | C | —

30. Live2D 리깅 시 일러스트의 모든 이동 가능한 부위(눈, 홍채, 머리카락, 입 안쪽 등)를 별도 레이어로 분리해야 하며, 대칭 캐릭터의 경우에도 기본 48개 이상의 파츠가 필요하다.
    — 출처: GrifNMore "Pricing Vtubers" | C | ★

31. Live2D 리깅 아티스트는 파츠를 9개 방향(cardinal directions)으로 배열하고, 기본 표정(눈 깜빡임, 미소 등)을 생성한 후 물리 시뮬레이션을 설정한다.
    — 출처: GrifNMore "Pricing Vtubers" | C | —

32. VRoid Studio는 무료 3D 아바타 제작 도구로, 기본적인 애니메 스타일 3D 모델을 제작할 수 있다.
    — 출처: 다수 출처 | C | —

### C-2. 비용 구조: 2D (Live2D)

33. PNGTuber(정지 이미지 기반) 아바타의 비용은 $40~$200 수준이다.
    — 출처: Pixel Studios / BuzzFlick / VTuber Game | C | —

34. 입문용 Live2D 모델(일러스트 + 리깅)은 $450~$1,450이며, 일러스트 $250~$700 + 리깅 $200~$750으로 구성된다.
    — 출처: Cloud Animations | C | —

35. 중급 Live2D 커스텀 모델은 $1,600~$3,300이며, 일러스트 $800~$1,500 + 리깅 $800~$1,800이다.
    — 출처: Cloud Animations | C | —

36. 프리미엄 Live2D 모델(에이전시급)은 $3,500~$7,500이며, 일러스트 $2,000~$4,000 + 리깅 $1,500~$3,500이다.
    — 출처: Cloud Animations | C | —

37. 풀바디 Live2D 모델에 대해 프로 아티스트는 $2,000~$5,000 이상을 청구하며, 2019년 $200~$1,000 수준에서 팬데믹 이후 수요 급증으로 가격이 크게 상승했다.
    — 출처: BuzzFlick | C | —

38. 고도로 디테일한 Live2D 아바타(70° 머리 회전 범위, 다층 헤어 물리)는 약 $5,000까지 비용이 소요될 수 있다.
    — 출처: Viverse "VTuber Cost 2025" | C | ★

### C-3. 비용 구조: 3D

39. 입문용 3D 모델은 $1,300~$3,800이며, 일러스트 $800~$1,800 + 리깅 $500~$2,000이다.
    — 출처: Cloud Animations | C | —

40. 고급 3D 모델(기업·모션캡처용)은 $5,000~$15,000 이상이며, 아트워크 $3,000~$7,000 + 리깅 $2,000~$8,000이다.
    — 출처: Cloud Animations | C | —

41. 3D 모델의 고급 애니메이션(점프, 댄스 등)은 $1,000~$3,000의 추가 비용이 발생한다.
    — 출처: Delta Animations | C | —

42. 역대 가장 비싼 VTuber 모델은 복합 리깅·3D 기능·브랜드 커스터마이징 포함 시 $15,000을 초과한다.
    — 출처: ARwall / Cloud Animations | C | —

### C-4. 추가 비용

43. 아티스트는 상업 라이선스 비용으로 일러스트·리깅 기본 가격의 1.5~3배를 추가 청구한다.
    — 출처: Cloud Animations | C | ★

44. 러시 오더(급행 제작, 통상 2주 이내) 수수료는 기본 가격의 50%~200%가 추가된다.
    — 출처: Cloud Animations / ShiraLive2D | C | —

45. 대부분의 아티스트는 1~3회의 마이너 수정만 기본 포함하며, 메이저 수정(헤어스타일 변경, 신규 의상 등)은 시간당 추가 과금된다.
    — 출처: Cloud Animations | C | —

46. 의상 추가·시즌 테마 업데이트는 아트워크와 리깅 작업 모두 필요하여 가장 빈번한 반복 비용 항목 중 하나이다.
    — 출처: Viverse "VTuber Cost 2025" | C | —

47. 인기 아티스트의 대기 목록(waitlist)은 6개월까지 연장될 수 있다.
    — 출처: Cloud Animations | C | ★

---

## D. 트래킹 기술

### D-1. 페이스 트래킹

48. Apple iPhone의 TrueDepth 센서는 30,000개의 적외선 도트를 얼굴에 투사하여 60fps로 얼굴 기하학을 재구성하며, ARKit은 이를 52개의 블렌드셰이프 계수(jawOpen, eyeBlinkLeft 등)로 매핑한다.
    — 출처: MoCap Online VTuber Guide | B | —

49. iPhone ARKit 페이스 트래킹은 iPhone X(2017년 출시) 이후 Face ID 탑재 모든 iPhone에서 사용 가능하다.
    — 출처: MoCap Online VTuber Guide | B | —

50. VTube Studio는 웹캠(OpenSeeFace 사용) 또는 연결된 iPhone/Android 기기를 통한 페이스 트래킹을 지원한다.
    — 출처: VTube Studio 공식 / Live3D 비교 | B | —

51. 2022년 VTube Studio는 NVIDIA RTX 그래픽 카드를 활용한 AI 가속 페이셜 모션 캡처 업데이트를 출시했다.
    — 출처: Wikipedia "VTuber" | A | ★

52. VBridger는 VTube Studio와 Live2D 전용 페이스 트래킹 플러그인으로, iPhone ARKit 데이터를 증강·혼합·수정하여 보다 정밀한 표현 제어를 가능하게 한다.
    — 출처: Steam "VBridger" | A | —

53. VBridger가 지원하는 입력 소스에는 iFacialMocap(iPhone), FaceMotion3D(iPhone), MeowFace(Android), VTubeStudio(iPhone), MediaPipe(웹캠), NVIDIA(웹캠)가 포함된다.
    — 출처: Steam "VBridger" | A | —

54. VSeeFace는 무료 VRM 아바타 퍼펫팅 프로그램으로, iFacialMocap/FaceMotion3D/VTube Studio/MeowFace를 통한 Perfect Sync(52개 ARKit 블렌드셰이프)를 지원한다.
    — 출처: VSeeFace 공식 사이트 | A | —

55. 표준 웹캠 트래킹은 iPhone ARKit에 비해 측면 각도와 가변 조명에서 안정성이 크게 떨어지며, 눈 트래킹 정확도가 빠르게 저하된다.
    — 출처: MoCap Online VTuber Guide | B | —

56. 니지산지 소속 Livers는 통상 iPhone 페이셜 모션 캡처 + ANYCOLOR 사내 리깅 Live2D 모델 + NIJISANJI 앱(비매품)으로 스트리밍한다.
    — 출처: VTuber Wiki "NIJISANJI" | B | —

### D-2. 모션캡처(상반신/전신)

57. 전신 트래킹 단계: Level 1(페이스만) → Level 2(VR 컨트롤러 + Vive Tracker 3개, $300~$600 추가) → Level 3(관성 모캡 슈트, $1,500 이상) → Level 4(모캡 슈트 + 광학 페이스 캡처 in UE5).
    — 출처: MoCap Online VTuber Guide | B | —

58. Rokoko Smartsuit Pro II(약 $2,500)는 19개 IMU 센서를 탑재하며, VTuber·인디 개발자 사이에서 가장 대중적인 관성 풀바디 트래킹 슈트이다.
    — 출처: MoCap Online / Rokoko 공식 | B | —

59. Perception Neuron Studio(약 $1,500)는 17개 센서 구성의 저가형 관성 풀바디 캡처를 제공한다.
    — 출처: MoCap Online VTuber Guide | C | —

60. Xsens MVN Awinda는 $5,000 이상의 전문가급 관성 트래킹으로, 2024년 소프트웨어 구독료가 월 $500~$800 이상으로 인상되어 커뮤니티 반발이 있었다.
    — 출처: Rokoko 비교 가이드 | C | ★

61. Rokoko Smartgloves(약 $695)는 Smartsuit Pro II와 결합하여 핑거 트래킹을 추가한다.
    — 출처: MoCap Online Full Body Guide | B | —

62. Rokoko Coil Pro는 UWB(Ultra-Wideband) 기반 위치 보정 장치로, IMU 단독 사용 시 발생하는 드리프트 문제를 대폭 감소시킨다.
    — 출처: beforesandafters.com Rokoko 리뷰 | D | ★

### D-3. 핸드 트래킹

63. Leap Motion Controller는 IR 카메라 기반 광학 핸드 트래커로, VSeeFace 등에서 선택적 핸드 트래킹에 사용된다.
    — 출처: VSeeFace 공식 / MoCap Online | B | —

64. 핸드 트래킹 글러브, 모캡 슈트, 바디 트래커 등 액세서리는 $100~$500의 추가 비용이 발생하며 제작 시간도 증가시킨다.
    — 출처: Viverse "VTuber Cost 2025" | C | —

65. 니지산지의 Niji 3D 기술은 스튜디오 없이 3D 모델 스트리밍을 지원하나, 범위가 상반신과 핸드 트래킹으로 제한된다.
    — 출처: VTuber Wiki "NIJISANJI" | B | —

---

## E. 방송 소프트웨어

66. VTube Studio는 가장 널리 사용되는 2D VTuber 소프트웨어로, iOS(iPhone/iPad), Android, Steam(PC/Mac)에서 동작하며 Live2D 모델 전용이다.
    — 출처: Live3D 비교 / vtubermodelcommissions.com | B | —

67. VSeeFace는 무료 3D VRM 아바타 퍼펫팅 프로그램으로, Windows 8 이상 64비트에서 동작하며 VMC 프로토콜을 통한 데이터 송수신을 지원한다.
    — 출처: VSeeFace 공식 사이트 | A | —

68. VMagicMirror는 Windows 데스크톱 전용 VRM 아바타 애플리케이션으로, 특수 장비 없이 키보드·마우스만으로 아바타를 조작할 수 있으며, 웹캠을 통한 머리 모션 캡처와 사운드 기반 립싱크를 지원한다.
    — 출처: SaaSHub / Live3D | B | —

69. Animaze(구 FaceRig)는 자체 인디 아바타 렌더 엔진을 사용하며, Live2D·VRM·GLB 등 다양한 포맷을 지원하고, 암호화된 .avatar 포맷으로 모델 역공학을 방지한다.
    — 출처: GitHub Gist VTuber Software List | B | ★

70. OBS(Open Broadcaster Software)는 모든 VTuber 소프트웨어와 연동되는 핵심 방송 백본으로, 게임 캡처·Spout2·가상 카메라를 통해 투명 배경 합성이 가능하다.
    — 출처: vtubermodelcommissions.com / VSeeFace | B | —

71. VTube Studio는 VTube Studio API를 제공하여 VBridger 등 서드파티 플러그인이 Live2D 모델을 제어할 수 있게 한다.
    — 출처: Steam "VBridger" | A | —

---

## F. 3D 라이브·콘서트 기술

72. 홀로라이브는 2020년 1월 토요스 PIT에서 첫 단독 3D 콘서트 "Nonstop Story"를 개최하여, 23명의 멤버가 풀 3D로 공연했다.
    — 출처: Shapes.inc VTuber Timeline | B | —

73. 2024년 홀로라이브 EN은 실제 무대 요소와 AR·공간 컴퓨팅을 결합한 "Mixed Reality Concert Series"를 출시했다.
    — 출처: SkyQuestt VTuber Market Report | C | ★

74. 니지산지 EN은 2024년 4월 14일 첫 AR 스테이지 이벤트 "COLORS"를 개최했으며, 대부분 참가 Livers의 최초 3D 등장이었고 라이브 밴드와 AR 기술이 결합되었다.
    — 출처: NIJISANJI 공식 이벤트 페이지 / VTuber Wiki | A | —

75. 니지산지는 2024년 12월 31일 오사카 국제 컨벤션 센터에서 "COUNTDOWN LIVE 2024→2025"를 개최했으며, 21명의 VTuber가 출연했고 입장권은 14,300엔이었다.
    — 출처: vchavcha.com | B | ★

76. NexStage Project는 미국에서 Unreal Engine 기반 실시간 3D 콘서트를 기획한 사례로, 5벌의 프로급 모션캡처 슈트와 Motion Workshop 하드웨어를 사용하며, 미국 내 동시 5인 라이브 캡처가 가능한 스튜디오는 3곳뿐이었다고 밝혔다.
    — 출처: VTuber NewsDrop 인터뷰 | D | ★

77. NexStage의 프로듀서는 VTuber 팬이 실시간 모션캡처의 난이도와 복잡성을 인지하지 못할 수 있다고 언급했으며, 일본 외 지역에서 3D 콘서트를 보기 어려운 이유가 기술 진입장벽 때문이라고 설명했다.
    — 출처: VTuber NewsDrop 인터뷰 | D | ★

78. 한국 가상 아이돌 PLAVE는 만화(만화) 스타일 비주얼과 고정밀 3D 모션캡처를 결합하여 음악·댄스 중심 활동을 전개한다.
    — 출처: vchavcha.com 2025 VTuber Recap | B | —

79. PLAVE는 2025년 8월 첫 아시아 투어 "DASH: Quantum Leap"를 시작했으며, 서울 고척 스카이돔 앙코르 공연(2회)에 약 37,000명이 현장 관람했다.
    — 출처: vchavcha.com 2025 VTuber Recap | B | ★

80. PLAVE 티켓 사전 판매 시 피크 트래픽이 530,000건을 초과했으며 대기자가 30,000명 이상이었다.
    — 출처: vchavcha.com 2025 VTuber Recap | B | ★

81. Cover Corporation(홀로라이브)은 2025~2026 회계연도에 메타버스 프로젝트 holoEarth에서 33억 엔의 손실 처리를 포함해 9.1억 엔의 순손실을 보고했다.
    — 출처: Wikipedia "Hololive Production" | A | ★

---

## G. AI 기술 동향

### G-1. AI VTuber (Neuro-sama)

82. Neuro-sama는 영국 프로그래머 Vedal이 개발한 AI VTuber로, 2022년 12월 19일 Twitch에서 데뷔했다.
    — 출처: Wikipedia "Neuro-sama" / Fandom Wiki | A | —

83. Neuro-sama의 원형은 2018~2019년에 리듬 게임 osu!를 플레이하도록 설계된 신경망 AI였다.
    — 출처: Wikipedia "Neuro-sama" | A | —

84. Neuro-sama는 LLM(대규모 언어 모델)을 핵심 엔진으로 사용하여 실시간 채팅 응답·성격·음성을 생성하며, Microsoft Azure TTS("Ashley" 음성, 25% 피치 업)를 사용한다.
    — 출처: Wikipedia "Neuro-sama" / VTuber Wiki | A | —

85. Vedal에 따르면, Neuro-sama의 LLM은 2025년 초 기준 2B(20억) 파라미터이며 q2_k 양자화를 사용한다.
    — 출처: VTuber Fandom Wiki "Neuro-sama" | B | ★

86. Neuro-sama의 게임플레이 AI는 LLM과 별도 모듈로 동작하며, 컴퓨터 비전을 통해 화면 캡처(예: 80×60 그레이스케일)를 분석하여 커서 이동·클릭을 출력한다.
    — 출처: Grokipedia "Neuro-sama" | B | —

87. 2023년 초, Neuro-sama가 홀로코스트 부정 발언을 생방송 중 생성하여 콘텐츠 필터링 문제가 부각되었다.
    — 출처: futureaiblog.com / Wikipedia "Neuro-sama" | A | —

88. Neuro-sama의 첫 커스텀 모델은 2023년 5월 27일에 공개되었으며, VTuber 겸 아티스트 Anny가 디자인하고 Otozuki Teru가 모델링했다.
    — 출처: Wikipedia "Neuro-sama" | A | —

89. 2025년 1월 1일, Neuro-sama는 서바톤 중 Twitch 하이프 트레인 역대 최고 레벨(111)을 달성했다.
    — 출처: Wikipedia "Neuro-sama" / VTuber Fandom Wiki | A | —

90. 2026년 1월까지 Neuro-sama의 Twitch 채널은 약 100만 팔로워를 보유하며, Twitch 전체 역대 3위 구독 채널·VTuber 1위가 되었다(최대 343,215 유료 구독).
    — 출처: Wikipedia "Neuro-sama" / VTuber Fandom Wiki | A | —

91. Vedal은 2025년 11월 15일 Neuro-sama의 3D 모델 데뷔 스트림을 진행했다.
    — 출처: Wikipedia "Neuro-sama" | A | ★

### G-2. AI 음성 합성

92. 오픈소스 AI VTuber 프로젝트 "Open-LLM-VTuber"는 sherpa-onnx, MeloTTS, GPTSoVITS, Bark, CosyVoice, Edge TTS, Fish Audio, Azure TTS, OpenAI TTS 등 다양한 TTS 엔진을 지원한다.
    — 출처: GitHub Open-LLM-VTuber | A | —

93. GPTSoVITS는 음성 클로닝(voice cloning)을 지원하여 AI VTuber에 원하는 음색을 부여하는 데 사용된다.
    — 출처: GitHub Open-LLM-VTuber / ai-vtuber topic | B | —

94. Live2D Cubism 5.0에는 "Motion-sync" 기능이 추가되어 오디오 입력 기반 립싱크 애니메이션 베이킹을 에디터 내에서 지원한다.
    — 출처: Live2D 공식 문서 5.0 Update History | A | ★

### G-3. AI 일러스트 활용 논란

95. Animaze는 암호화된 .avatar 포맷을 제공하여, AI 기반 모델 생성에 크리에이터의 모델·리그가 역공학되어 무단 사용되는 것을 방지한다고 명시했다.
    — 출처: GitHub Gist VTuber Software List (Animaze 개발자 코멘트) | B | ★

96. 2026년 5월, 게임 Neverness to Everness(Hotta Studio)에서 AI 생성 배경 아트 사용이 발각되어 VTuber Ironmouse가 스폰서십을 해지했고, Shylily는 방송을 조기 종료했다.
    — 출처: NTE Guide 타임라인 | B | —

97. Hotta Studio는 AI 도구 사용이 소수의 배경·환경 에셋에 한정되었으며 캐릭터·스토리는 전부 인간이 제작했다고 공식 해명했다.
    — 출처: NTE Guide 타임라인 | B | —

98. VTuber 커뮤니티 내에서 AI 생성 아트를 VTuber 아바타에 사용하는 행위는 기존 일러스트레이터·리거의 생계를 위협한다는 비판이 지속적으로 제기되고 있다.
    — 출처: toolify.ai AI VTuber Art Debate 종합 | D | —

---

## H. 니지산지 모델 버전 체계 (2.0 / 3.0 브러시업)

99. 니지산지 Livers는 데뷔 후 "2.0 브러시업"을 받을 수 있으며, 이는 움직임 범위 확장과 표정 추가를 포함한다. 2022년 이후 신규 멤버는 데뷔 시 2.0이 기본 적용된다.
    — 출처: VTuber Wiki "NIJISANJI" | B | —

100. "3.0 브러시업"은 2021년에 시작되었으며, 새로운 표정·확장된 움직임·토글 옵션을 포함하고 추첨 시스템으로 배분된다.
     — 출처: VTuber Wiki "NIJISANJI" | B | —

101. 2022년 11월 기준, 니지산지 146명의 Livers가 2.0 브러시업을 받았다.
     — 출처: VTuber Wiki "NIJISANJI" | B | —

102. 2024년 3월 기준, 니지산지 JP 85명 + ID 2명 + KR 5명 = 92명, EN 16명이 3.0 브러시업을 받았다.
     — 출처: VTuber Wiki "NIJISANJI" | B | —

---

## I. 시장 규모

103. 2024년 글로벌 VTuber 시장 규모는 약 $25.4억(USD 2.54 Billion)으로 평가되었다.
     — 출처: SkyQuestt Market Report | C | —

104. 2033년까지 VTuber 시장은 $136.2억(USD 13.62 Billion)에 달할 것으로 전망되며, 2026~2033 CAGR은 20.5%이다.
     — 출처: SkyQuestt Market Report | C | —

105. 2025년 5월 기준 홀로라이브는 3개 언어(일본어·인도네시아어·영어)로 88명의 활동 VTuber를 관리하며, YouTube 총 구독자 8,000만 명 이상을 보유한다.
     — 출처: Wikipedia "Hololive Production" | A | —

106. 2026년 6월 기준 니지산지는 196명의 활동 Livers(JP 151, ID 6, KR 11, EN 28)를 관리하며, YouTube 총 구독자 6,000만 명 이상이다.
     — 출처: VTuber Wiki "NIJISANJI" | B | —

---

*끝.*
