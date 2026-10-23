# Danh mục kỹ năng

Phần khó nhất và khó sao chép nhất. Crawler thì ai viết cũng được; một danh mục kỹ
năng song ngữ đã ngồi duyệt tay từng dòng thì không. Đây cũng là thứ sẽ công bố
theo giấy phép mở.

## Định dạng `data/skills_seed.csv`

| cột | ý nghĩa |
|---|---|
| `skill_id` | chữ thường, gạch nối, không dấu. Không bao giờ đổi sau khi đã dùng |
| `name_vi` | tên tiếng Việt |
| `name_en` | tên tiếng Anh |
| `canonical_lang` | `vi` hoặc `en` — ngôn ngữ dùng để hiển thị |
| `skill_group` | nhóm hiển thị trên radar |
| `skill_type` | `tool` / `tech` / `cert` / `domain` / `soft` / `language` |
| `esco_code` | mã ESCO, để trống nếu chưa ánh xạ |
| `vnqf_level` | bậc Khung trình độ quốc gia, để trống nếu chưa đối chiếu |
| `ai_replacement_score` | 0–1, nhóm gán tay: khả năng AI làm thay. 0 = AI chưa với tới, 1 = AI làm thay gần hết |
| `aliases` | các cách viết khác, ngăn bằng dấu `\|` |

## Quy tắc đặt tên chuẩn

Tên công cụ, công nghệ và chứng chỉ **giữ nguyên dạng tiếng Anh**, vì thị trường
gọi như vậy: `Power BI`, `Kubernetes`, `AWS`. `canonical_lang = en`.

Kỹ năng nghiệp vụ và kỹ năng nghề **đặt tên tiếng Việt**, kèm nhãn tiếng Anh để đối
chiếu quốc tế: `Phân tích nghiệp vụ` / `Business analysis`. `canonical_lang = vi`.

## Quy tắc alias

Mỗi alias phải là chuỗi **thật sự xuất hiện trong tin tuyển dụng**, không bịa.
Bắt buộc có đủ bốn dạng khi áp dụng được:

1. dạng tiếng Anh gốc: `Power BI`
2. dạng viết liền hoặc viết tắt: `PowerBI`, `PBI`
3. dạng tiếng Việt: `báo cáo BI`, `làm dashboard`
4. dạng không dấu: `bao cao BI`

Khớp alias **không phân biệt hoa thường và không phân biệt dấu**. Cẩn thận với alias
quá ngắn gây khớp nhầm: `R`, `Go`, `C` phải có luật biên từ riêng, đánh dấu trong
cột `aliases` bằng tiền tố `\b` để code biết cần khớp chặt.

## Quy trình duyệt

1. Chạy trích kỹ năng, xuất `data/unmatched_terms.csv` xếp theo tần suất
2. Với mỗi cụm từ trên xuống, chọn một trong ba:
   - **gộp**: thêm vào `aliases` của một kỹ năng đã có
   - **tạo mới**: thêm một dòng mới vào `skills_seed.csv`
   - **loại**: thêm vào `data/stopterms.txt` (ví dụ "chăm chỉ", "nhiệt tình",
     tên công ty, tên quận)
3. Chạy lại, kiểm tra tỷ lệ cụm ánh xạ được đã tăng
4. Tăng `version` ở cuối mỗi phiên duyệt

Dừng khi 50 cụm chưa khớp tiếp theo đều là rác. Thường rơi vào khoảng 300–400 kỹ năng.

## Tập chuẩn đo F1

`data/goldset.jsonl`, 300 tin gán nhãn tay, mỗi dòng:

```json
{"posting_id": "...", "lang": "mixed", "skills": ["sql", "power-bi"]}
```

Chia đều 100 tin thuần Việt, 100 thuần Anh, 100 trộn. Công bố F1 **tách riêng ba
nhóm**, vì nhóm trộn luôn khó nhất và đó chính là chỗ đề tài tạo giá trị.

Nếu có người thứ hai gán chéo được 50 tin thì tính thêm hệ số Cohen's kappa. Không
có thì ghi rõ "một người gán nhãn, chưa đo được độ đồng thuận".

## Công bố

Khi xong: xuất `taxonomy_v<version>.csv` + `taxonomy_v<version>.json` kèm giấy phép
**CC BY 4.0**, và một `README` ngắn nói rõ phạm vi, cách dựng, và những gì nó chưa
phủ được.
