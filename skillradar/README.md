# SkillRadar VN

Chỉ số nhu cầu kỹ năng của thị trường lao động Việt Nam, dựng từ tin tuyển dụng
công khai. Bài dự thi mã BTL86-59.

## Bắt đầu

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/probe_sources.py > probe_report.txt   # chọn nguồn
python -m src.crawl.run --dry-run                # kiểm tra tuân thủ, không tải
python -m src.crawl.run                          # chạy thật
```

## Tài liệu

| file | nội dung |
|---|---|
| `CLAUDE.md` | ngữ cảnh và ràng buộc cứng — đọc trước tiên |
| `PLAN.md` | kế hoạch 12 ngày, có tiêu chí hoàn thành từng việc |
| `docs/DATA_SCHEMA.md` | lược đồ ba tầng bronze / silver / gold |
| `docs/METRICS.md` | công thức mọi chỉ số |
| `docs/TAXONOMY.md` | cách dựng và duyệt danh mục kỹ năng |
| `docs/COMPLIANCE.md` | chính sách thu thập, để trả lời giám khảo |
| `docs/DEPLOY.md` | deploy lên Cloudflare Pages |

## Giấy phép

Mã nguồn: MIT. Danh mục kỹ năng công bố riêng theo CC BY 4.0.
