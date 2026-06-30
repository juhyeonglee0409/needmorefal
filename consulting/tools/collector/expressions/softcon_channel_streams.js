// target: viewership.softc.one/channel/naverchzzk/{channelId}/streams
// extracts: broadcast rows (시작/종료 시간, 카테고리, 시청자, 채팅, 팔로워)
// placeholder: {CHANNEL_ID} — replaced by collector at runtime
(() => {
  const channelId = {CHANNEL_ID};
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const onlyNumber = s => norm(s).replace(/,/g, '');
  const datePrefix = value => {
    const text = norm(value).replace(/\s+\(/, '(');
    return /^\d{2}\.\d{2}/.test(text) ? '2026.' + text : text;
  };
  const streamAnchors = Array.from(document.querySelectorAll('a'))
    .filter(a => a.href && a.href.includes('/channel/naverchzzk/' + channelId + '/streams/') && /[0-9]$/.test(a.href));
  const seen = new Set();
  const rows = [];
  for (const a of streamAnchors) {
    if (seen.has(a.href)) continue;
    seen.add(a.href);
    const leaves = Array.from(a.querySelectorAll('div,span,p')).map((el, i) => ({
      i,
      tag: el.tagName,
      text: norm(el.innerText || el.textContent),
      cls: String(el.className || ''),
      childCount: el.children.length
    })).filter(x => x.text);
    const labelIndex = leaves.findIndex(x => x.text === '카테고리 / 제목');
    const before = labelIndex >= 0 ? leaves.slice(0, labelIndex) : leaves;
    const categoryIndex = before.findIndex(x => x.cls.includes('foreground-40') && x.text);
    const categoryRaw = categoryIndex >= 0 ? before[categoryIndex].text.replace(/^LIVE/, '') : '';
    const titleLeaf = before.slice(Math.max(categoryIndex + 1, 0)).find(x => x.cls.includes('gap-1') && x.text && !x.text.includes('foreground'));
    let title = titleLeaf ? titleLeaf.text : '';
    const adult = title.includes('연령제한') || before.some(x => x.text === '연령제한');
    title = title.replace(/^연령제한/, '').replace('연령제한', '').trim();
    const period = before.find(x => x.text.includes('~') && /\d{2}\.\d{2}/.test(x.text))?.text || '';
    const parts = period.split('~');
    const startTime = datePrefix(parts[0] || '');
    const endTime = parts[1] && parts[1] !== 'LIVE' ? datePrefix(parts[1]) : (parts[1] || '');
    const rootCells = before.filter(x => x.tag === 'DIV' && x.cls.includes('justify-end') && x.text);
    const durationCellIndex = rootCells.findIndex(x => /h$/.test(x.text));
    const cells = durationCellIndex >= 0 ? rootCells.slice(durationCellIndex) : rootCells;
    rows.push({
      streamId: a.href.split('/').pop(),
      values: {
        '시작 시간': startTime,
        '종료 시간': endTime,
        '카테고리': categoryRaw.replace(/,\s*/g, '|'),
        '연령': adult ? '성인' : '전체',
        '시작제목': title,
        '방송 시간': onlyNumber((cells[0]?.text || '').replace(/h$/, '')),
        '최고 시청자': onlyNumber(cells[1]?.text || ''),
        '평균 시청자': onlyNumber(cells[2]?.text || ''),
        '전체 채팅수': onlyNumber(cells[3]?.text || ''),
        '팔로워 증감': onlyNumber(cells[4]?.text || ''),
        '구독자 증감': ''
      }
    });
  }
  const bodyText = norm(document.body?.innerText || '');
  return JSON.stringify({
    url: location.href,
    title: document.title,
    checkpoint: /Security Checkpoint|보안 검문|브라우저를 확인/.test(bodyText),
    rateLimited: /Too Many Requests|rate limit|요청이 너무 많/i.test(bodyText),
    notFound: /존재하지 않는 페이지|404/.test(bodyText),
    rowCount: rows.length,
    rows
  });
})()
