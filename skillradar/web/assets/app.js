// Trang học sinh v2: lướt nghề -> một ngày đi làm (cảnh từ tin thật) -> thẻ kỹ năng -> bộ bài -> hồ sơ chia sẻ.
// Chữ hiển thị nằm hết trong copy.vi.json; phép tính nằm trong logic.js (có test).
import { treeSkills, unlocked, rarity, shields, level, oneIn, salaryInsight, encodeChallenge, decodeChallenge } from './logic.js';

const app = document.getElementById('app');
let T, D;

// ---------- tiện ích ----------
function h(tag, props = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === 'class') e.className = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else if (k === 'style') e.style.cssText = v;
    else if (v !== false && v != null) e.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat()) if (c != null && c !== false) e.append(c.nodeType ? c : String(c));
  return e;
}
const svgUse = (id, cls = 'i') => { const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); s.setAttribute('class', cls);
  const u = document.createElementNS('http://www.w3.org/2000/svg', 'use'); u.setAttribute('href', '#' + id); s.append(u); return s; };
const fill = (s, v) => s.replace(/\{(\w+)\}/g, (_, k) => v[k] ?? '');
// như fill nhưng biến có thể là phần tử DOM (để tô nổi một cụm trong câu do người biên tập viết)
const fillEl = (s, v) => s.split(/(\{\w+\})/).map(part => { const m = /^\{(\w+)\}$/.exec(part); return m ? (v[m[1]] ?? '') : part; });
const fmt = n => Number(n).toLocaleString('vi-VN');
const tr = vnd => (vnd / 1e6).toLocaleString('vi-VN', { maximumFractionDigits: 1 });
const k10 = w => Math.max(1, Math.round(w * 10));
const ddmm = d => d.split('-').reverse().slice(0, 2).join('/');
const store = {
  get(k, d) { try { return JSON.parse(localStorage.getItem('sr2:' + k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem('sr2:' + k, JSON.stringify(v)); } catch { /* chế độ riêng tư: chỉ giữ trong phiên */ } },
};
const deck = () => new Set(store.get('deck', []));
const addCard = id => { const d = deck(); d.add(id); store.set('deck', [...d]); renderCount(); };
const fam = id => D.families.find(f => f.id === id);
const sk = id => D.byId[id];
const glyph = name => { const w = name.replace(/[()/]/g, ' ').split(/\s+/).filter(Boolean);
  return name.length <= 5 ? name : w.slice(0, 2).map(x => x[0]).join('').toUpperCase(); };
const famLower = f => f.name.split('/')[0].trim().toLowerCase();
function renderCount() { const b = document.getElementById('deckCount'); if (b) b.textContent = deck().size; }

function sourceBox() {
  const dates = D.meta.sources.map(s => `${s.source} ${ddmm(s.latest)}`).join(', ');
  return h('details', { class: 'src' }, h('summary', {}, T.source.label), h('p', {}, fill(T.source.body, { n: fmt(D.meta.n_open), dates })),
    h('a', { href: 'data.html' }, T.source.data_link));
}

// ---------- thẻ nghề ----------
function roleCard(fid, extra = {}) {
  const f = fam(fid), first = D.scenes[fid]?.[0], top = first ? sk(first.skill) : null;
  return h('article', { class: 'rc ' + (extra.cls || '') },
    h('span', { class: 'arch' }, T.archetypes[fid] || ''),
    h('div', { class: 'rname' }, f.name.split('/')[0].trim()),
    h('div', { class: 'bigfact' }, h('b', {}, fmt(f.n_open)), h('span', {}, T.swipe.open_now)),
    h('div', { class: 'minis' },
      h('div', { class: 'mini' }, h('b', {}, f.salary_median_vnd ? tr(f.salary_median_vnd) + ' tr' : '—'),
        f.salary_median_vnd ? T.swipe.salary : T.swipe.salary_none),
      top ? h('div', { class: 'mini' }, h('b', {}, `${k10(first.weight)}/10`), fill(T.swipe.need, { skill: top.vi })) : null),
    first ? h('figure', { class: 'quote' }, h('q', {}, first.quote),
      h('small', {}, fill(T.swipe.quote_src, { source: first.source, date: ddmm(first.date) }))) : null,
    extra.stamps ? [h('span', { class: 'stamp yes' }, 'THỬ'), h('span', { class: 'stamp no' }, 'BỎ')] : null);
}

// ---------- màn hình ----------
function home() {
  const m = D.meta, d = deck(), order = T.swipe_order;
  const started = store.get('swipeIdx', 0) > 0 || d.size > 0;
  return [h('section', { class: 'hero' },
      h('div', {},
        h('p', { class: 'eyebrow' }, T.home.eyebrow),
        h('h1', {}, T.home.title),
        h('p', { class: 'lead', style: 'margin-top:14px' }, T.home.lead),
        h('div', { class: 'row' },
          h('a', { class: 'btn primary', href: '#/luot' }, started ? T.home.cta_continue : T.home.cta, svgUse('i-arrow')),
          d.size ? h('a', { class: 'btn', href: '#/bai' }, T.home.cta_deck) : null),
        h('div', { class: 'stats' },
          h('span', {}, h('b', {}, fmt(m.n_open)), T.home.stat_open),
          h('span', {}, h('b', {}, m.taxonomy.skills), T.home.stat_skills),
          h('span', {}, h('b', {}, m.days_collected), T.home.stat_days))),
      h('div', { class: 'preview', 'aria-hidden': 'true' }, roleCard(order[2]), roleCard(order[1]), roleCard(order[0], { cls: 'front' }))),
    h('div', { class: 'how' }, T.home.how.map((x, i) => h('div', {}, h('span', { class: 'n' }, `0${i + 1}`), h('b', {}, x.t), h('span', { class: 'muted small' }, x.d)))),
    h('div', { style: 'margin-top:20px' }, sourceBox())];
}

function swipe() {
  const order = T.swipe_order.filter(id => fam(id));
  let i = store.get('swipeIdx', 0);
  if (i >= order.length) return [h('div', { class: 'col', style: 'text-align:center' },
    h('h2', {}, T.swipe.done_title), h('p', { class: 'lead' }, T.swipe.done_lead),
    h('a', { class: 'btn primary block', href: '#/bai' }, T.home.cta_deck),
    h('button', { class: 'btn ghost block', onclick: () => { store.set('swipeIdx', 0); route(); } }, T.swipe.restart))];
  const fid = order[i];
  const front = roleCard(fid, { cls: 'front', stamps: true });
  const stage = h('div', { class: 'stage' },
    order[i + 2] ? roleCard(order[i + 2], { cls: 'b2' }) : null, order[i + 1] ? roleCard(order[i + 1], { cls: 'b1' }) : null, front);
  const decide = yes => {
    front.style.transform = `translateX(${yes ? 140 : -140}%) rotate(${yes ? 18 : -18}deg)`;
    store.set('swipeIdx', i + 1);
    setTimeout(() => { yes ? (location.hash = `#/ngay/${fid}/0`) : route(); }, 220);
  };
  // kéo thẻ (chuột / cảm ứng)
  let x0 = null, dx = 0;
  const yes = front.querySelector('.stamp.yes'), no = front.querySelector('.stamp.no');
  front.addEventListener('pointerdown', e => { x0 = e.clientX; dx = 0; front.classList.add('drag'); front.setPointerCapture(e.pointerId); });
  front.addEventListener('pointermove', e => { if (x0 == null) return; dx = e.clientX - x0;
    front.style.transform = `translateX(${dx}px) rotate(${dx / 18}deg)`;
    yes.style.opacity = Math.max(0, Math.min(1, dx / 100)); no.style.opacity = Math.max(0, Math.min(1, -dx / 100)); });
  const end = () => { if (x0 == null) return; x0 = null; front.classList.remove('drag');
    if (Math.abs(dx) > 100) decide(dx > 0); else { front.style.transform = ''; yes.style.opacity = no.style.opacity = 0; } };
  front.addEventListener('pointerup', end); front.addEventListener('pointercancel', end);
  onKey = e => { if (e.key === 'ArrowRight') decide(true); if (e.key === 'ArrowLeft') decide(false); };
  return [h('div', { class: 'col' },
    h('div', { class: 'row', style: 'justify-content:space-between' },
      h('span', { class: 'pill' }, fill(T.swipe.progress, { i: i + 1, n: order.length })),
      h('a', { class: 'small', href: '#/bai' }, T.home.cta_deck)),
    stage,
    h('div', { class: 'swipebar' },
      h('button', { class: 'round', 'aria-label': T.swipe.skip, onclick: () => decide(false) }, svgUse('i-x')),
      h('button', { class: 'btn primary', onclick: () => decide(true) }, T.swipe.try, svgUse('i-arrow'))),
    h('p', { class: 'hint' }, T.swipe.hint))];
}

function skillCardEl(fid, sid) {
  const s = sk(sid), f = fam(fid), w = (f.skills.find(x => x[0] === sid) || [])[1] ?? s.open.share;
  const pay = f.skills.find(x => x[0] === sid) || [];
  const rar = rarity(s.open.share), sh = shields(s.ai), k = k10(w);
  const scene = (D.scenes[fid] || []).find(x => x.skill === sid);
  const flip = h('div', { class: 'flip', role: 'button', tabindex: 0, 'aria-label': `${s.vi}. ${T.card.tap_flip}` },
    h('div', { class: 'inner' },
      h('div', { class: `face front ${rar}` }, h('div', { class: 'cardin' },
        h('div', { class: 'rarity' }, h('span', { class: 'tier' }, T.card.rarity[rar]), h('span', {}, f.name.split('/')[0].trim())),
        h('div', { class: 'art' }, h('span', { class: 'glyph' }, glyph(s.vi))),
        h('div', { class: 'cname' }, s.vi),
        h('div', { class: 'stat' }, h('span', { class: 'k' }, T.card.demand),
          h('span', { class: 'dots10' }, Array.from({ length: 10 }, (_, j) => h('i', { class: j < k ? 'on' : '' }))),
          h('b', {}, fill(T.card.demand_val, { k }))),
        h('div', { class: 'stat' }, h('span', { class: 'k' }, T.card.pay),
          pay[2] != null ? [h('b', {}, tr(pay[2]) + ' tr'), h('span', {}, `· ${tr(pay[3])} tr nếu tin không đòi*`)] : h('span', {}, T.card.pay_none)),
        h('div', { class: 'stat' }, h('span', { class: 'k' }, T.card.shield),
          sh == null ? h('span', {}, T.card.shield_none) : [
            h('span', { class: 'shields', 'aria-label': `${sh}/5` }, Array.from({ length: 5 }, (_, j) => { const e = svgUse('i-shield', j < sh ? '' : 'off'); return e; })),
            h('span', {}, T.card.shield_text[sh - 1])]))),
      h('div', { class: 'face back' },
        h('p', { class: 'eyebrow', style: 'color:var(--duck)' }, T.card.back_title),
        scene ? [h('q', {}, scene.quote), h('small', {}, fill(T.day.quote_src, { source: scene.source, date: ddmm(scene.date) }))] : null,
        h('div', {}, fill(T.card.back_demand, { n: fmt(Math.round(w * f.n_open)), total: fmt(f.n_open), family: famLower(f) })),
        pay[2] != null ? h('div', {}, T.card.back_pay) : null,
        h('div', {}, T.card.back_ai), h('div', {}, T.card.back_rarity))));
  const toggle = () => flip.classList.toggle('on');
  flip.addEventListener('click', toggle);
  flip.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
  return flip;
}

function showCard(fid, sid, onDone) {
  const close = () => { ov.remove(); onDone && onDone(); };
  const btn = h('button', { class: 'btn primary', onclick: close }, T.day.next, svgUse('i-arrow'));
  const ov = h('div', { class: 'overlay', role: 'dialog', 'aria-modal': 'true', 'aria-label': T.card.new },
    h('div', { class: 'col' }, h('p', { class: 'eyebrow' }, T.card.new), skillCardEl(fid, sid), h('p', { class: 'tapflip' }, T.card.tap_flip), btn));
  document.body.append(ov);
  btn.focus();
}

function day(fid, idx) {
  const f = fam(fid), scenes = D.scenes[fid] || [];
  if (!f || !scenes.length) { location.hash = '#/luot'; return []; }
  const i = Number(idx) || 0;
  if (i >= scenes.length) { location.hash = `#/ket/${fid}`; return []; }
  const sc = scenes[i];
  store.set('lastFam', fid);
  // trộn đáp án tất định theo cảnh để lần nào cũng như nhau
  const seed = [...fid].reduce((a, ch) => a + ch.charCodeAt(0), 0) + i * 5;
  const opts = [...sc.distractors];
  opts.splice(seed % 3, 0, sc.skill);   // đáp án đúng nằm ở vị trí khác nhau giữa các cảnh
  // câu trích thật, che cụm kỹ năng thành ô trống; trả lời xong thì hiện nguyên văn
  const [b0, b1] = sc.blank || [0, 0];
  const blank = h('mark', { class: 'blank', 'aria-label': 'ô trống' }, '\u2002?\u2002');
  const quoteEl = h('q', {}, sc.quote.slice(0, b0), blank, sc.quote.slice(b1));
  const fb = h('div', { 'aria-live': 'polite' });
  const answer = (pick, btn) => {
    list.querySelectorAll('.opt').forEach(b => { b.disabled = true; if (b.dataset.id === sc.skill) b.classList.add('right'); });
    blank.textContent = sc.quote.slice(b0, b1); blank.classList.add('filled');
    const right = pick === sc.skill;
    if (!right) btn.classList.add('wrong');
    const res = store.get('results', {}); (res[fid] ||= [])[i] = right; store.set('results', res);
    const vars = { family: famLower(f), k: k10(sc.weight), skill: sk(sc.skill).vi, picked: sk(pick).vi };
    fb.replaceChildren(h('div', { class: 'toast' }, svgUse('i-spark'), h('span', {}, fill(right ? T.day.right : T.day.wrong, vars))),
      h('button', { class: 'btn primary block', style: 'margin-top:10px', onclick: () => { addCard(sc.skill);
        showCard(fid, sc.skill, () => { location.hash = `#/ngay/${fid}/${i + 1}`; }); } }, T.day.get_card, svgUse('i-arrow')));
  };
  const list = h('div', { class: 'opts' }, opts.map(id => {
    const s = sk(id); const b = h('button', { class: 'opt', 'data-id': id }, h('span', { class: 'ico' }, glyph(s.vi)),
      h('span', {}, s.vi, h('small', {}, s.group)));
    b.addEventListener('click', () => answer(id, b)); return b; }));
  return [h('div', { class: 'col' },
    h('div', { class: 'scenehead' }, h('span', { class: 'clock' }, `${sc.time} · ${f.name.split('/')[0].trim()}`),
      h('span', { class: 'dots', 'aria-label': fill(T.day.progress, { i: i + 1, n: scenes.length }) }, scenes.map((_, j) => h('i', { class: j <= i ? 'on' : '' })))),
    h('div', { class: 'chat' }, h('span', { class: 'avatar' }, 'TN'), h('div', { class: 'bubble' }, h('b', {}, T.day.boss), T.day.greetings[i] || T.day.greetings[0])),
    h('figure', { class: 'quote' }, quoteEl, h('small', {}, fill(T.day.quote_src, { source: sc.source, date: ddmm(sc.date) }))),
    h('h2', {}, T.day.ask), list, fb)];
}

function nextBest(f, owned) {
  const A = D.meta.assumptions;
  return treeSkills(f).map(([id]) => id).filter(id => !owned.has(id))
    .map(id => ({ id, k: oneIn(f, new Set([...owned, id]), A) })).filter(x => x.k)
    .sort((a, b) => a.k - b.k)[0];
}

function levelBox(f, owned) {
  const L = level(f, owned), name = T.level.names[L.lv - 1];
  const pct = L.nextAt ? Math.min(100, 100 * L.cards / L.nextAt) : 100;
  return h('div', { class: 'level' }, h('div', { class: 't' },
      h('span', {}, fill(T.level.label, { family: f.name.split('/')[0].trim(), name, lv: L.lv })),
      h('span', { class: 'muted' }, L.nextAt ? fill(T.level.next, { have: L.cards, need: L.nextAt, lv: L.lv + 1 }) : T.level.max)),
    h('div', { class: 'xp' }, h('i', { style: `width:${pct}%` })));
}

function insightBox(f) {
  const s = salaryInsight(f);
  if (!s) return null;
  const max = Math.max(s.raisePay, s.entryPay);
  return h('div', { class: 'insight' },
    h('b', { class: 'h' }, fill(T.deck.insight, { entry: sk(s.entry).vi, raise: sk(s.raise).vi })),
    fill(T.deck.insight_sub, { family: famLower(f) }),
    h('div', { class: 'bars2' },
      h('span', {}, fill(T.deck.insight_with, { skill: sk(s.raise).vi })), h('i', { style: `width:${100 * s.raisePay / max}%` }), h('b', {}, tr(s.raisePay)),
      h('span', {}, fill(T.deck.insight_with, { skill: sk(s.entry).vi })), h('i', { class: 'g', style: `width:${100 * s.entryPay / max}%` }), h('b', {}, tr(s.entryPay))),
    h('p', { class: 'muted small', style: 'margin:6px 0 0' }, T.deck.insight_note));
}

function unlockBox(f, owned) {
  const k = oneIn(f, owned, D.meta.assumptions);
  return h('div', { class: 'unlock' }, h('p', { class: 'eyebrow' }, `${owned.size} thẻ`),
    h('div', { class: 'big' }, k ? fillEl(T.deck.one_in, { k: h('em', {}, `1 trong ${k}`), family: famLower(f) })
      : fill(T.deck.one_in_none, { family: famLower(f) })),
    h('p', { class: 'small' }, T.deck.unlock_note));
}

function endOfDay(fid) {
  const f = fam(fid), owned = deck(), res = store.get('results', {})[fid] || [], n = (D.scenes[fid] || []).length;
  const nb = nextBest(f, owned);
  return [h('div', { class: 'col' },
    h('p', { class: 'eyebrow' }, fill(T.day.end_title, { family: famLower(f) })),
    h('h2', {}, fill(T.day.end_score, { right: res.filter(Boolean).length, n })),
    h('p', { class: 'muted' }, T.day.end_lead),
    levelBox(f, owned), unlockBox(f, owned), insightBox(f),
    nb ? h('button', { class: 'next', onclick: () => { addCard(nb.id); showCard(fid, nb.id, route); } },
      svgUse('i-chart'), h('span', {}, `${T.deck.next}: ${sk(nb.id).vi}`), h('span', { class: 'plus' }, fill(T.deck.next_gain, { k: nb.k }))) : null,
    h('a', { class: 'btn primary block', href: `#/ho-so/${fid}` }, T.deck.profile, svgUse('i-arrow')),
    h('a', { class: 'btn ghost block', href: '#/luot' }, T.deck.swipe_more))];
}

function deckView() {
  const owned = deck();
  if (!owned.size) return [h('div', { class: 'col' }, h('h2', {}, T.deck.title), h('div', { class: 'empty' }, T.deck.empty),
    h('a', { class: 'btn primary block', href: '#/luot' }, T.home.cta))];
  const played = Object.keys(store.get('results', {})).filter(fam);
  const A = D.meta.assumptions;
  const fits = D.families.filter(f => f.in_scope).map(f => ({ f, k: oneIn(f, owned, A), L: level(f, owned) }))
    .filter(x => x.k && x.L.cards).sort((a, b) => a.k - b.k).slice(0, 6);
  const ch = store.get('challenge', null);
  const mine = ch && fam(ch.family) ? oneIn(fam(ch.family), owned, A) : null;
  return [h('div', { class: 'col', style: 'max-width:720px' },
    h('h2', {}, T.deck.title),
    ch && fam(ch.family) ? h('div', {}, h('p', { class: 'eyebrow' }, T.challenge.compare), h('div', { class: 'compare' },
      h('div', {}, h('span', { class: 'small muted' }, T.challenge.you), h('b', {}, mine ? `1/${mine}` : '—'), `${owned.size} thẻ`),
      h('div', {}, h('span', { class: 'small muted' }, T.challenge.friend), h('b', {}, `1/${oneIn(fam(ch.family), new Set(ch.ids), A) || '—'}`), `${ch.ids.length} thẻ`))) : null,
    h('div', { class: 'minicards' }, [...owned].filter(sk).map(id => {
      const s = sk(id), r = rarity(s.open.share), home = played.find(p => fam(p).skills.some(x => x[0] === id)) || fits[0]?.f.id || 'cntt';
      return h('button', { class: `mc ${r}`, onclick: () => showCard(home, id) }, h('span', {}, h('small', {}, T.card.rarity[r]), s.vi));
    })),
    h('h3', { style: 'margin-top:8px' }, T.deck.fits),
    fits.map(({ f, k }) => h('a', { class: 'fam-row', href: `#/ho-so/${f.id}` }, h('strong', {}, f.name),
      h('span', { class: 'num small' }, `1 trong ${k}`), levelBox(f, owned).querySelector('.xp'))),
    h('a', { class: 'btn primary block', href: `#/ho-so/${store.get('lastFam', fits[0]?.f.id || '')}` }, T.deck.profile),
    h('a', { class: 'btn ghost block', href: '#/luot' }, T.deck.swipe_more), sourceBox())];
}

// ---------- hồ sơ chia sẻ ----------
function profileData(fid) {
  const f = fam(fid), owned = deck(), A = D.meta.assumptions;
  const mine = treeSkills(f).map(([id]) => id).filter(id => owned.has(id));
  const top3 = (mine.length ? mine : [...owned]).slice(0, 3).filter(sk);
  const sh = top3.map(id => shields(sk(id).ai)).filter(x => x != null);
  return { f, owned, top3, k: oneIn(f, owned, A), L: level(f, owned), next: nextBest(f, owned),
    shield: sh.length ? Math.round(sh.reduce((a, b) => a + b, 0) / sh.length) : null };
}

function profile(fid) {
  if (!fid || !fam(fid)) fid = store.get('lastFam', null);
  if (!fid || !fam(fid)) return [h('div', { class: 'col' }, h('div', { class: 'empty' }, T.share.no_family), h('a', { class: 'btn primary block', href: '#/luot' }, T.home.cta))];
  const p = profileData(fid), year = new Date().getFullYear();
  const link = location.origin + location.pathname + encodeChallenge(fid, p.owned);
  const story = h('div', { class: 'story' },
    h('p', { class: 'eyebrow' }, fill(T.share.eyebrow, { year })),
    h('div', {}, h('div', { class: 'sub' }, T.share.type), h('div', { class: 'arche' }, T.archetypes[fid]),
      h('div', { class: 'sub' }, fill(T.share.sub, { family: p.f.name.split('/')[0].trim(), lv: p.L.lv, n: p.owned.size }))),
    h('div', { class: 'fan' }, p.top3.map(id => h('div', { class: 'm' }, h('small', {}, T.card.rarity[rarity(sk(id).open.share)]), sk(id).vi))),
    h('div', { class: 'sgrid' },
      h('div', {}, h('b', {}, p.k ? `1/${p.k}` : '—'), fill(T.share.stat_one_in, { family: famLower(p.f) })),
      h('div', {}, h('b', {}, p.shield ? `${p.shield}/5` : '—'), T.share.stat_shield)),
    p.next ? h('div', { class: 'goal' }, h('span', {}, T.share.goal), h('b', {}, `${sk(p.next.id).vi} → 1/${p.next.k}`)) : null,
    h('div', { class: 'chal' }, T.share.challenge, ' →'),
    h('div', { class: 'src' }, fill(T.share.source, { n: fmt(D.meta.n_open), date: new Date(D.meta.generated_at).toLocaleDateString('vi-VN') })));
  const status = h('span', { class: 'small muted', 'aria-live': 'polite' });
  const copy = async () => { try { await navigator.clipboard.writeText(link); status.textContent = T.share.copied; } catch { prompt(T.share.copy, link); } };
  return [h('div', { class: 'col' }, story,
    h('div', { class: 'row', style: 'justify-content:center' },
      h('button', { class: 'btn primary', onclick: () => saveImage(p, link, false) }, T.share.save),
      h('button', { class: 'btn', onclick: () => saveImage(p, link, true) }, T.share.send),
      h('button', { class: 'btn ghost', onclick: copy }, T.share.copy)), status)];
}

// Vẽ hồ sơ ra PNG 1080×1920 (khổ story) bằng canvas — không cần thư viện
const CANVAS_FONTS = ['700 34px "Be Vietnam Pro"', '500 40px "Be Vietnam Pro"', '800 118px "Bricolage Grotesque"',
  '800 42px "Bricolage Grotesque"', '700 80px "JetBrains Mono"'];
async function saveImage(p, link, share) {
  // canvas chỉ dùng được phông đã tải; ép tải đúng các mặt chữ (kể cả bộ tiếng Việt) trước khi vẽ
  await Promise.all(CANVAS_FONTS.map(f => document.fonts.load(f, 'Kiểu của mình ộữ 1/14')));
  const W = 1080, H = 1920, c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  const bg = g.createLinearGradient(0, 0, W * 0.6, H * 1.1); bg.addColorStop(0, '#0e2a33'); bg.addColorStop(0.55, '#16414d'); bg.addColorStop(1, '#b5470b');
  g.fillStyle = bg; g.fillRect(0, 0, W, H);
  g.fillStyle = 'rgba(255,201,60,.12)'; g.beginPath(); g.arc(W - 60, 100, 380, 0, Math.PI * 2); g.fill();
  const text = (t, x, y, font, color, max) => { g.font = font; g.fillStyle = color; g.fillText(t, x, y, max); };
  const P = 90;
  text(fill(T.share.eyebrow, { year: new Date().getFullYear() }).toUpperCase(), P, 190, '700 34px "Be Vietnam Pro"', '#ffc93c');
  text(T.share.type, P, 300, '500 40px "Be Vietnam Pro"', '#c9dadb');
  text(T.archetypes[p.f.id], P, 420, '800 118px "Bricolage Grotesque"', '#ffffff', W - 2 * P);
  text(fill(T.share.sub, { family: p.f.name.split('/')[0].trim(), lv: p.L.lv, n: p.owned.size }), P, 490, '500 40px "Be Vietnam Pro"', '#c9dadb');
  p.top3.forEach((id, i) => {
    const cw = 270, ch = 380, x = P + i * 315, y = 600 + (i === 1 ? -20 : 0);
    g.save(); g.translate(x + cw / 2, y + ch / 2); g.rotate((i - 1) * 0.15);
    g.fillStyle = '#ffc93c'; g.beginPath(); g.roundRect(-cw / 2 - 8, -ch / 2 - 8, cw + 16, ch + 16, 34); g.fill();
    g.fillStyle = '#ffffff'; g.beginPath(); g.roundRect(-cw / 2, -ch / 2, cw, ch, 28); g.fill();
    g.fillStyle = '#b5470b'; g.font = '700 26px "Be Vietnam Pro"'; g.fillText(T.card.rarity[rarity(sk(id).open.share)].toUpperCase(), -cw / 2 + 24, -ch / 2 + 50);
    g.fillStyle = '#0e2a33'; g.font = '800 42px "Bricolage Grotesque"';
    const words = sk(id).vi.split(' '); let line = '', ly = -ch / 2 + 110;
    for (const w of words) { if (g.measureText(line + w).width > cw - 48 && line) { g.fillText(line.trim(), -cw / 2 + 24, ly); line = ''; ly += 50; } line += w + ' '; }
    g.fillText(line.trim(), -cw / 2 + 24, ly); g.restore();
  });
  const box = (x, big, small) => { g.fillStyle = 'rgba(255,255,255,.08)'; g.beginPath(); g.roundRect(x, 1100, 430, 210, 30); g.fill();
    text(big, x + 34, 1200, '700 80px "JetBrains Mono"', '#ffffff'); text(small, x + 34, 1265, '500 32px "Be Vietnam Pro"', '#c9dadb', 380); };
  box(P, p.k ? `1/${p.k}` : '—', fill(T.share.stat_one_in, { family: famLower(p.f) }));
  box(P + 470, p.shield ? `${p.shield}/5` : '—', T.share.stat_shield);
  if (p.next) {
    text(T.share.goal, P, 1390, '500 34px "Be Vietnam Pro"', '#c9dadb');
    text(`${sk(p.next.id).vi} → 1/${p.next.k}`, P, 1445, '700 44px "Be Vietnam Pro"', '#ffc93c', W - 2 * P);
  }
  g.fillStyle = '#ffc93c'; g.beginPath(); g.roundRect(P, 1480, W - 2 * P, 140, 34); g.fill();
  text(T.share.challenge + '  →', P + 50, 1570, '700 50px "Be Vietnam Pro"', '#0e2a33');
  text(fill(T.share.source, { n: fmt(D.meta.n_open), date: new Date(D.meta.generated_at).toLocaleDateString('vi-VN') }), P, 1720, '500 30px "Be Vietnam Pro"', '#9db3b8', W - 2 * P);
  const blob = await new Promise(r => c.toBlob(r, 'image/png'));
  const file = new File([blob], `skillradar-${p.f.id}.png`, { type: 'image/png' });
  if (share && navigator.canShare && navigator.canShare({ files: [file] })) {
    try { await navigator.share({ files: [file], text: `${T.archetypes[p.f.id]} — ${link}` }); return; } catch { /* người dùng hủy */ }
  }
  const a = h('a', { href: URL.createObjectURL(blob), download: file.name }); document.body.append(a); a.click(); a.remove();
}

function challengeView() {
  const ch = decodeChallenge(location.hash);
  if (!ch || !fam(ch.family)) { location.hash = '#/'; return []; }
  const ids = ch.ids.filter(sk), f = fam(ch.family);
  store.set('challenge', { family: ch.family, ids });
  const k = oneIn(f, new Set(ids), D.meta.assumptions);
  return [h('div', { class: 'col', style: 'text-align:center' },
    h('p', { class: 'eyebrow' }, T.challenge.eyebrow),
    h('h2', {}, fill(T.challenge.title, { type: T.archetypes[ch.family] })),
    h('p', { class: 'lead' }, fill(T.challenge.lead, { n: ids.length, family: famLower(f), k: k || '—' })),
    h('div', { class: 'minicards' }, ids.map(id => h('div', { class: `mc ${rarity(sk(id).open.share)}` }, h('span', {}, h('small', {}, T.card.rarity[rarity(sk(id).open.share)]), sk(id).vi)))),
    h('a', { class: 'btn primary block', href: '#/luot' }, T.challenge.cta))];
}

// ---------- định tuyến ----------
let onKey = null;
document.addEventListener('keydown', e => { if (onKey && !document.querySelector('.overlay')) onKey(e); });
function route() {
  onKey = null;
  const [, page, a, b] = (location.hash || '#/').split('/');
  const view = { '': home, 'luot': swipe, 'ngay': () => day(a, b), 'ket': () => endOfDay(a), 'bai': deckView,
    'ho-so': () => profile(a), 'thach': challengeView }[page] || home;
  const nodes = view();
  if (nodes.length) app.replaceChildren(...nodes.flat().filter(Boolean));
  renderCount();
}
let last = location.hash;
window.addEventListener('hashchange', () => { document.querySelector('.overlay')?.remove(); if (location.hash !== last) window.scrollTo(0, 0); last = location.hash; route(); });

async function boot() {
  const get = p => fetch(p).then(r => { if (!r.ok) throw new Error(p); return r.json(); });
  const [copy, meta, skills, families, scenes] = await Promise.all(
    ['copy.vi.json', 'data/meta.json', 'data/skills.json', 'data/families.json', 'data/scenes.json'].map(get));
  T = copy; D = { meta, skills, families, scenes, byId: Object.fromEntries(skills.map(s => [s.id, s])) };
  document.getElementById('footer').textContent = fill(T.footer, { date: new Date(meta.generated_at).toLocaleDateString('vi-VN') });
  route();
}
document.getElementById('theme').onclick = () => {
  const dark = matchMedia('(prefers-color-scheme: dark)').matches;
  const cur = document.documentElement.dataset.theme || (dark ? 'dark' : 'light');
  document.documentElement.dataset.theme = cur === 'dark' ? 'light' : 'dark';
};
boot().catch(e => { app.textContent = 'Không tải được dữ liệu (' + e.message + '). Hãy mở trang qua máy chủ, không mở file trực tiếp.'; });
