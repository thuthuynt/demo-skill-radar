// Trang cơ quan quản lý: tổng quan nhu cầu kỹ năng theo nhóm nghề và địa phương.
import { h, fill, fmt, pct, tr, store, load, bar, tiles, commonTiles, frame, method, csvButton, change12 } from '../assets/pro.js';
import { aiBadge, familyAi } from '../assets/logic.js';

const app = document.getElementById('app');
const N_PROV = 8;
let D, G, C;

function heatTable() {
  const fams = D.families.filter(f => f.in_scope).sort((a, b) => b.n_open - a.n_open);
  const top = D.provinces.filter(p => !['toan-quoc', 'nuoc-ngoai', 'mien-bac', 'mien-trung', 'mien-nam', 'khong-ro'].includes(p.code)).slice(0, N_PROV);
  const ids = new Set(top.map(p => p.code));
  const cell = (f, code) => f.by_province[code] || 0;
  const other = f => Object.entries(f.by_province).filter(([c]) => !ids.has(c)).reduce((s, [, n]) => s + n, 0);
  const max = Math.max(...fams.flatMap(f => top.map(p => cell(f, p.code))));
  // nền một màu, đậm theo số tin (thang tuần tự); chữ luôn màu mực để đủ tương phản
  const bg = n => n ? `background:color-mix(in srgb, var(--water) ${Math.round(8 + 50 * Math.sqrt(n / max))}%, var(--surface))` : '';
  const table = h('table', { class: 'heat' },
    h('thead', {}, h('tr', {}, h('th', {}, 'Nhóm nghề'), top.map(p => h('th', { class: 'num' }, p.name)), h('th', { class: 'num' }, 'Khác'), h('th', { class: 'num' }, 'Tổng'))),
    h('tbody', {}, fams.map(f => h('tr', {}, h('td', {}, f.name),
      top.map(p => h('td', { class: 'num', style: bg(cell(f, p.code)), title: `${f.name} · ${p.name}: ${fmt(cell(f, p.code))} tin` }, fmt(cell(f, p.code)))),
      h('td', { class: 'num' }, fmt(other(f))), h('td', { class: 'num' }, h('b', {}, fmt(f.n_open)))))));
  const csv = csvButton(C.csv, 'skillradar-nhom-nghe-tinh.csv', () => [
    ['Nhóm nghề', ...top.map(p => p.name), 'Khác', 'Tổng'],
    ...fams.map(f => [f.name, ...top.map(p => cell(f, p.code)), other(f), f.n_open])]);
  return h('section', { class: 'section' }, h('header', {}, h('h2', {}, G.heat_title), csv),
    h('div', { class: 'scroll' }, table), h('p', { class: 'note' }, G.heat_note));
}

function skillsBlock() {
  const prov = store.get('province', '');
  const provs = D.provinces.filter(p => D.skills.some(s => s.by_province.some(x => x[0] === p.code)));
  const rows = D.skills.map(s => [s, prov ? (s.by_province.find(x => x[0] === prov) || [])[1] : s.open.share])
    .filter(r => r[1] != null).sort((a, b) => b[1] - a[1]).slice(0, 15);
  const max = rows[0]?.[1] || 1;
  const select = h('select', { onchange: e => { store.set('province', e.target.value); render(); } },
    h('option', { value: '' }, G.all_country), provs.map(p => h('option', { value: p.code, selected: p.code === prov }, `${p.name} (${fmt(p.n_open)})`)));
  return h('div', { class: 'card' }, h('header', { class: 'filters', style: 'justify-content:space-between;margin-bottom:10px' },
      h('h2', {}, G.skills_title), h('label', {}, G.pick_province, select)),
    h('table', {}, h('tbody', {}, rows.map(([s, v]) => h('tr', {}, h('td', {}, s.vi), h('td', {}, bar(v, max, pct(v))))))));
}

function aiBlock() {
  const rows = D.families.filter(f => f.in_scope).map(f => [f, familyAi(f, D.byId)]).filter(r => r[1] != null).sort((a, b) => b[1] - a[1]);
  const max = rows[0]?.[1] || 1;
  return h('div', { class: 'card' }, h('h2', {}, G.ai_title),
    h('table', { style: 'margin-top:10px' }, h('tbody', {}, rows.map(([f, a]) => h('tr', {}, h('td', {}, f.name),
      h('td', {}, bar(a, max, a.toFixed(2), 'acc')), h('td', {}, h('span', { class: 'chip' }, C.ai[aiBadge({ score: a })])))))),
    h('p', { class: 'note' }, G.ai_note));
}

function salaryBlock() {
  const rows = D.families.filter(f => f.in_scope && f.salary_median_vnd).sort((a, b) => b.salary_median_vnd - a.salary_median_vnd);
  const max = rows[0]?.salary_median_vnd || 1;
  return h('div', { class: 'card' }, h('h2', {}, G.salary_title),
    h('table', { style: 'margin-top:10px' }, h('tbody', {}, rows.map(f => h('tr', {}, h('td', {}, f.name),
      h('td', {}, bar(f.salary_median_vnd, max, `${tr(f.salary_median_vnd)} tr`)), h('td', { class: 'small muted num' }, `${fmt(f.salary_n)} tin`))))),
    h('p', { class: 'note' }, G.salary_note));
}

function trendBlock() {
  const all = D.skills.filter(s => s.open.share >= 0.02).map(s => ({ s, c: change12(s) })).filter(x => x.c);
  const up = all.filter(x => x.c.delta > 0).sort((a, b) => b.c.delta - a.c.delta).slice(0, 6);
  const down = all.filter(x => x.c.delta < 0).sort((a, b) => a.c.delta - b.c.delta).slice(0, 6);
  const row = ({ s, c }) => h('tr', {}, h('td', {}, s.vi), h('td', { class: 'small muted' }, c.source),
    h('td', { class: 'num' }, h('span', { class: `chip ${c.delta > 0 ? 'up' : 'down'}` }, `${c.delta > 0 ? '+' : ''}${(100 * c.delta).toFixed(1)} điểm %`)),
    h('td', { class: 'num' }, pct(c.now, 1)),
    h('td', {}, c.beats == null ? '—' : h('span', { class: `chip ${c.beats ? 'up' : 'warn'}` }, c.beats ? G.yes : G.no)));
  return h('section', { class: 'section card' }, h('h2', {}, G.trend_title),
    h('div', { class: 'scroll', style: 'margin-top:10px' }, h('table', {},
      h('thead', {}, h('tr', {}, h('th', {}, G.col_skill), h('th', {}, G.col_source), h('th', { class: 'num' }, G.col_change), h('th', { class: 'num' }, G.col_now), h('th', {}, G.col_model))),
      h('tbody', {}, up.map(row), down.map(row)))),
    h('p', { class: 'note' }, G.trend_note));
}

function qualityBlock() {
  const st = D.status, ev = st.extract_eval;
  const fam = Object.fromEntries(D.families.map(f => [f.id, f.name]));
  return h('section', { class: 'section card' }, h('h2', {}, G.quality_title),
    h('p', { class: 'note' }, G.q_coverage),
    h('table', {}, h('tbody', {}, st.coverage_by_family.filter(c => fam[c.job_family_id]).map(c =>
      h('tr', {}, h('td', {}, fam[c.job_family_id]), h('td', {}, bar(c.share, 1, pct(c.share))), h('td', { class: 'num small muted' }, `${fmt(c.n)} tin`))))),
    h('ul', { class: 'small', style: 'margin-top:14px' },
      h('li', {}, `${G.q_f1}: `, ev?.all ? `${ev.all.f1} (${ev.all.n} tin)` : G.q_f1_none),
      h('li', {}, fill(G.q_latency, { d: st.median_latency_days })),
      h('li', {}, fill(G.q_forecast, { list: st.forecast.map(f => `${f.source} ${f.beats}/${f.n}`).join(', ') })),
      h('li', {}, fill(G.q_blocked, { list: st.blocked_or_excluded_sources.join(', ') }))));
}

function render() {
  app.replaceChildren(
    h('p', { class: 'eyebrow' }, G.eyebrow), h('h1', {}, G.title), h('p', { class: 'lead' }, G.lead),
    tiles(commonTiles(D)),
    heatTable(),
    h('section', { class: 'section grid2' }, skillsBlock(), aiBlock()),
    h('section', { class: 'section grid2' }, salaryBlock(), h('div', { class: 'off' }, h('h2', {}, G.gap_title), h('p', {}, G.gap_off))),
    trendBlock(), qualityBlock(), method(D));
}

load().then(d => { D = d; G = d.C.gov; C = d.C.common; frame(D, 'gov'); render(); })
  .catch(e => { app.textContent = 'Không tải được dữ liệu (' + e.message + ').'; });
