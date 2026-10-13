"""Trích kỹ năng: silver `posting` -> gold `fact_posting_skill` + data/unmatched_terms.csv.

    python -m src.extract.run

Khớp từ điển `data/skills_seed.csv`:
- alias ≤3 ký tự hoặc có tiền tố `\\b`: khớp chặt (giữ dấu, phân biệt hoa thường, biên từ)
- alias còn lại: không phân biệt hoa thường và dấu, theo biên từ
Bỏ qua mục quyền lợi / phúc lợi (chứa "được đào tạo", "giờ hành chính"... gây khớp nhầm).
"""

import csv
import re
import sys
from collections import Counter, defaultdict

import duckdb

from src.build.normalize import fold
from src.build.silver import DB
from src.config import ROOT
from src.log import get_logger

log = get_logger("extract")

SEED = ROOT / "data" / "skills_seed.csv"
STOPTERMS = ROOT / "data" / "stopterms.txt"
UNMATCHED = ROOT / "data" / "unmatched_terms.csv"

# Tiêu đề mục (dòng ngắn). Thứ tự: quyền lợi trước, vì "Kỹ năng" có thể nằm trong tiêu đề khác
HEADINGS = [
    ("benefit", r"(quyen loi|phuc loi|che do dai ngo|dai ngo|benefits?|perks|what we offer|"
                r"why you ll love|top \d reasons|thu nhap|we offer|thoi gian lam viec|dia diem lam viec)"),
    ("requirement", r"(yeu cau|requirements?|qualifications?|your skills|skills and experience|"
                    r"what you need|must have|nice to have|ky nang|tieu chuan|dieu kien)"),
    ("description", r"(mo ta|job description|responsibilit|nhiem vu|the job|cong viec|trach nhiem|what you ll do)"),
]
MAX_HEADING_LEN = 60


def sections(text: str) -> list[tuple[str, str]]:
    """[(mục, dòng)], đã bỏ các dòng thuộc mục quyền lợi."""
    out, current = [], "description"
    for line in (text or "").splitlines():
        f = fold(line)
        if f and len(line) <= MAX_HEADING_LEN:
            kind = next((k for k, pat in HEADINGS if re.search(pat, f)), None)
            if kind:
                current = kind
                continue
        if line.startswith("Kỹ năng:"):  # dòng kỹ năng có cấu trúc của vietnamworks
            out.append(("requirement", line))
        elif current != "benefit" and f:
            out.append((current, line))
    return out


def load_dictionary() -> tuple[list, dict]:
    """Trả về (danh sách (skill_id, alias, strict, exact), dim_skill rows)."""
    entries, dim = [], {}
    with open(SEED, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            dim[row["skill_id"]] = row
            names = {fold(row["name_vi"]), fold(row["name_en"])}
            for alias in row["aliases"].split("|"):
                alias = alias.strip()
                if not alias:
                    continue
                strict = alias.startswith("\\b") or len(alias) <= 3
                alias = alias.removeprefix("\\b")
                entries.append((row["skill_id"], alias, strict, fold(alias) in names))
    return entries, dim


def compile_matchers(entries):
    """Hai regex hợp: khớp chặt trên văn bản gốc, khớp lỏng trên văn bản đã fold."""
    strict = {a: (sid, ex) for sid, a, s, ex in entries if s}
    loose = {fold(a): (sid, ex) for sid, a, s, ex in entries if not s and fold(a)}

    def alt(keys):
        return "|".join(re.escape(k) for k in sorted(keys, key=len, reverse=True))

    strict_re = re.compile(rf"(?<![\w+#.]){alt(strict)}(?![\w+#])") if strict else None
    loose_re = re.compile(rf"(?<!\w){alt(loose)}(?!\w)") if loose else None
    return strict_re, strict, loose_re, loose


def match(title: str, desc: str, matchers) -> dict[str, tuple[str, str, str]]:
    """skill_id -> (cụm khớp, cách khớp, mục) — giữ lần khớp đầu tiên, ưu tiên mục yêu cầu."""
    strict_re, strict, loose_re, loose = matchers
    found: dict[str, tuple[str, str, str]] = {}
    rank = {"requirement": 0, "title": 1, "description": 2}
    for sec, line in [("title", title)] + sections(desc):
        hits = []
        if strict_re:
            hits += [(m.group(0), *strict[m.group(0)]) for m in strict_re.finditer(line)]
        if loose_re:
            hits += [(m.group(0), *loose[m.group(0)]) for m in loose_re.finditer(fold(line))]
        for term, sid, exact in hits:
            if sid not in found or rank[sec] < rank[found[sid][2]]:
                found[sid] = (term, "dict_exact" if exact else "dict_alias", sec)
    return found


# --- cụm chưa khớp ---

TRIGGER = re.compile(
    r"(?:thành thạo|sử dụng thành thạo|sử dụng được|biết sử dụng|kinh nghiệm (?:về|với|làm)?|"
    r"kiến thức (?:về)?|am hiểu (?:về)?|hiểu biết (?:về)?|kỹ năng|chứng chỉ|"
    r"proficient in|experience (?:in|with)|knowledge of|familiar with|skilled in)\s+"
    r"([^\n,;:.()\-–/]{3,60})", re.I)
TECH_TOKEN = re.compile(r"(?<![\w.])([A-Z][A-Za-z0-9+#]*[A-Z0-9+#][A-Za-z0-9+#]*(?:\s?[0-9]{3,5})?)(?![\w])")
CUT = re.compile(r"\s(và|hoặc|là|có|để|trong|cho|các|với|tốt|and|or|is|a|the)\s.*$", re.I)


def candidates(line: str) -> list[str]:
    out = [CUT.sub("", m.group(1)).strip() for m in TRIGGER.finditer(line)]
    out += TECH_TOKEN.findall(line)
    return [c for c in out if 2 <= len(c) <= 50]


def main() -> int:
    entries, dim = load_dictionary()
    matchers = compile_matchers(entries)
    stop = {fold(l) for l in STOPTERMS.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")}
    known = {fold(a) for _, a, _, _ in entries} | {fold(r["name_vi"]) for r in dim.values()}

    con = duckdb.connect(str(DB))
    posts = con.execute("""SELECT posting_id, title, description FROM posting""").fetchall()
    facts, cand_count, cand_posts, cand_examples, cand_display = [], Counter(), Counter(), defaultdict(list), {}
    for pid, title, desc in posts:
        for sid, (term, how, sec) in match(title, desc, matchers).items():
            facts.append((pid, sid, term, how, sec))
        seen_here = set()
        for sec, line in sections(desc):
            if sec != "requirement":
                continue
            for c in candidates(line):
                k = fold(c)
                if not k or k in known or k in stop or any(k == s or k.startswith(s + " ") for s in stop):
                    continue
                cand_count[k] += 1
                cand_display.setdefault(k, Counter())[c] += 1
                if k not in seen_here:
                    cand_posts[k] += 1
                    seen_here.add(k)
                if len(cand_examples[k]) < 2 and line.strip()[:200] not in cand_examples[k]:
                    cand_examples[k].append(line.strip()[:200])

    con.execute("DROP TABLE IF EXISTS fact_posting_skill")
    con.execute("""CREATE TABLE fact_posting_skill (posting_id VARCHAR, skill_id VARCHAR,
                   matched_term VARCHAR, match_method VARCHAR, section VARCHAR)""")
    con.executemany("INSERT INTO fact_posting_skill VALUES (?, ?, ?, ?, ?)", facts)

    con.execute("DROP TABLE IF EXISTS dim_skill")
    con.execute("""CREATE TABLE dim_skill AS SELECT * FROM read_csv(?, header=true, all_varchar=true)""",
                [str(SEED)])

    # chỉ số kiểm tra: tỷ lệ tin trong phạm vi có ≥1 kỹ năng chuyên môn (không tính mềm/ngoại ngữ)
    cov = con.execute("""
        SELECT p.job_family_id, count(DISTINCT p.posting_id) n,
               count(DISTINCT f.posting_id) FILTER (WHERE d.skill_type NOT IN ('soft','language')) hit
        FROM posting p LEFT JOIN fact_posting_skill f USING (posting_id)
        LEFT JOIN dim_skill d USING (skill_id)
        WHERE p.in_scope AND NOT p.is_repost GROUP BY 1 ORDER BY n DESC""").fetchall()
    tot = sum(n for _, n, _ in cov)
    log.info("tin vào %d, dòng kỹ năng ra %d", len(posts), len(facts))
    log.info("tỷ lệ tin trong phạm vi có ≥1 kỹ năng chuyên môn: %.1f%%", 100 * sum(h for *_, h in cov) / tot)
    for fam, n, hit in cov:
        log.info("  %-22s %6d tin  %5.1f%%", fam, n, 100 * hit / n)
    con.close()

    with open(UNMATCHED, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["term", "term_folded", "postings", "mentions", "example_1", "example_2", "decision"])
        for k, n in sorted(cand_posts.items(), key=lambda x: -x[1]):
            if n < 3:
                break
            ex = cand_examples[k] + ["", ""]
            w.writerow([cand_display[k].most_common(1)[0][0], k, n, cand_count[k], ex[0], ex[1], ""])
    log.info("cụm chưa khớp (≥3 tin): %d -> %s", sum(1 for n in cand_posts.values() if n >= 3), UNMATCHED)
    return 0


if __name__ == "__main__":
    sys.exit(main())
