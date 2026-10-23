"""Làm mới trang rà soát dữ liệu web/du-lieu/index.html (bản sao: docs/data-review.html).

    python -m src.build.review

Tính lại các bảng tổng hợp từ kho duckdb + logs/coverage.jsonl và thay khối dữ liệu
nhúng `window.__DATA = …;` trong trang. Giao diện trang giữ nguyên. Không có dữ liệu cá nhân:
chỉ số đếm, tỷ lệ, và 40 tin mẫu (tiêu đề, công ty, tỉnh, lương, kỹ năng).
"""

import datetime as dt
import json
import re

import duckdb

from src.config import LOG_DIR, WAREHOUSE_DIR
from src.log import get_logger

log = get_logger("review")
ROOT = WAREHOUSE_DIR.parent
PAGES = [ROOT / "web/du-lieu/index.html", ROOT / "docs/data-review.html"]


def conv(v):
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    if hasattr(v, "as_integer_ratio") and not isinstance(v, (int, bool)):
        return float(v)
    return v


def build(c) -> dict:
    def q(s):
        r = c.sql(s)
        return [{k: conv(v) for k, v in zip(r.columns, row)} for row in r.fetchall()]

    def load(p, key):
        d = json.load(open(ROOT / p))
        return d[key] if isinstance(d, dict) else d

    fam = {f["id"]: f for f in load("web/data/families.json", "families")}
    prov = {p["code"]: p for p in load("web/data/provinces.json", "provinces")}
    web_sk = {s["id"]: s for s in load("web/data/skills.json", "skills")}
    D = {}

    cov = {}
    for line in open(LOG_DIR / "coverage.jsonl"):
        r = json.loads(line)
        cov[(r["date"], r["source"])] = r
    D["crawl_daily"] = [{"date": d, "source": s, "open": r["open"], "new": r["new"], "fetched": r["fetched"],
                         "parsed": r["parsed"], "failed": r["failed"], "blocked": bool(r.get("blocked"))}
                        for (d, s), r in sorted(cov.items())]

    k = q("""select (select count(*) from posting) postings_total,
      (select count(*) from posting where origin='crawl') postings_crawled,
      (select count(*) from posting where origin='archive') postings_archive,
      (select count(*) from base) postings_analysis,
      (select count(*) from base_open) postings_open,
      (select count(*) from dim_skill) skills,
      (select count(*) from fact_posting_skill) skill_rows,
      (select count(distinct company_key) from posting where company_key is not null) companies,
      (select count(distinct province_code) from posting where province_code is not null) provinces,
      (select count(*) filter (where is_repost) from posting) reposts,
      (select count(distinct period_month) from posting where origin='archive') archive_months""")[0]
    k.update(days_crawled=len({d for d, _ in cov}), first_day=min(d for d, _ in cov),
             last_day=max(d for d, _ in cov), sources=len({s for _, s in cov}))
    D["headline"] = [k]

    D["source_profile"] = q("""
    with s as (select posting_id, count(*) n from fact_posting_skill group by 1)
    select p.source, count(*) postings,
     count(*) filter (where origin='crawl') crawled, count(*) filter (where origin='archive') archived,
     count(*) filter (where is_open) open_now,
     avg((salary_min is not null)::int) with_salary, avg((province_code is not null)::int) with_province,
     avg((company is not null)::int) with_company, avg((s.n is not null)::int) with_skill,
     avg(coalesce(s.n,0)) skills_per_posting
    from posting p left join s using(posting_id) group by 1 order by postings desc""")

    label = {"title": "Job title", "company": "Company", "province_code": "Province", "posted_at": "Posted date",
             "valid_through": "Closing date", "salary_min": "Salary", "seniority": "Seniority level",
             "job_family_id": "Job family", "description": "Description text"}
    expr = ", ".join(f"avg(({f} is not null and {f} <> 'unknown')::int) {f}" if f == "seniority"
                     else f"avg(({f} is not null)::int) {f}" for f in label)
    row = q(f"select {expr} from base")[0]
    D["completeness"] = [{"field": v, "column": f, "filled": round(row[f], 4)} for f, v in label.items()]

    D["mix"] = (q("select 'Language' dim, case lang when 'vi' then 'Vietnamese' when 'en' then 'English' when 'mixed' then 'Mixed' else 'Unknown' end val, count(*) n from base group by 1,2")
                + q("select 'Seniority' dim, seniority val, count(*) n from base group by 1,2")
                + q("select 'Skill found in' dim, section val, count(*) n from fact_posting_skill f join base b using(posting_id) group by 1,2"))

    sk = {s["skill_id"]: s for s in q("select skill_id, name_vi, name_en, skill_group, skill_type from dim_skill")}
    top = q("""select val fam, skill_id, share from m_skill_open where dim='job_family'
               qualify row_number() over (partition by val order by share desc)=1""")
    fams = []
    for r in q("""with s as (select posting_id, count(*) n from fact_posting_skill group by 1)
                  select job_family_id, count(*) postings, count(*) filter (where is_open) open_now,
                         avg((s.n is not null)::int) with_skill
                  from base b left join s using(posting_id) where job_family_id is not null group by 1"""):
        f = fam.get(r["job_family_id"], {})
        t = next((x for x in top if x["fam"] == r["job_family_id"]), None)
        med = f.get("salary_median_vnd")
        fams.append({"family": f.get("name", r["job_family_id"]), "postings": r["postings"], "open_now": r["open_now"],
                     "with_skill": round(r["with_skill"], 4), "salary_median_m": med / 1e6 if med else None,
                     "top_skill": f'{sk[t["skill_id"]]["name_vi"]} · {t["share"]:.0%}' if t else None})
    D["families"] = sorted(fams, key=lambda r: -r["postings"])

    D["provinces"] = [{"province": prov.get(r["province_code"], {}).get("name", r["province_code"]), "open_now": r["n"]}
                      for r in q("select province_code, count(*) n from base_open where province_code is not null group by 1 order by 2 desc")]

    ai = {r["skill_id"]: r["ai_impact_score"] for r in q("select skill_id, ai_impact_score from m_ai")}
    D["skills"] = []
    for r in q("select * from m_skill_open where dim='all' order by share desc"):
        hist = (web_sk.get(r["skill_id"]) or {}).get("history") or {}
        src, series = max(hist.items(), key=lambda kv: len(kv[1]), default=(None, []))
        D["skills"].append({
            "skill": sk[r["skill_id"]]["name_vi"], "skill_en": sk[r["skill_id"]]["name_en"],
            "group": sk[r["skill_id"]]["skill_group"], "type": sk[r["skill_id"]]["skill_type"],
            "open_postings": r["n"], "share_open": round(r["share"], 4),
            "ai_score": round(ai[r["skill_id"]], 3) if ai.get(r["skill_id"]) is not None else None,
            "l12m": [[p[0], p[1]] for p in series[-12:]], "l12m_source": src})

    D["archive_months"] = q("""select strftime(period_month, '%Y-%m') as "month", source, count(*) postings
                               from posting where origin='archive' group by 1,2 order by 1,2""")

    D["sample"] = q("""with s as (select posting_id, count(*) n, string_agg(d.name_vi, ', ' order by d.name_vi) skills
                       from fact_posting_skill f join dim_skill d using(skill_id) group by 1)
    select b.posting_id, b.source, b.title, b.company, b.province_code, b.job_family_id, b.posted_at,
           b.salary_min, b.salary_max, b.salary_unit, s.n n_skills, s.skills
    from base_open b join s using(posting_id) where b.salary_min is not null and b.company is not null
    order by hash(b.posting_id) limit 40""")
    for r in D["sample"]:
        r["posting_id"] = r["posting_id"][:10]
        r["province"] = prov.get(r.pop("province_code"), {}).get("name")
        fid = r.pop("job_family_id")
        r["family"] = fam.get(fid, {}).get("name", fid)
        u, lo, hi = r.pop("salary_unit"), r.pop("salary_min"), r.pop("salary_max")
        f = (lambda v: f"{v / 1e6:.0f} tr") if u == "VND" else (lambda v: f"{v:,.0f} USD")
        r["salary"] = f(lo) + (" – " + f(hi) if hi and hi != lo else "")
    return D


def main() -> int:
    c = duckdb.connect(str(WAREHOUSE_DIR / "skillradar.duckdb"), read_only=True)
    D = build(c)
    blob = json.dumps(D, ensure_ascii=False).replace("</", "<\\/")
    day = dt.date.today().strftime("%d/%m/%Y")
    for p in PAGES:
        s = p.read_text()
        m = re.search(r"window\.__DATA = (.*?);\nwindow\.dash", s, re.S)
        assert m, f"không thấy khối dữ liệu trong {p}"
        s = s[:m.start(1)] + blob + s[m.end(1):]
        s = re.sub(r"Snapshot of the SkillRadar VN warehouse on \d\d/\d\d/\d{4}", f"Snapshot of the SkillRadar VN warehouse on {day}", s)
        p.write_text(s)
    log.info("trang rà soát: %s", {k: len(v) for k, v in D.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
