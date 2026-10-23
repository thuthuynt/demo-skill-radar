// Dùng chung cho trang nhà trường và cơ quan quản lý: tải dữ liệu, khung trang, bảng, CSV.
export function h(tag, props = {}, ...kids) {
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
export const fill = (s, v) => s.replace(/\{(\w+)\}/g, (_, k) => v[k] ?? '');
export const fmt = n => Number(n).toLocaleString('vi-VN');
export const pct = (x, d = 0) => (100 * x).toLocaleString('vi-VN', { maximumFractionDigits: d }) + '%';
export const tr = vnd => vnd == null ? '—' : (vnd / 1e6).toLocaleString('vi-VN', { maximumFractionDigits: 1 });
export const ddmm = d => d.split('-').reverse().slice(0, 2).join('/');
export const store = {
  get(k, d) { try { return JSON.parse(localStorage.getItem('srpro:' + k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem('srpro:' + k, JSON.stringify(v)); } catch { /* chế độ riêng tư */ } },
};

export async function load() {
  const get = p => fetch(p).then(r => { if (!r.ok) throw new Error(p); return r.json(); });
  const [C, meta, skills, families, provinces, status] = await Promise.all(
    ['../copy.pro.vi.json', '../data/meta.json', '../data/skills.json', '../data/families.json',
     '../data/provinces.json', '../data/status.json'].map(get));
  return { C, meta, skills, families, provinces, status, byId: Object.fromEntries(skills.map(s => [s.id, s])) };
}

// thanh ngang một màu, nhãn số trực tiếp (không cần chú giải)
export const bar = (value, max, label, cls = '') =>
  h('span', { class: 'bar ' + cls }, h('i', { style: `width:${Math.max(2, 120 * value / (max || 1))}px` }), h('span', {}, label));

export function tiles(items) {
  return h('div', { class: 'tiles' }, items.map(([v, l]) => h('div', { class: 'tile' }, h('b', {}, v), h('span', {}, l))));
}

export function commonTiles(D) {
  const C = D.C.common, m = D.meta;
  return [[fmt(m.n_open), C.tile_open], [m.days_collected, C.tile_days], [m.taxonomy.skills, C.tile_skills],
    [`${m.history_months.itviec ?? 0} / ${m.history_months.vietnamworks ?? 0}`, C.tile_hist]];
}

export function frame(D, page) {
  const C = D.C.common;
  document.getElementById('aud').textContent = D.C[page].aud;
  document.querySelectorAll('nav a').forEach(a => { if (a.dataset.page === page) a.setAttribute('aria-current', 'page'); });
  const dates = D.meta.sources.map(s => `${s.source} ${ddmm(s.latest)}`).join(', ');
  document.getElementById('foot').replaceChildren(
    h('span', {}, fill(C.updated, { date: new Date(D.meta.generated_at).toLocaleDateString('vi-VN') })),
    h('span', {}, fill(C.sources, { dates })),
    h('a', { href: '../data.html' }, C.data_link), h('a', { href: '../' }, C.student_link));
  document.getElementById('theme').onclick = () => {
    const dark = matchMedia('(prefers-color-scheme: dark)').matches;
    const cur = document.documentElement.dataset.theme || (dark ? 'dark' : 'light');
    document.documentElement.dataset.theme = cur === 'dark' ? 'light' : 'dark';
  };
}

export function method(D) {
  const C = D.C.common;
  return h('details', { class: 'method card' }, h('summary', {}, C.method), h('ul', {}, C.method_body.map(t => h('li', {}, t))));
}

// CSV có BOM để Excel mở đúng tiếng Việt
export function csvButton(label, name, rowsFn) {
  return h('button', { class: 'btn', onclick: () => {
    const esc = v => { const s = v == null ? '' : String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
    const text = '﻿' + rowsFn().map(r => r.map(esc).join(',')).join('\n');
    const a = h('a', { href: URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8' })), download: name });
    document.body.append(a); a.click(); a.remove();
  } }, label);
}

// Thay đổi tỷ trọng 12 tháng qua trên chuỗi lưu trữ dài nhất: TB 3 tháng cuối − TB 3 tháng đầu cửa sổ
export function change12(skill) {
  const [src, series] = Object.entries(skill.history || {}).sort((a, b) => b[1].length - a[1].length)[0] || [];
  const s = (series || []).slice(-12);
  if (s.length < 8) return null;
  const avg = xs => xs.reduce((a, p) => a + p[1], 0) / xs.length;
  const first = avg(s.slice(0, 3)), last = avg(s.slice(-3));
  return { source: src, delta: last - first, now: last, beats: skill.forecast?.[src]?.beats_naive ?? null };
}

// Đường xu hướng: 12 điểm tháng cuối của chuỗi lưu trữ dài nhất (cùng chuỗi với trend() và change12()).
// Tháng không có dữ liệu để trống, không nối qua, đúng nguyên tắc không nội suy.
export function trendSvg(skill, { w = 96, h = 26, axes = false } = {}) {
  const [src, series] = Object.entries(skill.history || {}).sort((a, b) => b[1].length - a[1].length)[0] || [];
  const pts = (series || []).slice(-12);
  if (pts.length < 2) return null;
  const mi = m => { const [y, mo] = m.split('-').map(Number); return y * 12 + mo - 1; };
  const m0 = mi(pts[0][0]), m1 = mi(pts.at(-1)[0]);
  const pad = axes ? { l: 40, r: 10, t: 10, b: 24 } : { l: 3, r: 3, t: 3, b: 3 };
  const ymax = Math.max(...pts.map(p => p[1])) * 1.15 || 0.01;
  const step = ymax > 0.3 ? 0.1 : ymax > 0.12 ? 0.05 : ymax > 0.05 ? 0.02 : 0.01;
  const top = Math.ceil(ymax / step) * step;
  const X = m => pad.l + (mi(m) - m0) / Math.max(1, m1 - m0) * (w - pad.l - pad.r);
  const Y = v => h - pad.b - v / top * (h - pad.t - pad.b);
  const segs = [];
  pts.forEach((p, i) => (i && mi(p[0]) - mi(pts[i - 1][0]) === 1 ? segs.at(-1) : segs[segs.push([]) - 1]).push(p));
  const line = segs.map(s => `<polyline points="${s.map(p => `${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join(' ')}" fill="none" stroke="var(--water)" stroke-width="${axes ? 2.5 : 1.8}" stroke-linecap="round" stroke-linejoin="round"/>`).join('');
  const lbl = m => m.slice(5) + '/' + m.slice(2, 4);
  const pctl = v => (100 * v).toLocaleString('vi-VN', { maximumFractionDigits: 1 }) + '%';
  let grid = '', xl = '';
  if (axes) {
    for (let v = 0; v <= top + 1e-9; v += step) grid += `<line x1="${pad.l}" x2="${w - pad.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text x="${pad.l - 6}" y="${Y(v) + 4}" text-anchor="end" font-size="11" fill="var(--muted)">${pctl(v)}</text>`;
    const every = m1 - m0 > 8 ? 2 : 1;
    for (let k = m0; k <= m1; k += every) { const m = `${Math.floor(k / 12)}-${String(k % 12 + 1).padStart(2, '0')}`; xl += `<text x="${X(m)}" y="${h - 6}" text-anchor="middle" font-size="11" fill="var(--muted)">${lbl(m)}</text>`; }
  }
  const dots = pts.map((p, i) => `<circle cx="${X(p[0])}" cy="${Y(p[1])}" r="${axes ? 4 : i === pts.length - 1 ? 2.6 : 0}" fill="var(--water)"><title>${lbl(p[0])}: ${pctl(p[1])} (${p[2]}/${p[3]} tin)</title></circle>`).join('');
  const wrap = document.createElement('span');
  wrap.className = axes ? 'trendchart' : 'spark';
  wrap.innerHTML = `<svg viewBox="0 0 ${w} ${h}" ${axes ? 'width="100%"' : `width="${w}" height="${h}"`} role="img" aria-label="Tỷ trọng 12 tháng, nguồn ${src}">${grid}${xl}${line}${dots}</svg>`;
  wrap.dataset.source = src;
  return wrap;
}
