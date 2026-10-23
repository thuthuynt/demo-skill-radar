// Trang nhà trường: đối chiếu chương trình đào tạo với kỹ năng nhà tuyển dụng yêu cầu.
import { h, fill, fmt, pct, tr, store, load, bar, tiles, frame, method, csvButton, change12, trendSvg } from '../assets/pro.js';
import { trend, aiBadge, familyAi } from '../assets/logic.js';

const app = document.getElementById('app');
const TOP = 20;   // số kỹ năng đối chiếu cho mỗi nhóm nghề
let D, U, C;

function render() {
  const fams = D.families.filter(f => f.in_scope).sort((a, b) => b.n_open - a.n_open);
  const fid = store.get('family', fams[0].id);
  const f = fams.find(x => x.id === fid) || fams[0];
  const rows = f.skills.slice(0, TOP);
  const taught = new Set(store.get('taught:' + f.id, []));
  const total = rows.reduce((s, r) => s + r[1], 0);
  const covered = rows.reduce((s, r) => s + (taught.has(r[0]) ? r[1] : 0), 0) / (total || 1);
  const gaps = rows.filter(r => !taught.has(r[0])).slice(0, 8);
  const ai = familyAi(f, D.byId);
  const maxW = rows[0]?.[1] || 1;

  const select = h('select', { onchange: e => { store.set('family', e.target.value); render(); } },
    fams.map(x => h('option', { value: x.id, selected: x.id === f.id }, `${x.name} (${fmt(x.n_open)})`)));

  const toggle = (id, on) => { on ? taught.add(id) : taught.delete(id); store.set('taught:' + f.id, [...taught]); render(); };
  const table = h('table', {},
    h('thead', {}, h('tr', {}, h('th', {}, U.col_taught), h('th', {}, U.col_skill), h('th', {}, U.col_share),
      h('th', {}, U.col_trend), h('th', { class: 'num' }, U.col_pay), h('th', {}, U.col_ai))),
    h('tbody', {}, rows.map(([id, w, sw, swo]) => {
      const s = D.byId[id], t = trend(s.history), a = aiBadge(s.ai);
      return h('tr', {},
        h('td', {}, h('input', { type: 'checkbox', 'aria-label': `${U.col_taught}: ${s.vi}`, checked: taught.has(id), onchange: e => toggle(id, e.target.checked) })),
        h('td', {}, s.vi, h('div', { class: 'small muted' }, s.group)),
        h('td', {}, bar(w, maxW, pct(w))),
        h('td', { style: 'white-space:nowrap' }, trendSvg(s), h('span', { class: `chip ${t === 'up' ? 'up' : t === 'down' ? 'down' : ''}` }, C.trend[t])),
        h('td', { class: 'num' }, sw != null ? `${tr(sw)} / ${tr(swo)}` : '—'),
        h('td', {}, h('span', { class: `chip ${a === 'high' ? 'warn' : ''}` }, C.ai[a])));
    })));

  const rising = D.skills.filter(s => s.open.share >= 0.02).map(s => ({ s, c: change12(s) }))
    .filter(x => x.c && x.c.delta > 0).sort((a, b) => b.c.delta - a.c.delta).slice(0, 8);
  const maxR = rising[0]?.c.delta || 1;

  app.replaceChildren(
    h('p', { class: 'eyebrow' }, U.eyebrow), h('h1', {}, U.title), h('p', { class: 'lead' }, U.lead),
    h('div', { class: 'section filters' }, h('label', {}, U.pick_family, select)),
    tiles([[fmt(f.n_open), fill(U.tile_family_open, { family: f.name.toLowerCase() })],
      [tr(f.salary_median_vnd), U.tile_salary],
      [ai != null ? ai.toFixed(2) : '—', `${U.tile_ai}: ${C.ai[aiBadge({ score: ai })]}`]]),
    h('section', { class: 'section grid2' },
      h('div', { class: 'card' }, h('h2', {}, U.coverage_title), h('div', { class: 'big', style: 'margin-top:10px' }, pct(covered)),
        h('div', { class: 'meter', role: 'meter', 'aria-valuenow': Math.round(100 * covered), 'aria-valuemin': 0, 'aria-valuemax': 100 },
          h('i', { style: `width:${100 * covered}%` })),
        h('p', { class: 'note' }, U.coverage_body)),
      h('div', { class: 'card' }, h('h2', {}, U.gap_title),
        gaps.length ? h('ol', {}, gaps.map(([id, w]) => h('li', {}, `${D.byId[id].vi} — ${pct(w)} tin`))) : h('p', {}, U.gap_none))),
    h('section', { class: 'section' },
      h('header', {}, h('h2', {}, U.table_title), csvButton(C.csv, `skillradar-${f.id}.csv`, () => [
        [U.col_taught, U.col_skill, U.col_share, U.col_trend, 'Lương có (tr)', 'Lương không (tr)', U.col_ai],
        ...rows.map(([id, w, sw, swo]) => { const s = D.byId[id];
          return [taught.has(id) ? 'x' : '', s.vi, (100 * w).toFixed(1), C.trend[trend(s.history)], sw && tr(sw), swo && tr(swo), C.ai[aiBadge(s.ai)]]; })])),
      h('div', { class: 'scroll' }, table), h('p', { class: 'note' }, U.trend_note)),
    h('section', { class: 'section card' }, h('h2', {}, U.rising_title), h('p', { class: 'note' }, U.rising_body),
      h('table', {}, h('tbody', {}, rising.map(({ s, c }) => h('tr', {}, h('td', {}, s.vi),
        h('td', {}, bar(c.delta, maxR, `+${(100 * c.delta).toFixed(1)} điểm %`, 'acc')), h('td', { class: 'small muted' }, c.source)))))),
    method(D));
}

load().then(d => { D = d; U = d.C.uni; C = d.C.common; frame(D, 'uni'); render(); })
  .catch(e => { app.textContent = 'Không tải được dữ liệu (' + e.message + ').'; });
