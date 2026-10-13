# Lược đồ dữ liệu

Ba tầng. Nguyên tắc: tầng bronze giữ nguyên để lúc nào cũng chạy lại được từ đầu;
mọi phép biến đổi nằm trong code có phiên bản.

## Bronze — JSONL thô

`warehouse/bronze/<YYYY-MM-DD>/<source>.jsonl`, mỗi dòng một tin.

| trường | kiểu | ghi chú |
|---|---|---|
| `posting_id` | str | sha1 của `source` + URL đã chuẩn hóa |
| `source` | str | tên nguồn, ví dụ `itviec` |
| `url` | str | URL tin, đã bỏ tham số theo dõi |
| `crawled_at` | str | ISO 8601, UTC |
| `posted_at_raw` | str | chuỗi ngày đăng như trang hiển thị |
| `title_raw` | str | tiêu đề |
| `company_raw` | str | tên công ty |
| `location_raw` | str | địa điểm như trang hiển thị |
| `salary_raw` | str | chuỗi lương, chưa phân tích |
| `description_raw` | str | toàn bộ mô tả, đã bỏ thẻ HTML |
| `html_sha1` | str | để phát hiện tin sửa nội dung |

**Lọc trước khi ghi đĩa**: xóa email, số điện thoại và tên người liên hệ khỏi
`description_raw` bằng regex. Không có ngoại lệ. Đây là cam kết trong hồ sơ dự thi.

## Silver — duckdb, bảng `posting`

| trường | ghi chú |
|---|---|
| `posting_id` | khóa chính |
| `source`, `url`, `crawled_at` | |
| `posted_at` | DATE, phân tích từ `posted_at_raw` |
| `title` | đã gọn khoảng trắng |
| `company_id` | khóa tới `dim_company` |
| `province_code` | chuẩn hóa về mã tỉnh, xem `data/provinces.csv` |
| `seniority` | `fresher` / `junior` / `mid` / `senior` / `unknown`, suy từ tiêu đề |
| `salary_min`, `salary_max`, `salary_unit` | NULL nếu tin ghi "thỏa thuận" |
| `lang` | `vi` / `en` / `mixed`, nhận diện trên mô tả |
| `description` | |
| `is_repost` | TRUE nếu trùng công ty + tiêu đề gần giống trong 30 ngày |

**Khử trùng**: hai tin cùng `company_id`, tiêu đề có khoảng cách Levenshtein chuẩn
hóa dưới 0,15, cách nhau dưới 30 ngày thì tin sau đánh `is_repost = TRUE`.
Mọi chỉ số tính trên `is_repost = FALSE`.

## Gold — duckdb

### `fact_posting_skill` — hạt `một tin × một kỹ năng`

Quyết định thiết kế quan trọng nhất. Mọi chỉ số về sau chỉ là phép gộp trên bảng này.

| trường | ghi chú |
|---|---|
| `posting_id` | |
| `skill_id` | khóa tới `dim_skill` |
| `matched_term` | cụm thực tế xuất hiện trong tin |
| `match_method` | `dict_exact` / `dict_alias` / `rule` |
| `section` | `requirement` / `description` / `title`, nếu tách được |

### Bảng chiều

- `dim_skill`: `skill_id`, `name_vi`, `name_en`, `canonical_lang`, `skill_group`,
  `skill_type`, `esco_code`, `vnqf_level`, `ai_expert_score`, `version`
- `dim_company`: `company_id`, `name`, `name_normalized`
- `dim_province`: `province_code`, `name`, `region`
- `dim_job_family`: `job_family_id`, `name`; bảng nối `job_family_skill` với trọng số
  (tỷ lệ tin của nhóm nghề có yêu cầu kỹ năng đó, tính từ dữ liệu, không nhập tay)

### `dim_training_quota` — phía cung

`major_name`, `job_family_id`, `province_code`, `year`, `quota`, `source_note`.

`source_note` **bắt buộc**: lấy từ đâu, ngày nào. Nhập tay từ đề án tuyển sinh công
bố công khai. Nếu không kịp thu đủ, nhập một tập nhỏ và ghi rõ phạm vi trên giao
diện, **không được ước lượng**.

## Quy ước chung

- Mọi thời điểm lưu UTC, hiển thị giờ Việt Nam
- Không xóa dữ liệu bronze
- Mỗi lần đổi danh mục kỹ năng thì tăng `version`, để số liệu hai kỳ vẫn so được
