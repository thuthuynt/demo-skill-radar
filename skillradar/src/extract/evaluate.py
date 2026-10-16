"""Đo chất lượng trích kỹ năng trên tập chuẩn gán tay.

    python -m src.extract.evaluate

Precision / recall / F1 (micro, theo cặp tin × kỹ năng), tách vi / en / mixed, kèm cỡ mẫu.
Ghi kết quả ra logs/extract_eval.json để trang trạng thái dùng.
"""

import json
import sys

import duckdb

from src.build.silver import DB
from src.config import LOG_DIR
from src.extract.goldset import GOLD, read_jsonl
from src.extract.run import compile_matchers, load_dictionary, match


def prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3),
            "f1": round(2 * p * r / (p + r), 3) if p + r else 0.0}


def main() -> int:
    gold = read_jsonl(GOLD)
    if not gold:
        sys.exit(f"Chưa có nhãn trong {GOLD}. Chạy: python -m src.extract.goldset serve")
    entries, dim = load_dictionary()
    matchers = compile_matchers(entries, {s for s, r in dim.items() if r["skill_type"] == "domain"})
    con = duckdb.connect(str(DB), read_only=True)
    text = dict(((pid, (t, d)) for pid, t, d in con.execute(
        "SELECT posting_id, title, description FROM posting WHERE posting_id IN (SELECT unnest(?))",
        [[g["posting_id"] for g in gold]]).fetchall()))
    con.close()

    counts = {}
    for g in gold:
        if g["posting_id"] not in text:
            continue
        pred = set(match(*text[g["posting_id"]], matchers))
        truth = set(g["skills"])
        for grp in (g["lang"], "all"):
            c = counts.setdefault(grp, {"n": 0, "tp": 0, "fp": 0, "fn": 0})
            c["n"] += 1
            c["tp"] += len(pred & truth)
            c["fp"] += len(pred - truth)
            c["fn"] += len(truth - pred)

    result = {grp: {"n": c["n"], **prf(c["tp"], c["fp"], c["fn"])} for grp, c in counts.items()}
    print(f"{'nhóm':6} {'n':>4} {'P':>6} {'R':>6} {'F1':>6}")
    for grp in ("vi", "en", "mixed", "all"):
        if grp in result:
            r = result[grp]
            print(f"{grp:6} {r['n']:4d} {r['precision']:6.3f} {r['recall']:6.3f} {r['f1']:6.3f}")
    (LOG_DIR / "extract_eval.json").write_text(json.dumps(
        {**result, "labelers": 1, "note": "một người gán nhãn, chưa đo được độ đồng thuận"},
        ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
