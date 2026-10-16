"""Cảnh "Một ngày làm…" cho trang học sinh, dựng hoàn toàn từ tin tuyển dụng thật.

Mỗi nhóm nghề: 3 cảnh = 3 kỹ năng chuyên môn (không tính kỹ năng mềm / ngoại ngữ) có tỷ lệ tin
cao nhất. Mỗi cảnh trích NGUYÊN VĂN một dòng yêu cầu / mô tả của một tin đang mở trong nhóm có nhắc
kỹ năng đó (đã lọc dữ liệu cá nhân ở bronze; bỏ thêm dòng có tên công ty, liên hệ, đường dẫn).
Hai thẻ nhiễu là kỹ năng phổ biến của nhóm nghề KHÁC mà nhóm này hiếm khi cần (< 3% tin).
Chọn tất định (theo hash) để chạy lại ra cùng kết quả.
"""

import hashlib
import re

from src.build.normalize import fold
from src.extract.run import sections

N_SCENES = 3
MIN_WEIGHT = 0.08                 # kỹ năng phải xuất hiện ở ≥ 8% tin của nhóm mới thành cảnh
MAX_DISTRACTOR_WEIGHT = 0.03
DOMAIN_TYPES = ("domain", "tool", "tech", "cert")
BAD_LINE = re.compile(r"\[đã ẩn\]|công ty|\bcty\b|tnhh|https?://|www\.|@|liên hệ|zalo|hotline|\d{4,}|^kỹ năng\s*:", re.I)
VI_MARK = re.compile(r"[ăâđêôơưàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]", re.I)
BULLET = re.compile(r"^[\s\-–•*+·\d.)]+")
TIMES = ["09:00", "13:30", "16:00"]


def _h(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()


def clean(line: str) -> str:
    return BULLET.sub("", line).strip().rstrip(";,")


def blank_span(q: str, term: str) -> list[int] | None:
    """Vị trí [đầu, cuối) của cụm kỹ năng trong câu gốc, để giao diện che thành ô trống."""
    ft = fold(term)
    for i in range(len(q)):
        if i and q[i - 1].isalnum():
            continue
        for j in range(i + 1, min(len(q), i + len(term) + 8) + 1):
            if fold(q[i:j]) == ft and (j == len(q) or not q[j].isalnum()):
                return [i, j]
    return None


def pick_quote(con, family_id: str, skill_id: str):
    """Dòng thật ngắn gọn nhắc kỹ năng; ưu tiên tiếng Việt, độ dài ~90 ký tự."""
    rows = con.execute("""
        SELECT p.posting_id, p.source, p.crawled_at, p.lang, p.description, f.matched_term
        FROM fact_posting_skill f JOIN base_open p USING (posting_id)
        WHERE p.job_family_id = ? AND f.skill_id = ? AND f.section IN ('requirement', 'description')""",
        [family_id, skill_id]).fetchall()
    best = None
    for pid, source, crawled, lang, desc, term in rows:
        # khớp cả từ, không khớp chuỗi con ("Excel" không được khớp "Excellence")
        term_re = re.compile(r"(?<!\w)" + re.escape(fold(term)) + r"(?!\w)")
        for _, line in sections(desc):
            q = clean(line)
            if not (30 <= len(q) <= 150) or BAD_LINE.search(q) or not term_re.search(fold(q)):
                continue
            key = (not VI_MARK.search(q), abs(len(q) - 90) // 20, _h(q))
            if best is None or key < best[0]:
                best = (key, {"quote": q, "blank": blank_span(q, term), "source": source, "date": str(crawled), "posting_id": pid})
            break
    return best[1] if best else None


def build_scenes(con, families: list[dict], dim: dict) -> dict:
    weights = {f["id"]: {s: w for s, w, *_ in f["skills"]} for f in families}
    out = {}
    for f in families:
        fid = f["id"]
        targets = [s for s, w, *_ in f["skills"]
                   if dim[s]["skill_type"] in DOMAIN_TYPES and w >= MIN_WEIGHT][:N_SCENES + 2]
        # kỹ năng nhiễu: top của nhóm khác, nhóm này hiếm cần
        pool_all = sorted({s for g in families if g["id"] != fid for s, w, *_ in g["skills"][:6]
                           if dim[s]["skill_type"] in DOMAIN_TYPES
                           and weights[fid].get(s, 0) < MAX_DISTRACTOR_WEIGHT}, key=_h)
        scenes = []
        for sid in targets:
            q = pick_quote(con, fid, sid)
            if not q:
                continue
            # thẻ nhiễu khác nhóm kỹ năng với đáp án, để không gây nhầm ("Kế toán" vs "Kế toán thuế")
            pool = [p for p in pool_all if dim[p]["skill_group"] != dim[sid]["skill_group"]]
            k = int(_h(fid + sid), 16)
            distract = [pool[k % len(pool)], pool[(k // 7 + 1) % len(pool)]] if len(pool) >= 2 else []
            if len(set(distract)) < 2:
                distract = pool[:2]
            scenes.append({"time": TIMES[len(scenes)], "skill": sid, "weight": round(weights[fid][sid], 4),
                           "distractors": distract, **q})
            if len(scenes) == N_SCENES:
                break
        out[fid] = scenes
    return out
