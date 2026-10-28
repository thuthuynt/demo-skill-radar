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


# Nghề trong nhóm nghề (chốt 28/10/2026, 7 nhóm lớn): (id, tên, luật theo tiêu đề đã fold).
# Thứ tự quan trọng: luật cụ thể trước, luật chung ("kế toán", "kinh doanh") cuối.
# Không khớp luật nào -> None: trang ghi "chưa gán nghề cụ thể", không đoán.
OCCUPATIONS = {
    "cntt": [
        ("data-analyst", "Phân tích dữ liệu (Data Analyst)",
         r"data analyst|phan tich du lieu|bi analyst|bi developer|business intelligence|power bi"),
        ("data-engineer", "Kỹ sư dữ liệu (Data Engineer)", r"data engineer|ky su du lieu|\betl\b|data platform|data warehouse"),
        ("business-analyst", "Phân tích nghiệp vụ (Business Analyst)", r"business analyst|\bba\b|phan tich nghiep vu"),
        ("tester", "Kiểm thử phần mềm (Tester / QA)",
         r"tester|\bqa\b|\bqc\b|quality control|test engineer|test automation|automation test|kiem thu|sdet"),
        ("devops", "DevOps / Cloud", r"devops|devsecops|\bsre\b|cloud|platform engineer|kubernetes"),
        # tên vị trí AI, không phải tin chỉ nhắc AI như một kỹ năng ("business analyst ai")
        ("ai-engineer", "Kỹ sư AI / Data Scientist",
         r"data scien|khoa hoc du lieu|machine learning|\bml engineer|deep learning|computer vision|\bnlp\b|tri tue nhan tao|"
         r"\bai (engineer|agent|software|developer|specialist|researcher|automation|solution|intern|operations)|"
         r"(thuc tap sinh|staff|expert) ai\b"),
        ("it-security", "An toàn thông tin", r"security|bao mat|an toan thong tin|an ninh mang|pentest|soc analyst|incident"),
        ("mobile-dev", "Lập trình mobile", r"mobile|android|\bios\b|flutter|react native"),
        ("frontend-dev", "Lập trình frontend", r"front ?end|reactjs|react developer|vuejs|angular"),
        ("fullstack-dev", "Lập trình fullstack", r"full ?stack"),
        ("software-dev", "Lập trình viên / kỹ sư phần mềm (backend)",
         r"back ?end|\bjava\b|\bnet\b|golang|\bphp\b|python|nodejs|node js|ruby|\bc\b|software|developer|lap trinh|"
         r"ky su phan mem|architect|technical lead|tech lead|javascript"),
        ("it-pm", "Quản lý dự án / sản phẩm IT (PM, PO)",
         r"project (manager|leader|management)|product (owner|manager)|scrum|quan ly du an|delivery manager|\bpm\b|\bpo\b|brse"),
        ("it-support", "Hỗ trợ kỹ thuật IT (IT support)",
         r"it support|helpdesk|help desk|ho tro ky thuat|technical support|nhan vien it|it staff|it executive|"
         r"ky thuat vien it|it technician|ky su it|it engineer|van hanh ung dung"),
        ("it-system", "Quản trị hệ thống / mạng",
         r"system admin|network|quan tri mang|quan tri he thong|\berp\b|\bsap\b|infrastructure|ha tang"),
        ("it-manager", "Trưởng phòng IT", r"it manager|truong phong it|truong phong cong nghe|head of|\bcto\b|giam doc cong nghe"),
    ],
    "kinh-doanh": [
        ("sales-bds", "Kinh doanh bất động sản", r"bat dong san|real estate|moi gioi"),
        ("sales-supervisor", "Giám sát bán hàng / kinh doanh khu vực",
         r"giam sat (ban hang|kinh doanh)|sales supervisor|\basm\b|area sales|kinh doanh khu vuc"),
        ("sales-b2b", "Kinh doanh B2B / dự án / khách hàng lớn",
         r"b2b|khach hang doanh nghiep|key account|account manager|kinh doanh du an|ky su (kinh doanh|ban hang)|"
         r"sales engineer|kinh doanh ky thuat"),
        ("business-dev", "Phát triển kinh doanh / thị trường quốc tế",
         r"business development|phat trien kinh doanh|phat trien doi tac|kinh doanh quoc te|xuat khau"),
        ("sales-field", "Kinh doanh thị trường (sales thị trường)", r"kinh doanh thi truong|sales? thi truong|phat trien thi truong"),
        ("sales-consultant", "Tư vấn bán hàng / telesales",
         r"telesale|tu van|cham soc khach hang|consultant"),
        ("sales-rep", "Nhân viên kinh doanh (chung)", r"kinh doanh|sales?|ban hang"),
    ],
    "ke-toan": [
        ("chief-accountant", "Kế toán trưởng", r"ke toan truong|chief accountant|phu trach ke toan|truong phong ke toan"),
        ("auditor", "Kiểm toán / kiểm soát nội bộ", r"kiem toan|audit|kiem soat noi bo"),
        ("tax-accountant", "Kế toán thuế", r"ke toan thue|\btax\b"),
        ("cost-accountant", "Kế toán giá thành / quản trị", r"gia thanh|ke toan quan tri|\bcost\b"),
        ("ledger-accountant", "Kế toán chi tiết (công nợ, thanh toán, kho, bán hàng)",
         r"cong no|thanh toan|ke toan ban hang|doanh thu|ke toan kho|payable|receivable"),
        ("internal-accountant", "Kế toán nội bộ", r"ke toan noi bo"),
        ("general-accountant", "Kế toán tổng hợp", r"ke toan tong hop|general accountant"),
        ("accountant", "Kế toán viên (chung)", r"ke toan|accountant|accounting"),
    ],
    "marketing": [
        ("digital-marketing", "Digital marketing / quảng cáo / SEO",
         r"digital|performance|\bads\b|quang cao|facebook|google|\bseo\b|\bsem\b|growth|e commerce|ecommerce|san thuong mai"),
        ("content-marketing", "Content / mạng xã hội",
         r"content|noi dung|copywriter|bien tap|creator|writer|video|tiktok|social media|\bkol\b|\bkoc\b|livestream"),
        ("brand-marketing", "Brand / trade marketing", r"brand|thuong hieu|trade marketing"),
        ("pr-event", "Truyền thông / PR / sự kiện", r"truyen thong|\bpr\b|event|su kien|media|bao chi"),
        ("marketing-general", "Marketing tổng hợp", r"marketing"),
    ],
    "nhan-su": [
        ("cnb", "C&B / tiền lương", r"\bc b\b|tien luong|payroll|compensation|bao hiem xa hoi|cham cong"),
        ("recruiter", "Tuyển dụng", r"tuyen dung|recruit|talent acquisition|headhunt"),
        ("hr-training", "Đào tạo nội bộ (L&D)", r"dao tao|training|\bl d\b|learning"),
        ("hr-admin", "Hành chính – nhân sự", r"hanh chinh|hanh chanh"),
        ("hr-generalist", "Nhân sự tổng hợp / HRBP", r"nhan su|\bhr|human resource|doi tac nhan su"),
    ],
    "tai-chinh-ngan-hang": [
        ("bank-risk", "Quản trị rủi ro / tuân thủ", r"rui ro|\brisk\b|tuan thu|compliance|kiem soat"),
        ("relationship-manager", "Quan hệ khách hàng / tín dụng ngân hàng",
         r"quan he khach hang|relationship|\brm\b|khach hang (doanh nghiep|ca nhan|uu tien)|tin dung|credit|cho vay"),
        ("bank-teller", "Giao dịch viên / dịch vụ ngân hàng",
         r"giao dich vien|teller|phong giao dich|thanh toan quoc te|remittance|dich vu khach hang"),
        ("financial-analyst", "Phân tích tài chính / đầu tư",
         r"phan tich|dau tu|chung khoan|investment|analyst|nguon von|treasury|hoach dinh tai chinh|ke hoach tai chinh"),
        ("insurance-advisor", "Tư vấn bảo hiểm / tài chính", r"bao hiem|insurance|tu van tai chinh"),
    ],
    "logistics": [
        ("purchasing", "Mua hàng / thu mua",
         r"mua hang|thu mua|purchas|procurement|cung ung|vat tu|dau thau|sourcing"),
        ("import-export", "Xuất nhập khẩu / chứng từ / hải quan",
         r"xuat nhap khau|\bxnk\b|import|export|hai quan|customs|chung tu"),
        ("supply-planner", "Lập kế hoạch chuỗi cung ứng", r"supply chain|chuoi cung ung|planner|ke hoach"),
        ("warehouse", "Kho vận / thủ kho", r"\bkho\b|warehouse"),
        ("transport", "Điều phối vận tải / giao nhận",
         r"dieu phoi|van tai|giao nhan|forward|transport|dispatch|logistics coordinator"),
        ("logistics-general", "Logistics tổng hợp", r"logistics"),
    ],
}


def occupation(family: str, title: str) -> str | None:
    f = fold(title)
    return next((oid for oid, _name, pat in OCCUPATIONS.get(family, []) if re.search(pat, f)), None)


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
