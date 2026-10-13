"""Bóc tin và lọc dữ liệu cá nhân, trên trang tin thật tải ngày 12/10/2026.

vietnamworks_job.html: email người liên hệ thật đã được thay bằng địa chỉ giả
`nguoi.lien.he@congty.test` trước khi lưu vào repo; test kiểm tra nó bị lọc.
"""

import json
from pathlib import Path

from src.crawl.parse import EMAIL, PHONE, bronze_record, normalize_url, scrub

FIXTURES = Path(__file__).parent / "fixtures"


def record(source, method, fixture):
    html = (FIXTURES / fixture).read_text(encoding="utf-8")
    return bronze_record(source, method, "https://example.vn/tin?utm_source=x", html)


def test_itviec_jsonld():
    r = record("itviec", "jsonld", "itviec_job.html")
    assert r["company_raw"] == "LEAP"
    assert r["posted_at_raw"] == "2026-09-27"
    assert r["valid_through_raw"] == "2026-11-01"
    assert "Hồ Chí Minh" in r["location_raw"]
    assert len(r["description_raw"]) > 1000


def test_vietnamworks_next_flight():
    r = record("vietnamworks", "next_flight", "vietnamworks_job.html")
    assert r["title_raw"] == "Quản lý vận hành kinh doanh (SOM)"
    assert r["posted_at_raw"].startswith("2026-09-12")
    assert r["location_raw"] == "Hà Nội"
    assert "Kỹ năng: Google Sheets" in r["description_raw"]


def test_no_contact_details_reach_disk():
    for args in [("itviec", "jsonld", "itviec_job.html"),
                 ("jobsgo", "jsonld", "jobsgo_job.html"),
                 ("timviec365", "timviec365", "timviec365_job.html"),
                 ("vietnamworks", "next_flight", "vietnamworks_job.html")]:
        dumped = json.dumps(record(*args), ensure_ascii=False)
        assert "nguoi.lien.he@congty.test" not in dumped
        assert not EMAIL.search(dumped)
        assert not PHONE.search(dumped)


def test_scrub_text():
    out = scrub("Yêu cầu SQL.\nLiên hệ: Chị Hương 0901 234 567\nGửi CV về hr@abc.vn hoặc Mr. Nam")
    assert "Yêu cầu SQL." in out
    for leaked in ("Hương", "0901", "hr@abc.vn", "Nam"):
        assert leaked not in out


def test_normalize_url_drops_tracking():
    assert normalize_url("https://ITviec.com/a/?utm_source=x&id=1") == "https://itviec.com/a?id=1"


def test_jobsgo_jsonld():
    r = record("jobsgo", "jsonld", "jobsgo_job.html")
    assert r["title_raw"] == "Chuyên Viên An Toàn Lao Động (HSE)"
    assert r["posted_at_raw"].startswith("2026-08-25")
    assert "None" not in r["salary_raw"]


def test_timviec365_html():
    r = record("timviec365", "timviec365", "timviec365_job.html")
    assert r["title_raw"] == "Tuyển Nhân Viên Kinh Doanh Xe"
    # nhà tuyển dụng của tin, không phải công ty trong khối "tin liên quan"
    assert r["company_raw"] == "Công ty TNHH Global Technology"
    assert r["parser_version"] == 2
    assert r["posted_at_raw"] == "2026-10-10"
    assert r["valid_through_raw"] == "2026-11-10"
    # khối chi tiết chính, không phải tin gợi ý bên cạnh
    assert r["location_raw"] == "Đồng Nai"
    assert r["salary_raw"] == "20.000.000 VNĐ"
    assert r["description_raw"].startswith("Mô tả công việc:")
