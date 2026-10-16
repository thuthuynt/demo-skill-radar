"""Dự báo ARIMA: tháng thiếu mẫu để trống (không nội suy), tháng đủ mẫu không có kỹ năng = 0."""

from datetime import date

import duckdb

from src.build.gold import forecasts


def test_forecast_gap_and_zero_months():
    con = duckdb.connect()
    con.execute("""CREATE TABLE m_skill_month (source VARCHAR, month DATE, skill_id VARCHAR,
                   n INT, total INT, "share" DOUBLE, ok BOOLEAN)""")
    months = [date(2025, m, 1) for m in range(1, 13)] + [date(2026, m, 1) for m in range(1, 5)]
    for i, m in enumerate(months):
        ok = m != date(2025, 6, 1)                  # tháng 6/2025 thiếu mẫu
        con.execute("INSERT INTO m_skill_month VALUES ('src', ?, 'other', 50, 100, 0.5, ?)", [m, ok])
        if i % 4 != 3:                              # cứ 4 tháng có 1 tháng kỹ năng 'x' vắng mặt -> phải tính 0
            con.execute("INSERT INTO m_skill_month VALUES ('src', ?, 'x', 10, 100, ?, ?)", [m, 0.1 + 0.01 * i, ok])
    rows = [r for r in forecasts(con, 12) if r[1] == "x"]
    assert len(rows) == 6                           # 6 tháng tới
    assert rows[0][2] == date(2026, 5, 1)
    n_months = rows[0][12]
    assert n_months == 15                           # 16 tháng lưới - 1 tháng thiếu mẫu (tháng vắng kỹ năng vẫn tính)
    for r in rows:
        assert 0 <= r[5] <= r[4] <= r[6]            # lo <= dự báo <= hi
