# Kế hoạch 10 ngày — hạn nộp 22/10/2026

Làm xong việc mới sang việc sau. **[người]** = việc bạn tự làm, Claude Code không thay được.
**Không có ngày đệm.** Phải cắt thì cắt theo thứ tự ưu tiên trong `CLAUDE.md`, từ dưới lên.

Crawler chạy trước mọi thứ: từ 13/10 nó chạy nền mỗi ngày, song song với mọi việc khác.

Chỉ số theo tháng chưa bật ở vòng 2 (chưa có tháng đủ 60% số ngày). Lát cắt nhu cầu
dùng ảnh chụp tỷ trọng trên tin đang mở — xem `docs/METRICS.md` §1a.

---

## 12/10 — Khung repo ✅

- [x] venv Python 3.11, `src/config.py`, logger ghi `logs/`
- [x] `src/crawl/polite.py`: robots.txt, Crawl-delay, ≥2 s/host, dừng host khi 403/429/tường chống bot
- [x] Test: URL bị Disallow trả về False, không phát sinh request
- [x] Email liên hệ thật trong `config/sources.yaml`
- [x] Chọn nguồn: itviec (JSON-LD) + vietnamworks (Next.js flight), crawler thật chạy, lọc dữ liệu cá nhân có test
- [x] `launchd` chạy crawler 07:00 mỗi ngày (`ops/com.ducklytics.skillradar.crawl.plist`)
- [x] Kiểm tra backfill: **GO** — itviec 31 tháng, vietnamworks 36 tháng có ≥100 tin lưu trữ;
      23/24 trang lưu trữ mẫu bóc được (`logs/wayback_check.json`)
- [ ] **[người]** Đọc điều khoản sử dụng itviec, vietnamworks, jobsgo, timviec365, đặt `terms_checked: true`
- [ ] **[người]** Gửi email xin phép (4 nguồn đang crawl + vieclam24h, vieclamtot), ghi vào `docs/COMPLIANCE.md`
- [x] Chốt phạm vi: văn phòng mọi ngành + lao động phổ thông. Thêm nguồn jobsgo (10k tin) +
      timviec365 (12,7k tin). vieclam24h, vieclamtot, mywork trả 403 -> không crawl, chỉ
      thêm nếu được cho phép qua email

## 13/10 — Chọn nguồn, crawl thật

- Chạy `src/probe_sources.py`, chọn **2 nguồn** (JobPosting > sitemap > JSON nhúng > HTML).
  Bỏ nguồn bị robots.txt chặn, có tường chống bot, hoặc điều khoản cấm thu thập.
  Ghi vào `config/sources.yaml` kèm trích đoạn robots.txt. Chốt phạm vi nghề theo nguồn.
- Crawler thật: URL từ sitemap → `warehouse/bronze/urls.jsonl`; tin →
  `warehouse/bronze/YYYY-MM-DD/<source>.jsonl` kèm object JSON-LD nguyên văn.
  Lọc dữ liệu cá nhân trước khi ghi đĩa (cắt theo mốc "Liên hệ:", "Anh/Chị…", email, SĐT).
- **[người]** Gửi email xin phép các cổng, ghi vào `docs/COMPLIANCE.md`.
- **[người]** Đặt `launchd` chạy crawler mỗi ngày; không tắt hẳn máy.
- **Kiểm tra backfill (go / no-go):** đếm số tin lưu trên Internet Archive theo tháng
  cho 2 nguồn. Đủ 12 tháng có mẫu dùng được → backfill chạy nền từ 14/10 và bật dự báo
  ở 19/10. Không đủ → dự báo tắt, giao diện ghi lý do.

> Xong khi: ≥1.000 tin trong bronze, chạy lại không sinh trùng, quyết định backfill
> đã ghi vào file này.

## 14/10 — Silver và trích kỹ năng

**Tiến độ (làm sớm, đêm 12–13/10):**
- [x] Silver `posting` (27,6k tin, 4 nguồn + lưu trữ): `python -m src.build.silver`
- [x] `data/provinces.csv` 34 tỉnh + 63 tên cũ; khớp tỉnh 98%
- [x] Nhóm nghề: luật tiêu đề + danh mục nguồn, 92% gán được; lao động phổ thông ưu tiên theo tiêu đề
- [x] Sửa alias rộng (training, recruitment, infosec, admin, negotiation, PM); bỏ mục quyền lợi khi khớp
- [x] Trích kỹ năng -> `fact_posting_skill`; 85,3% tin trong phạm vi có ≥1 kỹ năng chuyên môn
      (lao động phổ thông chỉ 25% — danh mục chưa có kỹ năng nghề này)
- [x] `data/unmatched_terms.csv`: 3,2k cụm (≥3 tin), cột `decision` để duyệt
- [x] Bổ sung 60 kỹ năng + 13 lượt alias từ `data/skill_candidates.csv` (13/10) -> 159 kỹ năng,
      93,2% tin trong phạm vi có ≥1 kỹ năng chuyên môn; lao động phổ thông 81%, giáo dục còn 70%
- [ ] **[người]** Duyệt `ai_expert_score` của 60 kỹ năng mới — hiện là ĐỀ XUẤT của Claude
      (cột `note`/`ai_expert_score` trong `data/skill_candidates.csv`), phải do bạn chốt trước khi công bố
- [x] Sửa lọc dữ liệu cá nhân che nhầm "Tiếng Anh"; silver khôi phục chữ "Anh" cho ~2,1k chỗ đã ghi


- Silver duckdb: tách trường, `data/provinces.csv` (34 tỉnh sau 7/2025, kèm tên cũ),
  cấp độ từ tiêu đề, khử trùng tin đăng lại (`rapidfuzz`).
- Nhóm nghề: luật theo tiêu đề → `job_family_id`, không khớp thì `unknown`.
- Sửa `skills_seed.csv`: alias ≤3 ký tự có `\b`, giữ dấu, phân biệt hoa thường.
  Dọn `data/ai_tools.txt` (bỏ `prompt` đơn lẻ, `trí tuệ nhân tạo`, `Claude`/`Copilot` trần).
- Trích kỹ năng bằng từ điển + luật; xuất `data/unmatched_terms.csv` (tần suất, 2 câu ví dụ).

> Xong khi: ≥85% tin trong phạm vi nghề có ít nhất 1 kỹ năng; `unmatched_terms.csv` ≥200 cụm.

## 15–16/10 — Danh mục và tập chuẩn **[người, ~20 giờ]**

- Duyệt `unmatched_terms.csv`: gộp alias / tạo kỹ năng mới / đưa vào `stopterms.txt`.
  Mục tiêu 300+ kỹ năng.
- Gán nhãn **150 tin** (50 vi / 50 en / 50 trộn) vào `data/goldset.jsonl`, lấy từ tin
  không dùng khi duyệt. Thiếu tin tiếng Anh thì lấy hết số có, ghi cỡ mẫu.

Song song (Claude Code): bảng gold `fact_posting_skill` + bảng chiều, theo `docs/DATA_SCHEMA.md`.

> Xong khi: 300+ kỹ năng; `python -m src.extract.evaluate` in F1 theo 3 nhóm kèm cỡ mẫu.

## 17/10 — Chỉ số, export, verify

- **[người, ~nửa ngày]** Nhập tay tập nhỏ chỉ tiêu tuyển sinh, có `source_note`.
  Không kịp → ẩn lát cắt lệch cung cầu.
- Chỉ số theo `docs/METRICS.md`: tỷ trọng tin đang mở, tiếp cận việc làm, điểm AI
  (tín hiệu 2 + 3), đồng xuất hiện, lệch cung cầu (nếu có chỉ tiêu). Số "mỗi tháng"
  ghi "quy đổi từ N ngày".
- `src.build.export` → `web/data/*.json` (<1 MB, kèm `meta.json`).
- `src.build.verify` tính lại mọi con số bằng SQL, lệch thì thoát lỗi.

> Xong khi: `web/data/skills.json` có số thật, `verify` chạy qua.

## 18–19/10 — Giao diện

Thay `RAW`, `JOBS`, `QUOTA` trong `web/index.html` bằng `fetch()` từ `web/data/`.
- Biểu đồ theo tháng → ảnh chụp tin đang mở, ghi "hiện có N ngày".
- Dự báo: nếu backfill **go** → mô hình + khoảng tin cậy + mốc ngây thơ bên cạnh,
  ghi rõ phần lịch sử là dữ liệu lưu trữ. Nếu **no-go** → "chưa đủ lịch sử để dự báo".
- Nhãn điểm AI "điểm chuyên gia + đồng xuất hiện".
- Trang trạng thái: F1 + cỡ mẫu, tỷ lệ ánh xạ, tỷ lệ tin chưa gán nhóm nghề, số tin,
  số nguồn, số ngày thu thập, độ trễ trung vị, độ phủ theo ngày, phiên bản danh mục.
- Chân trang: nguồn và thời điểm cập nhật thật.

> Xong khi: 4 lát cắt chạy số thật (hoặc ghi lý do tắt), không còn chữ "mô phỏng".

## 20/10 — Deploy

- **[người]** Cloudflare Pages: build output directory → `skillradar/web`.
- `make deploy` = build → export → verify → commit + push. Xem `docs/DEPLOY.md`.

> Xong khi: link mở được trên điện thoại ở chế độ ẩn danh; một lệnh cập nhật được dữ liệu.

## 21/10 — Kiểm thử và quay video

Điện thoại + máy tính, nền sáng + tối; mọi con số khớp duckdb; đọc lại mọi chữ tìm chỗ
hứa thứ chưa có; quay video.

## 22/10 — Nộp

Cập nhật dữ liệu lần cuối sáng 22/10, `make deploy`, nộp link.
