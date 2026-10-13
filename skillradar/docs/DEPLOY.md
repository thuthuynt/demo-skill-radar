# Deploy lên Cloudflare Pages

Chỉ deploy thư mục `web/`. Đây là trang tĩnh thuần, không có backend.

Dùng dự án Cloudflare Pages **đã nối git** với repo này, tên miền
<https://demo-skill-radar.ducklytics.com>. Pages tự build lại mỗi khi push lên
`main`. Không dùng `wrangler pages deploy`, không tạo dự án Pages mới.

## Lần đầu **[người]**

Trong Cloudflare dashboard → dự án Pages → Settings → Builds:

- Framework preset: **None**
- Build command: *(để trống)*
- Build output directory: đổi từ `/` thành **`skillradar/web`**

Sau khi đổi, cập nhật mục "Triển khai" trong `README.md` ở gốc repo cho khớp.

`web/data/*.json` **được commit vào repo** — đó là cách dữ liệu lên site.
Không đưa `warehouse/`, `logs/` hay file duckdb vào git.

## Mỗi lần cập nhật dữ liệu

```bash
make deploy
```

`Makefile`:

```make
deploy: build
	git add web/
	git diff --cached --quiet || git commit -m "Cập nhật dữ liệu $$(date -u +%Y-%m-%d)"
	git push origin main

build:
	python -m src.extract.run
	python -m src.build.gold
	python -m src.build.export
	python -m src.build.verify      # dừng nếu có số liệu không truy ngược được
```

`verify` lỗi thì `make` dừng trước bước commit, không có gì lên site.

## Kiểm tra trước khi coi là xong

- [ ] Mở link ở chế độ ẩn danh, trên điện thoại
- [ ] `web/data/meta.json` có thời điểm cập nhật và số ngày thu thập đúng
- [ ] Tổng dung lượng `web/data/` dưới 1 MB
- [ ] Không còn chữ "mô phỏng" trên giao diện
- [ ] Mọi con số "mỗi tháng" có ghi "quy đổi từ N ngày"
- [ ] Nền sáng và nền tối đều đúng
- [ ] Mở bằng 3G chậm vẫn hiện trong 3 giây
