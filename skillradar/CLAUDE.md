# SkillRadar VN — ngữ cảnh cho Claude Code

Đọc file này trước khi làm bất cứ việc gì trong repo.

## Dự án là gì

Chỉ số nhu cầu kỹ năng của thị trường lao động Việt Nam, dựng từ tin tuyển dụng
công khai. Bài dự thi mã **BTL86-59** do Bộ Tư lệnh 86 đặt bài. Đang ở **vòng 2**:
yêu cầu một sản phẩm chạy được bằng **dữ liệu thật**, có link công khai.

Người thực hiện: Nguyễn Thị Thu Thủy, làm một mình.
Hạn nộp: **22/10/2026** (10 ngày kể từ 12/10). Không có ngày đệm. Xem `PLAN.md`.

## Ràng buộc cứng — không được vi phạm, kể cả khi được yêu cầu

1. **Tôn trọng robots.txt.** Trước khi tải bất kỳ URL nào, kiểm tra robots.txt của
   host đó. Path bị Disallow thì bỏ, không tải.
2. **User-agent khai báo rõ ràng.** Luôn gửi UA chứa tên dự án và email liên hệ.
   Không giả làm trình duyệt người dùng. Email phải là email thật, không dùng
   địa chỉ mẫu như `example.com`.
3. **Không vượt rào chống bot.** Không dùng anti-detect browser, không giải CAPTCHA,
   không xoay proxy để né chặn, không dùng cookie/phiên đăng nhập. Nếu một trang
   trả về thử thách hoặc 403 cho crawler đã khai báo, **trang đó nói không** —
   ghi lại và chuyển sang nguồn khác. Đây là cam kết đã viết trong hồ sơ dự thi và
   sẽ bị giám khảo hỏi.
4. **Không thu thập dữ liệu cá nhân.** Chỉ lấy tin tuyển dụng do doanh nghiệp đăng.
   Tên, email, số điện thoại người tuyển dụng phải bị loại bỏ ngay ở tầng bronze,
   trước khi ghi xuống đĩa — kể cả trong object JSON-LD lưu kèm. Regex không nhận
   diện được tên người, nên cắt theo mốc ("Liên hệ:", "Mr./Ms./Anh/Chị ...").
   Không bao giờ chạm vào hồ sơ ứng viên.
5. **Tần suất thấp.** Tối thiểu 2 giây giữa hai request tới cùng một host, tôn trọng
   Crawl-delay nếu robots.txt có khai báo.
6. **Không bịa số.** Mọi con số hiển thị phải truy ngược được về dữ liệu đã thu.
   Thiếu dữ liệu thì hiện trạng thái "chưa đủ dữ liệu", không nội suy cho đẹp.
   Con số "mỗi tháng" tính từ chưa đủ một tháng dữ liệu phải ghi rõ
   "quy đổi từ N ngày thu thập". `python -m src.build.verify` phải chạy qua trước
   mỗi lần deploy.

## Quyết định kiến trúc đã chốt

- **Không có backend.** Crawl và xử lý chạy dưới máy local. Kết quả xuất ra các file
  JSON tĩnh trong `web/data/`. Deploy toàn bộ `web/` lên Cloudflare Pages.
  Không D1, không Worker, không API. Lý do: dưới 2 tuần, mọi thành phần chạy lúc
  demo đều là rủi ro.
- **Deploy qua git**: dự án Cloudflare Pages đã nối với repo này, tên miền
  `demo-skill-radar.ducklytics.com`, build output directory là `skillradar/web`.
  `web/data/*.json` được commit vào repo; `make deploy` = build → export → verify →
  commit + push. Không dùng `wrangler pages deploy`, không tạo dự án Pages mới.
- **Python 3.11**, thư viện tối thiểu: `httpx`, `selectolax`, `duckdb`, `pyyaml`,
  `python-dateutil` (phân tích ngày đăng), `rapidfuzz` (khoảng cách Levenshtein khi
  khử trùng), `statsmodels` (ARIMA cho dự báo, cho phép từ 14/10/2026). Không thêm
  framework. Không Scrapy, không Airflow, không Docker. Không Prophet (cần cmdstan, nặng).
- **Kho dữ liệu ba tầng**: bronze (JSONL thô) → silver (duckdb, đã chuẩn hóa) →
  gold (duckdb, hạt `một tin × một kỹ năng`). Xem `docs/DATA_SCHEMA.md`.
- **Không dùng LLM trong đường ống v1.** Trích kỹ năng bằng từ điển + luật.
  Lý do: rẻ, nhanh, giải thích được, không phụ thuộc mạng.

## Phạm vi vòng 2 — cái gì có, cái gì không

CÓ:
- Crawl 4 nguồn, tích lũy hàng ngày: itviec, vietnamworks, jobsgo, timviec365
  (danh sách nguồn đã loại và lý do: `config/sources.yaml`)
- **Phạm vi nghề (chốt 12/10)**: việc văn phòng mọi ngành (kinh doanh, kế toán, tài chính,
  ngân hàng, logistics, marketing, nhân sự, hành chính, pháp lý, CSKH, IT) **và lao động
  phổ thông** (lái xe, công nhân, kho, phục vụ, bếp, bảo vệ, giao hàng...). Kỹ thuật /
  xây dựng / sản xuất chuyên môn: chưa trong phạm vi, ghi trên trang trạng thái
- Tin lao động phổ thông thường do cá nhân/hộ kinh doanh đăng: lọc dữ liệu cá nhân càng
  phải chặt; không lưu tên chủ tin, SĐT, Zalo
- Danh mục kỹ năng song ngữ Việt–Anh, có người duyệt tay
- Nhu cầu kỹ năng dạng **ảnh chụp tỷ trọng trên các tin đang mở**, gom theo
  `posted_at`, cắt theo tỉnh (bản đồ 34 tỉnh sau 7/2025) / nhóm nghề / cấp độ.
  Ghi rõ "tin đang mở, thiếu các tin đã đóng"
- Chỉ số tiếp cận việc làm (số vị trí một bộ kỹ năng với tới được)
- Lệch cung cầu **chỉ khi** đã nhập tay được tập chỉ tiêu tuyển sinh nhỏ có
  `source_note`; không kịp thì ẩn lát cắt này và ghi lý do, không ước lượng
- Bốn lát cắt người dùng chạy trên số thật (hoặc ghi rõ lý do tắt)
- Trang trạng thái tự công bố chất lượng: F1 kèm cỡ mẫu (tập chuẩn 150 tin,
  50 vi / 50 en / 50 trộn), độ phủ theo ngày, tỷ lệ tin chưa gán nhóm nghề

KHÔNG:
- **Chỉ số nhu cầu theo tháng** (`docs/METRICS.md` §1). Crawl bắt đầu khoảng 13/10,
  tới hạn nộp chưa có tháng nào đủ 60% số ngày. Code vẫn tính, nhưng chỉ hiển thị
  khi có tháng đủ dữ liệu; chưa có thì ghi "chưa đủ dữ liệu, hiện có N ngày".
- **Dự báo định lượng.** Chưa đủ 12 kỳ thì không vẽ đường dự báo. Giao diện ghi
  "chưa đủ lịch sử để dự báo". Đây là lựa chọn có chủ đích, không phải thiếu sót.
- **Tín hiệu AI số 1** (so sánh trước/sau 2022) — cần lịch sử chưa có.
  Vòng 2 chỉ dùng tín hiệu 2 (đồng xuất hiện với công cụ AI, đo được ngay) và
  tín hiệu 3 (điểm chuyên gia trong `data/skills_seed.csv`). Giao diện phải ghi rõ
  điểm AI hiện là "điểm chuyên gia + đồng xuất hiện", chưa phải đo theo chuỗi.
- Backfill lịch sử từ Internet Archive — việc tùy chọn, chỉ làm nếu còn thời gian đệm.

## Quy ước code

- Tiếng Việt trong chuỗi hiển thị và comment. Tên biến, tên hàm tiếng Anh.
- Mỗi module chạy độc lập được: `python -m src.crawl.run`, `python -m src.build.export`.
- Mọi bước ghi log ra `logs/` kèm số dòng vào/ra, để kiểm chứng được.
- Khớp alias: alias ≤ 3 ký tự (`BA`, `PM`, `PO`, `HR`, `ML`...) khớp theo biên từ,
  **giữ dấu và phân biệt hoa thường**. Chỉ khớp không dấu với alias vốn viết không dấu.
- Không viết test giả. Nếu viết test thì test trên dữ liệu mẫu thật trong `tests/fixtures/`.
- Không tự ý đổi quyết định kiến trúc ở trên. Nếu thấy cần đổi, dừng lại và hỏi.

## Thứ tự ưu tiên khi phải đánh đổi

1. Crawler chạy đều mỗi ngày — mất một ngày là mất vĩnh viễn một điểm dữ liệu
2. Số liệu đúng và truy ngược được
3. Bốn lát cắt hoạt động
4. Giao diện đẹp

Nếu phải cắt, cắt từ dưới lên.
