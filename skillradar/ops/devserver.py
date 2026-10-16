"""Máy chủ xem thử web/ trên máy: như `python -m http.server` nhưng cấm trình duyệt lưu đệm,
để sửa xong tải lại là thấy ngay (http.server mặc định để trình duyệt giữ bản cũ).

    python3 skillradar/ops/devserver.py [cổng]     # mặc định 8090
"""

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"


class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8090
    print(f"http://localhost:{port}  ->  {WEB}")
    ThreadingHTTPServer(("127.0.0.1", port), partial(NoCache, directory=str(WEB))).serve_forever()
