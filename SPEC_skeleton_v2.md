# needmorefal 구현 명세 v2

> 이 문서는 다른 세션에서 구현할 때 사용하는 명세서.
> 함께 로딩할 것: project.json (CREW 레지스터), CREW_Core_v1_1_EN.md, 현재 소스 파일들.

---

## 1. 프로젝트 상태 요약

needmorefal은 스트리머 채널 데이터 해석 컨설팅 서비스의 랜딩페이지.
Vercel 배포, 커스텀 도메인 연결 완료. 웹 퍼스트로 진행 (모바일 최소 구현은 확보됨).

### 파일 구조

```
index.html
css/style.css
js/main.js
data/auro_rank_1_11000.js
samples/
  report1/r1_p1~6.webp   — 디자인 버전 (6p, 724KB)
  report2/r2_p01~11.webp  — 텍스트 버전 (11p, 1.3MB)
```

### 프로젝트 카드

- **목표**: 서비스 가치를 데이터 오독 데모로 증명하는 랜딩페이지를 완성·배포. 웹 퍼스트.
- **성공 기준**: 오독 패턴 체험, 3스크롤 이내 CTA 도달, 문의 전환, 서비스 이해도 전달
- **금지**: 전형적 AI 문체, 비효율적 시스템 구축

### Owner 컨텍스트

- 프리랜서, 사업자등록 없음 (매출 발생 시 전환 예정)
- 닉네임: Isaac
- 경력 없음. 포트폴리오 중심 신뢰 구축
- 현재 2개 채널 컨설팅 진행 중
- 신뢰 레이어 전략: 작업물이 말하게 한다 (샘플 리포트 = 핵심 신뢰 신호)
- 문의: contact@needmorefal.com (Namecheap 이메일 포워딩)

---

## 2. 확정된 설계 결정

### 2-1. 모바일 레이어 모델 (구현 완료)

데스크톱 3컬럼의 x축을 모바일에서 z축으로 전환.

- 기본 레이어: 콘텐츠 / 좌 패널: WHITE / 우 패널: BLACK
- 진입: 고정 핸들(peek handle) 탭. 엣지 스와이프 불가 (OS 선점).
- 패널: 80vw/max-340px, 백드롭 dim, 스와이프·ESC·탭으로 닫기
- 핸들: 펄스 애니메이션 + 8초 간격 랭크 변화

### 2-2. 카테고리 페이지 전환 (구현 완료)

- `page-section[data-page]` + `nav-cat[data-target]` 패턴
- 5페이지: main, lol, general, chat, vtuber
- 더미 페이지: 히어로 + CTA + 푸터 최소 구조

### 2-3. 버그 수정 (구현 완료)

- B1: nav position sticky/relative 충돌 → relative 제거
- B2: word-break: break-all → keep-all (860px 미디어쿼리)
- B3: nav-cat 핸들러 → 페이지 전환 JS 교체

### 2-4. 브랜딩 변경 (구현 완료)

- 도메인 표기: needmorefal.gg → needmorefal
- 로고: `needmorefal<span>.gg</span>` → `needmore<span>fal</span>` (네온 포인트: .gg → fal)
- mailto: faust.12108@gmail.com → contact@needmorefal.com
- cta-sub 텍스트 소거
- dev-change-log: opacity 0.05 (hover/open 시 1)

### 2-5. 소거된 대안

| 소거 | 이유 |
|------|------|
| 모바일 y축 스택 | 동시성 상실 |
| 엣지 스와이프 | OS 제스처 선점 |
| 모바일 카드 스와이퍼 | 레이어 모델로 대체 |
| 사업자 정보 표시 | 프리랜서, 없음. 용역이라 법적 의무 아님 |

---

## 3. 샘플 리포트 이미지 뷰어 (구현 완료)

### 3-1. 배경

기존: sample_report.html을 iframe으로 로딩. 텍스트 선택 가능 → 경쟁자가 구조·문체 복제 가능.

변경: PDF를 래스터 이미지(WebP)로 변환해서 서빙. 텍스트 추출 불가, 레이아웃 복제 불가.

### 3-2. 파일

```
samples/
  report1/         — 디자인 버전 "채널 성장 진단 보고서" (6페이지, 총 724KB)
    r1_p1.webp     68KB
    r1_p2.webp    147KB
    r1_p3.webp    126KB
    r1_p4.webp    110KB
    r1_p5.webp    117KB
    r1_p6.webp    148KB
  report2/         — 텍스트 버전 "채널 성장 분석 및 전략 제언" (11페이지, 총 1.3MB)
    r2_p01.webp   124KB
    r2_p02.webp   122KB
    ...
    r2_p11.webp    85KB
```

200dpi, WebP quality 82. 원본 대비: report1 47MB→724KB, report2 459KB→1.3MB(래스터화 비용이지만 복제 방지가 우선).

### 3-3. HTML

```html
<div id="sampleModal" class="sample-modal" role="dialog" aria-modal="true" aria-hidden="true">
  <div class="sample-modal-panel">
    <button type="button" class="sample-modal-close" id="sampleModalClose" aria-label="닫기">&times;</button>
    <div class="sample-tab-bar">
      <button class="sample-tab active" data-report="report1">디자인 버전</button>
      <button class="sample-tab" data-report="report2">분석 보고서</button>
    </div>
    <div class="sample-viewer" id="sampleViewer"></div>
    <div class="sample-page-info" id="samplePageInfo">1 / 6</div>
  </div>
</div>
```

### 3-4. JS

```js
const sampleReports = {
  report1: { title: '채널 성장 진단 보고서', pages: 6, prefix: 'samples/report1/r1_p', ext: '.webp' },
  report2: { title: '채널 성장 분석 및 전략 제언', pages: 11, prefix: 'samples/report2/r2_p', ext: '.webp' }
};

function loadSampleReport(reportKey) {
  const report = sampleReports[reportKey];
  const viewer = document.getElementById('sampleViewer');
  viewer.innerHTML = '';
  for (let i = 1; i <= report.pages; i++) {
    const num = report.pages > 9 ? String(i).padStart(2, '0') : String(i);
    const img = document.createElement('img');
    img.src = report.prefix + num + report.ext;
    img.alt = report.title + ' ' + i + '페이지';
    img.loading = i <= 2 ? 'eager' : 'lazy';
    img.draggable = false;
    img.addEventListener('contextmenu', e => e.preventDefault());
    viewer.appendChild(img);
  }
  document.querySelectorAll('.sample-tab').forEach(t => t.classList.toggle('active', t.dataset.report === reportKey));
  viewer.scrollTop = 0;
}
```

### 3-5. 복제 방지 (최소)

- `pointer-events: none` on images
- `contextmenu` preventDefault
- `user-select: none`
- `img.draggable = false`
- WebP 래스터 자체가 텍스트 추출 원천 차단

---

## 4. 타이포그래피 스케일 재설계

### 4-1. 토큰 정의

root 15px→16px. 7단 스케일을 CSS 커스텀 프로퍼티로 정의.

```css
html { font-size: 16px; }
:root {
  --fs-display:   2.25rem;   /* 36px */
  --fs-heading-l: 1.5rem;    /* 24px */
  --fs-heading:   1.25rem;   /* 20px */
  --fs-body:      1rem;      /* 16px */
  --fs-ui:        1rem;      /* 16px */
  --fs-label:     0.875rem;  /* 14px */
  --fs-micro:     0.75rem;   /* 12px */
}
```

절대 최소 12px. 현재 9px까지 내려가는 곳이 있으나 전부 12px 이상으로.

### 4-2. 적용 원칙

- 매핑 테이블을 일괄 적용하지 않는다
- 영역(zone) 단위로 font-size + padding/gap/width를 동시에 조정한다
- 타이포가 레이아웃을 결정한다 (레이아웃에 타이포를 끼워넣지 않는다)
- 각 영역 완료 후 브라우저에서 데스크톱+모바일 확인 후 다음 영역으로

### 4-3. 영역별 적용 순서

#### Zone 1: Nav
- 대상: .logo, .nav-cat, .nav-cta
- 현재: 0.72rem (10.8px) — 너무 작음
- 목표: --fs-ui (16px)
- 레이아웃 리스크: 글자 커지면 5개 탭이 넘칠 수 있음
- 동시 조정: nav padding, nav-cat gap, 모바일 wrap 확인, 필요시 nav-cats overflow-x: auto

#### Zone 2: Hero
- 대상: .hero h1, .hero-label, .hero p
- 목표: h1 → --fs-display, label → --fs-label, p → --fs-body
- 동시 조정: hero padding, line-height

#### Zone 3: Lessons (오독 패턴)
- 대상: .lesson-num, .lesson-title, .lesson-concept, .lesson-toggle-btn, .lesson-view
- 목표: title → --fs-heading, num/concept → --fs-label, toggle → --fs-ui, view → --fs-body
- 동시 조정: lesson padding, toggle button min-width

#### Zone 4: Pricing
- 대상: .pricing-name, .pricing-price, .pricing-desc, .pricing-tag, .sample-btn
- 목표: name/price → --fs-heading, desc → --fs-body, tag → --fs-micro, sample-btn → --fs-ui
- 동시 조정: pricing-card padding, pricing-header gap

#### Zone 5: CTA + Footer
- 대상: .cta-section h2/p, .cta-btn, footer
- 목표: h2 → --fs-heading-l, p → --fs-body, btn → --fs-ui, footer → --fs-label
- 동시 조정: cta-section padding

#### Zone 6: Sidebar Cards
- 대상: .s-name, .s-stat, .s-trend, .s-rank, .team-header 하위
- 목표: name → --fs-heading, stat → --fs-label, trend → --fs-micro, team-sub/range → --fs-label
- 레이아웃 리스크: 카드 안에서 stat 줄바꿈
- 동시 조정: s-card padding, sidebar-w 재검토

#### Zone 7: Modal
- 대상: .modal-name, .modal-rank, .modal-metric-*, .modal-interpretation, .modal-section-label, .modal-cta
- 목표: name → --fs-heading, rank → --fs-label, metric-label → --fs-micro, interp → --fs-body, cta → --fs-ui
- 레이아웃 리스크: metric grid 폭
- 동시 조정: modal-metric grid gap, modal padding

#### Zone 8: 기타
- .content-intro h2/p, .category-label, .dev-change-log summary
- 각각 매핑 후 확인

### 4-4. 모바일 오버라이드 (860px)

Display와 Heading-L만 한 단계 축소. 나머지는 데스크톱과 동일.

```css
@media (max-width: 860px) {
  .hero h1 { font-size: 1.5rem; }
  .s-name { font-size: 1.125rem; }
  .s-stat { font-size: var(--fs-micro); }
}
```

### 4-5. 스케일 바깥 (변경하지 않음)

- .team-header .team-label (1.6rem) — 장식 타이포
- .peek-handle (0.45rem) — 모바일 핸들 장식
- .peek-handle .peek-count (0.55rem) — 핸들 숫자

### 4-6. 구현 방법

- 브라우저 실시간 확인 필수 (코드 단독 적용 금지)
- Zone 1개 완료 → 커밋 → 다음 Zone
- 깨지는 시점에서 바로 레이아웃 조정

---

## 5. MVP 필수 항목 (미구현)

### 기술 (기계적 작업)

| # | 항목 | 상세 |
|---|------|------|
| T1 | script async | `data/auro_rank_1_11000.js`에 async 추가 + 로딩 완료 후 renderCards 보장 |
| T2 | favicon | 브라우저 탭 + apple-touch-icon |
| T3 | meta description | `<meta name="description" content="...">` |
| T4 | OG 태그 | og:title, og:description, og:image (카톡/트위터 공유 미리보기) |

### 콘텐츠 (Owner 소재 필요)

| # | 항목 | 상세 |
|---|------|------|
| C1 | 운영자 소개 | Isaac + 한 줄 관점 + "현재 2개 채널 컨설팅 진행 중". 배치: 푸터 근처 또는 CTA 아래 |
| C2 | 개인정보 고지 | mailto 수집에 대한 최소 한 줄. 푸터 |

---

## 6. 후순위

### 성능
- 데이터 파일 페이지네이션/초기 로딩 축소
- 이벤트 위임 전환 (카드 클릭)

### SEO/메타
- canonical URL, robots.txt, sitemap.xml
- 구조화 데이터 (JSON-LD)

### 콘텐츠 (내장재)
- 카테고리 페이지 실제 콘텐츠
- 카테고리별 사이드바 분기
- FAQ
- 사례/실적 추가

### 접근성
- skip navigation
- 헤딩 위계 검증
- 색상 대비 검증

### 기타
- 404 커스텀 (Vercel)
- noscript fallback
- 이미지 에러 처리
- 로고 이미지
- 소셜 링크

---

## 7. 구현 체크리스트

### 완료됨
- [x] nav position 충돌 수정 (B1)
- [x] word-break 수정 (B2)
- [x] page-section 구조 도입
- [x] nav-cat → data-target 연결
- [x] 페이지 전환 JS 교체 (B3)
- [x] 5개 카테고리 더미 페이지
- [x] 모바일 레이어 모델
- [x] samples/ 디렉토리 배치 (이미지 파일)
- [x] 샘플 리포트 이미지 뷰어 구현 (섹션 3)
- [x] sample_report.html, css/sample_report.css 삭제
- [x] 브랜딩 변경 (needmorefal.gg → needmorefal, 네온 fal)
- [x] mailto → contact@needmorefal.com
- [x] cta-sub 텍스트 소거
- [x] dev-change-log opacity 처리

### 다음
- [ ] 타이포그래피 스케일 재설계 (섹션 4, Zone 1~8)
- [ ] script async 전환 (T1)
- [ ] favicon 추가 (T2)
- [ ] meta description 추가 (T3)
- [ ] OG 태그 추가 (T4)
- [ ] 운영자 소개 삽입 (C1 — Owner 소재 확정 후)
- [ ] 개인정보 고지 삽입 (C2)
- [ ] 기존 기능 회귀 테스트: 카드, 모달, 레슨 토글, 페이지 전환

---

## 8. 참고: 현재 코드의 주요 구조

### HTML 골격

```
<nav>
  logo | nav-cats (5 buttons) | nav-cta
</nav>
<div class="main-layout">
  <aside class="sidebar-left">    ← WHITE (모바일: fixed 좌측 패널)
  <main class="content">
    <div class="page-section" data-page="main">  ← 메인 콘텐츠
    <div class="page-section" data-page="lol">    ← 더미
    <div class="page-section" data-page="general"> ← 더미
    <div class="page-section" data-page="chat">    ← 더미
    <div class="page-section" data-page="vtuber">  ← 더미
    [sample-modal, dev-change-log]                 ← page-section 바깥
  </main>
  <aside class="sidebar-right">   ← BLACK (모바일: fixed 우측 패널)
</div>
```

### 반응형 브레이크포인트

- 1560px → sidebar 300px
- 1280px → sidebar 240px
- **860px** → 모바일 전환 (레이어 모델)
- 600px → 모바일 미세 조정

### JS 모듈

- renderCards + cycleCards + swapOneCard (카드)
- openModal + closeModal (스트리머 모달)
- openSampleModal + closeSampleModal + loadSampleReport (이미지 뷰어)
- nav-cat 핸들러 (페이지 전환)
- initMobileLayerModel (레이어 모델)
- drawChart (캔버스)
- 레슨 토글
- 스크롤 화살표
