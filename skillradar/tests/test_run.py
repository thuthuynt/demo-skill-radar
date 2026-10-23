import json
from datetime import datetime, timezone

from src.crawl import run


def test_done_today_needs_every_source(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "LOG_DIR", tmp_path)
    today = datetime.now(timezone.utc).date().isoformat()
    srcs = [{"name": "itviec"}, {"name": "jobsgo"}]
    assert not run.done_today(srcs)  # chưa có coverage.jsonl
    with open(tmp_path / "coverage.jsonl", "w") as f:
        f.write(json.dumps({"date": "2026-01-01", "source": "jobsgo"}) + "\n")
        f.write(json.dumps({"date": today, "source": "itviec"}) + "\n")
    assert not run.done_today(srcs)  # jobsgo chỉ có dòng của ngày cũ
    with open(tmp_path / "coverage.jsonl", "a") as f:
        f.write(json.dumps({"date": today, "source": "jobsgo"}) + "\n")
    assert run.done_today(srcs)
