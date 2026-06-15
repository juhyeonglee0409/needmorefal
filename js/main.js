const streamerData = window.streamerData || {};

function fmtFol(value) {
  const n = Number(value) || 0;
  if (n >= 10000) {
    const man = n / 10000;
    const text = man >= 100 ? Math.round(man).toLocaleString() : man.toFixed(1).replace(/\.0$/, '');
    return text + '만';
  }
  return n.toLocaleString();
}

function calcTrend(chart) {
  if (!Array.isArray(chart) || chart.length < 2) {
    return { label: '—', dir: '' };
  }
  const first = Number(chart[0]) || 0;
  const last = Number(chart[chart.length - 1]) || 0;
  if (!first && !last) {
    return { label: '—', dir: '' };
  }
  const diff = last - first;
  const pct = first ? Math.round((diff / first) * 100) : 0;
  if (diff > 0) return { label: '+' + pct + '%', dir: 'up' };
  if (diff < 0) return { label: pct + '%', dir: 'down' };
  return { label: '0%', dir: '' };
}

function platformLabel(platform) {
  const labels = {
    afreeca: 'SOOP',
    twitch: 'Twitch',
    chzzk: 'CHZZK',
    cime: 'CIME'
  };
  return labels[platform] || platform || '—';
}

function formatCardStat(entry) {
  const rankText = '#' + entry.rank.toLocaleString();
  return '<span class="s-rank-inline">' + rankText + '</span> 팔로워 ' + fmtFol(entry.followers)
    + ' · ' + platformLabel(entry.platform);
}

function getStreamerModal(key) {
  const d = streamerData[key];
  if (!d) return null;
  const t = calcTrend(d.chart || []);
  return {
    metrics: {
      rank: '#' + d.rank.toLocaleString(),
      name: d.name,
      platform: platformLabel(d.platform),
      channelId: d.channelId || '—',
      followers: fmtFol(d.followers),
      trend: t.label,
      trendDir: t.dir
    },
    dateRange: 'AURO rank 1-11000 · 2026-06-15',
    chart: d.chart || [],
    interp: '현재 카드는 <strong>AURO rank 1-11000</strong>의 공개 랭킹 데이터로 채워졌습니다. 이 데이터에는 순위, 채널명, 플랫폼, 팔로워, 채널 ID, 프로필 이미지만 포함되어 있어 평균 시청자·피크·카테고리·시계열은 표시하지 않습니다.'
  };
}

// ===== 카드 렌더링 =====
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, ch => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[ch]));
}

function renderCards() {
  // Fisher-Yates 셔플
  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  const entries = Object.entries(streamerData);
  const whitePool = entries.filter(([, d]) => d.side === 'WHITE');
  const blackPool = entries.filter(([, d]) => d.side === 'BLACK');

  const whitePicked = shuffle(whitePool).slice(0, 10).sort((a, b) => a[1].rank - b[1].rank);
  const blackPicked = shuffle(blackPool).slice(0, 10).sort((a, b) => a[1].rank - b[1].rank);

  function buildCardHTML(key, entry) {
    const safeName = escapeHtml(entry.name);
    const safeKey = escapeHtml(key);
    const imgAttr = entry.img ? ` style="--img:url('${entry.img}')"` : '';
    return `<button type="button" class="s-card"${imgAttr} data-key="${safeKey}" aria-label="${safeName} 상세 보기">
      <div class="s-rank">#${entry.rank.toLocaleString()}</div>
      <div class="s-info">
        <div class="s-name">${safeName}</div>
        <div class="s-stat">placeholder</div>
      </div>
    </button>`;
  }

  const whiteHTML = whitePicked.map(([key, entry]) => buildCardHTML(key, entry)).join('\n    ');
  const blackHTML = blackPicked.map(([key, entry]) => buildCardHTML(key, entry)).join('\n    ');

  // Insert into sidebars after team-header
  const whiteContainer = document.querySelector('.sidebar-left.sidebar-white') || document.querySelector('.sidebar-left');
  const blackContainer = document.querySelector('.sidebar-right.sidebar-black') || document.querySelector('.sidebar-right');

  const whiteHeader = whiteContainer.querySelector('.team-header');
  // Remove any existing cards
  whiteContainer.querySelectorAll('.s-card').forEach(c => c.remove());
  whiteHeader.insertAdjacentHTML('afterend', whiteHTML);

  const blackHeader = blackContainer.querySelector('.team-header');
  blackContainer.querySelectorAll('.s-card').forEach(c => c.remove());
  blackHeader.insertAdjacentHTML('afterend', blackHTML);

  // Update card stats with real data
  document.querySelectorAll('.s-card').forEach(card => {
    const d = streamerData[card.dataset.key];
    if (!d) return;
    const statEl = card.querySelector('.s-stat');
    if (statEl) {
      statEl.innerHTML = formatCardStat(d);
    }
  });

  // Bind click handlers
  document.querySelectorAll('.sidebar-white .s-card').forEach(card => {
    card.style.cursor = 'pointer';
    card.addEventListener('click', () => openModal(card, 'white'));
  });
  document.querySelectorAll('.sidebar-black .s-card').forEach(card => {
    card.style.cursor = 'pointer';
    card.addEventListener('click', () => openModal(card, 'black'));
  });
}

// ===== 모달 로직 =====
const overlay = document.getElementById('modalOverlay');
const panel = document.getElementById('modalPanel');
const modalCta = document.getElementById('modalCta');
const sampleModal = document.getElementById('sampleModal');
const sampleModalOpen = document.getElementById('sampleModalOpen');
const sampleModalClose = document.getElementById('sampleModalClose');

function openModal(card, team) {
  const key = card.dataset.key;
  const entry = streamerData[key];
  if (!entry) return;
  const name = entry.name;
  const rank = '#' + entry.rank.toLocaleString();
  const imgSrc = entry.img || '';

  const data = getStreamerModal(key);
  if (!data) return;

  // 팀 스타일
  panel.className = 'modal-panel open' + (team === 'black' ? ' team-black' : '');

  // 채우기
  document.getElementById('modalAvatar').src = imgSrc;
  document.getElementById('modalAvatar').alt = name + ' 프로필 이미지';
  document.getElementById('modalName').textContent = name;
  document.getElementById('modalRank').textContent = rank + ' · 팔로워 ' + data.metrics.followers;
  document.getElementById('modalInterp').innerHTML = data.interp;

  // 지표
  const m = data.metrics;
  document.getElementById('modalMetrics').innerHTML = `
    <div class="modal-metric">
      <div class="modal-metric-label">Rank</div>
      <div class="modal-metric-value">${m.rank}</div>
    </div>
    <div class="modal-metric">
      <div class="modal-metric-label">Platform</div>
      <div class="modal-metric-value">${m.platform}</div>
    </div>
    <div class="modal-metric">
      <div class="modal-metric-label">Followers</div>
      <div class="modal-metric-value">${m.followers}</div>
    </div>
    <div class="modal-metric">
      <div class="modal-metric-label">Channel</div>
      <div class="modal-metric-value" style="font-size:0.6rem;">${m.channelId}</div>
    </div>
    <div class="modal-metric">
      <div class="modal-metric-label">Trend</div>
      <div class="modal-metric-value ${m.trendDir}">${m.trend}</div>
    </div>
    <div class="modal-metric">
      <div class="modal-metric-label">Dataset</div>
      <div class="modal-metric-value" style="font-size:0.6rem;">${data.dateRange}</div>
    </div>
  `;

  // 차트
  const chartBox = document.querySelector('.modal-chart');
  chartBox.style.display = data.chart.length ? 'block' : 'none';
  drawChart(data.chart, team === 'black');

  overlay.classList.add('open');
  panel.focus({ preventScroll: true });
}

function closeModal() {
  overlay.classList.remove('open');
  panel.classList.remove('open');
}

overlay.addEventListener('click', closeModal);
document.getElementById('modalClose').addEventListener('click', closeModal);
modalCta.addEventListener('click', e => {
  e.preventDefault();
  closeModal();
  document.getElementById('contact').scrollIntoView({ behavior: 'smooth', block: 'start' });
});

function openSampleModal() {
  sampleModal.classList.add('open');
  sampleModal.setAttribute('aria-hidden', 'false');
  sampleModalClose.focus({ preventScroll: true });
}

function closeSampleModal() {
  sampleModal.classList.remove('open');
  sampleModal.setAttribute('aria-hidden', 'true');
}

sampleModalOpen.addEventListener('click', openSampleModal);
sampleModalClose.addEventListener('click', closeSampleModal);
sampleModal.addEventListener('click', e => {
  if (e.target === sampleModal) closeSampleModal();
});
document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  closeModal();
  closeSampleModal();
});

// Render cards on load
renderCards();

document.querySelectorAll('.nav-cat').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-cat').forEach(item => {
      item.classList.remove('active');
      item.setAttribute('aria-pressed', 'false');
    });
    btn.classList.add('active');
    btn.setAttribute('aria-pressed', 'true');
  });
});

// ===== 카드 순환 (flip animation) =====
function cycleCards() {
  const entries = Object.entries(streamerData);
  const whitePool = entries.filter(([, d]) => d.side === 'WHITE');
  const blackPool = entries.filter(([, d]) => d.side === 'BLACK');

  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  const newWhite = shuffle(whitePool).slice(0, 10).sort((a, b) => a[1].rank - b[1].rank);
  const newBlack = shuffle(blackPool).slice(0, 10).sort((a, b) => a[1].rank - b[1].rank);

  const whiteCards = document.querySelectorAll('.sidebar-white .s-card');
  const blackCards = document.querySelectorAll('.sidebar-black .s-card');
  const staggerDelay = 100; // ms between each card

  function flipCard(cardEl, [key, entry], delay, team) {
    setTimeout(() => {
      cardEl.classList.add('flip-out-fast');
      setTimeout(() => {
        // 카드 내용 교체
        if (entry.img) {
          cardEl.setAttribute('style', `--img:url('${entry.img}')`);
        } else {
          cardEl.removeAttribute('style');
        }
        cardEl.dataset.key = key;
        cardEl.setAttribute('aria-label', entry.name + ' 상세 보기');
        cardEl.querySelector('.s-name').textContent = entry.name;
        const rankText = '#' + entry.rank.toLocaleString();
        cardEl.querySelector('.s-rank').textContent = rankText;
        cardEl.querySelector('.s-stat').innerHTML = formatCardStat(entry);

        cardEl.classList.remove('flip-out-fast');
        cardEl.classList.add('flip-in-fast');

        // 클릭 핸들러 재바인딩
        const newCard = cardEl.cloneNode(true);
        cardEl.parentNode.replaceChild(newCard, cardEl);
        newCard.style.cursor = 'pointer';
        newCard.addEventListener('click', () => openModal(newCard, team));

        setTimeout(() => newCard.classList.remove('flip-in-fast'), 150);
      }, 150);
    }, delay);
  }

  whiteCards.forEach((card, i) => flipCard(card, newWhite[i], i * staggerDelay, 'white'));
  blackCards.forEach((card, i) => flipCard(card, newBlack[i], i * staggerDelay, 'black'));
}

// ===== 단일 카드 교체 (10초마다) =====
let isAnimating = false;

function swapOneCard() {
  if (isAnimating) return;
  isAnimating = true;

  // 랜덤으로 좌/우 사이드바 선택
  const isWhite = Math.random() < 0.5;
  const side = isWhite ? 'white' : 'black';
  const sideClass = isWhite ? '.sidebar-white' : '.sidebar-black';
  const cards = document.querySelectorAll(sideClass + ' .s-card');
  if (!cards.length) { isAnimating = false; return; }

  // 랜덤 카드 선택
  const idx = Math.floor(Math.random() * cards.length);
  const cardEl = cards[idx];

  // 현재 표시중인 이름들 수집
  const displayed = new Set();
  document.querySelectorAll('.s-card').forEach(el => {
    if (el.dataset.key) displayed.add(el.dataset.key);
  });

  // 풀에서 표시중이 아닌 것 중 랜덤 선택
  const pool = Object.entries(streamerData).filter(([key, d]) =>
    d.side === (isWhite ? 'WHITE' : 'BLACK') && !displayed.has(key)
  );
  if (!pool.length) { isAnimating = false; return; }
  const [key, entry] = pool[Math.floor(Math.random() * pool.length)];

  // 페이드 아웃
  cardEl.classList.add('flip-out');
  setTimeout(() => {
    if (entry.img) {
      cardEl.setAttribute('style', `--img:url('${entry.img}')`);
    } else {
      cardEl.removeAttribute('style');
    }
    cardEl.dataset.key = key;
    cardEl.setAttribute('aria-label', entry.name + ' 상세 보기');
    cardEl.querySelector('.s-name').textContent = entry.name;
    const rankText = '#' + entry.rank.toLocaleString();
    cardEl.querySelector('.s-rank').textContent = rankText;
    cardEl.querySelector('.s-stat').innerHTML = formatCardStat(entry);

    cardEl.classList.remove('flip-out');
    cardEl.classList.add('flip-in');

    // 클릭 핸들러 재바인딩
    const newCard = cardEl.cloneNode(true);
    cardEl.parentNode.replaceChild(newCard, cardEl);
    newCard.style.cursor = 'pointer';
    newCard.addEventListener('click', () => openModal(newCard, side));

    setTimeout(() => {
      newCard.classList.remove('flip-in');
      // 랭크순 재정렬
      const container = newCard.closest('.sidebar-left, .sidebar-right');
      if (container) {
        const allCards = Array.from(container.querySelectorAll('.s-card'));
        allCards.sort((a, b) => {
          const rA = parseInt(a.querySelector('.s-rank').textContent.replace(/[#,]/g, ''));
          const rB = parseInt(b.querySelector('.s-rank').textContent.replace(/[#,]/g, ''));
          return rA - rB;
        });
        allCards.forEach(c => container.appendChild(c));
      }
      isAnimating = false;
    }, 750);
  }, 750);
}

// 5분마다 전체 플립 (이스터에그)
setInterval(() => {
  if (isMobileViewport()) return;
  if (isAnimating) return;
  isAnimating = true;
  cycleCards();
  // stagger 끝나는 시간: 10장 × 100ms + flip 250ms × 2
  setTimeout(() => { isAnimating = false; }, 10 * 100 + 300);
}, 300000);

// 10초마다 랜덤 1장 교체
setInterval(() => {
  if (isMobileViewport()) return;
  swapOneCard();
}, 10000);

function isMobileViewport() {
  return window.matchMedia('(max-width: 860px)').matches;
}

// ===== 모바일 레이어 모델 =====
(function initMobileLayerModel() {
  const sidebarLeft = document.querySelector('.sidebar-left');
  const sidebarRight = document.querySelector('.sidebar-right');
  if (!sidebarLeft || !sidebarRight) return;

  sidebarLeft.id = sidebarLeft.id || 'whitePanel';
  sidebarRight.id = sidebarRight.id || 'blackPanel';

  const backdrop = document.createElement('div');
  backdrop.className = 'panel-backdrop';
  document.body.appendChild(backdrop);

  const peekLeft = document.createElement('button');
  peekLeft.type = 'button';
  peekLeft.className = 'peek-handle peek-handle-left';
  peekLeft.setAttribute('aria-label', 'WHITE 스트리머 패널 열기');
  peekLeft.setAttribute('aria-controls', sidebarLeft.id);
  peekLeft.setAttribute('aria-expanded', 'false');
  peekLeft.innerHTML = '<span class="peek-dot"></span><span>WHITE</span><span class="peek-count"></span>';
  document.body.appendChild(peekLeft);

  const peekRight = document.createElement('button');
  peekRight.type = 'button';
  peekRight.className = 'peek-handle peek-handle-right';
  peekRight.setAttribute('aria-label', 'BLACK 스트리머 패널 열기');
  peekRight.setAttribute('aria-controls', sidebarRight.id);
  peekRight.setAttribute('aria-expanded', 'false');
  peekRight.innerHTML = '<span class="peek-dot"></span><span>BLACK</span><span class="peek-count"></span>';
  document.body.appendChild(peekRight);

  function setHandleState(sidebar) {
    const leftOpen = sidebar === sidebarLeft && sidebar.classList.contains('panel-open');
    const rightOpen = sidebar === sidebarRight && sidebar.classList.contains('panel-open');
    peekLeft.setAttribute('aria-expanded', leftOpen ? 'true' : 'false');
    peekRight.setAttribute('aria-expanded', rightOpen ? 'true' : 'false');
  }

  function openPanel(sidebar) {
    if (!isMobileViewport()) return;
    sidebarLeft.classList.toggle('panel-open', sidebar === sidebarLeft);
    sidebarRight.classList.toggle('panel-open', sidebar === sidebarRight);
    backdrop.classList.add('active');
    document.body.classList.add('panel-active');
    document.body.style.overflow = 'hidden';
    setHandleState(sidebar);
  }

  function closePanel() {
    sidebarLeft.classList.remove('panel-open');
    sidebarRight.classList.remove('panel-open');
    backdrop.classList.remove('active');
    document.body.classList.remove('panel-active');
    document.body.style.overflow = '';
    peekLeft.setAttribute('aria-expanded', 'false');
    peekRight.setAttribute('aria-expanded', 'false');
  }

  peekLeft.addEventListener('click', () => openPanel(sidebarLeft));
  peekRight.addEventListener('click', () => openPanel(sidebarRight));
  backdrop.addEventListener('click', closePanel);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closePanel();
  });

  [peekLeft, peekRight].forEach(handle => {
    handle.addEventListener('touchstart', () => {
      handle.style.transform = 'translateY(-50%) scale(1.1)';
      handle.style.transition = 'transform 0.1s';
    }, { passive: true });
    handle.addEventListener('touchend', () => {
      setTimeout(() => {
        handle.style.transform = '';
        handle.style.transition = '';
      }, 100);
    }, { passive: true });
  });

  [sidebarLeft, sidebarRight].forEach(sidebar => {
    let startX = 0;
    const isLeft = sidebar.classList.contains('sidebar-left');
    sidebar.addEventListener('touchstart', e => {
      startX = e.touches[0].clientX;
    }, { passive: true });
    sidebar.addEventListener('touchend', e => {
      const dx = e.changedTouches[0].clientX - startX;
      if (isLeft && dx < -60) closePanel();
      if (!isLeft && dx > 60) closePanel();
    }, { passive: true });
  });

  function updatePeekCounts() {
    if (!isMobileViewport()) return;
    const whiteCards = sidebarLeft.querySelectorAll('.s-card');
    const blackCards = sidebarRight.querySelectorAll('.s-card');
    const wCount = peekLeft.querySelector('.peek-count');
    const bCount = peekRight.querySelector('.peek-count');
    if (whiteCards.length) {
      const randomW = whiteCards[Math.floor(Math.random() * whiteCards.length)];
      wCount.textContent = randomW.querySelector('.s-rank')?.textContent || '';
      wCount.style.opacity = '0';
      requestAnimationFrame(() => { wCount.style.opacity = '0.6'; });
    }
    if (blackCards.length) {
      const randomB = blackCards[Math.floor(Math.random() * blackCards.length)];
      bCount.textContent = randomB.querySelector('.s-rank')?.textContent || '';
      bCount.style.opacity = '0';
      requestAnimationFrame(() => { bCount.style.opacity = '0.6'; });
    }
  }

  function checkViewport() {
    const display = isMobileViewport() ? '' : 'none';
    peekLeft.style.display = display;
    peekRight.style.display = display;
    backdrop.style.display = display;
    if (!isMobileViewport()) closePanel();
  }

  checkViewport();
  updatePeekCounts();
  setInterval(updatePeekCounts, 8000);

  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(checkViewport, 150);
  });
})();

// ===== 미니 차트 (Canvas) =====
function drawChart(data, isNeon) {
  const canvas = document.getElementById('modalChart');
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  const w = rect.width, h = rect.height;
  ctx.clearRect(0, 0, w, h);

  const pad = { top: 16, right: 12, bottom: 16, left: 12 };
  const pw = w - pad.left - pad.right;
  const ph = h - pad.top - pad.bottom;
  if (!data || !data.length) return;
  const min = Math.min(...data) * 0.9;
  const max = Math.max(...data) * 1.1;
  const range = max - min || 1;

  const pts = data.map((v, i) => ({
    x: data.length === 1 ? pad.left + pw / 2 : pad.left + (i / (data.length - 1)) * pw,
    y: pad.top + ph - ((v - min) / range) * ph
  }));

  // 영역 fill
  const color = isNeon ? '0, 255, 163' : '200, 200, 220';
  const grad = ctx.createLinearGradient(0, pad.top, 0, h - pad.bottom);
  grad.addColorStop(0, `rgba(${color}, 0.15)`);
  grad.addColorStop(1, `rgba(${color}, 0)`);
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  pts.forEach(p => ctx.lineTo(p.x, p.y));
  ctx.lineTo(pts[pts.length-1].x, h - pad.bottom);
  ctx.lineTo(pts[0].x, h - pad.bottom);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // 라인
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  for (let i = 1; i < pts.length; i++) {
    const prev = pts[i-1], curr = pts[i];
    const cpx = (prev.x + curr.x) / 2;
    ctx.bezierCurveTo(cpx, prev.y, cpx, curr.y, curr.x, curr.y);
  }
  ctx.strokeStyle = isNeon ? 'rgba(0, 255, 163, 0.8)' : 'rgba(220, 220, 230, 0.6)';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // 끝점
  const last = pts[pts.length - 1];
  ctx.beginPath();
  ctx.arc(last.x, last.y, 3, 0, Math.PI * 2);
  ctx.fillStyle = isNeon ? '#00FFA3' : '#e0e0ea';
  ctx.fill();
}

// ===== 레슨 토글 =====
document.querySelectorAll('.lesson-toggle-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const lesson = btn.closest('.lesson');
    const view = btn.dataset.view;
    lesson.querySelectorAll('.lesson-toggle-btn').forEach(b => b.className = 'lesson-toggle-btn');
    btn.classList.add(view === 'reading' ? 'active-neon' : 'active');
    lesson.querySelectorAll('.lesson-view').forEach(v => v.classList.remove('active'));
    lesson.querySelector('.lesson-view.' + view).classList.add('active');
  });
});

// ===== 스크롤 화살표 =====
document.getElementById('scrollUp').addEventListener('click', () => {
  document.querySelectorAll('.sidebar, .content').forEach(el => el.scrollTo({top: 0, behavior: 'smooth'}));
});
document.getElementById('scrollDown').addEventListener('click', () => {
  document.querySelectorAll('.sidebar, .content').forEach(el => el.scrollTo({top: el.scrollHeight, behavior: 'smooth'}));
});
