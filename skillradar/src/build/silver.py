"""Bronze -> silver: bảng `posting` trong warehouse/skillradar.duckdb.

    python -m src.build.silver

Gộp hai luồng:
- `crawl`:   warehouse/bronze/<ngày>/<nguồn>.jsonl  (toàn bộ tin đang mở mỗi ngày)
- `archive`: warehouse/bronze_archive/<tháng>/<nguồn>.jsonl (MẪU bản lưu Internet Archive)

Mỗi tin một dòng. Tin đăng lại (cùng công ty, tiêu đề gần giống, cách nhau < 30 ngày,
kể cả khác nguồn) đánh `is_repost = TRUE`; mọi chỉ số tính trên `is_repost = FALSE`.
"""

import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta

import duckdb
from rapidfuzz.distance import Levenshtein

from src.build.normalize import (OUT_OF_SCOPE, fold, job_family, lang, provinces,
                                 salary, seniority)
from src.config import WAREHOUSE_DIR, load_assumptions
from src.log import get_logger

log = get_logger("silver")

DB = WAREHOUSE_DIR / "skillradar.duckdb"
COMPANY_NOISE = re.compile(
    r"\b(cong ty|cty|tnhh|mtv|co phan|cp|jsc|ltd|limited|company|co|corp|corporation|"
    r"inc|tap doan|chi nhanh|viet nam|vietnam|vn|group|tong cong ty|mot thanh vien)\b")


def company_key(name: str) -> str:
    return re.sub(r"\s+", " ", COMPANY_NOISE.sub(" ", fold(name))).strip() or fold(name)


def to_date(raw: str) -> date | None:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw or "")
    if not m:
        return None
    try:
        return date(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return None


def read_jsonl(pattern: str) -> list[tuple[str, dict]]:
    out = []
    for f in sorted(WAREHOUSE_DIR.glob(pattern)):
        with open(f, encoding="utf-8") as fh:
            out += [(f.parent.name, json.loads(line)) for line in fh]
    return out


def open_snapshots() -> tuple[dict[str, list[date]], dict[str, date]]:
    """url -> các ngày có trong danh sách tin đang mở; nguồn -> ngày chụp gần nhất."""
    seen: dict[str, list[date]] = defaultdict(list)
    latest: dict[str, date] = {}
    for f in sorted((WAREHOUSE_DIR / "bronze").glob("*/*.open.txt")):
        d = date.fromisoformat(f.parent.name)
        src = f.name.split(".")[0]
        latest[src] = max(latest.get(src, d), d)
        for url in f.read_text(encoding="utf-8").split():
            seen[url].append(d)
    return seen, latest


def build_rows() -> list[dict]:
    snaps, latest = open_snapshots()
    rows: dict[str, dict] = {}
    n_in = 0
    for origin, pattern in (("crawl", "bronze/20*/*.jsonl"), ("archive", "bronze_archive/20*/*.jsonl")):
        for _, r in read_jsonl(pattern):
            n_in += 1
            pid = r["posting_id"]
            ver = r.get("parser_version", 1)
            # giữ: bản crawl hơn bản lưu trữ; trong cùng luồng, parser mới hơn rồi bản thu sau
            if pid in rows:
                old = rows[pid]
                if old["origin"] == "crawl" and origin == "archive":
                    continue
                if origin == old["origin"] and (ver, r["crawled_at"]) <= (old["parser_version"], old["_crawled_ts"]):
                    continue
            posted = to_date(r["posted_at_raw"])
            archived = to_date(r.get("archived_at", ""))
            crawled = to_date(r["crawled_at"])
            fam, fam_how = job_family(r["source"], r["title_raw"], r.get("structured"))
            provs = provinces(r["location_raw"])
            smin, smax, sunit = salary(r["salary_raw"])
            days = snaps.get(r["url"], [])
            valid = to_date(r.get("valid_through_raw", ""))
            # timviec365 parser@1 lấy nhầm tên công ty ở khối "tin liên quan" -> không dùng
            company = "" if r["source"] == "timviec365" and ver < 2 else r["company_raw"].strip()
            rows[pid] = {
                "posting_id": pid, "origin": origin, "source": r["source"], "url": r["url"],
                "crawled_at": crawled, "archived_at": archived, "posted_at": posted,
                "valid_through": valid,
                # tháng quy về: ngày đăng nếu có, không thì ngày lưu / ngày thu
                "period_month": (posted or archived or crawled).replace(day=1),
                "title": re.sub(r"\s+", " ", r["title_raw"]).strip(),
                "company": company or None, "company_key": company_key(company) if company else None,
                "location_raw": r["location_raw"],
                "province_code": provs[0] if provs else None, "province_codes": provs,
                "seniority": seniority(r["title_raw"]),
                "salary_min": smin, "salary_max": smax, "salary_unit": sunit,
                "lang": lang(r["description_raw"]),
                "job_family_id": fam, "job_family_method": fam_how, "in_scope": fam not in OUT_OF_SCOPE,
                "description": r["description_raw"],
                # còn trong danh sách tin của ngày chụp gần nhất VÀ chưa quá hạn nộp
                "is_open": origin == "crawl" and latest.get(r["source"]) in days
                           and (valid is None or valid >= latest[r["source"]]),
                "first_seen_open": min(days) if days else None,
                "last_seen_open": max(days) if days else None,
                "is_repost": False, "repost_of": None,
                "parser_version": ver, "_crawled_ts": r["crawled_at"],
            }
    log.info("bronze vào %d dòng -> %d tin duy nhất", n_in, len(rows))
    return list(rows.values())


def mark_reposts(rows: list[dict], window_days: int, max_dist: float) -> int:
    """Trong cùng công ty: tiêu đề gần giống và đăng cách nhau < window_days -> tin sau là đăng lại."""
    by_company = defaultdict(list)
    for r in rows:
        if r["company_key"]:
            by_company[r["company_key"]].append(r)
    n = 0
    window = timedelta(days=window_days)
    for group in by_company.values():
        group.sort(key=lambda r: (r["posted_at"] or r["period_month"], r["origin"] != "crawl"))
        kept: list[dict] = []
        for r in group:
            t, d = fold(r["title"]), r["posted_at"] or r["period_month"]
            orig = next((k for k in reversed(kept)
                         if d - (k["posted_at"] or k["period_month"]) < window
                         and Levenshtein.normalized_distance(t, fold(k["title"])) < max_dist), None)
            if orig:
                r["is_repost"], r["repost_of"] = True, orig["posting_id"]
                n += 1
            else:
                kept.append(r)
    return n


def main() -> int:
    a = load_assumptions()
    rows = build_rows()
    n_rep = mark_reposts(rows, a["repost_window_days"], a["repost_title_distance"])
    log.info("đánh dấu đăng lại: %d tin", n_rep)

    con = duckdb.connect(str(DB))
    con.execute("DROP TABLE IF EXISTS posting")
    con.execute("""
        CREATE TABLE posting (
          posting_id VARCHAR PRIMARY KEY, origin VARCHAR, source VARCHAR, url VARCHAR,
          crawled_at DATE, archived_at DATE, posted_at DATE, valid_through DATE, period_month DATE,
          title VARCHAR, company VARCHAR, company_key VARCHAR, location_raw VARCHAR,
          province_code VARCHAR, province_codes VARCHAR[], seniority VARCHAR,
          salary_min DOUBLE, salary_max DOUBLE, salary_unit VARCHAR, lang VARCHAR,
          job_family_id VARCHAR, job_family_method VARCHAR, in_scope BOOLEAN,
          description VARCHAR, is_open BOOLEAN, first_seen_open DATE, last_seen_open DATE,
          is_repost BOOLEAN, repost_of VARCHAR, parser_version INTEGER)""")
    cols = [c for c in rows[0] if not c.startswith("_")]
    con.executemany(f"INSERT INTO posting ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                    [[r[c] for c in cols] for r in rows])
    summary = con.execute("""
        SELECT origin, source, count(*) n, sum(is_repost::INT) reposts, sum(is_open::INT) open_now,
               sum(in_scope::INT) in_scope
        FROM posting GROUP BY ALL ORDER BY ALL""").fetchall()
    for s in summary:
        log.info("silver %s", dict(zip(["origin", "source", "n", "reposts", "open_now", "in_scope"], s)))
    log.info("silver ra %d dòng vào %s (lúc %s)", len(rows), DB, datetime.now().isoformat(timespec="seconds"))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
