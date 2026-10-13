"""Kiểm tra backfill (go / no-go): đếm số tin tuyển dụng được Internet Archive lưu theo tháng.

    python -m src.backfill.wayback_check

Chỉ gọi CDX API (danh mục bản lưu), không tải trang lưu trữ nào. Kết quả ghi
logs/wayback_check.json và in bảng theo tháng.
"""

import json
import sys
from collections import Counter

from src.config import LOG_DIR, load_sources, user_agent
from src.crawl.polite import PoliteClient
from src.log import get_logger

log = get_logger("backfill")

CDX = "https://web.archive.org/cdx/search/cdx"
# Mẫu URL trang tin của từng nguồn (kể cả mẫu cũ)
PATTERNS = {
    "itviec": [("itviec.com/it-jobs/", None), ("itviec.com/viec-lam-it/", None)],
    "vietnamworks": [("vietnamworks.com/", "original:.*-jv$")],
}
MIN_POSTINGS_PER_MONTH = 100  # dưới mức này coi tháng đó không dùng được


def count(client: PoliteClient, prefix: str, flt: str | None) -> Counter:
    params = {"url": prefix, "matchType": "prefix", "output": "json",
              "fl": "timestamp,original", "collapse": "urlkey",
              "filter": ["statuscode:200"] + ([flt] if flt else []),
              "from": "2023", "limit": "200000"}
    url = str(client.client.build_request("GET", CDX, params=params).url)
    r = client.get(url)
    if r is None or r.status_code != 200:
        log.warning("CDX không trả lời cho %s", prefix)
        return Counter()
    rows = json.loads(r.text or "[]")[1:]
    return Counter(ts[:6] for ts, _ in rows)


def main() -> int:
    cfg = load_sources()
    client = PoliteClient(user_agent(cfg["contact_email"]), LOG_DIR / "blocked.jsonl")
    client.client.timeout = 300
    result = {}
    try:
        for source, pats in PATTERNS.items():
            months = Counter()
            for prefix, flt in pats:
                months += count(client, prefix, flt)
            result[source] = dict(sorted(months.items()))
    finally:
        client.close()
    usable = {s: [m for m, n in ms.items() if n >= MIN_POSTINGS_PER_MONTH] for s, ms in result.items()}
    (LOG_DIR / "wayback_check.json").write_text(json.dumps(
        {"by_month": result, "usable_months": usable, "threshold": MIN_POSTINGS_PER_MONTH},
        ensure_ascii=False, indent=1))
    for s, ms in result.items():
        print(f"### {s}: {len(usable[s])} tháng dùng được (≥{MIN_POSTINGS_PER_MONTH} tin)")
        for m, n in ms.items():
            print(f"  {m[:4]}-{m[4:]}  {n:>6}")
    go = all(len(u) >= 12 for u in usable.values())
    print("KẾT LUẬN:", "GO" if go else "NO-GO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
