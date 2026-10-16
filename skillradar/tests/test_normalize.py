"""Chuẩn hóa silver, trên chuỗi thật lấy từ tin đã thu ngày 12/10/2026."""

import pytest

from src.build.normalize import job_family, lang, provinces, salary, seniority


@pytest.mark.parametrize("raw,expected", [
    ("Quận 3, Hồ Chí Minh | Hà Nội", ["ho-chi-minh", "ha-noi"]),
    ("Thủ Dầu Một, Bình Dương", ["ho-chi-minh"]),        # sáp nhập 7/2025
    ("Bến Lức, Long An", ["tay-ninh"]),
    ("Hà Nam", ["ninh-binh"]),                          # không bị nhầm sang Hà Nội
    ("Hưng Yên | Hà Nội", ["hung-yen", "ha-noi"]),
    ("Toàn quốc", ["toan-quoc"]),
    ("Nước ngoài, Nước ngoài", ["nuoc-ngoai"]),
    ("Not Available", []),
])
def test_provinces(raw, expected):
    assert provinces(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("25tr-30tr ₫/tháng", (25e6, 30e6, "VND")),
    ("20.000.000 VNĐ", (20e6, 20e6, "VND")),
    ("$$ 1,500-2,000 /tháng", (1500, 2000, "USD")),
    ("Tới $ 2,500 /tháng", (None, 2500, "USD")),
    ("Up to $2000 USD MONTH", (None, 2000, "USD")),
    ("Trên 20 triệu", (20e6, None, "VND")),
    ("Thỏa thuận", (None, None, None)),
    ("You'll love it", (None, None, None)),
])
def test_salary(raw, expected):
    assert salary(raw) == expected


def test_seniority():
    assert seniority("Senior Data Engineer (Python)") == "senior"
    assert seniority("Thực Tập Sinh Kế Toán") == "fresher"
    assert seniority("Trưởng Phòng Kinh Doanh") == "senior"
    assert seniority("Nhân Viên Kinh Doanh") == "unknown"


def test_lang():
    vi = "Chúng tôi tìm kiếm nhân viên có kinh nghiệm làm việc với khách hàng, " * 3
    en = "We are looking for an engineer with strong experience building data pipelines " * 3
    assert lang(vi) == "vi"
    assert lang(en) == "en"


def test_job_family_labor_title_wins_over_source_category():
    # vietnamworks xếp vào "Kinh Doanh", nhưng tiêu đề là lao động phổ thông
    vnw = {"jobFunction": {"parentNameVI": "Kinh Doanh"}}
    assert job_family("vietnamworks", "Nhân Viên Giao Hàng", vnw) == ("lao-dong-pho-thong", "title_first")
    assert job_family("vietnamworks", "Chuyên viên kinh doanh B2B", vnw) == ("kinh-doanh", "source")
    assert job_family("timviec365", "Tuyển Tài Xế Xe Tải", {}) == ("lao-dong-pho-thong", "title_first")
    assert job_family("itviec", "Senior Java Developer", {}) == ("cntt", "source")


def test_degree_line_does_not_count_as_domain_skill():
    from src.extract.run import compile_matchers, match
    entries = [("audit", "kiểm toán", False, True), ("excel", "Excel", False, True)]
    m = compile_matchers(entries, {"audit"})
    found = match("Kế toán tổng hợp",
                  "Yêu cầu\nTốt nghiệp chuyên ngành Kế toán, Kiểm toán; thành thạo Excel", m)
    assert "audit" not in found and "excel" in found
    found = match("Kế toán tổng hợp", "Yêu cầu\nCó kinh nghiệm kiểm toán nội bộ", m)
    assert "audit" in found


def test_scene_blank_span_hides_whole_term():
    from src.build.scenes import blank_span
    q = "Thành thạo Excel nâng cao, Excellence là điểm cộng"
    i, j = blank_span(q, "excel")
    assert q[i:j] == "Excel" and i == 11
    q = "Có khả năng sử dụng phần mềm kế toán MISA."
    i, j = blank_span(q, "phan mem ke toan")
    assert q[i:j] == "phần mềm kế toán"
