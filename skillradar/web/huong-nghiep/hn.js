// Trang hướng nghiệp: chào -> trắc nghiệm Holland -> nghề hợp với bạn -> chi tiết nghề (tổng quan / thị trường / kỹ năng & CV).
// Chữ hiển thị trong copy.hn.vi.json; phép tính trong logic.js (có test). CV chỉ đọc trên máy người dùng.
import { h, fill, fmt, pct, tr, ddmm, load, bar, trendSvg } from '../assets/pro.js';
import { treeSkills, coverage, unlocked, aiBadge, familyAi, trend, salaryInsight,
  riasecScores, hollandCode, codeFit, matcher, cvSkills } from '../assets/logic.js';

const app = document.getElementById('app');
let D, T, P, units, M;
const store = {
  get(k, d) { try { return JSON.parse(localStorage.getItem('srhn:' + k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem('srhn:' + k, JSON.stringify(v)); } catch { /* chế độ riêng tư */ } },
};
const k10 = w => Math.max(1, Math.round(w * 10));
const unit = id => units.find(u => u.id === id);
const owned = () => new Set(store.get('owned', []));
const answers = () => store.get('answers', []);
const scores = () => riasecScores(T.quiz.items, answers());
const done = () => answers().filter(a => a != null).length === T.quiz.items.length;
const range = x => x.salary_range_vnd ? `${tr(x.salary_range_vnd[0])}–${tr(x.salary_range_vnd[1])}` : null;
// hồ sơ mới: xóa mọi thứ trang này lưu trên máy (tên, lớp, câu trả lời, kỹ năng)
const newProfile = () => Object.keys(localStorage).filter(k => k.startsWith('srhn:')).forEach(k => localStorage.removeItem(k));
// nhóm người dùng (học sinh, sinh viên, đi làm...) quyết định lời dẫn, gợi ý trong nghề và tab mở trước
const persona = () => T.personas[store.get('persona', '')] || null;
const typeChip = t => h('span', { class: `rt rt-${t}` }, T.types[t].emoji, ' ', T.types[t].name);

// ---------- biểu đồ ----------

// lục giác RIASEC: mỗi đỉnh một nhóm, bán kính = điểm
function hexChart(sc) {
  const S = 260, c = S / 2, R = 92, order = 'RIASEC'.split('');
  const pt = (i, r) => { const a = -Math.PI / 2 + i * Math.PI / 3; return [c + r * Math.cos(a), c + r * Math.sin(a)]; };
  const poly = r => order.map((_, i) => pt(i, typeof r === 'function' ? r(i) : r).map(v => v.toFixed(1)).join(',')).join(' ');
  const grid = [1, 2 / 3, 1 / 3].map(f => `<polygon points="${poly(R * f)}" fill="none" stroke="var(--line)"/>`).join('');
  const labels = order.map((t, i) => { const [x, y] = pt(i, R + 26);
    return `<text x="${x}" y="${y}" text-anchor="middle" dominant-baseline="middle" font-size="12" font-weight="700" fill="var(--ink)">${T.types[t].emoji} ${T.types[t].name}</text>`
      + `<text x="${x}" y="${y + 14}" text-anchor="middle" font-size="11" fill="var(--muted)">${Math.round(100 * sc[t])}%</text>`; }).join('');
  const el = h('div', { class: 'hex' });
  el.innerHTML = `<svg viewBox="-30 -10 ${S + 60} ${S + 30}" role="img" aria-label="Điểm sáu nhóm sở thích">${grid}
    <polygon points="${poly(i => Math.max(0.04, sc[order[i]]) * R)}" fill="var(--duck)" fill-opacity=".55" stroke="var(--bill)" stroke-width="2"/>${labels}</svg>`;
  return el;
}

// dải lương p25–p75 trên thang chung của mọi nghề, chấm là trung vị
function salaryBand(x, max) {
  const [lo, hi] = x.salary_range_vnd, med = x.salary_median_vnd;
  const X = v => `${(100 * v / max).toFixed(1)}%`;
  return h('div', { class: 'band' },
    h('div', { class: 'track' }, h('i', { style: `left:${X(lo)};width:calc(${X(hi)} - ${X(lo)})` }),
      med ? h('b', { style: `left:${X(med)}`, title: `Trung vị ${tr(med)} tr` }) : null),
    h('div', { class: 'ends' }, h('span', { style: `left:${X(lo)}` }, `${tr(lo)} tr`), h('span', { style: `left:${X(hi)}` }, `${tr(hi)} tr`)));
}

// tỷ lệ tin nhắc công cụ AI theo nửa năm: đường nối các kỳ đủ tin, kỳ thiếu tin để trống (không nội suy)
function aiLine(f) {
  const P = D.C.common.ai_trend, rows = f.ai_trend, W = 340, H = 160, pad = { l: 50, r: 44, t: 18, b: 26 };
  const max = Math.max(0.01, ...rows.map(r => r[1] ?? 0)) * 1.2;
  const X = i => pad.l + i * (W - pad.l - pad.r) / Math.max(1, rows.length - 1);
  const Y = v => H - pad.b - v / max * (H - pad.t - pad.b);
  const segs = [];
  rows.forEach(([, v], i) => { if (v == null) return; (i && rows[i - 1][1] != null ? segs.at(-1) : segs[segs.push([]) - 1]).push([X(i), Y(v)]); });
  const grid = [0, max / 2, max].map(v => `<line x1="${pad.l}" x2="${W - pad.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/>`
    + `<text x="${pad.l - 6}" y="${Y(v) + 4}" text-anchor="end" font-size="11" fill="var(--muted)">${pct(v, 1)}</text>`).join('');
  const pts = rows.map(([p, v, n], i) => `<text x="${X(i)}" y="${H - 6}" text-anchor="middle" font-size="11" fill="var(--muted)">${P.periods[p]}</text>`
    + (v == null ? `<text x="${X(i)}" y="${Y(0) - 6}" text-anchor="middle" font-size="10" fill="var(--muted)">${fill(P.none, { n })}</text>`
      : `<circle cx="${X(i)}" cy="${Y(v)}" r="4" fill="var(--water)"><title>${pct(v, 1)} (${n} tin)</title></circle>`
        + `<text x="${X(i)}" y="${Y(v) - 9}" text-anchor="middle" font-size="12" font-weight="700" fill="var(--ink)">${pct(v, 1)}</text>`)).join('');
  const line = segs.map(sg => `<polyline points="${sg.map(p => p.map(v => v.toFixed(1)).join(',')).join(' ')}" fill="none" stroke="var(--water)" stroke-width="2.5" stroke-linejoin="round"/>`).join('');
  const el = h('div', { class: 'ailine' });
  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="${T.job.ai_chart}">${grid}${line}${pts}</svg>`;
  return el;
}

// ---------- màn hình ----------

// biểu tượng radar: vòng tròn, tia quét xoay, các chấm (nghề) sáng lên khi tia quét qua
function radar() {
  const blips = [[38, -52], [-58, -20], [20, 44], [-30, 50], [62, 18]];
  // chấm sáng đúng lúc tia (xoay theo chiều kim đồng hồ, 4 giây/vòng) quét tới góc của nó
  const at = (x, y) => ((Math.atan2(y, x) * 180 / Math.PI + 360) % 360) / 90;
  const el = h('div', { class: 'radar', 'aria-hidden': 'true' });
  el.innerHTML = `<svg viewBox="-100 -100 200 200">
    <defs><linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="var(--duck)" stop-opacity="0"/><stop offset="1" stop-color="var(--duck)" stop-opacity=".85"/></linearGradient></defs>
    <circle r="96" class="r-bg"/>${[32, 64, 96].map(r => `<circle r="${r}" class="r-ring"/>`).join('')}
    <path d="M-96 0H96M0-96V96" class="r-ring"/>
    <g class="r-sweep"><path d="M0 0L96 0A96 96 0 0 0 67.9 -67.9Z" fill="url(#sweep)"/><line x1="0" y1="0" x2="96" y2="0" class="r-beam"/></g>
    ${blips.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="5" class="r-blip" style="animation-delay:${at(x, y).toFixed(2)}s"/>`).join('')}
    <circle r="5" class="r-core"/></svg>`;
  return el;
}

function welcome() {
  const W = T.welcome, name = store.get('name', ''), grade = store.get('persona', '');
  const input = h('input', { type: 'text', value: name, placeholder: W.name_ph, autocomplete: 'given-name', maxlength: 40,
    oninput: e => store.set('name', e.target.value.trim()) });
  return [h('section', { class: 'hello' }, radar(),
    h('p', { class: 'wave' }, W.hi), h('h1', {}, W.title),
    h('ol', { class: 'steps' }, W.steps.map(s => h('li', {}, s))),
    h('div', { class: 'form card' },
      h('label', {}, W.name_label, input),
      h('fieldset', {}, h('legend', {}, W.grade_label), h('div', { class: 'pills' }, Object.entries(T.personas).map(([g, p]) =>
        h('button', { type: 'button', class: 'pill' + (g === grade ? ' on' : ''), 'aria-pressed': String(g === grade),
          onclick: e => { store.set('persona', g); e.currentTarget.parentNode.querySelectorAll('.pill').forEach(b => {
            b.classList.toggle('on', b === e.currentTarget); b.setAttribute('aria-pressed', String(b === e.currentTarget)); }); } }, p.label)))),
      // bắt đầu = làm trắc nghiệm mới cho tên vừa nhập, không dùng lại câu trả lời cũ
      h('a', { class: 'btn primary wide', href: '#/test', onclick: () => { store.set('answers', []); store.set('owned', []); } }, W.cta, ' →'),
      done() ? h('div', { class: 'saved' }, h('p', { class: 'small' }, name ? fill(W.saved, { name }) : W.saved_anon),
        h('a', { class: 'btn', href: '#/ket-qua' }, W.cta_result),
        h('button', { class: 'btn', onclick: () => { newProfile(); render(); } }, W.new_profile)) : null))];
}

function quiz() {
  const Q = T.quiz, items = Q.items, ans = answers();
  const gap = ans.findIndex(a => a == null);
  let i = Math.min(gap < 0 ? ans.length : gap, items.length - 1);
  const wrap = h('section', { class: 'quiz' });
  const draw = () => {
    const [t, text] = items[i], cur = answers()[i];
    wrap.replaceChildren(
      h('div', { class: 'qhead' }, h('span', { class: 'small muted' }, fill(Q.progress, { i: i + 1, n: items.length })),
        i > 0 ? h('button', { class: 'link', onclick: () => { i--; draw(); } }, Q.back) : h('span')),
      h('div', { class: 'progress' }, h('i', { style: `width:${100 * i / items.length}%` })),
      h('div', { class: 'qcard card' }, h('p', { class: 'small muted' }, Q.ask), h('h2', {}, text)),
      h('div', { class: 'scale' }, Q.scale.map(([emo, label], v) => h('button', { class: 'opt' + (cur === v ? ' on' : ''),
        onclick: () => {
          const a = answers(); a[i] = v; store.set('answers', a);
          if (i < items.length - 1) { i++; draw(); } else location.hash = '#/ket-qua';
        } }, h('span', { class: 'emo' }, emo), label))));
  };
  draw();
  return [wrap];
}

function jobCard(u, sc) {
  const x = u.x, fit = codeFit(u.code, sc), ai = aiBadge({ impact: familyAi(x, D.byId) });
  return h('a', { class: 'jc', href: `#/nghe/${u.id}` },
    h('div', { class: 'jtop' }, h('span', { class: 'fit' }, fill(T.result.fit, { p: pct(fit) })),
      h('span', { class: 'codes' }, [...u.code].map(t => h('i', { class: `dot rt-${t}`, title: T.types[t].name }, t)))),
    h('h3', {}, u.name), h('p', {}, u.what),
    h('div', { class: 'facts' },
      h('span', {}, h('b', {}, fmt(x.n_open)), T.result.open),
      h('span', {}, h('b', {}, range(x) ? `${range(x)} tr` : '—'), range(x) ? T.result.salary : T.result.salary_none),
      h('span', {}, h('b', {}, D.C.student.ai_scale[ai]), T.job.tile_ai)));
}

const groupHref = f => f.occupations.length ? `#/nhom/${f.id}` : `#/nghe/${f.id}`;

function groupCard({ f, us, fit }) {
  const R = T.result, short = D.C.student.families[f.id]?.short;
  return h('a', { class: 'jc', href: groupHref(f) },
    h('div', { class: 'jtop' }, h('span', { class: 'fit' }, fill(R.group_fit, { p: pct(fit) }))),
    h('h3', {}, f.name), short ? h('p', {}, short) : null,
    h('div', { class: 'facts' },
      h('span', {}, h('b', {}, fmt(f.n_open)), R.open),
      h('span', {}, h('b', {}, range(f) ? `${range(f)} tr` : '—'), range(f) ? R.salary : R.salary_none),
      h('span', {}, h('b', {}, us.length), R.group_jobs)));
}

function groupView(fid) {
  const f = D.families.find(x => x.id === fid && x.in_scope);
  if (!f) { location.hash = '#/ket-qua'; return []; }
  const G = T.group, J = T.job, sc = scores();
  const us = units.filter(u => u.fam === f).sort((a, b) => codeFit(b.code, sc) - codeFit(a.code, sc) || b.x.n_open - a.x.n_open);
  return [h('a', { class: 'back', href: done() ? '#/ket-qua' : '#/' }, G.back),
    h('h1', { class: 'jt' }, f.name), h('p', { class: 'lead' }, D.C.student.families[f.id]?.short),
    h('div', { class: 'tiles' }, h('div', { class: 'tile' }, h('b', {}, fmt(f.n_open)), h('span', {}, J.tile_open)),
      h('div', { class: 'tile' }, h('b', {}, range(f) || '—'), h('span', {}, range(f) ? J.tile_salary : J.tile_salary_none)),
      h('div', { class: 'tile' }, h('b', {}, us.length), h('span', {}, T.result.group_jobs))),
    h('section', { class: 'section' }, h('h2', {}, G.jobs_title), h('p', { class: 'note', style: 'margin:4px 0 12px' }, G.jobs_lead),
      h('div', { class: 'jcs' }, us.map(u => jobCard(u, sc))))];
}

function results() {
  if (!done()) { location.hash = '#/test'; return []; }
  const R = T.result, sc = scores(), code = hollandCode(sc), name = store.get('name', '');
  // nhóm nghề xếp theo nghề hợp nhất trong nhóm
  const groups = D.families.filter(f => f.in_scope).map(f => {
    const us = units.filter(u => u.fam === f);
    return { f, us, fit: Math.max(...us.map(u => codeFit(u.code, sc))) };
  }).sort((a, b) => b.fit - a.fit || b.f.n_open - a.f.n_open);
  const list = h('div', { class: 'jcs' });
  let all = false;
  const more = h('button', { class: 'btn wide', onclick: () => { all = !all; draw(); } });
  const draw = () => { list.replaceChildren(...(all ? groups : groups.slice(0, 6)).map(groupCard));
    more.textContent = all ? R.show_less : fill(R.show_all, { n: groups.length }); };
  draw();
  return [h('p', { class: 'wave' }, name ? fill(R.hi, { name }) : R.hi_anon),
    h('section', { class: 'card me' },
      h('p', { class: 'eyebrow' }, R.code),
      h('div', { class: 'code' }, [...code].map(t => h('span', { class: `big-letter rt-${t}` }, t))),
      h('p', { class: 'note', style: 'margin-top:4px' }, R.code_note),
      hexChart(sc),
      h('div', { class: 'types' }, [...code].map(t => h('div', {}, typeChip(t), h('p', {}, T.types[t].short))))),
    h('section', { class: 'section' }, h('h2', {}, R.groups_title), h('p', { class: 'note', style: 'margin:4px 0 12px' }, R.groups_lead),
      persona() ? h('p', { class: 'insight', style: 'margin:0 0 12px' }, persona().result_lead) : null, list, more),
    h('p', { class: 'note' }, R.disclaimer),
    h('a', { class: 'btn wide', href: '#/test', onclick: () => store.set('answers', []) }, R.redo)];
}

// ---------- chi tiết nghề ----------

// gợi ý theo nhóm người dùng, lấy kỹ năng và vị trí khởi đầu từ dữ liệu của nghề
function personaTip(u) {
  const p = persona();
  if (!p) return null;
  const skills = treeSkills(u.x).slice(0, 3).map(([id]) => D.byId[id].vi).join(', ');
  const entry = (T.paths[u.fam.id] || [])[0]?.[0] || u.name;
  return h('div', { class: 'card tip' }, h('h3', {}, p.tip_title), h('p', {}, fill(p.tip, { skills, entry })),
    p.cta ? h('a', { class: 'btn primary wide', href: `#/nghe/${u.id}/2` }, p.cta) : null);
}

// tin của công ty: tải jobs.json lần đầu bấm vào, rồi giữ lại
let jobsP = null;
const jobs = () => jobsP ??= fetch('../data/jobs.json').then(r => r.json());
const money = ([lo, hi, cur]) => cur === 'VND' ? `${[lo, hi].filter(Boolean).map(tr).join('–')} tr` : `${[lo, hi].filter(Boolean).map(fmt).join('–')} ${cur}`;

function companyItem(unitId, name, n) {
  const J = T.job, body = h('div', { class: 'cojobs' }, h('p', { class: 'note' }, J.co_loading));
  return h('details', { class: 'co', ontoggle: async e => {
    if (!e.currentTarget.open || body.dataset.done) return;
    body.dataset.done = '1';
    try {
      const { units: U, postings: P } = await jobs();
      const ids = U[unitId]?.[name] || [];
      body.replaceChildren(ids.length < n ? h('p', { class: 'small muted' }, fill(J.co_shown, { k: ids.length, n })) : '',
        ...ids.map(id => { const p = P[id], prov = D.provinces.find(v => v.code === p.province)?.name;
          return h('article', { class: 'job' },
            h('a', { href: p.url, target: '_blank', rel: 'noopener' }, p.title, ' ↗'),
            h('p', { class: 'small muted' }, [prov, p.salary ? money(p.salary) : J.co_nosalary, ddmm(p.date), p.source].filter(Boolean).join(' · ')),
            p.skills.length ? h('div', { class: 'chips' }, p.skills.map(sid => D.byId[sid] ? h('span', { class: 'chip' }, D.byId[sid].vi) : null)) : null,
            p.lines.length ? h('ul', { class: 'small' }, p.lines.map(l => h('li', {}, l))) : null); }));
    } catch { body.replaceChildren(h('p', { class: 'note' }, J.co_error)); }
  } }, h('summary', {}, h('span', {}, name), h('small', {}, fill(J.companies_n, { n }))), body);
}

function overview(u) {
  const J = T.job, x = u.x, f = u.fam, sc = scores(), mine = done() ? hollandCode(sc) : '';
  const shared = [...u.code].filter(t => mine.includes(t));
  const steps = T.paths[f.id] || [];
  const ai = aiBadge({ impact: familyAi(x, D.byId) });
  const day = D.C.student.families[f.id]?.day;
  const cos = (x.companies?.[0]?.[1] ?? 0) >= 3 ? x.companies : f.companies || [];
  return [
    done() ? h('div', { class: 'card why' }, h('h3', {}, J.why),
      h('p', {}, shared.length ? fill(J.why_body, { code: u.code, match: shared.map(t => T.types[t].name.toLowerCase()).join(', ') })
        : fill(J.why_none, { code: u.code })),
      h('div', { class: 'chips' }, [...u.code].map(typeChip))) : null,
    personaTip(u),
    h('div', { class: 'tiles' }, h('div', { class: 'tile' }, h('b', {}, fmt(x.n_open)), h('span', {}, J.tile_open)),
      h('div', { class: 'tile' }, h('b', {}, range(x) || '—'), h('span', {}, range(x) ? J.tile_salary : J.tile_salary_none)),
      h('div', { class: 'tile' }, h('b', {}, D.C.student.ai_scale[ai]), h('span', {}, J.tile_ai))),
    h('section', { class: 'section card prose' }, h('h3', {}, J.what), h('p', {}, u.what),
      day ? [h('h3', { style: 'margin-top:12px' }, J.day), h('p', {}, day)] : null),
    steps.length ? h('section', { class: 'section card' }, h('h2', {}, J.path), h('p', { class: 'note', style: 'margin:4px 0 12px' }, J.path_lead),
      h('ol', { class: 'ladder' }, steps.map(([label, id]) => {
        const s = id ? unit(id) : null, pay = s?.x.salary_median_vnd;
        return h('li', { class: id === u.id ? 'here' : '' },
          s ? h('a', { href: `#/nghe/${id}` }, label) : h('span', {}, label),
          h('small', {}, id === u.id ? J.path_you + ' · ' : '', pay ? fill(J.path_pay, { p: tr(pay) }) : s ? J.path_nodata : ''));
      }))) : null,
    h('section', { class: 'section card' }, h('h2', {}, J.companies), h('p', { class: 'note', style: 'margin:4px 0 12px' }, J.companies_lead),
      // nghề ít tin (công ty đầu chỉ 2 tin) thì xem công ty của cả nhóm nghề
      cos.length ? [cos !== x.companies ? h('p', { class: 'small muted' }, fill(J.companies_family, { family: f.name })) : null,
        h('div', { class: 'cos' }, cos.map(([n, c]) => companyItem(cos === x.companies ? u.id : f.id, n, c)))]
        : h('p', { class: 'note' }, J.companies_none)),
  ];
}

function market(u) {
  const J = T.job, x = u.x, f = u.fam, S = D.C.student;
  const withSal = units.filter(v => v.x.salary_median_vnd);
  const maxPay = Math.ceil(Math.max(...units.map(v => v.x.salary_range_vnd?.[1] || 0)) / 1e7) * 1e7;
  const rank = x.salary_median_vnd ? withSal.filter(v => v.x.salary_median_vnd < x.salary_median_vnd).length : null;
  const provs = Object.entries(f.by_province).filter(([c]) => D.provinces.some(p => p.code === c && p.region))
    .sort((a, b) => b[1] - a[1]).slice(0, 5);
  const tree = treeSkills(x).slice(0, 10);
  const ins = salaryInsight(f), basePay = ins ? (f.skills.find(s => s[0] === ins.raise) || [])[3] : null;
  const ai = aiBadge({ impact: familyAi(x, D.byId) });
  const quotes = (D.scenes[f.id] || []).slice(0, 2);
  return [
    h('section', { class: 'card' }, h('h2', {}, J.salary_title),
      x.salary_range_vnd ? [h('p', { class: 'note', style: 'margin:4px 0 14px' }, fill(J.salary_lead, { n: fmt(x.salary_n) })), salaryBand(x, maxPay),
        h('p', { class: 'note' }, fill(J.salary_scale, { max: tr(maxPay) })),
        rank != null ? h('p', { class: 'insight' }, '💡 ', fill(J.salary_rank, { k: rank, n: withSal.length - 1 })) : null]
        : h('p', { class: 'note' }, J.salary_none)),
    h('section', { class: 'section card' }, h('h2', {}, J.skills_title), h('p', { class: 'note', style: 'margin:4px 0 12px' }, J.skills_lead),
      h('table', { class: 'skillbars' }, h('tbody', {}, tree.map(([sid, w]) => { const s = D.byId[sid], t = trend(s.history);
        // chọn một kỹ năng: mở / đóng biểu đồ 12 tháng ngay dưới dòng đó
        const toggle = e => { const row = e.currentTarget, open = row.nextElementSibling?.classList.contains('trendrow');
          row.parentNode.querySelectorAll('.trendrow').forEach(r => r.remove());
          row.parentNode.querySelectorAll('tr.on').forEach(r => { r.classList.remove('on'); r.setAttribute('aria-expanded', 'false'); });
          if (open) return;
          const chart = trendSvg(s, { w: 420, h: 190, axes: true });
          row.classList.add('on'); row.setAttribute('aria-expanded', 'true');
          row.after(h('tr', { class: 'trendrow' }, h('td', { colspan: 2 }, chart
            ? [chart, h('p', { class: 'note' }, fill(J.trend_note, { source: chart.dataset.source }))] : h('p', { class: 'note' }, J.trend_none)))); };
        return h('tr', { class: 'pickable', tabindex: 0, role: 'button', 'aria-expanded': 'false', onclick: toggle,
          onkeydown: e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(e); } } },
          h('td', {}, s.vi, ' ', t !== 'none' ? h('span', { class: `tr tr-${t}`, title: T.trend_label[t] }, T.trend[t]) : null),
          h('td', {}, bar(w, tree[0][1], `${k10(w)}/10`))); })))),
    ins && basePay ? h('section', { class: 'section card' }, h('h2', {}, J.pay_title),
      h('p', { class: 'insight' }, '💡 ', fill(S.insight, { entry: D.byId[ins.entry].vi, raise: D.byId[ins.raise].vi, raisePay: tr(ins.raisePay), basePay: tr(basePay) }))) : null,
    provs.length ? h('section', { class: 'section card' }, h('h2', {}, J.where), h('p', { class: 'note', style: 'margin:4px 0 12px' }, J.where_lead),
      h('table', {}, h('tbody', {}, provs.map(([c, n]) => h('tr', {}, h('td', {}, D.provinces.find(p => p.code === c).name),
        h('td', {}, bar(n / f.n_open, provs[0][1] / f.n_open, pct(n / f.n_open)))))))) : null,
    h('section', { class: 'section card' }, h('h2', {}, J.ai_title),
      h('p', {}, h('span', { class: `chip ${ai === 'high' ? 'warn' : ''}` }, S.ai_scale[ai]), ' ', S.ai_body[ai]),
      h('h3', { style: 'margin-top:14px' }, J.ai_chart), h('p', { class: 'small muted' }, D.C.common.ai_trend.lead, ' (', f.name, ')'),
      aiLine(f), h('p', { class: 'note' }, D.C.common.ai_trend.note), h('p', { class: 'note' }, J.ai_monthly)),
    quotes.length ? h('section', { class: 'section' }, h('h2', { style: 'margin-bottom:10px' }, J.quotes),
      quotes.map(q => h('figure', { class: 'quote' }, h('q', {}, q.quote), h('small', {}, fill(J.quote_src, { source: q.source, date: ddmm(q.date) }))))) : null,
  ];
}

// thư viện đọc PDF / Word chỉ tải khi người dùng chọn file
const loadScript = src => new Promise((ok, fail) => document.head.append(h('script', { src, onload: ok, onerror: fail })));
async function readCv(file) {
  if (/\.pdf$/i.test(file.name)) {
    if (!window.pdfjsLib) await loadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js');
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    const pdf = await pdfjsLib.getDocument({ data: await file.arrayBuffer() }).promise;
    let out = '';
    for (let p = 1; p <= pdf.numPages; p++) out += (await (await pdf.getPage(p)).getTextContent()).items.map(i => i.str).join(' ') + '\n';
    return out;
  }
  if (/\.docx$/i.test(file.name)) {
    if (!window.mammoth) await loadScript('https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js');
    return (await mammoth.extractRawText({ arrayBuffer: await file.arrayBuffer() })).value;
  }
  return file.text();
}

function fitCheck(u) {
  const F = T.fit, x = u.x, tree = treeSkills(x), A = D.meta.assumptions;
  const box = h('div'), cvOut = h('div', { class: 'cvout', 'aria-live': 'polite' });
  const draw = () => {
    const own = owned(), c = coverage(x, own), n = unlocked(x, own, A);
    const missing = tree.filter(([id]) => !own.has(id)).slice(0, 3);
    box.replaceChildren(
      h('div', { class: 'card' }, h('h2', {}, F.title), h('p', { class: 'note', style: 'margin:4px 0 12px' }, F.lead),
        h('div', { class: 'gauge' }, h('b', {}, pct(c)), h('span', {}, F.meter)),
        h('div', { class: 'meter' }, h('i', { style: `width:${100 * c}%` })),
        h('p', { class: 'small' }, own.size && n ? fill(F.unlock, { n: fmt(n), total: fmt(x.n_open) }) : F.unlock_none),
        h('div', { class: 'chips pick' }, tree.map(([id, w]) => h('button', { class: 'skill' + (own.has(id) ? ' on' : ''), 'aria-pressed': String(own.has(id)),
          onclick: () => { const o = owned(); o.has(id) ? o.delete(id) : o.add(id); store.set('owned', [...o]); draw(); } },
          own.has(id) ? '✓ ' : '+ ', D.byId[id].vi, h('small', {}, ` ${k10(w)}/10`)))),
        own.size ? h('button', { class: 'link', onclick: () => { store.set('owned', []); draw(); cvOut.replaceChildren(); } }, F.reset) : null),
      h('div', { class: 'card section' }, h('h3', {}, F.next),
        missing.length ? h('ol', { class: 'next' }, missing.map(([id, w]) => h('li', {}, fill(F.next_item, { skill: D.byId[id].vi, k: k10(w) }))))
          : h('p', {}, F.all_set)));
  };
  const scan = text => {
    if (!text.trim()) { cvOut.replaceChildren(h('p', { class: 'note' }, F.cv_empty)); return; }
    const found = cvSkills(text, M), o = owned();
    const inTree = tree.filter(([id]) => found.has(id));
    inTree.forEach(([id]) => o.add(id)); store.set('owned', [...o]);
    const cvCov = coverage(x, found), treeIds = new Set(tree.map(([id]) => id));
    const other = [...found].filter(id => !treeIds.has(id)).map(id => D.byId[id].vi);
    draw();
    cvOut.replaceChildren(h('div', { class: 'cvres' },
      h('p', { class: 'big' }, pct(cvCov)), h('p', {}, fill(F.cv_result, { p: pct(cvCov) })),
      found.size ? null : h('p', { class: 'note' }, fill(F.cv_none, { k: D.meta.taxonomy.skills })),
      inTree.length ? [h('h3', {}, fill(F.cv_found, { n: inTree.length })), h('div', { class: 'chips' }, inTree.map(([id]) => h('span', { class: 'chip up' }, '✓ ', D.byId[id].vi)))] : null,
      h('h3', {}, F.cv_missing), h('div', { class: 'chips' }, tree.filter(([id]) => !found.has(id)).slice(0, 6).map(([id]) => h('span', { class: 'chip down' }, D.byId[id].vi))),
      other.length ? [h('h3', {}, F.cv_other), h('p', { class: 'small muted' }, other.join(', '))] : null));
  };
  const fileIn = h('input', { type: 'file', accept: '.pdf,.docx,.txt', class: 'sr', id: 'cvfile', onchange: async e => {
    const file = e.target.files[0]; if (!file) return;
    cvOut.replaceChildren(h('p', { class: 'note' }, F.cv_reading));
    try { scan(await readCv(file)); } catch { cvOut.replaceChildren(h('p', { class: 'note' }, F.cv_error)); }
    e.target.value = '';
  } });
  const paste = h('textarea', { rows: 4, placeholder: F.cv_paste_ph });
  draw();
  return [box, h('section', { class: 'section card' }, h('h2', {}, '📄 ', F.cv_title), h('p', { class: 'note', style: 'margin:4px 0 12px' }, F.cv_lead),
    fileIn, h('label', { for: 'cvfile', class: 'btn primary wide' }, F.cv_pick),
    h('details', { class: 'paste' }, h('summary', {}, F.cv_paste), paste, h('button', { class: 'btn wide', onclick: () => scan(paste.value) }, F.cv_scan)),
    cvOut)];
}

function jobView(id, tab) {
  const u = unit(id);
  if (!u) { location.hash = '#/ket-qua'; return []; }
  const J = T.job, t = tab == null ? persona()?.tab ?? 0 : Number(tab) || 0;
  const body = [overview, market, fitCheck][t](u);
  const back = u.fam.occupations.length ? [`#/nhom/${u.fam.id}`, fill(J.back_group, { family: u.fam.name })]
    : [done() ? '#/ket-qua' : '#/', T.group.back];
  return [h('a', { class: 'back', href: back[0] }, back[1]),
    h('p', { class: 'eyebrow' }, u.fam.name), h('h1', { class: 'jt' }, u.name),
    h('nav', { class: 'tabs', role: 'tablist' }, J.tabs.map((label, i) => h('a', { role: 'tab', href: `#/nghe/${id}/${i}`,
      'aria-selected': String(i === t), class: i === t ? 'on' : '' }, label))),
    h('div', { class: 'tabbody' }, body)];
}

function render() {
  const [, page, a, b] = (location.hash || '#/').split('/');
  const nodes = ({ test: quiz, 'ket-qua': results, nhom: () => groupView(a), nghe: () => jobView(a, b) }[page] || welcome)();
  if (nodes.length) app.replaceChildren(...nodes.filter(Boolean));
}
window.addEventListener('hashchange', () => { window.scrollTo(0, 0); render(); });

Promise.all([load(), fetch('../copy.hn.vi.json').then(r => r.json()), fetch('../data/scenes.json').then(r => r.json())]).then(([d, t, sc]) => {
  D = d; T = t; D.scenes = sc; M = matcher(D.skills);
  // một "nghề" = nghề cụ thể nếu nhóm đã tách nghề, không thì cả nhóm nghề
  units = D.families.filter(f => f.in_scope).flatMap(f => (f.occupations.length ? f.occupations : [f])
    .map(x => ({ id: x.id, name: x.name, fam: f, x, ...T.units[x.id] })));
  document.getElementById('reset').onclick = () => { newProfile(); location.hash = '#/'; render(); };
  document.getElementById('theme').onclick = () => {
    const dark = matchMedia('(prefers-color-scheme: dark)').matches;
    const cur = document.documentElement.dataset.theme || (dark ? 'dark' : 'light');
    document.documentElement.dataset.theme = cur === 'dark' ? 'light' : 'dark';
  };
  render();
}).catch(e => { app.textContent = 'Không tải được dữ liệu (' + e.message + ').'; });
