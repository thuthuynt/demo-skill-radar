"""Đọc cấu hình từ config/*.yaml."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
LOG_DIR = ROOT / "logs"
WAREHOUSE_DIR = ROOT / "warehouse"


def load_yaml(name: str) -> dict:
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_sources() -> dict:
    return load_yaml("sources.yaml")


def load_assumptions() -> dict:
    return load_yaml("assumptions.yaml")


def user_agent(contact_email: str) -> str:
    """UA khai báo rõ tên dự án và email liên hệ (ràng buộc cứng số 2)."""
    email = (contact_email or "").strip()
    if "@" not in email or email.endswith(("example.com", "example.org")):
        raise SystemExit(
            "Thiếu email liên hệ thật trong config/sources.yaml (contact_email). "
            "Không chạy crawler khi chưa có.")
    return f"SkillRadarVN-Research/0.1 (nghien cuu thi truong lao dong; lien he: {email})"
