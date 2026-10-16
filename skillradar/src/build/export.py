"""Bảng m_* -> web/data/*.json (giao diện tĩnh đọc các file này).

    python -m src.build.export

Mọi con số lấy từ duckdb; `python -m src.build.verify` tính lại bằng SQL độc lập và so.
Tỷ lệ làm tròn 4 chữ số. Tổng dung lượng phải < 1 MB.
"""

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone

import duckdb

from src.build.normalize import FAMILIES, OUT_OF_SCOPE
from src.build.silver import DB
from src.config import LOG_DIR, ROOT, load_assumptions
from src.log import get_logger

log = get_logger("export")

OUT = ROOT / "web" / "data"
MAX_BYTES = 1_000_000
TOP_PROVINCES = 12      # tỉnh có nhiều tin đang mở nhất, dùng cho lát cắt theo tỉnh
TOP_PAIRS = 400


def r4(x):
    return None if x is None else round(float(x), 4)


def rows(con, sql, *params):
    cur = con.execute(sql, list(params))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def write(name: str, obj) -> int:
    path = OUT / name
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8")
    return path.stat().st_size


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    a = load_assumptions()
    con = duckdb.connect(str(DB), read_only=True)

    # --- tỉnh ---
    prov_names = {}
    with open(ROOT / "data" / "provinces.csv", encoding="utf-8") as f:
        for p in csv.DictReader(f):
            prov_names[p["province_code"]] = {"name": p["name"], "region": p["region"]}
    prov_open = {r["province"]: r["n"] for r in rows(con, """
        SELECT province_code province, count(*) n FROM base_open WHERE province_code IS NOT NULL GROUP BY 1""")}
    top_prov = sorted(prov_open, key=prov_open.get, reverse=True)[:TOP_PROVINCES]

    # --- kỹ năng ---
    dim = {r["skill_id"]: r for r in rows(con, "SELECT * FROM dim_skill")}
    open_all = {r["skill_id"]: r for r in rows(con, "SELECT skill_id, n, \"share\" FROM m_skill_open WHERE dim = 'all'")}
    by_cut = defaultdict(lambda: defaultdict(list))
    for r in rows(con, """SELECT dim, val, skill_id, n, "share" FROM m_skill_open
                         WHERE dim IN ('job_family', 'province', 'seniority') AND n >= 5"""):
        if r["dim"] == "province" and r["val"] not in top_prov:
            continue
        by_cut[r["skill_id"]][r["dim"]].append([r["val"], r4(r["share"]), r["n"]])
    ai = {r["skill_id"]: r for r in rows(con, "SELECT * FROM m_ai")}
    hist = defaultdict(lambda: defaultdict(list))
    for r in rows(con, """SELECT source, strftime(month, '%Y-%m') m, skill_id, n, total, "share"
                         FROM m_skill_month WHERE ok ORDER BY month"""):
        hist[r["skill_id"]][r["source"]].append([r["m"], r4(r["share"]), r["n"], r["total"]])
    fc = defaultdict(dict)
    for r in rows(con, """SELECT source, skill_id, list(strftime(month, '%Y-%m') ORDER BY h) AS months,
                                list("share" ORDER BY h) AS share, list(lo ORDER BY h) AS lo, list(hi ORDER BY h) AS hi,
                                any_value(naive) AS naive, any_value(slope) AS slope, any_value(mae_model) AS mae_model,
                                any_value(mae_naive) AS mae_naive, any_value(beats_naive) AS beats_naive,
                                any_value(n_months) AS n_months,
                                any_value(model) AS model
                         FROM m_forecast GROUP BY ALL"""):
        fc[r["skill_id"]][r["source"]] = {
            "months": r["months"], "share": [r4(x) for x in r["share"]], "lo": [r4(x) for x in r["lo"]],
            "hi": [r4(x) for x in r["hi"]], "naive": r4(r["naive"]), "trend_per_month": r4(r["slope"]),
            "mae_model": r4(r["mae_model"]), "mae_naive": r4(r["mae_naive"]),
            "beats_naive": r["beats_naive"], "n_months": r["n_months"], "model": r["model"]}

    skills = []
    for sid, d in dim.items():
        o = open_all.get(sid)
        x = ai.get(sid)
        cuts = by_cut[sid]
        skills.append({
            "id": sid, "vi": d["name_vi"], "en": d["name_en"], "lang": d["canonical_lang"],
            "group": d["skill_group"], "type": d["skill_type"],
            "open": {"n": o["n"], "share": r4(o["share"])} if o else {"n": 0, "share": 0},
            "by_family": sorted(cuts["job_family"], key=lambda v: -v[1])[:8],
            "by_province": sorted(cuts["province"], key=lambda v: -v[1]),
            "by_seniority": cuts["seniority"],
            "ai": {"expert": r4(x["expert"]), "cooc": r4(x["cooc"]), "score": r4(x["ai_score"]),
                   "has_cooc": x["has_cooc"]} if x else None,
            "history": hist[sid],
            "forecast": fc[sid],
        })
    skills.sort(key=lambda s: -s["open"]["n"])

    # --- nhóm nghề ---
    fam_prov = defaultdict(dict)
    for r in rows(con, "SELECT * FROM m_family_province"):
        fam_prov[r["job_family_id"]][r["province"]] = r["n_open"]
    fam_skill = defaultdict(list)
    for r in rows(con, "SELECT job_family_id, skill_id, weight FROM m_family_skill ORDER BY weight DESC"):
        fam_skill[r["job_family_id"]].append([r["skill_id"], r4(r["weight"])])
    # lương: trung vị điểm giữa khoảng lương VND/tháng, chỉ tin có ghi lương; < 30 tin thì không công bố
    salary = {r["f"]: r for r in rows(con, """
        SELECT job_family_id f, count(*) n,
               median((coalesce(salary_min, salary_max) + coalesce(salary_max, salary_min)) / 2) med
        FROM base_open WHERE salary_unit = 'VND' AND coalesce(salary_min, salary_max) BETWEEN 1e6 AND 2e8
        GROUP BY 1""")}
    families = [{"id": f, "name": FAMILIES[f], "in_scope": f not in OUT_OF_SCOPE,
                 "salary_median_vnd": round(salary[f]["med"], -5) if f in salary and salary[f]["n"] >= 30 else None,
                 "salary_n": salary[f]["n"] if f in salary else 0,
                 "n_open": sum(fam_prov[f].values()), "by_province": fam_prov[f],
                 "skills": fam_skill[f][:30]} for f in FAMILIES if fam_prov.get(f)]

    # --- đồng xuất hiện ---
    pairs = rows(con, f"SELECT a, b, n, lift FROM m_cooc ORDER BY lift * ln(n) DESC LIMIT {TOP_PAIRS}")

    # --- meta + trạng thái ---
    snaps = rows(con, """SELECT source, max(last_seen_open) latest, count(*) FILTER (WHERE is_open) n_open
                        FROM posting WHERE origin = 'crawl' GROUP BY 1 ORDER BY 1""")
    days = sorted({p.parent.name for p in (ROOT / "warehouse" / "bronze").glob("20*/*.open.txt")})
    n_open = con.execute("SELECT count(*) FROM base_open").fetchone()[0]
    coverage = rows(con, """
        SELECT p.job_family_id, count(DISTINCT p.posting_id) n,
               count(DISTINCT f.posting_id) FILTER (WHERE d.skill_type NOT IN ('soft', 'language')) hit
        FROM base p LEFT JOIN fact_posting_skill f USING (posting_id) LEFT JOIN dim_skill d USING (skill_id)
        GROUP BY 1 ORDER BY n DESC""")
    latency = con.execute("""SELECT median(crawled_at - posted_at) FROM base
                             WHERE origin = 'crawl' AND posted_at IS NOT NULL""").fetchone()[0]
    months_ok = {r["source"]: r["n"] for r in rows(con, """
        SELECT source, count(DISTINCT month) n FROM m_skill_month WHERE ok GROUP BY 1""")}
    fc_stats = rows(con, """SELECT source, count(DISTINCT skill_id) n,
                            count(DISTINCT skill_id) FILTER (WHERE beats_naive) beats FROM m_forecast GROUP BY 1""")
    eval_path = LOG_DIR / "extract_eval.json"
    f1 = json.loads(eval_path.read_text()) if eval_path.exists() else None
    tax_ver = (ROOT / "data" / "TAXONOMY_VERSION").read_text().strip()

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": snaps, "n_open": n_open, "days_collected": len(days),
        "first_day": days[0] if days else None, "last_day": days[-1] if days else None,
        "taxonomy": {"version": tax_ver, "skills": len(dim)},
        "history_months": months_ok,
        "assumptions": {k: a[k] for k in ("apply_rate_ceiling", "apply_rate_midpoint", "apply_rate_width",
                                          "new_hire_rate", "min_periods_for_forecast")},
        "notes": {
            "open": "Tỷ trọng trên các tin đang mở tại ngày chụp gần nhất của từng nguồn; thiếu các tin đã đóng.",
            "history": "Chuỗi tháng lấy từ MẪU bản lưu Internet Archive (~150 tin/tháng/nguồn); chỉ dùng tỷ trọng, "
                       "không dùng số đếm. Tháng dưới 80 tin bị bỏ, không nội suy.",
            "ai": "Điểm chuyên gia + đồng xuất hiện với công cụ AI, chưa đo theo chuỗi thời gian.",
            "forecast": "ARIMA trên chuỗi mẫu (chưa tách mùa vụ), luôn kèm mốc ngây thơ (trung bình 3 tháng cuối) "
                        "và kết quả kiểm tra ngược 3 tháng.",
        },
    }
    status = {
        "coverage_by_family": [{**c, "share": r4(c["hit"] / c["n"])} for c in coverage],
        "extract_eval": f1 or {"note": "chưa có tập chuẩn gán nhãn"},
        "median_latency_days": None if latency is None else round(float(latency), 1),
        "forecast": fc_stats,
        "blocked_or_excluded_sources": ["vieclam24h", "vieclamtot", "mywork", "careerviet", "job3s",
                                        "careerlink", "topcv"],
    }
    provinces = [{"code": c, **prov_names.get(c, {"name": c, "region": None}), "n_open": n}
                 for c, n in sorted(prov_open.items(), key=lambda kv: -kv[1])]
    con.close()

    sizes = {n: write(n, o) for n, o in [("meta.json", meta), ("skills.json", skills), ("families.json", families),
                                         ("cooc.json", pairs), ("provinces.json", provinces),
                                         ("status.json", status)]}
    total = sum(sizes.values())
    log.info("xuất %s, tổng %.0f KB", {k: f"{v / 1024:.0f}KB" for k, v in sizes.items()}, total / 1024)
    if total > MAX_BYTES:
        log.error("web/data vượt 1 MB (%d byte)", total)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
