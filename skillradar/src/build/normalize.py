"""Hàm chuẩn hóa thuần (không I/O) cho tầng silver: tỉnh, cấp độ, lương, ngôn ngữ, nhóm nghề."""

import csv
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"


def fold(s: str) -> str:
    """Bỏ dấu, chữ thường, gọn khoảng trắng: 'Hồ Chí Minh' -> 'ho chi minh'."""
    s = unicodedata.normalize("NFD", s or "").replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip()


# --- tỉnh ---

@lru_cache(maxsize=1)
def _province_index() -> list[tuple[str, str]]:
    """(tên đã fold, mã tỉnh), tên dài trước để 'ha nam' không ăn vào 'ha noi'."""
    pairs = []
    with open(DATA / "provinces.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            names = [row["name"], *row["old_names"].split("|"), *row["aliases"].split("|")]
            pairs += [(fold(n), row["province_code"]) for n in names if n.strip()]
    return sorted(set(pairs), key=lambda p: -len(p[0]))


FOREIGN = re.compile(r"\b(quoc te|nuoc ngoai|overseas|international)\b")
# mã ngoài danh sách tỉnh: tin tuyển nhiều nơi / theo miền
AREA = [("toan-quoc", r"\b(toan quoc|nationwide)\b"), ("mien-bac", r"\bmien bac\b"),
        ("mien-trung", r"\bmien trung\b"), ("mien-nam", r"\b(mien nam|dbscl|mien tay)\b")]


def provinces(location: str) -> list[str]:
    """Mọi tỉnh trong chuỗi địa điểm, theo thứ tự xuất hiện, không trùng.
    Định dạng thường gặp: 'Quận 3, Hồ Chí Minh | Hà Nội'."""
    out = []
    for seg in (location or "").split("|"):
        f = fold(seg)
        if not f:
            continue
        if FOREIGN.search(f):
            code = "nuoc-ngoai"
        elif area := next((c for c, pat in AREA if re.search(pat, f)), None):
            code = area
        else:
            # ưu tiên phần sau dấu phẩy cuối (tỉnh), rồi mới tìm trong cả đoạn
            tail = fold(seg.split(",")[-1])
            code = next((c for n, c in _province_index() if tail == n), None) or \
                next((c for n, c in _province_index() if re.search(rf"\b{re.escape(n)}\b", f)), None)
        if code and code not in out:
            out.append(code)
    return out


# --- cấp độ ---

SENIORITY = [
    ("fresher", r"\b(intern|internship|thuc tap|fresher|moi tot nghiep|sinh vien)\b"),
    ("senior", r"\b(senior|sr|lead|leader|truong nhom|truong phong|truong bo phan|head|manager|"
               r"quan ly|giam doc|director|principal|chief|pho phong|chuyen gia|expert|architect)\b"),
    ("junior", r"\b(junior|jr)\b"),
    ("mid", r"\b(middle|mid|mid level)\b"),
]


def seniority(title: str) -> str:
    f = fold(title)
    return next((lvl for lvl, pat in SENIORITY if re.search(pat, f)), "unknown")


# --- lương ---

NEGOTIABLE = re.compile(r"thoa thuan|thuong luong|canh tranh|negotiable|competitive|love it|hap dan")


def _amount(tok: str, unit_hint: str) -> float | None:
    t = tok.strip().lower()
    mult = 1.0
    if re.search(r"(tr|trieu|m)$", t):
        mult, t = 1e6, re.sub(r"(tr|trieu|m)$", "", t)
    elif t.endswith("k"):
        mult, t = 1e3, t[:-1]
    t = t.replace(" ", "")
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", t):        # 20.000.000 hoặc 1,500
        t = re.sub(r"[.,]", "", t)
    else:
        t = t.replace(",", ".")
    try:
        v = float(t) * mult
    except ValueError:
        return None
    # "10 - 15" không đơn vị trong tin VND -> triệu
    if unit_hint == "VND" and v < 1000:
        v *= 1e6
    return v


def _deaccent(s: str) -> str:
    """Bỏ dấu, chữ thường, GIỮ dấu câu (cần cho '1,500' và '20.000.000')."""
    s = unicodedata.normalize("NFD", s or "").replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def salary(raw: str) -> tuple[float | None, float | None, str | None]:
    """(min, max, đơn vị tiền) theo THÁNG. NULL nếu thỏa thuận / không đọc được."""
    t = _deaccent(raw)
    if not re.search(r"\d", t):
        return None, None, None
    unit = "USD" if re.search(r"usd|\$", t) else "VND"
    toks = re.findall(r"\d[\d.,]*(?:\s*(?:trieu|tr|k|m)\b)?", t)
    vals = [v for v in (_amount(x.replace("trieu", "tr"), unit) for x in toks) if v]
    if not vals:
        return None, None, None
    if re.search(r"/\s*nam|per year|/year|annual", t):
        vals = [v / 12 for v in vals]
    lo, hi = min(vals[:2]), max(vals[:2])
    if len(vals) == 1:
        if re.search(r"\b(tren|tu|from)\b", t):
            return lo, None, unit
        if re.search(r"\b(up to|upto|toi|toi da|den|max)\b", t):
            return None, hi, unit
    return lo, hi, unit


# --- ngôn ngữ ---

VI_MARK = re.compile(r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", re.I)


def lang(text: str) -> str:
    """vi / en / mixed theo tỷ lệ từ có dấu tiếng Việt."""
    words = re.findall(r"[^\W\d_]{2,}", text or "")
    if len(words) < 20:
        return "unknown"
    share = sum(bool(VI_MARK.search(w)) for w in words) / len(words)
    return "vi" if share >= 0.30 else "en" if share <= 0.03 else "mixed"


# --- nhóm nghề ---

FAMILIES = {
    "cntt": "Công nghệ thông tin",
    "kinh-doanh": "Kinh doanh / bán hàng",
    "ke-toan": "Kế toán / kiểm toán",
    "tai-chinh-ngan-hang": "Tài chính / ngân hàng / bảo hiểm",
    "marketing": "Marketing / truyền thông",
    "nhan-su": "Nhân sự",
    "hanh-chinh": "Hành chính / văn phòng",
    "logistics": "Logistics / xuất nhập khẩu",
    "phap-ly": "Pháp lý",
    "cskh": "Chăm sóc khách hàng",
    "giao-duc": "Giáo dục / đào tạo",
    "thiet-ke": "Thiết kế / sáng tạo",
    "quan-ly": "Quản lý điều hành",
    "dich-vu-ban-le": "Dịch vụ / bán lẻ tuyến đầu",
    "lao-dong-pho-thong": "Lao động phổ thông",
    # ngoài phạm vi vòng 2: vẫn lưu, không hiển thị chỉ số
    "ky-thuat-san-xuat": "Kỹ thuật / xây dựng / sản xuất",
    "y-te": "Y tế / dược",
    "khac": "Khác",
}
OUT_OF_SCOPE = {"ky-thuat-san-xuat", "y-te", "khac"}

# Luật theo tiêu đề (đã fold). Thứ tự quan trọng: lao động & dịch vụ tuyến đầu trước,
# vì "nhân viên giao hàng" thuộc nhóm "Kinh doanh" trên vietnamworks nhưng là lao động phổ thông.
TITLE_FIRST = [
    ("lao-dong-pho-thong", r"\b(lai xe|tai xe|driver|cong nhan|lao dong pho thong|ldpt|boc xep|"
                           r"phu kho|shipper|giao hang|giao nhan hang|bao ve|tap vu|ve sinh cong nghiep|"
                           r"giup viec|dau bep|phu bep|bep chinh|tho (may|han|dien|xay|son|moc|co khi|phu)|"
                           r"tho\b|lao dong|van hanh may|dong goi|xe nang|phu xe)\b"),
    ("dich-vu-ban-le", r"\b(phuc vu|pha che|barista|bartender|thu ngan|cashier|nhan vien ban hang tai|"
                       r"ban hang (tai )?cua hang|nhan vien cua hang|nhan vien sieu thi|le tan|receptionist|"
                       r"buong phong|nhan vien quay|tu van ban hang tai|nhan vien nha hang|ky thuat vien spa|"
                       r"ktv spa|nail)\b"),
]
TITLE_REST = [
    ("cntt", r"\b(developer|lap trinh|software|devops|tester|qa qc phan mem|it support|it helpdesk|"
             r"data engineer|data analyst|data scientist|backend|frontend|fullstack|full stack|"
             r"engineer it|system admin|quan tri mang|an ninh mang|security|cntt|ai engineer|machine learning)\b"),
    ("ke-toan", r"\b(ke toan|kiem toan|accountant|accounting|auditor|thu quy)\b"),
    ("tai-chinh-ngan-hang", r"\b(ngan hang|banking|tin dung|credit|tai chinh|finance|financial|chung khoan|"
                            r"dau tu|bao hiem|insurance|teller|giao dich vien)\b"),
    ("marketing", r"\b(marketing|truyen thong|content|seo|digital|brand|thuong hieu|pr|social media|"
                  r"quang cao|copywriter|media)\b"),
    ("nhan-su", r"\b(nhan su|tuyen dung|hr|human resource|recruiter|c b|tien luong|dao tao noi bo)\b"),
    ("logistics", r"\b(logistics|xuat nhap khau|xnk|import|export|kho van|thu kho|supply chain|"
                  r"chuoi cung ung|mua hang|purchasing|procurement|dieu phoi van tai|forwarder|chung tu)\b"),
    ("phap-ly", r"\b(phap ly|phap che|legal|luat su|lawyer|compliance|tuan thu)\b"),
    ("cskh", r"\b(cham soc khach hang|cskh|customer service|customer support|call center|tong dai)\b"),
    ("giao-duc", r"\b(giao vien|giang vien|teacher|tro giang|gia su|tutor|giao duc)\b"),
    ("thiet-ke", r"\b(thiet ke do hoa|graphic|designer|ui ux|video editor|dung phim|nhiep anh)\b"),
    ("hanh-chinh", r"\b(hanh chinh|van phong|thu ky|tro ly|assistant|secretary|admin|nhap lieu|le tan van phong)\b"),
    ("kinh-doanh", r"\b(kinh doanh|sales|sale|ban hang|telesales|tu van|business development|"
                   r"phat trien thi truong|account manager|dai dien thuong mai)\b"),
    ("quan-ly", r"\b(ceo|coo|giam doc dieu hanh|general manager|tong giam doc)\b"),
    ("y-te", r"\b(bac si|dieu duong|y ta|duoc si|nurse|doctor|pharmacist|ky thuat vien xet nghiem)\b"),
    ("ky-thuat-san-xuat", r"\b(ky su|engineer|ky thuat|technician|xay dung|kien truc|co khi|dien tu|"
                          r"san xuat|qa|qc|bao tri|giam sat cong trinh|autocad|plc)\b"),
]

VNW_FAMILY = {
    "Kinh Doanh": "kinh-doanh", "Kế Toán/Kiểm Toán": "ke-toan",
    "Kiến Trúc/Xây Dựng": "ky-thuat-san-xuat", "Sản Xuất": "ky-thuat-san-xuat",
    "Công Nghệ Thông Tin/Viễn Thông": "cntt", "Khoa Học & Kỹ Thuật": "ky-thuat-san-xuat",
    "Hậu Cần/Xuất Nhập Khẩu/Kho Bãi": "logistics", "Ngân Hàng & Dịch Vụ Tài Chính": "tai-chinh-ngan-hang",
    "Tiếp Thị, Quảng Cáo/Truyền Thông": "marketing", "Nhân Sự/Tuyển Dụng": "nhan-su",
    "Hành Chính Văn Phòng": "hanh-chinh", "Kỹ Thuật": "ky-thuat-san-xuat", "Pháp Lý": "phap-ly",
    "Giáo Dục": "giao-duc", "Dệt May/Da Giày": "ky-thuat-san-xuat", "Bất Động Sản": "kinh-doanh",
    "Thiết Kế": "thiet-ke", "Dịch Vụ Khách Hàng": "cskh", "CEO & General Management": "quan-ly",
    "Bán Lẻ/Tiêu Dùng": "dich-vu-ban-le", "Dược": "y-te", "Y Tế/Chăm Sóc Sức Khoẻ": "y-te",
    "Dịch Vụ Ăn Uống": "dich-vu-ban-le", "Bảo Hiểm": "tai-chinh-ngan-hang",
    "Nhà Hàng - Khách Sạn/Du Lịch": "dich-vu-ban-le", "Vận Tải": "logistics",
    "Nông/Lâm/Ngư Nghiệp": "ky-thuat-san-xuat",
    "Nghệ thuật, Truyền thông/In ấn/Xuất bản": "marketing",
}


def _by_title(title: str, rules) -> str | None:
    f = fold(title)
    return next((fam for fam, pat in rules if re.search(pat, f)), None)


def job_family(source: str, title: str, structured: dict | None) -> tuple[str, str]:
    """(job_family_id, cách gán). Cách gán ghi lại để kiểm chứng trên trang trạng thái."""
    if fam := _by_title(title, TITLE_FIRST):
        return fam, "title_first"
    if source == "itviec":
        return "cntt", "source"
    s = structured or {}
    if source == "vietnamworks":
        jf = s.get("jobFunction") or {}
        fam = VNW_FAMILY.get(jf.get("parentNameVI", "")) if isinstance(jf, dict) else None
        if fam:
            return fam, "source"
    if source == "jobsgo":
        ind = s.get("industry")
        first = ind[0] if isinstance(ind, list) and ind else ind
        if isinstance(first, str) and (fam := _by_title(first, TITLE_FIRST + TITLE_REST)):
            return fam, "source"
    if fam := _by_title(title, TITLE_REST):
        return fam, "title"
    return "khac", "none"
