// node --test tests/test_logic.mjs  — phép tính trang học sinh, trên số liệu thật đã xuất
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { coverage, applyRate, unlocked, scoreQuiz, tier, aiBadge, trend, bestNext, treeSkills } from '../web/assets/logic.js';

const load = n => JSON.parse(readFileSync(new URL(`../web/data/${n}`, import.meta.url)));
const families = load('families.json');
const A = load('meta.json').assumptions;
const it = families.find(f => f.id === 'cntt');

test('coverage 0 khi chưa có kỹ năng, 1 khi có đủ cây', () => {
  assert.equal(coverage(it, new Set()), 0);
  assert.equal(coverage(it, new Set(treeSkills(it).map(([id]) => id))), 1);
});

test('số tin mở khóa không vượt trần giả định và tăng theo kỹ năng', () => {
  const all = new Set(treeSkills(it).map(([id]) => id));
  const full = unlocked(it, all, A);
  assert.ok(full <= Math.round(it.n_open * A.apply_rate_ceiling));
  assert.ok(unlocked(it, new Set([treeSkills(it)[0][0]]), A) < full);
  assert.ok(Math.abs(applyRate(A.apply_rate_midpoint, A) - A.apply_rate_ceiling / 2) < 1e-9);
});

test('trắc nghiệm: nghề được chọn nhiều nhất đứng đầu, kèm lý do', () => {
  const ans = [{ text: 'số liệu', families: ['ke-toan', 'cntt'] }, { text: 'máy tính', families: ['cntt'] }];
  const r = scoreQuiz(ans, families);
  assert.equal(r[0].id, 'cntt');
  assert.deepEqual(r[0].reasons, ['số liệu', 'máy tính']);
  assert.equal(r.length, 2);
});

test('hạng thẻ, huy hiệu AI, xu hướng', () => {
  assert.equal(tier(0.3), 'common'); assert.equal(tier(0.1), 'valuable'); assert.equal(tier(0.01), 'rare');
  assert.equal(aiBadge(null), 'none'); assert.equal(aiBadge({ score: 0.6 }), 'high');
  const flat = { s: Array.from({ length: 12 }, (_, i) => [`m${i}`, 0.1]) };
  const up = { s: Array.from({ length: 12 }, (_, i) => [`m${i}`, 0.1 + 0.02 * i]) };
  assert.equal(trend(flat), 'flat'); assert.equal(trend(up), 'up'); assert.equal(trend({ s: [['m', 1]] }), 'none');
});

test('gợi ý học tiếp chỉ đưa kỹ năng chưa có và có lợi', () => {
  const owned = new Set([treeSkills(it)[0][0]]);
  const next = bestNext(families, owned, A);
  assert.ok(next.length > 0);
  for (const n of next) { assert.ok(!owned.has(n.id)); assert.ok(n.gain > 0); }
});
