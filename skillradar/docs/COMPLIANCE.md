# Chính sách thu thập dữ liệu

Tài liệu này để trả lời câu hỏi của giám khảo: "các bạn lấy dữ liệu thế nào".
Giữ nó cập nhật, và in kèm khi nộp.

## Nguyên tắc

1. **Chỉ tin tuyển dụng công khai** do doanh nghiệp chủ động đăng. Không bao giờ
   chạm tới hồ sơ ứng viên.
2. **Tôn trọng robots.txt.** Mọi URL đều được kiểm tra trước khi tải. Path bị
   Disallow thì không tải, kể cả khi lấy được về mặt kỹ thuật.
3. **User-agent khai báo rõ ràng**, có tên dự án và email liên hệ. Không giả làm
   trình duyệt người dùng.
4. **Không vượt rào.** Không dùng anti-detect browser, không giải CAPTCHA, không
   xoay proxy để né chặn, không dùng phiên đăng nhập. Trang nào trả về thử thách
   cho crawler đã khai báo thì ghi vào `logs/blocked.jsonl` và dừng, không thử lại
   bằng cách khác.
5. **Tần suất thấp**: tối thiểu 2 giây mỗi request cùng host, tôn trọng Crawl-delay.
6. **Không lưu dữ liệu cá nhân.** Email, số điện thoại, tên người liên hệ bị loại
   bỏ ngay trước khi ghi xuống đĩa, phù hợp Nghị định 13/2023.
7. **Công bố ở dạng tổng hợp.** Không xếp hạng hay chấm điểm từng doanh nghiệp
   tuyển dụng từ dữ liệu thu được.

## Ghi nhận nguồn

Mỗi nguồn được ghi tên trên giao diện, kèm thời điểm thu thập gần nhất.

## Đã liên hệ xin phép

| cổng | ngày gửi | kênh | phản hồi |
|---|---|---|---|
| | | | |

Điền bảng này kể cả khi không nhận được trả lời. Việc đã gửi đề nghị là một phần
của câu trả lời trước hội đồng.

## Nhật ký bị chặn

`logs/blocked.jsonl` ghi mọi lần một host từ chối, kèm thời điểm và mã lỗi. Không
xóa file này — nó chứng minh gặp chặn là dừng.

### Ghi chú về các dòng trong `blocked.jsonl`

- **2026-10-12 17:21 và 17:55 UTC, timviec365.vn, status 200 — báo nhầm.** Trang là một
  tin tuyển "Data Crawler / Web Scraping" có chữ "captcha" trong mô tả; bộ phát hiện tường
  chống bot cũ khớp chữ này và dừng cả nguồn. Trang trả 200 với nội dung tin bình thường,
  không có thử thách. Đã sửa bộ phát hiện (chỉ xét chữ ký kỹ thuật, `<title>`, và "captcha"
  trên trang ngắn) kèm test hồi quy. Các dòng gốc giữ nguyên, không xóa.
- vieclam24h.vn (403, cả robots.txt) và vieclamtot.com (403 Cloudflare ở sitemap) là chặn
  thật — đã dừng, không thử lại.

## 21/10/2026 — jobsgo chặn crawler, vietnamworks bỏ sitemap

- **jobsgo**: sau 122 request ngày 21/10, jobsgo.vn trả 403 kèm trang chặn của Cloudflare
  ("Attention Required") cho user-agent đã khai báo. Crawler dừng nguồn và ghi
  `logs/blocked.jsonl`. Theo cam kết, không vượt rào; backfill jobsgo qua Internet Archive
  cũng đã dừng (chưa ghi tin nào), vì làm vậy là đi vòng qua lệnh chặn. Ảnh chụp tin đang mở
  giữ ở ngày 21/10.
- **vietnamworks**: `sitemap/jobs.xml` và `sitemap/sitemap.xml` (khai báo trong robots.txt)
  trả 404 từ 14/10; trang tin đổi sang đuôi `-jd`, danh sách tin tải bằng API nội bộ.
  Không dùng API khi chưa được phép; ảnh chụp giữ ở 13/10.
