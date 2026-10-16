# Xem docs/DEPLOY.md. Chạy trong thư mục skillradar/.
PY = .venv/bin/python

.PHONY: build deploy test

build:
	$(PY) -m src.build.silver
	$(PY) -m src.extract.run
	$(PY) -m src.build.gold
	$(PY) -m src.build.export
	$(PY) -m src.build.verify      # dừng nếu có số liệu không truy ngược được

deploy: build
	git add web/
	git diff --cached --quiet || git commit -m "Cập nhật dữ liệu $$(date -u +%Y-%m-%d)"
	git push origin main

test:
	$(PY) -m pytest -q tests
