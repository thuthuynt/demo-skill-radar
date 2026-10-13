# Định nghĩa chỉ số

Mọi công thức ở đây phải khớp với code trong `src/build/`. Nếu lệch, sửa code,
đừng sửa tài liệu.

Quy ước chung: mọi chỉ số tính trên silver với `is_repost = FALSE` và trong phạm vi
nghề đã chốt (`PLAN.md` bước 1.1).

## 1. Nhu cầu kỹ năng

Không đếm tuyệt đối. Số tin thu được phụ thuộc độ phủ của crawler, nên đếm tuyệt
đối sẽ biến một thay đổi kỹ thuật thành một thay đổi của thị trường.

### 1a. Ảnh chụp tin đang mở — BẬT ở vòng 2

```
open(posting)    = tin xuất hiện trong lần crawl gần nhất
                   (hoặc validThrough ≥ ngày crawl, nếu nguồn có trường này)
share_open(skill) = số tin đang mở có skill / tổng số tin đang mở
```

Cắt theo tỉnh / nhóm nghề / cấp độ bằng cách lọc cả tử và mẫu. Có thể gom theo
`posted_at` (tuần) để xem tin mới đăng gần đây khác tin cũ thế nào.

Giao diện **phải** ghi: "Tỷ trọng trên các tin đang mở tại thời điểm cập nhật. Thiếu
các tin đã đóng trước khi bắt đầu thu thập." Tin còn mở lâu (khó tuyển) bị đại diện
quá mức so với tin đóng nhanh — đây là sai lệch đã biết, ghi trên trang trạng thái.

### 1b. Chỉ số theo tháng — TẮT ở vòng 2

```
share(skill, month) = số tin có skill trong tháng / tổng số tin trong tháng
index(skill, month) = 100 × share(skill, month) / share(skill, kỳ gốc)
```

Kỳ gốc = tháng đầy đủ đầu tiên thu thập được, ghi rõ trên giao diện.
Tháng dưới 60% số ngày crawl thành công (`min_days_coverage`) thì **không hiển thị**,
không nội suy.

Crawl bắt đầu khoảng 13/10/2026, nên tới hạn nộp vòng 2 chưa có tháng nào đạt ngưỡng.
Code vẫn tính, `export` chỉ xuất khi có ít nhất một tháng đạt. Chưa có thì giao diện
hiển thị: "Chưa đủ dữ liệu cho chỉ số theo tháng, hiện có N ngày thu thập."

## 2. Chỉ số tiếp cận việc làm

Đơn vị công bố ra công chúng: với bộ kỹ năng này, mỗi tháng nộp hồ sơ được vào bao
nhiêu vị trí.

```
coverage(job_family, skills) = Σ trọng số kỹ năng đang có / Σ trọng số toàn bộ
apply_rate(c)                = 0.34 / (1 + exp(-(c - 0.62) / 0.155))
reach(skills, province)      = Σ theo job_family [ số tin nhóm nghề tại tỉnh
                                × apply_rate(coverage) ]
```

Hằng số `0.34` là trần thực tế: ứng viên đáp ứng đủ yêu cầu vẫn không nộp được vào
toàn bộ tin của nhóm nghề, vì còn lọc theo cấp bậc, lĩnh vực, ngôn ngữ.
**Là giả định, phải ghi rõ trên giao diện.**

**Quy đổi theo tháng**: khi dữ liệu chưa đủ một tháng, "số tin nhóm nghề tại tỉnh"
là số tin đăng trong N ngày đã thu × 30 / N. Giao diện **phải** ghi
"quy đổi từ N ngày thu thập" cạnh con số. Tin không gán được nhóm nghề
(`job_family_id = unknown`) không tính vào reach, và tỷ lệ của chúng hiển thị trên
trang trạng thái.

## 3. Điểm tác động AI

Thiết kế đầy đủ có ba tín hiệu. **Vòng 2 chỉ chạy được hai.**

| tín hiệu | trạng thái vòng 2 |
|---|---|
| 1. Xu hướng tỷ trọng trước và sau cuối 2022 | **TẮT** — chưa có lịch sử |
| 2. Đồng xuất hiện với công cụ AI trong cùng tin | BẬT, đo từ dữ liệu thật |
| 3. Điểm chuyên gia gán tay cho từng kỹ năng | BẬT, trong `data/skills_seed.csv` |

```
cooc(skill) = tỷ lệ tin có skill mà đồng thời nhắc tới công cụ AI
              (danh sách trong data/ai_tools.txt)
ai_score    = 0.65 × ai_expert_score + 0.35 × chuẩn_hóa(cooc)
```

`data/ai_tools.txt` chỉ chứa tên sản phẩm/kỹ thuật cụ thể. Không dùng cụm chung dễ
khớp nhầm (`prompt` đơn lẻ, `trí tuệ nhân tạo`, `Claude` hay `Copilot` đứng một mình).

Giao diện **phải** ghi nhãn "điểm chuyên gia + đồng xuất hiện, chưa đo theo chuỗi
thời gian". Khi đủ 12 kỳ thì bật tín hiệu 1 và đổi trọng số.

## 4. Lệch cung cầu — có điều kiện

Chỉ tính khi `dim_training_quota` có dữ liệu nhập tay kèm `source_note`. Không có thì
**ẩn lát cắt** và ghi lý do trên giao diện, không ước lượng chỉ tiêu.

```
nhu_cầu_tuyển_mới(job_family, province, năm) = số tin/tháng × 12 × NEW_RATE
tỷ_lệ = nhu_cầu_tuyển_mới / chỉ_tiêu_tuyển_sinh
```

`số tin/tháng` quy đổi như mục 2, ghi rõ "quy đổi từ N ngày thu thập". Chỉ hiển thị
cho các cặp (nhóm nghề, tỉnh) có chỉ tiêu đã nhập; phạm vi tập chỉ tiêu ghi trên
giao diện.

`NEW_RATE` = tỷ lệ vị trí dành cho người mới ra trường. **Là giả định**, đặt 0.28,
khai báo trong `config/assumptions.yaml`, hiển thị trên giao diện. Phải nói rõ cần
khảo sát doanh nghiệp để hiệu chỉnh trước khi dùng cho quyết định phân bổ chỉ tiêu.

## 5. Dự báo — TẮT trong vòng 2

Không vẽ đường dự báo cho tới khi có **12 kỳ đầy đủ**. Chỗ biểu đồ dự báo hiển thị:
"Chưa đủ lịch sử để dự báo. Chỉ số sẽ bật khi đủ 12 kỳ, hiện có N kỳ."

Khi bật: chân trời 6–18 tháng, ARIMA hoặc Prophet có tách mùa vụ, luôn kèm khoảng
tin cậy, và **luôn hiển thị mốc ngây thơ bên cạnh**. Nếu mô hình không đánh bại
được mốc ngây thơ thì báo cáo đúng như vậy.

## 6. Chỉ số chất lượng — trang trạng thái

Công bố công khai, kể cả khi không đẹp.

| chỉ số | cách tính |
|---|---|
| F1 trích kỹ năng | trên `data/goldset.jsonl` (150 tin), tách theo vi / en / mixed, **kèm cỡ mẫu từng nhóm** |
| Tỷ lệ cụm ánh xạ được | số cụm khớp danh mục / tổng cụm trích ra |
| Tỷ lệ tin chưa gán nhóm nghề | số tin `job_family_id = unknown` / tổng số tin |
| Số tin, số nguồn | đếm trên silver, `is_repost = FALSE` |
| Số ngày thu thập | số ngày crawl thành công kể từ ngày đầu |
| Độ trễ thu thập | trung vị `crawled_at − posted_at` |
| Độ phủ theo ngày | số ngày crawl thành công / số ngày trong kỳ |
| Phiên bản danh mục | `dim_skill.version` |

## 7. Kiểm chứng

`python -m src.build.verify` tính lại mọi con số trong `web/data/*.json` bằng SQL
trên duckdb và thoát với mã lỗi khác 0 nếu có số lệch. `make deploy` dừng nếu bước
này lỗi.
