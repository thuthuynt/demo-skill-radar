"""Bóc tin từ HTML và lọc dữ liệu cá nhân trước khi ghi đĩa.

Hai cách bóc, chọn theo `method` của nguồn trong config/sources.yaml:
- `jsonld`:      thẻ <script type="application/ld+json"> có @type JobPosting (itviec)
- `next_flight`: dữ liệu Next.js App Router trong self.__next_f.push(...) (vietnamworks)
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from selectolax.lexbor import LexborHTMLParser as HTMLParser

MASK = "[đã ẩn]"

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# SĐT Việt Nam: 0xx / +84 / 84, cho phép dấu cách, chấm, gạch giữa các nhóm số
PHONE = re.compile(r"(?<!\d)(?:\+?84|0)(?:[\s.\-]?\d){8,10}(?!\d)")
# Danh xưng + tên viết hoa: "Mr. Nam", "Ms Lan Anh", "Chị Hương"
# "Tiếng Anh" không phải danh xưng: bản cũ che nhầm "Tiếng Anh Kỹ năng..." (sửa 13/10/2026)
HONORIFIC_NAME = re.compile(
    r"(?<![Tt]iếng )(?<!TIẾNG )\b(?:Mr|Mrs|Ms|Miss|Anh|Chị|Cô)\.?\s+"
    r"(?:[A-ZĐÀ-Ỹ][\wÀ-ỹ]*)(?:\s+[A-ZĐÀ-Ỹ][\wÀ-ỹ]*){0,3}")
# Sau các mốc này là thông tin người liên hệ -> cắt tới hết dòng
CONTACT_LINE = re.compile(
    r"((?:Người\s+)?liên\s+hệ|contact(?:\s+person)?|hotline|zalo)\s*[:\-–].*$",
    re.I | re.M)

# Khóa chứa thông tin liên hệ -> bỏ hẳn khỏi object lưu kèm
PII_KEYS = {"email", "telephone", "faxNumber", "contactPoint",
            "contactName", "contactEmail", "contactPhone", "emailAddress", "userId", "user"}

TRACKING_PARAMS = re.compile(r"^(utm_|fbclid|gclid|ref$|ref_|source$|click_source)", re.I)


# --- lọc dữ liệu cá nhân ---

def scrub(text: str) -> str:
    """Xóa email, SĐT, tên người liên hệ. Áp dụng cho mọi chuỗi trước khi ghi đĩa."""
    if not text:
        return text
    text = CONTACT_LINE.sub(lambda m: m.group(1) + ": " + MASK, text)
    text = EMAIL.sub(MASK, text)
    text = PHONE.sub(MASK, text)
    return HONORIFIC_NAME.sub(MASK, text)


def scrub_obj(obj):
    if isinstance(obj, dict):
        return {k: scrub_obj(v) for k, v in obj.items() if k not in PII_KEYS}
    if isinstance(obj, list):
        return [scrub_obj(v) for v in obj]
    if isinstance(obj, str):
        return scrub(obj)
    return obj


# --- tiện ích ---

def normalize_url(url: str) -> str:
    p = urlparse(url)
    q = [(k, v) for k, v in parse_qsl(p.query) if not TRACKING_PARAMS.match(k)]
    return urlunparse((p.scheme, p.netloc.lower(), p.path.rstrip("/") or "/", "",
                       urlencode(q), ""))


def html_to_text(html: str) -> str:
    if not html:
        return ""
    tree = HTMLParser(html)
    for node in tree.css("br, p, li, div, h1, h2, h3, h4, tr"):
        node.insert_after("\n")
    text = tree.text(separator=" ")
    return re.sub(r"[ \t\xa0]+", " ", re.sub(r"\n\s*\n+", "\n", text)).strip()


def _first(v):
    return v[0] if isinstance(v, list) and v else v


# --- jsonld ---

def find_job_posting(html: str) -> dict | None:
    """Trả về object JobPosting đầu tiên trong các thẻ JSON-LD."""
    tree = HTMLParser(html)
    for node in tree.css('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.text(strip=True), strict=False)
        except json.JSONDecodeError:
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                t = d.get("@type")
                if t == "JobPosting" or (isinstance(t, list) and "JobPosting" in t):
                    return d
                stack.extend(d.get("@graph", []))
    return None


def _jsonld_location(jp: dict) -> str:
    locs = jp.get("jobLocation") or []
    parts = []
    for loc in locs if isinstance(locs, list) else [locs]:
        addr = (loc or {}).get("address") or {}
        if isinstance(addr, str):
            parts.append(addr)
        else:
            parts.append(", ".join(str(addr[k]) for k in
                                   ("addressLocality", "addressRegion") if addr.get(k)))
    return " | ".join(p for p in parts if p)


def _jsonld_salary(jp: dict) -> str:
    s = jp.get("baseSalary")
    if not isinstance(s, dict):
        return str(s or "")
    v = s.get("value")
    if isinstance(v, dict):
        rng = "-".join(str(v[k]) for k in ("minValue", "maxValue") if v.get(k) is not None)
        val = rng or v.get("value") or ""
        return f"{val} {s.get('currency', '')} {v.get('unitText', '')}".strip() if val else ""
    return f"{v} {s.get('currency', '')}".strip() if v not in (None, "") else ""


def parse_jsonld(html: str) -> dict | None:
    jp = find_job_posting(html)
    if jp is None:
        return None
    org = _first(jp.get("hiringOrganization")) or {}
    return {
        "posted_at_raw": jp.get("datePosted") or "",
        "valid_through_raw": jp.get("validThrough") or "",
        "title_raw": jp.get("title") or "",
        "company_raw": org.get("name", "") if isinstance(org, dict) else str(org),
        "location_raw": _jsonld_location(jp),
        "salary_raw": _jsonld_salary(jp),
        "description_raw": html_to_text(jp.get("description") or ""),
        "structured": jp,
    }


# --- next_flight (Next.js App Router) ---

FLIGHT_CHUNK = re.compile(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', re.S)
TEXT_ROW = re.compile(rb'([0-9a-f]+):T([0-9a-f]+),')


def _flight(html: str) -> bytes:
    return "".join(json.loads(f'"{c}"') for c in FLIGHT_CHUNK.findall(html)).encode()


def _resolve(value, flight: bytes, depth: int = 0):
    """Thay các tham chiếu "$2a" bằng nội dung thật trong luồng flight."""
    if depth > 6:
        return value
    if isinstance(value, dict):
        return {k: _resolve(v, flight, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(v, flight, depth + 1) for v in value]
    if not (isinstance(value, str) and re.fullmatch(r"\$[0-9a-f]+", value)):
        return value
    ref = value[1:].encode()
    # dòng văn bản: "<id>:T<độ dài byte hex>,<nội dung>"
    for m in TEXT_ROW.finditer(flight):
        if m.group(1) == ref:
            return flight[m.end():m.end() + int(m.group(2), 16)].decode(errors="replace")
    # dòng JSON: "\n<id>:<json>\n"
    m = re.search(rb"(?:^|\n)" + re.escape(ref) + rb":([\[{].*)", flight)
    if m:
        try:
            return _resolve(json.loads(m.group(1).split(b"\n", 1)[0]), flight, depth + 1)
        except json.JSONDecodeError:
            pass
    return value


def parse_next_flight(html: str) -> dict | None:
    flight = _flight(html)
    i = flight.find(b'"jobDetail":{')
    if i < 0:
        return None
    try:
        detail, _ = json.JSONDecoder().raw_decode(flight[i + len(b'"jobDetail":'):].decode(errors="replace"))
    except json.JSONDecodeError:
        return None
    d = _resolve(detail, flight)

    def names(items, *keys):
        out = []
        for it in items if isinstance(items, list) else []:
            if isinstance(it, dict):
                out.append(next((str(it[k]) for k in keys if it.get(k)), ""))
        return [o for o in out if o]

    desc = "\n".join(html_to_text(d.get(k) or "") for k in ("jobDescription", "jobRequirement")
                     if isinstance(d.get(k), str))
    skills = names(d.get("skills"), "skillName", "skillNameVI", "name")
    return {
        "posted_at_raw": d.get("approvedOn") or d.get("onlineOn") or d.get("createdOn") or "",
        "valid_through_raw": d.get("expiredOn") or "",
        "title_raw": d.get("jobTitle") or "",
        "company_raw": d.get("companyName") or "",
        "location_raw": " | ".join(names(d.get("workingLocations"), "cityNameVI", "cityName", "address")),
        "salary_raw": d.get("prettySalaryVI") or d.get("prettySalary") or "",
        "description_raw": desc + (("\nKỹ năng: " + ", ".join(skills)) if skills else ""),
        "structured": d,
    }


# --- timviec365 (HTML dựng sẵn, không có JobPosting) ---

def _dmy(s: str) -> str:
    """'10/11/2026' -> '2026-11-10'; chuỗi khác giữ nguyên."""
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s or "")
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else (s or "")


def parse_timviec365(html: str) -> dict | None:
    tree = HTMLParser(html)
    h1 = tree.css_first("h1.titleNew")
    if h1 is None:
        return None

    def text(sel: str) -> str:
        n = tree.css_first(sel)
        return n.text(strip=True) if n else ""

    # cặp nhãn/giá trị: "Kinh nghiệm", "Hình thức làm việc", "Cập nhật", ...
    attrs = {}
    for lab_sel, val_sel in ((".titleContentSalary", ".valContentSalary"),
                             (".titleYauCauKhac", ".valYauCauKhac")):
        for lab in tree.css(lab_sel):
            val = lab.next
            while val is not None and (val.tag == "-text" or not val.css_matches(val_sel)):
                val = val.next
            if val is not None:
                attrs.setdefault(lab.text(strip=True), val.text(strip=True))

    sections = {}
    for h2 in tree.css("h2.titleInfoSpecific"):
        box = h2.parent.next
        while box is not None and box.tag == "-text":
            box = box.next
        if box is not None:
            sections[h2.text(strip=True)] = html_to_text(box.html)

    desc = "\n".join(f"{k}:\n{v}" for k, v in sections.items()
                     if k in ("Mô tả công việc", "Yêu cầu"))
    return {
        # trang chỉ có "Cập nhật" (đăng lại sẽ làm mới ngày) -> dùng thay ngày đăng
        "posted_at_raw": _dmy(attrs.get("Cập nhật", "")),
        "valid_through_raw": _dmy(text("span.valHanNop")),
        "title_raw": h1.text(strip=True),
        # .linkNtd là nhà tuyển dụng của tin; a.company_name nằm trong danh sách tin liên quan
        "company_raw": text(".boxTitleNameNtd .linkNtd"),
        # khối chi tiết chính; các .item_info khác trên trang là tin gợi ý
        "location_raw": attrs.get("Địa điểm", ""),
        "salary_raw": attrs.get("Mức lương", ""),
        "description_raw": desc,
        "structured": attrs,
    }


PARSERS = {"jsonld": parse_jsonld, "next_flight": parse_next_flight,
           "timviec365": parse_timviec365}
# Tăng khi sửa lỗi parser làm sai dữ liệu đã ghi; `run --refetch` tải lại bản cũ hơn.
# timviec365@2: sửa tên công ty (12/10/2026)
PARSER_VERSION = {"timviec365": 2}


def bronze_record(source: str, method: str, url: str, html: str) -> dict | None:
    """Một dòng bronze, đã lọc dữ liệu cá nhân. None nếu trang không bóc được."""
    fields = PARSERS[method](html)
    if fields is None:
        return None
    url = normalize_url(url)
    rec = {
        "posting_id": hashlib.sha1(f"{source}|{url}".encode()).hexdigest(),
        "source": source,
        "url": url,
        "crawled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        # tên công ty, địa điểm là dữ liệu doanh nghiệp: không lọc danh xưng ("Anh Phát")
        **{k: (v if k in ("company_raw", "location_raw") or not isinstance(v, str) else scrub(v))
           for k, v in fields.items() if k != "structured"},
        "html_sha1": hashlib.sha1(html.encode()).hexdigest(),
        "parser_version": PARSER_VERSION.get(method, 1),
        "structured": scrub_obj(fields["structured"]),
    }
    return rec
