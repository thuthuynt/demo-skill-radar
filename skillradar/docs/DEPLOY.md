# Deploy lên Cloudflare Pages

Chỉ deploy thư mục `web/`. Đây là trang tĩnh thuần, không có backend.

Dự án Cloudflare Pages `demo-skill-radar`, tên miền
<https://demo-skill-radar.ducklytics.com>. Dự án **đã mất kết nối git** (bản deploy cuối
qua git là 20/9) và Cloudflare không cho nối lại, nên từ 22/10 deploy bằng
`npx wrangler pages deploy` (tải thẳng `web/`). Push lên GitHub **không** tự deploy.

## Lần đầu trên một máy **[người]**

```bash
npx wrangler login      # mở trình duyệt, đăng nhập Cloudflare (OAuth)
```

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
	npx wrangler pages deploy web --project-name demo-skill-radar --branch main --commit-dirty=true

build:
	python -m src.extract.run
	python -m src.build.gold
	python -m src.build.export
	python -m src.build.verify      # dừng nếu có số liệu không truy ngược được
```

`verify` lỗi thì `make` dừng trước bước commit và deploy, không có gì lên site.

## Kiểm tra trước khi coi là xong

- [ ] Mở link ở chế độ ẩn danh, trên điện thoại
- [ ] `web/data/meta.json` có thời điểm cập nhật và số ngày thu thập đúng
- [ ] Tổng dung lượng `web/data/` dưới 1 MB
- [ ] Không còn chữ "mô phỏng" trên giao diện
- [ ] Mọi con số "mỗi tháng" có ghi "quy đổi từ N ngày"
- [ ] Nền sáng và nền tối đều đúng
- [ ] Mở bằng 3G chậm vẫn hiện trong 3 giây
