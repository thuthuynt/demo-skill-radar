import json

import httpx

from src.backfill import wayback


class FakeClient:
    """Trả lời CDX bằng một dòng bản lưu trong tháng `from` của request, đếm số lần hỏi."""

    def __init__(self):
        self.client = httpx.Client()
        self.calls = 0

    def get(self, url):
        self.calls += 1
        ts = httpx.URL(url).params["from"] + "01000000"
        row = [ts, "https://topcv.vn/viec-lam/ke-toan-j1.html", "20000"]
        return httpx.Response(200, text=json.dumps([["timestamp", "original", "length"], row]))


def test_build_index_refetches_when_range_grows(tmp_path, monkeypatch):
    monkeypatch.setattr(wayback, "ARCHIVE", tmp_path)
    c = FakeClient()
    assert list(wayback.build_index(c, "topcv", "2025-10", "2026-09")) == ["2025-10"]
    wayback.build_index(c, "topcv", "2025-11", "2026-06")  # nằm trong khoảng đệm: không hỏi lại
    assert c.calls == 1
    assert list(wayback.build_index(c, "topcv", "2025-01", "2026-09")) == ["2025-01"]
    assert c.calls == 2


def test_sample_full_month_takes_nothing():
    assert wayback.sample([("t", "u")] * 5, 0) == []
    assert len(wayback.sample(list(range(10)), 4)) == 4
