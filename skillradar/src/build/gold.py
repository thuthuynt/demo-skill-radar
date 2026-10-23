"""Silver + fact_posting_skill -> các bảng chỉ số `m_*` trong warehouse/skillradar.duckdb.

    python -m src.build.gold

Công thức theo docs/METRICS.md. Quy ước chung: chỉ tính tin `in_scope AND NOT is_repost`.
- m_skill_open:   tỷ trọng kỹ năng trên tin ĐANG MỞ (bản crawl), cắt theo nhóm nghề / tỉnh / cấp độ
- m_skill_month:  tỷ trọng theo tháng trên MẪU lưu trữ (archive), tách theo nguồn
- m_ai:           mức ảnh hưởng của AI = 0.65 × khả năng AI làm thay (nhóm đánh giá)
                  + 0.35 × thứ hạng % của mức đi cùng công cụ AI trong tin
- m_cooc:         cặp kỹ năng hay đi cùng nhau (lift)
- m_family:       số tin đang mở theo nhóm nghề × tỉnh, trọng số kỹ năng của từng nhóm (cho chỉ số tiếp cận)
- m_forecast:     ARIMA (statsmodels) trên chuỗi tháng + mốc ngây thơ + kiểm tra ngược
"""

import re
import sys
import warnings
from collections import defaultdict
from datetime import date

import duckdb
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src.build.normalize import fold
from src.build.silver import DB
from src.config import ROOT, load_assumptions
from src.log import get_logger

log = get_logger("gold")

AI_TOOLS = ROOT / "data" / "ai_tools.txt"
MIN_MONTH_N = 80        # tin/tháng/nguồn tối thiểu trong mẫu lưu trữ để tháng được dùng
MIN_SKILL_OPEN = 30     # tin đang mở tối thiểu để công bố tỷ trọng / điểm đồng xuất hiện
MIN_PAIR = 20           # số tin tối thiểu cho một cặp đồng xuất hiện
HORIZON = 6             # tháng dự báo
BACKTEST = 3            # tháng giữ lại để so mô hình với mốc ngây thơ
MIN_FORECAST_SHARE = 0.02  # chỉ dự báo kỹ năng có tỷ trọng TB ≥ 2%; thấp hơn chủ yếu là nhiễu mẫu


def ai_flags(con) -> None:
    """posting_ai(posting_id, has_ai): tin đang mở có nhắc tới công cụ AI (data/ai_tools.txt)."""
    terms = [fold(l) for l in AI_TOOLS.read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]
    pat = re.compile(r"(?<!\w)(" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r")(?!\w)")
    rows = con.execute("SELECT posting_id, title || ' ' || description FROM base_open").fetchall()
    con.execute("CREATE OR REPLACE TABLE posting_ai (posting_id VARCHAR, has_ai BOOLEAN)")
    con.executemany("INSERT INTO posting_ai VALUES (?, ?)", [(p, bool(pat.search(fold(t)))) for p, t in rows])


ORDERS = [((0, 1, 1), "n"), ((1, 1, 0), "n"), ((1, 0, 0), "c")]   # chọn theo AIC; chưa đủ tháng để tách mùa vụ


def fit_arima(y):
    """SARIMAX tốt nhất theo AIC. NaN (tháng thiếu mẫu) được Kalman filter bỏ qua, không nội suy."""
    best = None
    for order, trend in ORDERS:
        try:
            m = SARIMAX(y, order=order, trend=trend).fit(disp=False)
        except (ValueError, np.linalg.LinAlgError):
            continue
        if np.isfinite(m.aic) and (best is None or m.aic < best.aic):
            best = m
    return best


def forecasts(con, min_months: int) -> list[tuple]:
    """Mỗi (nguồn, kỹ năng) có ≥ min_months tháng dùng được: ARIMA 6 tháng tới + dải 80%,
    mốc ngây thơ (trung bình 3 tháng dùng được cuối), kiểm tra ngược 3 tháng cuối.
    Mô hình không thắng mốc ngây thơ thì ghi đúng như vậy."""
    out = []
    ok_months = defaultdict(list)
    for src, m in con.execute("SELECT DISTINCT source, month FROM m_skill_month WHERE ok ORDER BY 2").fetchall():
        ok_months[src].append(m)
    vals = defaultdict(dict)
    for src, sid, m, v in con.execute('SELECT source, skill_id, month, "share" FROM m_skill_month WHERE ok').fetchall():
        vals[(src, sid)][m] = v
    for (src, sid), bym in vals.items():
        months = ok_months[src]
        if len(months) < min_months:
            continue
        first, last = months[0], months[-1]
        grid = [date(first.year + (first.month - 1 + k) // 12, (first.month - 1 + k) % 12 + 1, 1)
                for k in range((last.year - first.year) * 12 + last.month - first.month + 1)]
        okset = set(months)
        # tháng dùng được mà không có tin chứa kỹ năng -> 0; tháng thiếu mẫu -> NaN
        y = np.array([bym.get(m, 0.0) if m in okset else np.nan for m in grid])
        if np.nanmean(y) < MIN_FORECAST_SHARE:
            continue
        train, test = y[:-BACKTEST], y[-BACKTEST:]
        tm = fit_arima(train)
        if tm is None:
            continue
        pred = tm.forecast(BACKTEST)
        mask = ~np.isnan(test)
        obs = train[~np.isnan(train)]
        naive_bt = obs[-3:].mean()
        mae_model = float(np.abs(pred[mask] - test[mask]).mean())
        mae_naive = float(np.abs(naive_bt - test[mask]).mean())
        fm = fit_arima(y)
        if fm is None:
            continue
        fc = fm.get_forecast(HORIZON)
        mean, ci = fc.predicted_mean, fc.conf_int(alpha=0.2)
        naive = float(y[~np.isnan(y)][-3:].mean())
        trend = (float(mean[-1]) - naive) / HORIZON       # thay đổi tỷ trọng / tháng mô hình dự kiến
        model = f"ARIMA{fm.model.order}" + ("+c" if fm.model.trend == "c" else "")
        for h in range(1, HORIZON + 1):
            m = date(last.year + (last.month - 1 + h) // 12, (last.month - 1 + h) % 12 + 1, 1)
            out.append((src, sid, m, h, max(0.0, float(mean[h - 1])), max(0.0, float(ci[h - 1, 0])),
                        float(ci[h - 1, 1]), naive, trend, mae_model, mae_naive, mae_model < mae_naive,
                        int((~np.isnan(y)).sum()), model))
    return out


def main() -> int:
    a = load_assumptions()
    con = duckdb.connect(str(DB))
    con.execute("CREATE OR REPLACE VIEW base AS SELECT * FROM posting WHERE in_scope AND NOT is_repost")
    con.execute("CREATE OR REPLACE VIEW base_open AS SELECT * FROM base WHERE is_open")
    con.execute("""CREATE OR REPLACE VIEW fact_domain AS
        SELECT f.* FROM fact_posting_skill f JOIN dim_skill d USING (skill_id)""")

    # 1. tỷ trọng trên tin đang mở, nhiều lát cắt (dim = 'all' | 'job_family' | 'province' | 'seniority')
    con.execute("""
        CREATE OR REPLACE TABLE m_skill_open AS
        WITH cut AS (
            SELECT posting_id, 'all' dim, 'all' val FROM base_open
            UNION ALL SELECT posting_id, 'job_family', job_family_id FROM base_open
            UNION ALL SELECT posting_id, 'province', province_code FROM base_open WHERE province_code IS NOT NULL
            UNION ALL SELECT posting_id, 'seniority', seniority FROM base_open),
        tot AS (SELECT dim, val, count(*) total FROM cut GROUP BY ALL)
        SELECT c.dim, c.val, f.skill_id, count(*) n, any_value(t.total) total,
               count(*) / any_value(t.total) AS "share"
        FROM cut c JOIN fact_posting_skill f USING (posting_id) JOIN tot t USING (dim, val)
        GROUP BY ALL""")

    # 2. tỷ trọng theo tháng trên mẫu lưu trữ, tách nguồn (mẫu khác nhau, không gộp)
    con.execute(f"""
        CREATE OR REPLACE TABLE m_skill_month AS
        WITH tot AS (SELECT source, period_month AS month, count(*) total FROM base
                     WHERE origin = 'archive' GROUP BY ALL)
        SELECT p.source, p.period_month AS month, f.skill_id, count(*) n, any_value(t.total) total,
               count(*) / any_value(t.total) AS "share", any_value(t.total) >= {MIN_MONTH_N} ok
        FROM base p JOIN fact_posting_skill f USING (posting_id)
        JOIN tot t ON t.source = p.source AND t.month = p.period_month
        WHERE p.origin = 'archive' GROUP BY ALL""")

    # 3. mức ảnh hưởng của AI
    # Chuẩn hóa bằng thứ hạng %, không min–max: các kỹ năng AI (LLM, prompt...) luôn ~100% đi cùng
    # công cụ AI, nên min–max dồn mọi kỹ năng khác về gần 0 và phần 0.35 gần như không đóng góp.
    # Kỹ năng chưa đủ tin để đo đồng xuất hiện: chỉ dùng khả năng AI làm thay, không gán 0.
    ai_flags(con)
    con.execute(f"""
        CREATE OR REPLACE TABLE m_ai AS
        WITH c AS (
            SELECT f.skill_id, count(*) n, avg(a.has_ai::INT) ai_tool_cooccurrence
            FROM base_open p JOIN fact_posting_skill f USING (posting_id) JOIN posting_ai a USING (posting_id)
            GROUP BY 1 HAVING count(*) >= {MIN_SKILL_OPEN}),
        r AS (SELECT skill_id, percent_rank() OVER (ORDER BY ai_tool_cooccurrence) ai_tool_cooccurrence_rank FROM c)
        SELECT d.skill_id, d.ai_replacement_score::DOUBLE ai_replacement_score, c.n, c.ai_tool_cooccurrence,
               r.ai_tool_cooccurrence_rank,
               coalesce(0.65 * d.ai_replacement_score::DOUBLE + 0.35 * r.ai_tool_cooccurrence_rank,
                        d.ai_replacement_score::DOUBLE) ai_impact_score,
               c.n IS NOT NULL has_cooc
        FROM dim_skill d LEFT JOIN c USING (skill_id) LEFT JOIN r USING (skill_id)
        WHERE d.ai_replacement_score <> ''""")

    # 4. đồng xuất hiện (lift = P(a,b) / P(a)P(b)) trên tin đang mở
    con.execute(f"""
        CREATE OR REPLACE TABLE m_cooc AS
        WITH f AS (SELECT DISTINCT posting_id, skill_id FROM fact_posting_skill
                   WHERE posting_id IN (SELECT posting_id FROM base_open)),
        n AS (SELECT count(*)::DOUBLE n FROM base_open),
        s AS (SELECT skill_id, count(*) c FROM f GROUP BY 1)
        SELECT x.skill_id a, y.skill_id b, count(*) n,
               count(*) * any_value(n.n) / (any_value(sa.c) * any_value(sb.c)) lift
        FROM f x JOIN f y ON x.posting_id = y.posting_id AND x.skill_id < y.skill_id
        JOIN s sa ON sa.skill_id = x.skill_id JOIN s sb ON sb.skill_id = y.skill_id, n
        GROUP BY ALL HAVING count(*) >= {MIN_PAIR}""")

    # 5. nhóm nghề: số tin đang mở theo tỉnh + trọng số kỹ năng (tỷ lệ tin của nhóm có kỹ năng đó)
    con.execute("""
        CREATE OR REPLACE TABLE m_family_province AS
        SELECT job_family_id, coalesce(province_code, 'khong-ro') province, count(*) n_open
        FROM base_open GROUP BY ALL""")
    con.execute(f"""
        CREATE OR REPLACE TABLE m_family_skill AS
        SELECT val job_family_id, skill_id, n, total, "share" AS weight FROM m_skill_open
        WHERE dim = 'job_family' AND n >= 5""")

    # 6. dự báo
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")      # cảnh báo hội tụ của statsmodels trên chuỗi ngắn
        rows = forecasts(con, a["min_periods_for_forecast"])
    con.execute("""CREATE OR REPLACE TABLE m_forecast (source VARCHAR, skill_id VARCHAR, month DATE, h INT,
                   "share" DOUBLE, lo DOUBLE, hi DOUBLE, naive DOUBLE, slope DOUBLE,
                   mae_model DOUBLE, mae_naive DOUBLE, beats_naive BOOLEAN, n_months INT, model VARCHAR)""")
    if rows:
        con.executemany("INSERT INTO m_forecast VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)

    for t in ("m_skill_open", "m_skill_month", "m_ai", "m_cooc", "m_family_province", "m_family_skill", "m_forecast"):
        log.info("%-18s %7d dòng", t, con.execute(f"SELECT count(*) FROM {t}").fetchone()[0])
    log.info("tháng dùng được theo nguồn: %s", con.execute(
        "SELECT source, count(DISTINCT month) FROM m_skill_month WHERE ok GROUP BY 1").fetchall())
    log.info("dự báo: %s", con.execute("""SELECT source, count(DISTINCT skill_id),
             sum(beats_naive::INT) FILTER (WHERE h = 1) FROM m_forecast GROUP BY 1""").fetchall())
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
