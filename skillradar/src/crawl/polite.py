"""Tầng tuân thủ: robots.txt, Crawl-delay, tần suất thấp, dừng khi bị chặn.

Mọi request của crawler phải đi qua PoliteClient. Không có đường tắt.
"""

import json
import re
import time
import urllib.robotparser as robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

MIN_DELAY = 2.0  # giây, tối thiểu giữa hai request cùng host (ràng buộc cứng số 5)

# Dấu hiệu trang thử thách chống bot. Chỉ xét chỗ không thể là nội dung tin: chữ ký kỹ
# thuật ở bất kỳ đâu, câu chặn trong <title>, và "captcha" chỉ ở trang ngắn — tin tuyển
# "Data Crawler / Web Scraping" có chữ captcha trong mô tả và từng làm dừng nhầm cả nguồn.
BOT_SIGNATURE = re.compile(r"cf-browser-verification|cf_chl_|/cdn-cgi/challenge-platform|"
                           r"datadome|perimeterx|px-captcha", re.I)
BOT_TITLE = re.compile(r"<title>[^<]*(just a moment|checking your browser|attention required|"
                       r"access denied|captcha)[^<]*</title>", re.I)
CHALLENGE_MAX_BYTES = 30_000


def is_bot_wall(html: str) -> bool:
    head = html[:20_000]
    return bool(BOT_SIGNATURE.search(head) or BOT_TITLE.search(head)
                or (len(html) < CHALLENGE_MAX_BYTES and re.search(r"captcha", html, re.I)))


class PoliteClient:
    def __init__(self, user_agent: str, blocked_log: Path,
                 min_delay: float = MIN_DELAY, transport: httpx.BaseTransport | None = None):
        self.ua = user_agent
        self.min_delay = min_delay
        self.blocked_log = blocked_log
        self.client = httpx.Client(
            headers={"User-Agent": user_agent, "Accept-Language": "vi,en;q=0.8"},
            follow_redirects=True, timeout=25.0, transport=transport)
        self._robots: dict[str, robotparser.RobotFileParser | None] = {}
        self._last: dict[str, float] = {}
        self.blocked_hosts: set[str] = set()

    # --- robots.txt ---

    def _host(self, url: str) -> str:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"

    def _rules(self, host: str) -> robotparser.RobotFileParser | None:
        """None nghĩa là không đọc được robots.txt -> coi như cấm hết."""
        if host not in self._robots:
            self._wait(host)
            try:
                r = self.client.get(f"{host}/robots.txt")
            except httpx.HTTPError:
                self._robots[host] = None
                return None
            rp = robotparser.RobotFileParser()
            if r.status_code == 200:
                rp.parse(r.text.splitlines())
            elif 400 <= r.status_code < 500 and r.status_code not in (401, 403, 429):
                rp.parse([])  # không có robots.txt -> cho phép, theo chuẩn RFC 9309
            else:
                rp = None  # 401/403/429/5xx: không chắc thì không tải
            self._robots[host] = rp
        return self._robots[host]

    def allowed(self, url: str) -> bool:
        host = self._host(url)
        if host in self.blocked_hosts:
            return False
        rp = self._rules(host)
        return rp is not None and rp.can_fetch(self.ua, url)

    def crawl_delay(self, host: str) -> float:
        rp = self._robots.get(host)
        declared = rp.crawl_delay(self.ua) if rp else None
        return max(self.min_delay, float(declared or 0))

    # --- tải ---

    def _wait(self, host: str) -> None:
        delay = self.crawl_delay(host) if host in self._robots else self.min_delay
        last = self._last.get(host)
        if last is not None:
            gap = time.monotonic() - last
            if gap < delay:
                time.sleep(delay - gap)
        self._last[host] = time.monotonic()

    def get(self, url: str) -> httpx.Response | None:
        """Trả về Response, hoặc None nếu robots cấm / host đã chặn / vừa bị chặn."""
        if not self.allowed(url):
            return None
        host = self._host(url)
        self._wait(host)
        r = self.client.get(url)
        if r.status_code in (403, 429) or is_bot_wall(r.text):
            self._block(host, url, r.status_code)
            return None
        return r

    def _block(self, host: str, url: str, status: int) -> None:
        """Host nói không -> dừng hẳn host đó trong lần chạy này và ghi lại."""
        self.blocked_hosts.add(host)
        self.blocked_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.blocked_log, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "at": datetime.now(timezone.utc).isoformat(),
                "host": host, "url": url, "status": status,
            }, ensure_ascii=False) + "\n")

    def close(self) -> None:
        self.client.close()
