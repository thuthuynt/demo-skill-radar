// Trang học sinh (bản đơn giản, không trò chơi): khám phá nghề -> trang nghề -> kỹ năng.
import { h, fill, fmt, tr, store, load, bar, tiles, frame, method, ddmm } from '../assets/pro.js';
import { treeSkills, trend, aiBadge, familyAi, salaryInsight } from '../assets/logic.js';

const app = document.getElementById('app');
let D, S, C, scenes;

const fold = s => (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase();
const k10 = w => Math.max(1, Math.round(w * 10));
const fam = id => D.families.find(f => f.id === id);
const inScope = () => D.families.filter(f => f.in_scope);
const need = w => h('span', { class: 'need', 'aria-hidden': 'true' }, Array.from({ length: 10 }, (_, i) => h('i', { class: i < k10(w) ? 'on' : '' })));
const aiOf = f => aiBadge({ score: familyAi(f, D.byId) });

// nghề gần giống: cosine trên trọng số kỹ năng (tỷ lệ tin cần kỹ năng)
function similar(f, n = 3) {
  const vec = x => Object.fromEntries(x.skills.map(([id, w]) => [id, w]));
  const a = vec(f), na = Math.hypot(...Object.values(a));
  return inScope().filter(g => g.id !== f.id).map(g => {
    const b = vec(g), dot = Object.keys(a).reduce((s, id) => s + a[id] * (b[id] || 0), 0);
    return { g, sim: dot / (na * Math.hypot(...Object.values(b))) };
  }).sort((x, y) => y.sim - x.sim).slice(0, n).map(x => x.g);
}

function jobCard(f) {
  const ai = aiOf(f);
  return h('a', { class: 'job', href: `#/nghe/${f.id}` },
    h('h3', {}, f.name), h('p', {}, S.families[f.id]?.short),
    h('div', { class: 'facts' },
      h('span', {}, h('b', {}, fmt(f.n_open)), S.card_open),
      h('span', {}, h('b', {}, f.salary_median_vnd ? tr(f.salary_median_vnd) + ' tr' : '—'), f.salary_median_vnd ? S.card_salary : S.salary_none)),
    h('div', { class: 'small' }, `${S.card_ai}: `, h('span', { class: `chip ${ai === 'high' ? 'warn' : ''}` }, S.ai_scale[ai])),
    h('span', { class: 'more' }, S.view, ' →'));
}

function listView() {
  const sort = store.get('sort', 'open');
  const cmp = { open: (a, b) => b.n_open - a.n_open, salary: (a, b) => (b.salary_median_vnd || 0) - (a.salary_median_vnd || 0),
    ai: (a, b) => (familyAi(a, D.byId) ?? 1) - (familyAi(b, D.byId) ?? 1) }[sort];
  const results = h('div', { class: 'results', 'aria-live': 'polite' });
  const grid = h('div', { class: 'jobs' }, inScope().sort(cmp).map(jobCard));
  const search = h('input', { type: 'search', placeholder: S.search_ph, 'aria-label': S.search_label, oninput: e => {
    const q = fold(e.target.value.trim());
    if (!q) { results.replaceChildren(); return; }
    const jobs = inScope().filter(f => fold(f.name + ' ' + (S.families[f.id]?.short || '')).includes(q)).slice(0, 5);
    const skills = D.skills.filter(s => fold(s.vi + ' ' + s.en).includes(q)).sort((a, b) => b.open.share - a.open.share).slice(0, 6);
    results.replaceChildren(
      ...jobs.map(f => h('a', { href: `#/nghe/${f.id}` }, h('span', {}, f.name), h('small', {}, S.search_jobs))),
      ...skills.map(s => h('a', { href: `#/ky-nang/${s.id}` }, h('span', {}, s.vi), h('small', {}, S.search_skills))),
      !jobs.length && !skills.length ? h('p', { class: 'note' }, S.search_none) : null);
  } });
  const select = h('select', { onchange: e => { store.set('sort', e.target.value); render(); } },
    ['open', 'salary', 'ai'].map(v => h('option', { value: v, selected: v === sort }, S[`sort_${v}`])));
  return [h('p', { class: 'eyebrow' }, S.eyebrow), h('h1', {}, S.title), h('p', { class: 'lead' }, S.lead),
    h('div', { class: 'search' }, h('label', { class: 'small muted' }, S.search_label), search, results),
    h('section', { class: 'section' }, h('header', {}, h('h2', {}, `${inScope().length} nhóm nghề`),
      h('label', { class: 'filters small muted' }, S.sort_label, select)), grid, h('p', { class: 'note' }, S.salary_explain)),
    method(D), h('p', { class: 'note' }, h('a', { href: '../tro-choi/' }, S.game_link))];
}

function jobView(id) {
  const f = fam(id);
  if (!f) { location.hash = '#/'; return []; }
  const copy = S.families[id] || {}, ai = aiOf(f), ins = salaryInsight(f);
  const provs = Object.entries(f.by_province).filter(([c]) => D.provinces.some(p => p.code === c && p.region))
    .sort((a, b) => b[1] - a[1]).slice(0, 3).map(([c, n]) => `${D.provinces.find(p => p.code === c).name} (${fmt(n)})`);
  const rows = treeSkills(f);
  const basePay = ins ? (f.skills.find(s => s[0] === ins.raise) || [])[3] : null;
  return [
    h('a', { class: 'back', href: '#/' }, S.back),
    h('h1', {}, f.name),
    h('div', { class: 'grid2 section', style: 'margin-top:16px' },
      h('div', { class: 'card prose' }, h('h3', {}, S.what), h('p', {}, copy.short), h('h3', { style: 'margin-top:12px' }, S.day), h('p', {}, copy.day)),
      h('div', {}, tiles([[fmt(f.n_open), S.n_open], [f.salary_median_vnd ? tr(f.salary_median_vnd) : '—', f.salary_median_vnd ? S.salary : S.salary_none]]),
        h('p', { class: 'note' }, S.salary_explain),
        provs.length ? h('p', { class: 'note' }, `${S.where}: ${provs.join(', ')}`) : null)),
    h('section', { class: 'section' }, h('h2', {}, S.skills_title), h('p', { class: 'note', style: 'margin:4px 0 12px' }, S.skills_lead),
      h('div', { class: 'scroll' }, h('table', {},
        h('thead', {}, h('tr', {}, h('th', {}, S.col_skill), h('th', {}, S.col_need), h('th', { class: 'hide-sm' }, S.col_type), h('th', { class: 'num hide-sm' }, S.col_pay))),
        h('tbody', {}, rows.map(([sid, w, sw, swo]) => { const s = D.byId[sid];
          return h('tr', {}, h('td', {}, h('a', { href: `#/ky-nang/${sid}` }, s.vi)),
            h('td', {}, need(w), `${k10(w)}/10`), h('td', { class: 'small muted hide-sm' }, S.type[s.type] || s.type),
            h('td', { class: 'num hide-sm' }, sw != null ? `${tr(sw)} / ${tr(swo)}` : '—')); })))),
      h('p', { class: 'note hide-sm' }, S.pay_note)),
    ins && basePay ? h('section', { class: 'section card' }, h('h2', {}, S.insight_title),
      h('p', {}, fill(S.insight, { entry: D.byId[ins.entry].vi, raise: D.byId[ins.raise].vi, raisePay: tr(ins.raisePay), basePay: tr(basePay) }))) : null,
    (scenes[id] || []).length ? h('section', { class: 'section' }, h('h2', {}, S.quotes_title), h('p', { class: 'note', style: 'margin:4px 0 10px' }, S.quotes_lead),
      h('div', { style: 'display:grid;gap:10px' }, scenes[id].map(q => h('figure', { class: 'quote' }, h('q', {}, q.quote),
        h('small', {}, fill(S.quote_src, { source: q.source, date: ddmm(q.date) })))))) : null,
    h('section', { class: 'section card' }, h('h2', {}, S.ai_title),
      h('p', {}, h('span', { class: `chip ${ai === 'high' ? 'warn' : ''}` }, S.ai_scale[ai]), ' ', S.ai_body[ai])),
    h('section', { class: 'section' }, h('h2', { style: 'margin-bottom:12px' }, S.similar_title), h('div', { class: 'jobs' }, similar(f).map(jobCard))),
  ];
}

function skillView(id) {
  const s = D.byId[id];
  if (!s) { location.hash = '#/'; return []; }
  const t = trend(s.history), ai = aiBadge(s.ai);
  const jobs = D.families.filter(f => f.in_scope).map(f => [f, (f.skills.find(x => x[0] === id) || [])[1]]).filter(x => x[1])
    .sort((a, b) => b[1] - a[1]).slice(0, 6);
  return [h('a', { class: 'back', href: '#/' }, S.back),
    h('p', { class: 'eyebrow' }, S.skill_eyebrow), h('h1', {}, s.vi), s.en && s.en !== s.vi ? h('p', { class: 'lead' }, s.en) : null,
    tiles([[`${k10(s.open.share)}/10`, S.skill_overall], [C.trend[t], S.skill_trend], [S.ai_scale[ai], S.skill_ai]]),
    h('section', { class: 'section card' }, h('h2', { style: 'margin-bottom:10px' }, S.skill_jobs),
      h('table', {}, h('tbody', {}, jobs.map(([f, w]) => h('tr', {}, h('td', {}, h('a', { href: `#/nghe/${f.id}` }, f.name)),
        h('td', {}, bar(w, jobs[0][1], `${k10(w)}/10 tin`))))))),
  ];
}

function render() {
  const [, page, arg] = (location.hash || '#/').split('/');
  const nodes = ({ nghe: () => jobView(arg), 'ky-nang': () => skillView(arg) }[page] || listView)();
  if (nodes.length) app.replaceChildren(...nodes.filter(Boolean));
}
window.addEventListener('hashchange', () => { window.scrollTo(0, 0); render(); });

Promise.all([load(), fetch('../data/scenes.json').then(r => r.json())]).then(([d, sc]) => {
  D = d; S = d.C.student; C = d.C.common; scenes = sc;
  frame(D, 'student'); render();
}).catch(e => { app.textContent = 'Không tải được dữ liệu (' + e.message + ').'; });
