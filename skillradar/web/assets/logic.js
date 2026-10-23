// Phép tính thuần cho trang học sinh (không đụng DOM) — có test: tests/test_logic.mjs
// Công thức tiếp cận việc làm theo docs/METRICS.md §2, hằng số lấy từ meta.json (assumptions).

const TREE_SIZE = 12;   // số kỹ năng hiển thị trên cây của một nghề

export function treeSkills(family) {
  return family.skills.slice(0, TREE_SIZE);   // [[skill_id, weight], ...] đã xếp giảm dần
}

export function coverage(family, owned) {
  const tree = treeSkills(family);
  const total = tree.reduce((s, [, w]) => s + w, 0);
  const have = tree.reduce((s, [id, w]) => s + (owned.has(id) ? w : 0), 0);
  return total ? have / total : 0;
}

export function applyRate(c, a) {
  return a.apply_rate_ceiling / (1 + Math.exp(-(c - a.apply_rate_midpoint) / a.apply_rate_width));
}

export function unlocked(family, owned, a) {
  return Math.round(family.n_open * applyRate(coverage(family, owned), a));
}

// Câu trả lời -> 3 nghề gợi ý kèm lý do. answers: [{text, families}] (đã chọn)
export function scoreQuiz(answers, families, n = 3) {
  const score = new Map(), why = new Map();
  for (const ans of answers) for (const f of ans.families) {
    score.set(f, (score.get(f) || 0) + 1);
    why.set(f, [...(why.get(f) || []), ans.text]);
  }
  const open = new Map(families.map(f => [f.id, f.n_open]));
  return [...score.keys()].filter(f => open.has(f))
    // hòa điểm thì nghề nhiều tin hơn đứng trước
    .sort((x, y) => score.get(y) - score.get(x) || open.get(y) - open.get(x))
    .slice(0, n).map(id => ({ id, score: score.get(id), reasons: why.get(id) }));
}

export function tier(share) {
  return share >= 0.2 ? 'common' : share >= 0.05 ? 'valuable' : 'rare';
}

export function aiBadge(ai) {
  if (!ai || ai.impact == null) return 'none';
  return ai.impact < 0.3 ? 'low' : ai.impact <= 0.5 ? 'mid' : 'high';
}

// Mô tả 12 tháng qua từ chuỗi lịch sử dài nhất: TB 3 tháng cuối so với TB 3 tháng đầu cửa sổ
export function trend(history) {
  const series = Object.values(history || {}).sort((a, b) => b.length - a.length)[0] || [];
  const last12 = series.slice(-12);
  if (last12.length < 8) return 'none';
  const avg = xs => xs.reduce((s, p) => s + p[1], 0) / xs.length;
  const a = avg(last12.slice(0, 3)), b = avg(last12.slice(-3));
  if (a === 0) return b > 0 ? 'up' : 'flat';
  const rel = (b - a) / a;
  return rel > 0.15 ? 'up' : rel < -0.15 ? 'down' : 'flat';
}

// Mức ảnh hưởng của AI lên nghề: trung bình mức ảnh hưởng của các kỹ năng, trọng số theo tỷ lệ tin
export function familyAi(family, skillsById) {
  let s = 0, w = 0;
  for (const [id, wt] of treeSkills(family)) {
    const sc = skillsById[id]?.ai?.impact;
    if (sc != null) { s += sc * wt; w += wt; }
  }
  return w ? s / w : null;
}

// Kỹ năng nên học tiếp: thêm thẻ nào làm tổng số tin mở khóa tăng nhiều nhất
export function bestNext(families, owned, a, k = 3) {
  const total = set => families.reduce((s, f) => s + unlocked(f, set, a), 0);
  const base = total(owned);
  const cands = new Set(families.flatMap(f => treeSkills(f).map(([id]) => id)).filter(id => !owned.has(id)));
  return [...cands].map(id => ({ id, gain: total(new Set([...owned, id])) - base }))
    .filter(x => x.gain > 0).sort((x, y) => y.gain - x.gain).slice(0, k);
}

// --- trò chơi (v2) ---

// Độ hiếm theo tỷ lệ toàn thị trường: thẻ hiếm = ít tin đòi hỏi
export function rarity(overallShare) {
  return overallShare >= 0.15 ? 'common' : overallShare >= 0.03 ? 'valuable' : 'rare';
}

// Khiên AI 1–5: càng khó bị AI thay càng nhiều khiên. null khi chưa có điểm.
export function shields(ai) {
  if (!ai || ai.impact == null) return null;
  return Math.max(1, Math.min(5, Math.round((1 - ai.impact) * 5)));
}

// Cấp độ trong một nghề theo số thẻ của cây kỹ năng nghề đó
export function level(family, owned) {
  const n = treeSkills(family).filter(([id]) => owned.has(id)).length;
  const lv = n >= 9 ? 5 : n >= 6 ? 4 : n >= 4 ? 3 : n >= 2 ? 2 : 1;
  return { lv, cards: n, nextAt: [2, 4, 6, 9, null][lv - 1] };
}

// "1 trong K tin": dễ hiểu hơn số tuyệt đối. null khi chưa mở khóa tin nào.
export function oneIn(family, owned, a) {
  const n = unlocked(family, owned, a);
  return n > 0 ? Math.max(1, Math.round(family.n_open / n)) : null;
}

// "Vé vào cửa" (nhiều tin cần, lương không cao hơn) vs "thứ tăng lương" (chênh lương lớn nhất, ≥ 2 triệu)
export function salaryInsight(family) {
  const withSal = family.skills.filter(s => s[2] != null && s[3] != null);
  const entry = withSal.filter(s => s[2] <= s[3]).sort((x, y) => y[1] - x[1])[0];
  const raise = withSal.filter(s => s[2] - s[3] >= 2e6).sort((x, y) => (y[2] - y[3]) - (x[2] - x[3]))[0];
  return entry && raise ? { entry: entry[0], entryPay: entry[2], raise: raise[0], raisePay: raise[2] } : null;
}

// Link thách đấu: bộ bài nằm trong đường dẫn, không cần máy chủ / tài khoản
export function encodeChallenge(familyId, ids) {
  return `#/thach/${familyId}/${[...ids].sort().join('.')}`;
}
export function decodeChallenge(hash) {
  const m = /^#\/thach\/([a-z-]+)\/([a-z0-9.+#-]+)$/.exec(hash || '');
  return m ? { family: m[1], ids: m[2].split('.').filter(Boolean) } : null;
}
