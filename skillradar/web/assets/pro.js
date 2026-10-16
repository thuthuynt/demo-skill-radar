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
