"""Backfill lịch sử tin tuyển dụng từ bản lưu Internet Archive.

    python -m src.backfill.wayback                    # 2025-01 .. 2026-09, 150 tin/nguồn/tháng
    python -m src.backfill.wayback --per-month 50     # thử nhanh

Với mỗi nguồn và mỗi tháng: hỏi CDX API danh sách trang tin được lưu trong tháng,
lấy mẫu đều tối đa N trang, tải bản lưu gốc (`id_`), bóc bằng đúng parser của crawler
hằng ngày, lọc dữ liệu cá nhân, ghi `warehouse/bronze_archive/<YYYY-MM>/<nguồn>.jsonl`.

Tách riêng khỏi `warehouse/bronze/` vì đây là MẪU bản lưu, không phải toàn bộ tin
đang mở: chỉ dùng được tỷ trọng trong tháng, không dùng được số đếm tuyệt đối.
Chạy lại được: bỏ qua URL đã có.
"""

import argparse
import fcntl
import json
import sys
import time
from datetime import date, datetime, timezone

import httpx

from src.config import LOG_DIR, WAREHOUSE_DIR, load_sources, user_agent
from src.crawl.parse import bronze_record, normalize_url
from src.crawl.polite import PoliteClient
from src.log import get_logger

log = get_logger("backfill")

ARCHIVE = WAREHOUSE_DIR / "bronze_archive"
CDX = "https://web.archive.org/cdx/search/cdx"
# Internet Archive giới hạn tần suất chặt hơn trang tuyển dụng -> 4 s/request
ARCHIVE_DELAY = 4.0
# Chỉ lấy trang chi tiết tin, không lấy trang danh sách / tìm kiếm
URL_FILTERS = {
    "itviec": [("itviec.com/it-jobs/", r"original:.*/it-jobs/[a-z0-9-]+-\d{3,5}$"),
               ("itviec.com/viec-lam-it/", r"original:.*/viec-lam-it/[a-z0-9-]+-\d{3,5}$")],
    "vietnamworks": [("vietnamworks.com/", r"original:.*/[a-z0-9][a-z0-9-]+-\d{6,8}-jv$")],
}


def months(start: str, end: str) -> list[str]:
    y, m = map(int, start.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= end:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def get_retry(client: PoliteClient, url: str, tries: int = 3):
    """Internet Archive hay ngắt kết nối giữa chừng -> thử lại, giãn cách tăng dần."""
    r = None
    for i in range(tries):
        try:
            r = client.get(url)
            if r is None or r.status_code < 500:
                return r
            log.warning("HTTP %d (lần %d): %s", r.status_code, i + 1, url[:120])
        except httpx.HTTPError as e:
            log.warning("lỗi %s (lần %d): %s", type(e).__name__, i + 1, url[:120])
        time.sleep(30 * (i + 1))
    return r


# Kích thước bản lưu (byte, nén) tối thiểu. vietnamworks: archive hay lưu trang khung
# Next.js chưa có dữ liệu tin (~24 KB thô). Ngưỡng đặt từ phân bố length của bản lưu
# bóc được vs không bóc được, xem logs/backfill_length_check.json.
MIN_LENGTH = {"vietnamworks": 10_000}  # khung 5–10 KB, trang đủ ≥10,9 KB (p01)


def build_index(client: PoliteClient, name: str, start: str, end: str) -> dict[str, list]:
    """Danh mục bản lưu trang tin của một nguồn, tải theo trang 5000 dòng (resumeKey),
    lưu đệm ở `bronze_archive/_index/<nguồn>.jsonl` để chạy lại không phải hỏi CDX.
    Trả về {YYYY-MM: [(timestamp, url gốc), ...]} theo tháng của bản lưu ĐẦU TIÊN."""
    idx_dir = ARCHIVE / "_index"
    idx_dir.mkdir(parents=True, exist_ok=True)
    # v2: có cột length (kích thước bản lưu) để bỏ trang khung rỗng của vietnamworks
    rows_f, state_f = idx_dir / f"{name}.v2.jsonl", idx_dir / f"{name}.v2.state.json"
    state = json.loads(state_f.read_text()) if state_f.exists() else {}
    for prefix, flt in URL_FILTERS[name]:
        st = state.setdefault(prefix, {"resume": None, "done": False})
        while not st["done"]:
            params = {"url": prefix, "matchType": "prefix", "output": "json",
                      "fl": "timestamp,original,length", "collapse": "urlkey",
                      "filter": ["statuscode:200", flt],
                      "from": start.replace("-", ""), "to": end.replace("-", ""),
                      "limit": "5000", "showResumeKey": "true"}
            if st["resume"]:
                params["resumeKey"] = st["resume"]
            r = get_retry(client, str(client.client.build_request("GET", CDX, params=params).url))
            if r is None or r.status_code != 200:
                log.warning("CDX không trả lời: %s, dừng ở resumeKey=%s", prefix, st["resume"])
                break
            data = json.loads(r.text or "[]")
            body = data[1:]
            resume = None
            if len(body) >= 2 and body[-2] == [] and len(body[-1]) == 1:
                resume, body = body[-1][0], body[:-2]
            with open(rows_f, "a", encoding="utf-8") as f:
                for ts, orig, length in body:
                    f.write(json.dumps([ts, orig, int(length or 0)]) + "\n")
            st["resume"], st["done"] = resume, resume is None
            state_f.write_text(json.dumps(state))
            log.info("CDX %s: +%d dòng, %s", prefix, len(body), "xong" if st["done"] else "còn tiếp")
    by_month: dict[str, dict] = {}
    if rows_f.exists():
        for line in open(rows_f, encoding="utf-8"):
            ts, orig, length = json.loads(line)
            if length < MIN_LENGTH.get(name, 0):
                continue
            m = f"{ts[:4]}-{ts[4:6]}"
            u = normalize_url(orig)
            # cùng URL lưu nhiều lần -> giữ bản sớm nhất
            if u not in by_month.setdefault(m, {}) or ts < by_month[m][u][0]:
                by_month[m][u] = (ts, orig)
    return {m: sorted(v.values()) for m, v in by_month.items()}


def sample(rows: list, n: int) -> list:
    """Lấy mẫu đều theo thời gian lưu trong tháng (rows đã sắp theo timestamp)."""
    if len(rows) <= n:
        return rows
    step = len(rows) / n
    return [rows[int(i * step)] for i in range(n)]


def done_urls() -> set[str]:
    seen = set()
    for f in ARCHIVE.glob("20*/*.jsonl"):  # bỏ qua _index/
        with open(f, encoding="utf-8") as fh:
            seen.update(json.loads(line)["url"] for line in fh)
    return seen


def backfill(client: PoliteClient, sources: list[dict], month_list: list[str], per_month: int) -> None:
    seen = done_urls()
    log.info("đã có %d tin lưu trữ", len(seen))
    with open(LOG_DIR / "backfill_coverage.jsonl", "a", encoding="utf-8") as cov:
        index = {s["name"]: build_index(client, s["name"], month_list[0], month_list[-1])
                 for s in sources}
        for month in month_list:
            for src in sources:
                name = src["name"]
                rows = index[name].get(month, [])
                todo = [(ts, o) for ts, o in rows if normalize_url(o) not in seen]
                out_file = ARCHIVE / month / f"{name}.jsonl"
                have = sum(1 for _ in open(out_file, encoding="utf-8")) if out_file.exists() else 0
                # chạy lại chỉ bù cho đủ per_month, không lấy mẫu thêm tháng đã đủ
                picked = sample(todo, max(0, per_month - have))
                st = {"month": month, "source": name, "captures": len(rows), "had": have,
                      "sampled": len(picked), "parsed": 0, "failed": 0, "skipped_robots": 0}
                out_dir = ARCHIVE / month
                out_dir.mkdir(parents=True, exist_ok=True)
                with open(out_dir / f"{name}.jsonl", "a", encoding="utf-8") as out:
                    for ts, orig in picked:
                        # trang gốc phải được robots.txt của chính nguồn cho phép
                        if not client.allowed(orig):
                            st["skipped_robots"] += 1
                            continue
                        r = get_retry(client, f"https://web.archive.org/web/{ts}id_/{orig}")
                        if "https://web.archive.org" in client.blocked_hosts:
                            log.error("Internet Archive đã chặn, dừng backfill")
                            cov.write(json.dumps(st) + "\n")
                            return
                        rec = bronze_record(name, src["method"], orig, r.text) if r is not None \
                            and r.status_code == 200 else None
                        if rec is None:
                            st["failed"] += 1
                            continue
                        rec["archived_at"] = datetime.strptime(ts, "%Y%m%d%H%M%S") \
                            .replace(tzinfo=timezone.utc).isoformat()
                        rec["archive_url"] = f"https://web.archive.org/web/{ts}/{orig}"
                        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        out.flush()
                        seen.add(rec["url"])
                        st["parsed"] += 1
                cov.write(json.dumps(st) + "\n")
                cov.flush()
                log.info("%s %s: %s", month, name, st)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default="2025-01")
    ap.add_argument("--to", dest="end", default="2026-09")
    ap.add_argument("--per-month", type=int, default=150)
    ap.add_argument("--source", action="append", help="chỉ chạy nguồn này")
    args = ap.parse_args()

    LOG_DIR.mkdir(exist_ok=True)
    lock = open(LOG_DIR / "backfill.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log.warning("đang có một lần backfill khác chạy")
        return 3

    cfg = load_sources()
    client = PoliteClient(user_agent(cfg["contact_email"]), LOG_DIR / "blocked.jsonl",
                          min_delay=ARCHIVE_DELAY)
    client.client.timeout = 120
    try:
        sources = [s for s in cfg["sources"] if s["name"] in URL_FILTERS
                   and (not args.source or s["name"] in args.source)]
        backfill(client, sources, months(args.start, args.end), args.per_month)
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
