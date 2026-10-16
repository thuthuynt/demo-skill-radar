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
  if (!ai || ai.score == null) return 'none';
  return ai.score < 0.3 ? 'low' : ai.score <= 0.5 ? 'mid' : 'high';
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

// Mức độ "đụng" AI của nghề: trung bình điểm AI các kỹ năng, trọng số theo tỷ lệ tin
export function familyAi(family, skillsById) {
  let s = 0, w = 0;
  for (const [id, wt] of treeSkills(family)) {
    const sc = skillsById[id]?.ai?.score;
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
