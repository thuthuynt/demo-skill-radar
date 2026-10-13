"""Kiểm thử tầng tuân thủ. Không có request thật ra mạng: dùng httpx.MockTransport.

robots.txt mẫu nằm trong tests/fixtures/. Khi đã chọn nguồn, thêm robots.txt thật
của nguồn đó vào fixtures và một ca kiểm thử tương ứng.
"""

from pathlib import Path

import httpx

from src.crawl.polite import PoliteClient

FIXTURES = Path(__file__).parent / "fixtures"
UA = "SkillRadarVN-Research/0.1 (test; lien he: test@skillradar.test)"
ROBOTS = (FIXTURES / "robots_disallow.txt").read_text(encoding="utf-8")


def make_client(tmp_path, handler):
    seen = []

    def record(request):
        seen.append(str(request.url))
        return handler(request)

    client = PoliteClient(UA, tmp_path / "blocked.jsonl", min_delay=0,
                          transport=httpx.MockTransport(record))
    return client, seen


def robots_then(page_status=200, page_text="<html>tin tuyen dung</html>"):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=ROBOTS)
        return httpx.Response(page_status, text=page_text)
    return handler


def test_disallowed_url_returns_false_and_is_never_fetched(tmp_path):
    client, seen = make_client(tmp_path, robots_then())
    url = "https://jobs.test/ung-vien/ho-so/123"

    assert client.allowed(url) is False
    assert client.get(url) is None
    assert seen == ["https://jobs.test/robots.txt"]  # chỉ robots.txt, không chạm trang


def test_allowed_url_is_fetched(tmp_path):
    client, seen = make_client(tmp_path, robots_then())
    url = "https://jobs.test/viec-lam/data-analyst-1"

    r = client.get(url)

    assert r is not None and r.status_code == 200
    assert seen == ["https://jobs.test/robots.txt", url]


def test_crawl_delay_from_robots_is_respected(tmp_path):
    client, _ = make_client(tmp_path, robots_then())
    client.allowed("https://jobs.test/viec-lam/x")
    assert client.crawl_delay("https://jobs.test") == 5.0


def test_403_blocks_host_and_logs(tmp_path):
    client, seen = make_client(tmp_path, robots_then(page_status=403))

    assert client.get("https://jobs.test/viec-lam/a") is None
    assert client.get("https://jobs.test/viec-lam/b") is None  # host đã dừng
    assert seen.count("https://jobs.test/viec-lam/b") == 0
    assert '"status": 403' in (tmp_path / "blocked.jsonl").read_text()


def test_bot_wall_page_blocks_host(tmp_path):
    client, _ = make_client(tmp_path, robots_then(page_text="<title>Just a moment...</title>"))
    assert client.get("https://jobs.test/viec-lam/a") is None
    assert "https://jobs.test" in client.blocked_hosts


def test_unreadable_robots_means_no_fetch(tmp_path):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(503)
        return httpx.Response(200, text="ok")

    client, seen = make_client(tmp_path, handler)
    assert client.get("https://jobs.test/viec-lam/a") is None
    assert seen == ["https://jobs.test/robots.txt"]


def test_job_post_mentioning_captcha_is_not_a_bot_wall(tmp_path):
    # tin tuyển "Data Crawler / Web Scraping" thật trên timviec365 từng làm dừng nhầm nguồn
    page = ("<html><head><title>Tuyển dụng Data Crawler/Web Scraping</title>"
            "<meta name='description' content='kinh nghiệm vượt captcha, proxy'></head><body>"
            + "<p>Mô tả công việc</p>" * 3000 + "</body></html>")
    client, _ = make_client(tmp_path, robots_then(page_text=page))
    assert client.get("https://jobs.test/viec-lam/data-crawler") is not None
    assert not client.blocked_hosts


def test_cloudflare_challenge_signature_blocks(tmp_path):
    page = "<html><head><title>Vui lòng chờ</title></head><body><script src='/cdn-cgi/challenge-platform/h/b/orchestrate'></script></body></html>"
    client, _ = make_client(tmp_path, robots_then(page_text=page))
    assert client.get("https://jobs.test/viec-lam/a") is None
    assert "https://jobs.test" in client.blocked_hosts
