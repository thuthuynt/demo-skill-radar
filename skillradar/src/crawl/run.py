"""Chạy crawler.

    python -m src.crawl.run --dry-run       # kiểm tra robots.txt cho URL hạt giống, không tải trang
    python -m src.crawl.run                 # chạy thật, tối đa max_pages_per_run tin mới mỗi nguồn
    python -m src.crawl.run --limit 5000    # lần đổ đầy đầu tiên

Mỗi lần chạy:
1. Tải sitemap tin của từng nguồn -> danh sách tin đang mở hôm nay
   (`warehouse/bronze/<ngày>/<nguồn>.open.txt`, dùng cho chỉ số tin đang mở).
2. Tải các tin chưa từng tải, xen kẽ giữa các nguồn, ghi
   `warehouse/bronze/<ngày>/<nguồn>.jsonl` (đã lọc dữ liệu cá nhân).
3. Ghi một dòng độ phủ vào `logs/coverage.jsonl`.
"""

import argparse
import fcntl
import json
import re
import sys
from datetime import datetime, timezone

import httpx

from src.config import LOG_DIR, WAREHOUSE_DIR, load_sources, user_agent
from src.crawl.parse import PARSER_VERSION, bronze_record, normalize_url
from src.crawl.polite import PoliteClient
from src.log import get_logger

log = get_logger("crawl")

BRONZE = WAREHOUSE_DIR / "bronze"
LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>")


def seed_urls(src: dict) -> list[str]:
    if src.get("listing_url"):
        return [src["listing_url"].format(page=1)]
    return list(src.get("sitemap_urls") or []) or [src["base_url"]]


def dry_run(client: PoliteClient, sources: list[dict]) -> int:
    if not sources:
        print("Chưa có nguồn nào trong config/sources.yaml. Chạy src/probe_sources.py trước.")
        return 1
    n_ok = n_total = 0
    for src in sources:
        print(f"### {src['name']}")
        for url in seed_urls(src):
            ok = client.allowed(url)
            n_total += 1
            n_ok += ok
            delay = client.crawl_delay(client._host(url))
            print(f"  {'CHO PHÉP' if ok else 'CẤM    '}  delay={delay:.1f}s  {url}")
    log.info("dry-run: %d/%d URL hạt giống được robots.txt cho phép", n_ok, n_total)
    return 0 if n_ok == n_total else 2


def sitemap_urls(client: PoliteClient, url: str) -> list[str]:
    """Đọc sitemap, đi xuống sitemap con nếu là chỉ mục."""
    r = client.get(url)
    if r is None or r.status_code != 200:
        log.warning("không tải được sitemap %s", url)
        return []
    locs = LOC.findall(r.text)
    if "<sitemapindex" in r.text[:500]:
        return [u for child in locs for u in sitemap_urls(client, child)]
    return locs


def listing_urls(client: PoliteClient, src: dict) -> list[str]:
    """Nguồn không có sitemap tin: đi các trang danh sách, gom link tin theo `link_pattern`.
    shortcut: chỉ thấy max_listing_pages trang đầu, tin cũ hơn bị bỏ sót; tăng nếu cần."""
    pattern = re.compile(src["link_pattern"])
    out: list[str] = []
    for page in range(1, src.get("max_listing_pages", 50) + 1):
        r = client.get(src["listing_url"].format(page=page))
        if r is None or r.status_code != 200:
            break
        found = pattern.findall(r.text)
        if not found:
            break
        out.extend(found)
    return out


def open_urls_of(client: PoliteClient, src: dict) -> list[str]:
    raw = listing_urls(client, src) if src.get("listing_url") else \
        [u for s in seed_urls(src) for u in sitemap_urls(client, s)]
    return list(dict.fromkeys(normalize_url(u) for u in raw))


def already_fetched() -> dict[str, int]:
    """url -> phiên bản parser cao nhất đã ghi cho url đó."""
    seen: dict[str, int] = {}
    for f in BRONZE.glob("*/*.jsonl"):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                seen[r["url"]] = max(seen.get(r["url"], 0), r.get("parser_version", 1))
    return seen


def crawl(client: PoliteClient, sources: list[dict], limit: int | None, refetch: bool = False) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    day_dir = BRONZE / today
    day_dir.mkdir(parents=True, exist_ok=True)
    seen = already_fetched()
    log.info("đã có %d tin trong bronze", len(seen))

    queues, stats = {}, {}
    with open(BRONZE / "urls.jsonl", "a", encoding="utf-8") as urls_log:
        for src in sources:
            name = src["name"]
            open_urls = open_urls_of(client, src)
            (day_dir / f"{name}.open.txt").write_text("\n".join(open_urls) + "\n", encoding="utf-8")
            new = [u for u in open_urls if u not in seen]
            current = PARSER_VERSION.get(src["method"], 1)
            # --refetch: tải lại tin còn mở mà bản ghi được bóc bằng parser cũ có lỗi
            stale = [u for u in open_urls if refetch and u in seen and seen[u] < current]
            for u in new:
                urls_log.write(json.dumps({"url": u, "source": name, "first_seen": today}) + "\n")
            cap = limit or src.get("max_pages_per_run", 200)
            queues[name] = (src, (new + stale)[:cap])
            stats[name] = {"date": today, "source": name, "open": len(open_urls),
                           "new": len(new), "fetched": 0, "parsed": 0, "failed": 0,
                           "blocked": False}
            log.info("%s: %d tin đang mở, %d chưa tải, %d cần tải lại, sẽ tải %d", name,
                     len(open_urls), len(new), len(stale), len(queues[name][1]))

    outs = {n: open(day_dir / f"{n}.jsonl", "a", encoding="utf-8") for n in queues}
    try:
        i = 0
        while any(q for _, q in queues.values()):
            # xen kẽ các nguồn: mỗi host vẫn chờ ≥2 s, nhưng tổng thời gian giảm
            for name, (src, q) in queues.items():
                if not q:
                    continue
                url = q.pop(0)
                if client._host(url) in client.blocked_hosts:
                    stats[name]["blocked"] = True
                    q.clear()
                    log.warning("%s: host đã chặn, dừng nguồn này", name)
                    continue
                st = stats[name]
                try:
                    r = client.get(url)
                except httpx.HTTPError as e:
                    st["failed"] += 1
                    log.warning("%s lỗi %s: %s", name, type(e).__name__, url)
                    continue
                if r is None or r.status_code != 200:
                    st["failed"] += 1
                    continue
                st["fetched"] += 1
                rec = bronze_record(name, src["method"], url, r.text)
                if rec is None:
                    st["failed"] += 1
                    log.warning("%s: không bóc được %s", name, url)
                    continue
                outs[name].write(json.dumps(rec, ensure_ascii=False) + "\n")
                outs[name].flush()
                st["parsed"] += 1
            i += 1
            if i % 50 == 0:
                log.info("tiến độ: %s", {n: s["parsed"] for n, s in stats.items()})
    finally:
        for f in outs.values():
            f.close()
        with open(LOG_DIR / "coverage.jsonl", "a", encoding="utf-8") as cov:
            for st in stats.values():
                cov.write(json.dumps(st, ensure_ascii=False) + "\n")
                log.info("xong %s", st)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="chỉ kiểm tra robots.txt, không tải trang")
    ap.add_argument("--limit", type=int, help="ghi đè max_pages_per_run cho lần chạy này")
    ap.add_argument("--refetch", action="store_true",
                    help="tải lại tin còn mở có bản ghi từ parser cũ (xem PARSER_VERSION)")
    ap.add_argument("--source", action="append",
                    help="chỉ chạy nguồn này (lặp lại được); mặc định chạy tất cả")
    args = ap.parse_args()

    cfg = load_sources()
    sources = [s for s in cfg.get("sources") or [] if not args.source or s["name"] in args.source]
    client = PoliteClient(user_agent(cfg.get("contact_email")), LOG_DIR / "blocked.jsonl")
    try:
        if args.dry_run:
            return dry_run(client, sources)
        # hai tiến trình cùng chạy sẽ vượt giới hạn 2 s/host và tải trùng -> chỉ cho một
        LOG_DIR.mkdir(exist_ok=True)
        lock = open(LOG_DIR / "crawl.lock", "w")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log.warning("đang có một lần crawl khác chạy, bỏ qua lần này")
            return 3
        return crawl(client, sources, args.limit, args.refetch)
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
