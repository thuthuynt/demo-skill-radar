"""Tin đang mở của các công ty "Đang tuyển nhiều nhất" (trang hướng nghiệp): bấm tên công ty để xem tin.

Mỗi (nghề hoặc nhóm nghề, công ty): tối đa MAX_PER_COMPANY tin mới nhất, gồm tiêu đề, tỉnh, lương, ngày đăng,
kỹ năng đã khớp và vài dòng yêu cầu / mô tả trích nguyên văn. Mô tả đã lọc dữ liệu cá nhân ở bronze; bỏ thêm
mục quyền lợi và các dòng có liên hệ, đường dẫn, số dài (cùng bộ lọc với cảnh trích dẫn).
File riêng (jobs.json), trang chỉ tải khi người dùng bấm vào một công ty.
"""

from src.build.scenes import BAD_LINE, clean
from src.extract.run import sections

MAX_PER_COMPANY = 3
MAX_LINES = 3
MAX_SKILLS = 8


def excerpt(desc: str) -> list[str]:
    """Vài dòng yêu cầu trước, rồi mô tả; mỗi dòng 20–160 ký tự, không có liên hệ / đường dẫn."""
    lines = [(k, clean(l)) for k, l in sections(desc)]
    ok = [(k, q) for k, q in lines if 20 <= len(q) <= 160 and not BAD_LINE.search(q)]
    return [q for k, q in sorted(ok, key=lambda kq: kq[0] != "requirement")][:MAX_LINES]


def build_jobs(con, keys: list[tuple[str, str, str]]) -> dict:
    """keys = [(unit, company_key, tên hiển thị)] -> {"units": {unit: {tên: [id]}}, "postings": {id: {...}}}."""
    units, postings = {}, {}
    for unit, ckey, cname in keys:
        rows = con.execute("""
            SELECT posting_id, source, url, title, province_code, posted_at, crawled_at,
                   salary_min, salary_max, salary_unit, description
            FROM base_open WHERE company_key = ? AND (job_family_id = ? OR occupation_id = ?)
            ORDER BY coalesce(posted_at, crawled_at) DESC, posting_id LIMIT ?""",
            [ckey, unit, unit, MAX_PER_COMPANY]).fetchall()
        units.setdefault(unit, {})[cname] = [r[0] for r in rows]
        for pid, source, url, title, prov, posted, crawled, smin, smax, sunit, desc in rows:
            if pid in postings:
                continue
            skills = [s for (s,) in con.execute(
                "SELECT DISTINCT skill_id FROM fact_posting_skill WHERE posting_id = ? ORDER BY skill_id", [pid]).fetchall()]
            postings[pid] = {"title": title, "source": source, "url": url, "province": prov,
                             "date": str(posted or crawled),
                             "salary": [smin, smax, sunit] if (smin or smax) else None,
                             "skills": skills[:MAX_SKILLS], "lines": excerpt(desc)}
    return {"units": units, "postings": postings}


if __name__ == "__main__":
    # tự kiểm: dòng liên hệ / phúc lợi bị loại, dòng yêu cầu được giữ và đứng trước
    d = "Mô tả công việc\n- Làm báo cáo doanh số hằng tuần cho phòng\nYêu cầu\n- Thành thạo Excel và SQL cơ bản\n" \
        "- Liên hệ: 0901234567\nQuyền lợi\n- Lương tháng 13 và bảo hiểm đầy đủ"
    got = excerpt(d)
    assert got == ["Thành thạo Excel và SQL cơ bản", "Làm báo cáo doanh số hằng tuần cho phòng"], got
    print("ok", got)
