// Trang học sinh: thử vai -> cây kỹ năng -> bộ bài. Chữ hiển thị nằm hết trong copy.vi.json.
import { treeSkills, unlocked, scoreQuiz, tier, aiBadge, trend, familyAi, bestNext } from './logic.js';

const app = document.getElementById('app');
let T, D;  // T: chữ, D: dữ liệu

// --- tiện ích ---
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
const fill = (s, vars) => s.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? '');
const pct = x => Math.round(100 * x) + '%';
const fmt = n => n.toLocaleString('vi-VN');
const store = {
  get(k, d) { try { return JSON.parse(localStorage.getItem('sr:' + k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem('sr:' + k, JSON.stringify(v)); } catch { /* chế độ riêng tư: chỉ giữ trong phiên */ } },
};
const deck = () => new Set(store.get('deck', []));
const saveDeck = s => { store.set('deck', [...s]); renderDeckCount(); };
const fam = id => D.families.find(f => f.id === id);
const famName = id => fam(id)?.name ?? id;

// --- khung ---
function renderDeckCount() { const b = document.getElementById('deckCount'); if (b) b.textContent = deck().size; }

function sourceBox() {
  const dates = D.meta.sources.map(s => `${s.source} ${s.latest.split('-').reverse().slice(0, 2).join('/')}`).join(', ');
  return h('details', { class: 'src' }, h('summary', {}, T.source.label),
    h('p', {}, fill(T.source.body, { n: fmt(D.meta.n_open), dates })),
    h('a', { href: 'data.html' }, T.source.data_link));
}

// --- màn hình ---
function home() {
  const m = D.meta;
  return [
    h('section', { class: 'hero' },
      h('p', { class: 'eyebrow' }, T.home.eyebrow),
      h('h1', {}, T.home.title),
      h('p', { class: 'lead' }, T.home.lead),
      h('div', { class: 'row' },
        h('a', { class: 'btn primary', href: '#/thu-vai' }, T.home.cta_try),
        h('a', { class: 'btn', href: '#/tat-ca' }, T.home.cta_know))),
    h('div', { class: 'stats' },
      h('div', { class: 'stat' }, h('b', {}, fmt(m.n_open)), T.home.stat_open),
      h('div', { class: 'stat' }, h('b', {}, m.taxonomy.skills), T.home.stat_skills),
      h('div', { class: 'stat' }, h('b', {}, m.days_collected), T.home.stat_days)),
    sourceBox(),
  ];
}

let answers = [];
function quiz() {
  const qs = T.quiz.questions;
  const i = answers.length;
  if (i >= qs.length) { finishQuiz(); return []; }
  const q = qs[i];
  const pick = ans => { answers.push(ans); route(); };
  return [h('div', { class: 'quiz' },
    h('div', { class: 'progress', role: 'progressbar', 'aria-valuemin': 0, 'aria-valuemax': qs.length, 'aria-valuenow': i },
      h('i', { style: `width:${100 * i / qs.length}%` })),
    h('p', { class: 'eyebrow' }, fill(T.quiz.eyebrow, { n: i + 1, total: qs.length })),
    h('h2', {}, T.quiz.title),
    h('div', { class: 'choices' },
      h('button', { class: 'choice', onclick: () => pick(q.a) }, q.a.text),
      h('span', { class: 'or', 'aria-hidden': 'true' }, 'hay'),
      h('button', { class: 'choice', onclick: () => pick(q.b) }, q.b.text)),
    h('button', { class: 'btn ghost small', onclick: () => pick({ text: '', families: [] }) }, T.quiz.skip))];
}

function finishQuiz() {
  const picks = scoreQuiz(answers.filter(a => a.text), D.families.filter(f => f.id !== 'quan-ly'), 6);
  store.set('deal', { shown: picks.slice(0, 3), spare: picks.slice(3) });
  answers = [];
  location.hash = '#/vai';
}

function roleCard(p, kept, onKeep, onRedraw) {
  const f = fam(p.id), copy = T.families[p.id];
  return h('article', { class: 'role-card' + (kept ? ' kept' : '') },
    h('p', { class: 'eyebrow' }, T.role.eyebrow),
    h('h3', {}, f.name),
    h('p', {}, copy?.short),
    p.reasons?.length ? h('p', { class: 'because' }, fill(T.deal.because, { reasons: p.reasons.join(', ') })) : null,
    h('div', { class: 'facts' },
      h('span', {}, h('b', {}, fmt(f.n_open)), T.role.open_jobs),
      h('span', {}, h('b', {}, f.salary_median_vnd ? (f.salary_median_vnd / 1e6).toLocaleString('vi-VN') + ' tr' : '—'),
        f.salary_median_vnd ? T.role.salary : T.role.salary_none)),
    h('div', { class: 'actions' },
      h('a', { class: 'btn primary small', href: `#/nghe/${p.id}` }, T.deal.open),
      onKeep ? h('button', { class: 'btn small', onclick: onKeep, 'aria-pressed': kept }, kept ? T.deal.kept : T.deal.keep) : null,
      onRedraw ? h('button', { class: 'btn ghost small', onclick: onRedraw }, T.deal.redraw) : null));
}

function dealView() {
  const deal = store.get('deal', null);
  if (!deal) { location.hash = '#/thu-vai'; return []; }
  const kept = new Set(store.get('kept', []));
  const toggle = id => { kept.has(id) ? kept.delete(id) : kept.add(id); store.set('kept', [...kept]); route(); };
  const redraw = i => {
    // rút vai khác: lấy từ hàng chờ của trắc nghiệm, hết thì lấy nghề nhiều tin chưa hiện
    const shownIds = new Set(deal.shown.map(p => p.id));
    const next = deal.spare.shift() || D.families.filter(f => !shownIds.has(f.id) && f.id !== 'quan-ly')
      .sort((a, b) => b.n_open - a.n_open).map(f => ({ id: f.id, reasons: [] }))[0];
    if (next) { deal.shown[i] = next; store.set('deal', deal); route(); }
  };
  return [
    h('p', { class: 'eyebrow' }, T.deal.eyebrow), h('h2', {}, T.deal.title),
    h('div', { class: 'deal' }, deal.shown.map((p, i) => roleCard(p, kept.has(p.id), () => toggle(p.id), () => redraw(i)))),
    h('p', { class: 'note' }, T.deal.method),
    h('div', { class: 'row', style: 'margin-top:16px' },
      h('a', { class: 'btn ghost small', href: '#/thu-vai' }, '↺ ' + T.home.cta_try),
      h('a', { class: 'btn ghost small', href: '#/tat-ca' }, T.home.cta_all)),
  ];
}

function skillCard(id, share, owned, onToggle) {
  const s = D.byId[id];
  // hạng theo tỷ lệ đang hiển thị (trong nghề trên cây kỹ năng, toàn thị trường trong bộ bài)
  const tr = trend(s.history), ai = aiBadge(s.ai), t = tier(share);
  return h('button', { class: 'skill', 'aria-pressed': owned, onclick: onToggle,
      'aria-label': `${s.vi}, ${pct(share)} tin. ${owned ? 'Đã có' : 'Chưa có'}` },
    h('span', { class: 'tick', 'aria-hidden': 'true' }, owned ? '✓' : ''),
    h('span', { class: 'name' }, s.vi),
    h('span', { class: 'share' }, h('i', { style: `--w:${Math.min(100, 100 * share)}%` }), pct(share)),
    h('span', { class: 'tags' },
      h('span', { class: `tag tier-${t}` }, T.card[`tier_${t}`]),
      h('span', { class: 'tag' }, (tr === 'up' ? '↑ ' : tr === 'down' ? '↓ ' : '') + T.card[`trend_${tr}`]),
      h('span', { class: `tag ai-${ai}` }, T.card[`ai_${ai}`])));
}

function roleView(id) {
  const f = fam(id);
  if (!f) { location.hash = '#/tat-ca'; return []; }
  const owned = deck(), A = D.meta.assumptions;
  const n = unlocked(f, owned, A), max = Math.round(f.n_open * A.apply_rate_ceiling);
  const aiScore = familyAi(f, D.byId);
  const toggle = sid => { owned.has(sid) ? owned.delete(sid) : owned.add(sid); saveDeck(owned); route(); };
  return [
    h('div', { class: 'role-head' },
      h('div', {},
        h('p', { class: 'eyebrow' }, T.role.eyebrow),
        h('h2', {}, f.name),
        h('p', { class: 'lead' }, T.families[id]?.day),
        h('div', { class: 'facts-row' },
          h('div', { class: 'fact' }, h('b', {}, fmt(f.n_open)), h('span', {}, T.role.open_jobs)),
          h('div', { class: 'fact' }, h('b', {}, f.salary_median_vnd ? (f.salary_median_vnd / 1e6).toLocaleString('vi-VN') : '—'),
            h('span', {}, f.salary_median_vnd ? `${T.role.per_month} · ${T.role.salary}` : T.role.salary_none)),
          aiScore != null ? h('div', { class: 'fact' }, h('b', {}, aiScore.toFixed(2)),
            h('span', {}, `${T.role.ai_title}: ${T.card['ai_' + aiBadge({ score: aiScore })]}`)) : null),
        h('h3', {}, T.role.skills_title),
        h('p', { class: 'muted small' }, T.role.skills_hint),
        h('div', { class: 'cards' }, treeSkills(f).map(([sid, w]) => skillCard(sid, w, owned.has(sid), () => toggle(sid))))),
      h('aside', { class: 'meter', 'aria-live': 'polite' },
        h('p', { class: 'eyebrow', style: 'color:var(--duck-yellow)' }, T.role.meter_title),
        h('div', { class: 'big' }, fmt(n)),
        h('div', {}, T.role.meter_unit),
        h('div', { class: 'bar' }, h('i', { style: `width:${max ? 100 * n / max : 0}%` })),
        h('div', { class: 'small' }, fill(T.role.meter_of, { n: fmt(f.n_open) })),
        h('p', { class: 'note' }, T.role.meter_note),
        h('a', { class: 'btn primary small', href: '#/bo-bai' }, `${T.deck.nav} (${owned.size})`))),
    sourceBox(),
  ];
}

function deckView() {
  const owned = deck(), A = D.meta.assumptions;
  const fams = D.families.filter(f => f.in_scope);
  const fit = fams.map(f => ({ f, n: unlocked(f, owned, A) })).sort((a, b) => b.n - a.n);
  const total = fit.reduce((s, x) => s + x.n, 0), maxN = Math.max(1, ...fit.map(x => x.n));
  const remove = sid => { owned.delete(sid); saveDeck(owned); route(); };
  const add = sid => { owned.add(sid); saveDeck(owned); route(); };
  if (!owned.size) return [h('p', { class: 'eyebrow' }, T.deck.eyebrow), h('h2', {}, T.deck.title),
    h('div', { class: 'empty', style: 'margin-top:16px' }, T.deck.empty, ' ', h('a', { href: '#/thu-vai' }, T.home.cta_try))];
  const next = bestNext(fams, owned, A);
  return [
    h('p', { class: 'eyebrow' }, T.deck.eyebrow), h('h2', {}, T.deck.title),
    h('div', { class: 'cards' }, [...owned].filter(id => D.byId[id]).map(id =>
      skillCard(id, D.byId[id].open.share, true, () => remove(id)))),
    h('p', { class: 'note' }, fill(T.deck.total, { n: fmt(total), all: fmt(D.meta.n_open) })),
    h('div', { class: 'fit' }, fit.filter(x => x.n > 0).slice(0, 8).map(({ f, n }) =>
      h('a', { class: 'fit-row', href: `#/nghe/${f.id}` },
        h('strong', {}, f.name),
        h('span', { class: 'track' }, h('i', { style: `width:${100 * n / maxN}%` })),
        h('span', { class: 'num' }, fill(T.deck.unlock, { n: fmt(n) }))))),
    next.length ? [h('h3', { style: 'margin-top:28px' }, T.deck.next),
      h('div', { class: 'cards' }, next.map(({ id, gain }) => {
        const card = skillCard(id, D.byId[id].open.share, false, () => add(id));
        card.querySelector('.tags').append(h('span', { class: 'tag tier-valuable' }, fill(T.deck.next_gain, { n: fmt(gain) })));
        return card;
      }))] : null,
    h('p', { class: 'note' }, T.role.meter_note),
  ];
}

function allView() {
  const fams = D.families.filter(f => f.in_scope).sort((a, b) => b.n_open - a.n_open);
  return [h('p', { class: 'eyebrow' }, T.all.eyebrow), h('h2', {}, T.all.title),
    h('div', { class: 'deal' }, fams.map(f => roleCard({ id: f.id }))), sourceBox()];
}

// --- định tuyến ---
function route() {
  const [, page, arg] = (location.hash || '#/').split('/');
  const view = { '': home, 'thu-vai': quiz, 'vai': dealView, 'nghe': () => roleView(arg), 'bo-bai': deckView, 'tat-ca': allView }[page] || home;
  const nodes = view();
  if (nodes.length) { app.replaceChildren(...nodes.flat().filter(Boolean)); }
  renderDeckCount();
}
let lastHash = location.hash;
window.addEventListener('hashchange', () => {
  if (!location.hash.startsWith('#/thu-vai')) answers = [];
  if (location.hash !== lastHash) window.scrollTo(0, 0);
  lastHash = location.hash; route();
});

async function boot() {
  const get = p => fetch(p).then(r => { if (!r.ok) throw new Error(p); return r.json(); });
  const [copy, meta, skills, families] = await Promise.all(
    [get('copy.vi.json'), get('data/meta.json'), get('data/skills.json'), get('data/families.json')]);
  T = copy;
  D = { meta, skills, families, byId: Object.fromEntries(skills.map(s => [s.id, s])) };
  document.getElementById('footer').textContent = fill(T.footer, { date: new Date(meta.generated_at).toLocaleDateString('vi-VN') });
  route();
}
document.getElementById('theme').onclick = () => {
  const dark = matchMedia('(prefers-color-scheme: dark)').matches;
  const cur = document.documentElement.dataset.theme || (dark ? 'dark' : 'light');
  document.documentElement.dataset.theme = cur === 'dark' ? 'light' : 'dark';
};
boot().catch(e => { app.textContent = 'Không tải được dữ liệu (' + e.message + '). Hãy mở trang qua máy chủ, không mở file trực tiếp.'; });
