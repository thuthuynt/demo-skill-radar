"""Tập chuẩn đo F1: lấy mẫu và gán nhãn tay.

    python -m src.extract.goldset sample   # chọn 150 tin -> data/goldset_todo.jsonl
    python -m src.extract.goldset serve    # mở http://localhost:8765 để gán nhãn -> data/goldset.jsonl

Giao diện KHÔNG gợi ý kết quả của bộ trích (không tích sẵn, không tô sáng), để nhãn
độc lập với chương trình — nếu gợi ý, người gán sẽ thiên về đồng ý và F1 bị thổi phồng.
"""

import csv
import hashlib
import json
import sys
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import duckdb

from src.build.silver import DB
from src.config import ROOT
from src.extract.run import SEED, sections

TODO = ROOT / "data" / "goldset_todo.jsonl"
GOLD = ROOT / "data" / "goldset.jsonl"
UI = Path(__file__).with_name("goldset_ui.html")
PER_LANG = 50
PORT = 8765


def sample() -> int:
    con = duckdb.connect(str(DB), read_only=True)
    rows = con.execute("""
        SELECT posting_id, lang, source, job_family_id, title, description FROM posting
        WHERE NOT is_repost AND in_scope AND lang IN ('vi', 'en', 'mixed')
          AND length(description) > 300""").fetchall()
    con.close()
    # thứ tự cố định theo hash -> chạy lại ra đúng mẫu cũ
    rows.sort(key=lambda r: hashlib.sha1(r[0].encode()).hexdigest())
    picked = []
    for lang in ("vi", "en", "mixed"):
        # xoay vòng theo (nhóm nghề, nguồn) để mẫu trải đều, không dồn vào nhóm đông
        buckets = defaultdict(list)
        for r in rows:
            if r[1] == lang:
                buckets[(r[3], r[2])].append(r)
        keys, chosen = sorted(buckets), []
        while len(chosen) < PER_LANG and any(buckets.values()):
            for k in keys:
                if buckets[k] and len(chosen) < PER_LANG:
                    chosen.append(buckets[k].pop(0))
        assert len(chosen) == PER_LANG, f"chỉ có {len(chosen)} tin {lang}"
        picked += chosen
    with open(TODO, "w", encoding="utf-8") as f:
        for pid, lang, src, fam, title, desc in picked:
            f.write(json.dumps({"posting_id": pid, "lang": lang, "source": src, "job_family_id": fam,
                                "title": title, "sections": sections(desc)}, ensure_ascii=False) + "\n")
    print(f"{len(picked)} tin -> {TODO}")
    return 0


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def skills() -> list[dict]:
    with open(SEED, encoding="utf-8") as f:
        return [{"id": r["skill_id"], "vi": r["name_vi"], "en": r["name_en"], "group": r["skill_group"],
                 "aliases": r["aliases"].replace("\\b", "")} for r in csv.DictReader(f)]


def save_label(label: dict) -> None:
    """Ghi đè nhãn của tin này, giữ nguyên các tin khác; ghi file tạm rồi đổi tên để không hỏng file."""
    labels = {r["posting_id"]: r for r in read_jsonl(GOLD)}
    labels[label["posting_id"]] = label
    tmp = GOLD.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for r in labels.values():
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(GOLD)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send(200, UI.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/state":
            state = {"items": read_jsonl(TODO), "skills": skills(),
                     "labels": {r["posting_id"]: r for r in read_jsonl(GOLD)}}
            self._send(200, json.dumps(state, ensure_ascii=False).encode(), "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/label":
            return self._send(404, b"not found", "text/plain")
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        known = {s["id"] for s in skills()}
        todo = {r["posting_id"]: r for r in read_jsonl(TODO)}
        # chỉ nhận tin trong mẫu và mã kỹ năng có trong danh mục
        if data.get("posting_id") not in todo or not set(data.get("skills", [])) <= known:
            return self._send(400, b"posting_id hoac skill_id khong hop le", "text/plain")
        save_label({"posting_id": data["posting_id"], "lang": todo[data["posting_id"]]["lang"],
                    "skills": sorted(set(data["skills"])),
                    "missing": [m.strip() for m in data.get("missing", []) if m.strip()],
                    "labeler": "thuy"})
        self._send(200, b"{}", "application/json")

    def log_message(self, *args):
        pass


def serve() -> int:
    if not TODO.exists():
        sys.exit("Chưa có mẫu. Chạy: python -m src.extract.goldset sample")
    print(f"Mở http://localhost:{PORT}  (Ctrl+C để dừng; nhãn lưu ngay vào {GOLD})")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit({"sample": sample, "serve": serve}.get(cmd, lambda: sys.exit(__doc__))())
