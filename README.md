# SkillRadar VN — Demo

Trang demo tĩnh cho SkillRadar VN: công cụ ước lượng giá trị và vòng đời
kỹ năng theo ngành, trường và thị trường lao động Việt Nam.

## Nội dung

- `index.html` — toàn bộ demo trong một file tĩnh (HTML + CSS + JS inline).
  Phụ thuộc bên ngoài duy nhất là Google Fonts.

## Chạy tại máy

```bash
python3 -m http.server 8000
# mở http://localhost:8000
```

## Triển khai

Site tĩnh, deploy qua Cloudflare Pages (kết nối trực tiếp với repo này,
tự động build lại mỗi khi push lên `main`):

- Framework preset: **None**
- Build command: *(để trống)*
- Build output directory: `/`

Tên miền: <https://demo-skill-radar.ducklytics.com>
