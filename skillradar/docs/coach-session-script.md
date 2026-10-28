# Lời nói — trình bày vòng 2 (khoảng 12 phút)

Đi theo deck 10 slide (`docs/coach-session.html`). Số liệu cập nhật 28/10/2026. Thời gian ghi trong ngoặc là gợi ý.
Chữ *nghiêng* là thao tác, không đọc.

---

## Slide 0 — Vì sao cần SkillRadar (45 giây)

Chào các anh chị. Em là Thủy, bài dự thi SkillRadar VN, mã BTL86-59.

Năm nay có gần 875 nghìn bạn trẻ đăng ký xét tuyển đại học, với hơn 7 triệu nguyện vọng.
Trung bình mỗi bạn chọn 8 ngành, và gần như không có dữ liệu nào cho biết ngành đó ngoài
thị trường đang cần gì.

Kết quả thấy rõ trong số liệu của Cục Thống kê quý III năm nay: cứ 11 thanh niên thì 1 bạn
thất nghiệp, ở thành phố là 1 trên 8, gấp bốn lần mức chung. 1,6 triệu bạn trẻ không học
cũng không làm.

Và thị trường đang đổi nhanh hơn. ILO tính có 11,5 triệu lao động Việt Nam, tức 1 trên 5
người, làm công việc chịu tác động của AI tạo sinh. Diễn đàn Kinh tế Thế giới dự báo đến
2030, gần 40% kỹ năng hiện có sẽ thay đổi, và 62% doanh nghiệp tại Việt Nam nói thiếu kỹ
năng là rào cản lớn nhất.

Học sinh, nhà trường, cơ quan quản lý đều cần một câu trả lời: hôm nay thị trường cần kỹ
năng gì, và AI đang thay đổi điều đó thế nào.

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

*Chỉ các con số bên phải.* Hơn 54 nghìn tin, 159 kỹ năng, 48 nghề cụ thể, 6 nguồn, trong đó
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
giản ở 49% số kỹ năng. Nên bọn em công bố kèm kết quả kiểm tra, chứ không khoe đường dự báo.
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
Business Analyst 28%, lập trình viên 25%, content marketing gần 19%. Trong khi đó kế toán
2%, logistics dưới 1%, lao động phổ thông 0.

ILO nói 1 trên 5 lao động chịu tác động của AI tạo sinh. Dữ liệu của bọn em cho thấy tác
động đó đang hiện ra trong tin tuyển dụng ở nghề nào trước. Với học sinh: muốn làm Tester,
BA hay content marketing, biết dùng công cụ AI đã là kỹ năng nhà tuyển dụng ghi trong tin.

## Slide 5 — Tiến độ và vướng mắc (1 phút 30)

Về tiến độ: crawler chạy mỗi ngày từ 12/10, có lịch sử 2025–2026 từ Internet Archive kể cả
vieclam24h và topcv, từ điển kỹ năng đã duyệt, mọi số khớp SQL, ba website đã chạy, trang học
sinh tách 48 nghề cụ thể, và 62 bài test tự động đều đạt.

Về vướng mắc, rủi ro lớn nhất là nguồn dữ liệu, không phải code. Chỉ trong một tuần, hai
trong bốn nguồn thay đổi: vietnamworks gỡ sitemap, jobsgo chặn một ngày.

Ngoài ra còn ba việc: tập kiểm tra độ chính xác 150 tin chưa gán nhãn xong nên chưa đo được F1; chưa gửi email xin phép các nguồn; và crawler đang chạy trên một laptop, máy tắt
là có nguy cơ mất ngày.

## Slide 6 — Bước tiếp theo (1 phút)

Năm việc tiếp theo: xin phép vietnamworks và jobsgo hoặc xin nguồn dữ liệu chính thức; gán
nhãn đủ 150 tin để công bố độ chính xác; chuyển crawler sang một máy chạy liên tục; bật chỉ
số theo tháng khi đủ dữ liệu; và thêm chỉ tiêu tuyển sinh để so cung với cầu.

Em muốn hỏi các anh chị hai điều: trong năm việc này, việc nào giám khảo quan tâm nhất?
Và anh chị có quen ai bên các trang tuyển dụng hoặc trường đại học không?

## Slide 7 — Demo (3 phút)

*Mở demo-skill-radar.ducklytics.com.*

**Học sinh (khoảng 1 phút 15).** *Bấm "Học sinh". Gõ "data" vào ô tìm kiếm.* Không ai nộp
đơn vào "công nghệ thông tin", mà vào một nghề cụ thể, nên trang học sinh tách nhóm nghề lớn
thành 48 nghề. *Mở Data Analyst.* 47 tin đang tuyển; cứ 10 tin thì 9 tin cần SQL, 7 tin cần
Power BI, 6 tin cần Python. *Kéo xuống.* Mức ảnh hưởng của AI, và xu hướng tin nhắc công cụ AI
của cả nhóm IT. *Kéo xuống "Nghề khác trong nhóm", bấm Tester* để so.
*Bấm vào kỹ năng Excel.* Đây là xu hướng 12 tháng; tháng nào thiếu dữ liệu thì để trống,
không nối cho đẹp.

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
