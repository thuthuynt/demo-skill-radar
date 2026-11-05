# Lời nói — trình bày vòng 2 (khoảng 12 phút)

Đi theo deck 12 slide (`web/presentation/index.html`, https://demo-skill-radar.ducklytics.com/presentation/). Số liệu cập nhật 5/11/2026. Thời gian ghi trong ngoặc là gợi ý.
Chữ *nghiêng* là thao tác, không đọc.
Mỗi lần bấm (→, Space hoặc click chuột) hiện thêm một box; hết box thì sang slide sau. ← quay lại slide trước, hiện đủ.

---

## Slide mở đầu — Câu chuyện của em (30–45 giây)

Chào các anh chị. Em là Thủy, nhóm Ducklytics, bài dự thi SkillRadar VN, mã BTL86-59.

*Kể chuyện của bản thân: lúc chọn ngành hoặc chọn việc, thiếu thông tin ra sao. Bấm sáu lần, mỗi lần hiện một câu hỏi
bên trái.* Chốt: "Hôm nay hàng trăm nghìn bạn trẻ vẫn đứng ở ngã rẽ đó."

## Slide 0 — Vì sao cần SkillRadar (45 giây)

Năm nay có gần 875 nghìn bạn trẻ đăng ký xét tuyển đại học, với hơn 7 triệu nguyện vọng.
Trung bình mỗi bạn chọn 8 ngành, và gần như không có dữ liệu nào cho biết ngành đó ngoài
thị trường đang cần gì.

Kết quả thấy rõ trong số liệu của Cục Thống kê quý III năm nay: cứ 11 thanh niên thì 1 bạn
thất nghiệp, ở thành phố là 1 trên 8, gấp bốn lần mức chung. 1,6 triệu bạn trẻ không đi học, không có việc, cũng không học nghề.
(Đây là nhóm NEET, không phải số thất nghiệp: tính cả người không tìm việc.)

Và thị trường đang đổi nhanh hơn. ILO tính có 11,5 triệu lao động Việt Nam, tức 1 trên 5
người, làm công việc chịu tác động của AI tạo sinh. Diễn đàn Kinh tế Thế giới dự báo đến
2030, gần 40% kỹ năng hiện có sẽ thay đổi, và 62% doanh nghiệp tại Việt Nam nói thiếu kỹ
năng là rào cản lớn nhất.

Học sinh, nhà trường, cơ quan quản lý đều cần một câu trả lời: hôm nay thị trường cần kỹ
năng gì, và AI đang thay đổi điều đó thế nào.

## Slide 0b — AI đang thay đổi cách người trẻ vào nghề (40 giây)

Ý lấy từ chương trình *Toàn cảnh Thế giới* (VTV24, 11/2026), ghi chép ở `docs/ai-video-notes.md`.
Bốn thẻ hiện lần lượt, câu chốt hiện cuối. Chỉ nói ý định tính, không đọc số của video.

> Tuần này VTV24 có một chương trình về AI và việc làm. Bốn điều đáng chú ý. Một: việc của nhân viên mới
> vào nghề đang được AI làm thay, nên vừa ra trường đã bị đòi như người đi làm 5 đến 10 năm. Hai: bằng cấp
> giảm giá, năng lực thực tế lên ngôi. Ba: lao động trí thức cũng chịu tác động, AI tham gia vào từng khâu
> của việc văn phòng. Bốn: người đang có việc phần lớn giữ được việc, nhưng tuyển mới chậm lại. Vậy nếu bằng
> cấp không còn đủ, thị trường đang hỏi kỹ năng gì, ngay hôm nay? Đó là việc của SkillRadar.

Nếu có mạng và còn thời gian: chọn mốc (16:20, 19:24, 22:07, 25:57) rồi bấm "Xem trích đoạn",
chiếu 20–30 giây. Rời slide là video tự tắt.

## Slide 1 — Tổng quan (30 giây)

**Vì sao làm (why).** Thông tin đó thật ra đã có sẵn, nằm rải rác trong hàng chục nghìn tin
tuyển dụng đăng công khai mỗi ngày, chỉ là chưa ai gom lại và đọc nó.

**Bọn em làm gì (what).** SkillRadar đọc tin tuyển dụng công khai mỗi ngày, tách ra kỹ năng
mà nhà tuyển dụng yêu cầu, rồi biến thành chỉ số: kỹ năng nào đang được cần nhiều, ở nghề
nào, tỉnh nào, lương ra sao, và AI đang ảnh hưởng tới nó thế nào. Mọi con số đều lấy từ dữ
liệu thật và truy ngược được.

**Dành cho ai (who).** Ba nhóm người dùng, mỗi nhóm một trang riêng:
- **Học sinh, sinh viên 17–23 tuổi**, nhóm chính: chọn nghề và biết mình cần học gì.
- **Nhà trường**: đối chiếu chương trình đào tạo với nhu cầu thực tế.
- **Cơ quan quản lý**: nắm thị trường lao động theo vùng và theo nhóm nghề.

*Chỉ các con số bên phải.* Hơn 66 nghìn tin, 159 kỹ năng, 47 nghề cụ thể, 6 nguồn, trong đó
2 nguồn lấy qua Internet Archive.

## Slide 2 — Kiến trúc: từ crawl tới website (1 phút 30)

Toàn bộ hệ thống chạy trên một laptop, không có backend.

*Chỉ cột bên trái.* Bọn em lấy dữ liệu từ 4 trang tuyển dụng. Hôm nay itviec và timviec365
chạy bình thường. vietnamworks gỡ sitemap từ 14/10 nên số liệu đứng ở ngày 13/10. jobsgo
từng chặn bọn em một ngày rồi mở lại.

*Chỉ ô crawler.* Crawler chạy 7 giờ sáng mỗi ngày, có lượt dự phòng 12 giờ 30, và theo
năm nguyên tắc đã viết trong hồ sơ dự thi: kiểm tra robots.txt, khai báo danh tính kèm email
thật, mỗi trang cách nhau ít nhất 2 giây, gặp 403 hay CAPTCHA là dừng, và xóa thông tin cá
nhân trước khi lưu. Trang nào từ chối thì bọn em dừng, không tìm cách vượt rào.

Với các trang chặn crawler như vieclam24h, topcv, bọn em không gửi request tới trang gốc mà
chỉ lấy bản lưu công khai trên Internet Archive, ghi rõ nguồn. Internet Archive cũng cho bọn
em lịch sử theo tháng từ 2025. Lâu dài, bọn em sẽ đề xuất hợp tác để có dữ liệu chính thức.

*Chỉ phần giữa và bên phải.* Dữ liệu đi qua ba tầng kho, bronze, silver, gold. Trước khi lên
web, một bước kiểm tra tính lại mọi con số bằng SQL độc lập; lệch là dừng, không deploy.
Website là file tĩnh nên lúc demo không có gì phải chạy.

## Slide 3 — Lưu trữ và biến đổi, qua một tin thật (1 phút 30)

*Chỉ hàng trên.* Bronze là dữ liệu thô. Silver là mỗi tin một dòng sạch: chuẩn về 34 tỉnh
theo bản đồ mới, lương quy về VND mỗi tháng, xếp vào 15 nhóm nghề. Gold là mỗi dòng một cặp
tin và kỹ năng.

*Chỉ hàng dưới.* Đây là một tin thật trên itviec, Data Engineer ở Hà Nội. Từ điển của bọn
em tìm được 12 kỹ năng trong tin này: SQL, Spark, Python, dbt, Airflow…

Bọn em không dùng AI để trích kỹ năng, mà dùng từ điển 159 kỹ năng có tên tiếng Việt và
tiếng Anh, cộng luật. Cách này rẻ, nhanh, và giải thích được. Mỗi dòng giữ lại cụm từ đã
khớp, nên con số nào trên web cũng truy ngược được tới câu gốc trong tin.

## Slide 4 — Mô hình: bọn em tính gì (1 phút)

Bọn em tính bốn thứ.

Một, tỷ trọng nhu cầu: bao nhiêu phần trăm tin đang mở cần kỹ năng đó. Ví dụ tiếng Anh giao
tiếp gần 41%, Excel khoảng 31%.

Hai, chênh lệch lương giữa tin có và không có kỹ năng. Đây là tương quan, không phải nhân quả.

Ba, mức ảnh hưởng của AI: ghép khả năng AI làm thay, do nhóm đánh giá, với mức kỹ năng đó
đi cùng công cụ AI trong tin tuyển dụng.

Bốn, dự báo bằng ARIMA. Em nói thẳng: khi kiểm tra ngược, mô hình chỉ thắng cách dự báo đơn
giản ở 50% số lần kiểm tra. Nên bọn em công bố kèm kết quả kiểm tra, chứ không khoe đường dự báo.
Khi đủ một năm dữ liệu hằng ngày, bọn em sẽ đo lại.

## Slide AI 1 — Tin IT nhắc công cụ AI tăng gấp 4 (1 phút)

Đây là phát hiện chính về AI. Bọn em đếm tỷ lệ tin tuyển dụng nhắc tới công cụ AI như
ChatGPT, Copilot, LLM, trên mẫu bản lưu Internet Archive từ đầu 2025.

*Chỉ dòng CNTT.* Ở nhóm công nghệ thông tin, tỷ lệ này tăng từ 5% nửa đầu 2025 lên gần 20%
năm 2026, gấp bốn lần trong 18 tháng. Marketing đi theo sau, từ 2% lên gần 9%.

*Chỉ các dòng dưới.* Kế toán, kinh doanh, hành chính vẫn dưới 3%. Nghĩa là AI đi vào tin
tuyển dụng theo từng nghề, không đều.

Em nói rõ giới hạn: đây là mẫu, khoảng 150 tin mỗi tháng mỗi nguồn. Và "nhắc tới công cụ AI"
là tín hiệu nhà tuyển dụng muốn người biết dùng AI, chưa phải số việc làm bị mất.

## Slide AI 2 — Hôm nay, theo từng nghề (1 phút)

*Chỉ bảng.* Đây là tin đang mở hôm nay. Cứ 3 tin tuyển Tester thì 1 tin yêu cầu công cụ AI.
Business Analyst 32%, lập trình viên 23%, content marketing gần 17%. Trong khi đó kế toán
2%, logistics hơn 1%, lao động phổ thông gần như 0.

ILO nói 1 trên 5 lao động chịu tác động của AI tạo sinh. Dữ liệu của bọn em cho thấy tác
động đó đang hiện ra trong tin tuyển dụng ở nghề nào trước. Với học sinh: muốn làm Tester,
BA hay content marketing, biết dùng công cụ AI đã là kỹ năng nhà tuyển dụng ghi trong tin.

## Slide 5 — Tiến độ (1 phút)

Crawler chạy mỗi ngày từ 12/10, hiện có 23 ngày dữ liệu và hơn 12 nghìn tin đang mở. Có lịch sử
2025–2026 từ Internet Archive kể cả vieclam24h và topcv, từ điển kỹ năng đã duyệt, mọi số khớp SQL,
ba website đã chạy, và trang hướng nghiệp mới có trắc nghiệm Holland, quét CV. 66 bài test tự động đều đạt.

## Slide 6 — Lộ trình 3, 6, 12 tháng (1 phút)

Ba tháng tới: đưa crawler lên máy chủ chạy liên tục, công bố độ chính xác trên 150 tin gán nhãn, bật
chỉ số tháng thật, và gửi đề xuất hợp tác dữ liệu. Sáu tháng: kịp mùa tuyển sinh 2027, thí điểm trang
hướng nghiệp ở vài trường THPT, so cung với cầu, mở rộng sang nghề kỹ thuật. Mười hai tháng: đủ 12 kỳ
để dự báo, đo tác động AI theo chuỗi, và mở dữ liệu.

Chi phí cả năm đầu khoảng 11 triệu đồng cho máy chủ và gán nhãn, vì không có backend và web tĩnh
miễn phí. Chi phí lớn nhất nếu mở rộng là con người, không phải hạ tầng.

## Slide 7 — Demo (3 phút)

*Mở demo-skill-radar.ducklytics.com.*

**Hướng nghiệp (khoảng 1 phút 15).** *Mời mọi người quét QR trên slide. Mở /huong-nghiep/, chọn
"Sinh viên", làm vài câu trắc nghiệm (hoặc chiếu video demo trên slide).* Kết quả là mã Holland
và các nhóm nghề hợp nhất. *Mở một nghề, tab Thị trường.* Bấm vào một kỹ năng để xem xu hướng
12 tháng; tháng nào thiếu dữ liệu thì để trống, không nối cho đẹp. Biểu đồ AI cho thấy tỷ lệ tin
nhắc công cụ AI theo nửa năm. *Tab Tổng quan, bấm tên một công ty* để xem tin thật của công ty đó.
*Tab Kỹ năng & CV:* chọn kỹ năng đã có hoặc quét CV, CV chỉ đọc trên máy.

**Nhà trường (khoảng 45 giây).** *Bấm "Nhà trường".* Nhà trường chọn một nhóm nghề và đánh
dấu kỹ năng mình đang dạy, rồi xem mình phủ được bao nhiêu phần nhu cầu. Mỗi kỹ năng có
đường xu hướng nhỏ. *Bấm "Tải CSV".* Có thể tải về để đối chiếu với chương trình.

**Cơ quan quản lý (khoảng 45 giây).** *Bấm "Cơ quan quản lý".* Nhu cầu theo tỉnh và theo
nhóm nghề, lương theo nhóm nghề, và các kỹ năng biến động mạnh nhất 12 tháng, kèm cột cho
biết dự báo có đáng tin không.

**Kết (15 giây).** *Quay lại slide, bấm "Xem dữ liệu đã thu thập".* Còn đây là toàn bộ dữ
liệu bọn em đang có, để các anh chị tự kiểm tra. Em xin hết, mong nhận góp ý của các anh chị.

---

## Nếu bị hỏi

- **"Chuyên gia" chấm điểm AI là ai?** Hiện là nhóm tự đánh giá, nên trên web ghi rõ "nhóm
  đánh giá". Bước tiếp theo là nhờ người trong ngành chấm lại.
- **Sao không dùng AI để đọc tin?** Từ điển + luật rẻ, nhanh, giải thích được từng kết quả.
  Nếu sau này dùng AI thì cũng phải đo độ chính xác như cách hiện tại.
- **Dữ liệu có đại diện cho cả thị trường không?** Chưa. Đây là tin đang mở trên 4 trang,
  thiếu tin đã đóng và các ngành kỹ thuật, xây dựng, sản xuất. Trang trạng thái ghi rõ điều này.
- **Có thu thập dữ liệu cá nhân không?** Không. Tên, số điện thoại, email người đăng bị xóa
  trước khi ghi xuống đĩa.
