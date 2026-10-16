"""Kiểm chứng web/data/*.json bằng SQL độc lập trên silver + fact (không đọc bảng m_*).

    python -m src.build.verify      # thoát mã 1 nếu có số lệch -> `make deploy` dừng

Kiểm: tổng tin đang mở, tỷ trọng tin đang mở của MỌI kỹ năng, số tin đang mở của mọi nhóm nghề,
tỷ trọng theo tháng của mọi điểm lịch sử, tổng tin đang mở theo tỉnh.
"""

import json
import sys

import duckdb

from src.build.silver import DB
from src.config import ROOT
from src.log import get_logger

log = get_logger("verify")

DATA = ROOT / "web" / "data"
TOL = 6e-5  # dữ liệu xuất làm tròn 4 chữ số

OPEN = "SELECT posting_id FROM posting WHERE in_scope AND NOT is_repost AND is_open"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> int:
    con = duckdb.connect(str(DB), read_only=True)
    errors = []

    def check(label, got, want, tol=0):
        if got is None or want is None or abs(got - want) > tol:
            errors.append(f"{label}: json={got} sql={want}")

    meta, skills, families, provinces = load("meta.json"), load("skills.json"), load("families.json"), load("provinces.json")
    n_open = con.execute(f"SELECT count(*) FROM ({OPEN})").fetchone()[0]
    check("meta.n_open", meta["n_open"], n_open)

    share = dict(con.execute(f"""
        SELECT skill_id, count(DISTINCT posting_id) / {n_open} FROM fact_posting_skill
        WHERE posting_id IN ({OPEN}) GROUP BY 1""").fetchall())
    for s in skills:
        check(f"skill {s['id']} open.share", s["open"]["share"], share.get(s["id"], 0), TOL)

    fam = dict(con.execute(f"""SELECT job_family_id, count(*) FROM posting
                               WHERE posting_id IN ({OPEN}) GROUP BY 1""").fetchall())
    sal = {f: (n, m) for f, n, m in con.execute(f"""
        SELECT job_family_id, count(*), median((coalesce(salary_min, salary_max) + coalesce(salary_max, salary_min)) / 2)
        FROM posting WHERE posting_id IN ({OPEN}) AND salary_unit = 'VND'
          AND coalesce(salary_min, salary_max) BETWEEN 1e6 AND 2e8 GROUP BY 1""").fetchall()}
    for f in families:
        check(f"family {f['id']} n_open", f["n_open"], fam.get(f["id"]))
        n, med = sal.get(f["id"], (0, None))
        want = round(med, -5) if n >= 30 else None
        if f["salary_median_vnd"] != want:
            errors.append(f"family {f['id']} salary: json={f['salary_median_vnd']} sql={want}")

    prov = dict(con.execute(f"""SELECT province_code, count(*) FROM posting
                                WHERE posting_id IN ({OPEN}) AND province_code IS NOT NULL GROUP BY 1""").fetchall())
    for p in provinces:
        check(f"province {p['code']} n_open", p["n_open"], prov.get(p["code"]))

    # lương có / không có kỹ năng trong nhóm nghề (phần tử 3, 4 của families[].skills)
    prem = {(f, s): (nw, nwo, mw, mwo) for f, s, nw, nwo, mw, mwo in con.execute(f"""
        WITH p AS (SELECT posting_id, job_family_id f, (coalesce(salary_min, salary_max) + coalesce(salary_max, salary_min)) / 2 sal
                   FROM posting WHERE posting_id IN ({OPEN}) AND salary_unit = 'VND'
                     AND coalesce(salary_min, salary_max) BETWEEN 1e6 AND 2e8),
             has AS (SELECT DISTINCT posting_id, skill_id FROM fact_posting_skill)
        SELECT p.f, k.skill_id, count(*) FILTER (WHERE h.posting_id IS NOT NULL), count(*) FILTER (WHERE h.posting_id IS NULL),
               median(sal) FILTER (WHERE h.posting_id IS NOT NULL), median(sal) FILTER (WHERE h.posting_id IS NULL)
        FROM p JOIN (SELECT DISTINCT skill_id FROM fact_posting_skill) k ON true
        LEFT JOIN has h ON h.posting_id = p.posting_id AND h.skill_id = k.skill_id
        GROUP BY ALL""").fetchall()}
    for f in families:
        for sid, _w, sw, swo in f["skills"]:
            nw, nwo, mw, mwo = prem.get((f["id"], sid), (0, 0, None, None))
            want = [round(mw, -5), round(mwo, -5)] if nw >= 30 and nwo >= 30 else [None, None]
            if [sw, swo] != want:
                errors.append(f"salary {f['id']} {sid}: json={[sw, swo]} sql={want}")

    # cảnh: trích dẫn phải có nguyên văn trong tin nguồn; tin đang mở, đúng nhóm nghề, có kỹ năng đó
    scenes = load("scenes.json")
    n_scenes = 0
    for fid, ss in scenes.items():
        for sc in ss:
            n_scenes += 1
            row = con.execute(f"""SELECT p.job_family_id, p.description, p.posting_id IN ({OPEN}),
                                 EXISTS (SELECT 1 FROM fact_posting_skill x WHERE x.posting_id = p.posting_id AND x.skill_id = ?)
                                 FROM posting p WHERE p.posting_id = ?""", [sc["skill"], sc["posting_id"]]).fetchone()
            if not row or row[0] != fid or sc["quote"] not in row[1] or not row[2] or not row[3]:
                errors.append(f"scene {fid} {sc['skill']}: trích dẫn không truy ngược được về tin {sc['posting_id']}")

    month = {(src, m, sid): v for src, m, sid, v in con.execute("""
        WITH base AS (SELECT * FROM posting WHERE in_scope AND NOT is_repost AND origin = 'archive'),
        tot AS (SELECT source, period_month, count(*) t FROM base GROUP BY ALL)
        SELECT b.source, strftime(b.period_month, '%Y-%m'), f.skill_id, count(DISTINCT b.posting_id) / any_value(t.t)
        FROM base b JOIN fact_posting_skill f USING (posting_id) JOIN tot t USING (source, period_month)
        GROUP BY ALL""").fetchall()}
    n_points = 0
    for s in skills:
        for src, pts in s["history"].items():
            for m, sh, _n, _t in pts:
                check(f"history {src} {m} {s['id']}", sh, month.get((src, m, s["id"])), TOL)
                n_points += 1
    con.close()

    log.info("đã kiểm %d kỹ năng, %d nhóm nghề, %d tỉnh, %d điểm lịch sử, %d cảnh", len(skills), len(families),
             len(provinces), n_points, n_scenes)
    if errors:
        for e in errors[:30]:
            log.error("LỆCH %s", e)
        log.error("%d số không khớp", len(errors))
        return 1
    log.info("mọi số khớp với SQL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
