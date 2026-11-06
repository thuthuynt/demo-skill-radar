# Lời nói — trình bày vòng 2 (khoảng 13 phút)

Deck 13 slide: `web/presentation/index.html`, https://demo-skill-radar.ducklytics.com/presentation/.
Số liệu cập nhật 5/11/2026. Thời gian trong ngoặc là gợi ý. Chữ *nghiêng* là thao tác, không đọc.

Cách bấm: →, Space hoặc click chuột hiện thêm một box; hết box thì sang slide sau. ← quay lại slide
trước, hiện đủ box. Phím N bật ghi chú. Số lần bấm của từng slide ghi trong ngoặc vuông.

---

## 1. Mất phương hướng khi chọn nghề (40 giây) [6 lần bấm]

Chào các anh chị. Em là Thủy, nhóm Ducklytics, bài dự thi SkillRadar VN, mã BTL86-59.

*Kể chuyện của bản thân, 30 giây: lúc chọn ngành hoặc chọn việc, thiếu thông tin ra sao. Mỗi câu
hỏi bấm một lần cho nó hiện ra: Học ngành gì? Ra trường làm gì? Lương bao nhiêu? Cần kỹ năng gì?
Nghề này còn cần người không? AI có làm thay mình không?*

Mất phương hướng khi chọn nghề không phải chuyện của riêng ai: hôm nay, hàng trăm nghìn bạn trẻ vẫn
đứng ở ngã rẽ đó.

## 2. Vì sao cần SkillRadar (45 giây) [5 lần bấm]

*Bấm.* Cứ 5 cử nhân thì có 1 người đi làm trái ngành. Ở khoa học tự nhiên, toán và công nghệ thông
tin, con số này là hơn 60%. (Nghiên cứu của Trường Quốc tế, ĐHQG Hà Nội, trên dữ liệu điều tra lao
động 2018–2020.)

*Bấm.* Theo Cục Thống kê quý III năm nay, cứ 8 thanh niên 15–24 tuổi ở thành thị thì có 1 bạn thất
nghiệp.

*Bấm.* 1,6 triệu bạn trẻ không đi học, không có việc, cũng không học nghề. Đây là nhóm NEET, tính
cả người không tìm việc, nên không phải số thất nghiệp.

*Bấm.* ILO tính 20% lao động Việt Nam, tức 11,5 triệu người, làm công việc chịu tác động của
AI tạo sinh.

*Bấm.* Diễn đàn Kinh tế Thế giới dự báo đến năm 2030, 39% kỹ năng hiện có sẽ thay đổi hoặc lỗi
thời. Nhưng chưa có công cụ nào cho biết hôm nay thị trường Việt Nam cần kỹ năng gì, và AI đang
thay đổi điều đó ra sao.

## 3. AI đang thay đổi cách người trẻ vào nghề (45 giây) [5 lần bấm]

Ý lấy từ chương trình Toàn cảnh Thế giới của VTV24 tháng 11. Chỉ nói ý, không đọc số trong video.

*Bấm.* Một: vừa ra trường đã bị đòi hỏi như người có 5 đến 10 năm kinh nghiệm, vì việc của nhân
viên mới đang được AI làm thay.
*Bấm.* Hai: bằng cấp giảm giá, năng lực thực tế lên ngôi.
*Bấm.* Ba: lao động trí thức cũng chịu tác động; AI tham gia vào từng khâu của công việc văn phòng.
*Bấm.* Bốn: ít sa thải, nhưng tuyển mới chậm lại. Người đang có việc giữ được việc, người trẻ tìm
việc đầu tiên khó hơn hẳn.
*Bấm.* Vậy nếu bằng cấp không còn đủ, người trẻ cần biết thị trường đang hỏi kỹ năng gì, ngay hôm nay?

Nếu có mạng và còn thời gian: chọn mốc 19:24 "Người trẻ khó tìm việc", bấm "Xem trích đoạn", chiếu
20–30 giây. Rời slide là video tự tắt.

## 4. SkillRadar VN (30 giây)

SkillRadar đọc tin tuyển dụng công khai mỗi ngày, tách ra kỹ năng nhà tuyển dụng yêu cầu, rồi biến
thành chỉ số: kỹ năng nào đang được cần, ở nghề nào, tỉnh nào, lương ra sao, và AI ảnh hưởng tới nó
thế nào. Mọi con số đều lấy từ dữ liệu thật và truy ngược được.

Ba nhóm người dùng, mỗi nhóm một trang: học sinh, sinh viên chọn nghề và biết cần học gì; nhà
trường đối chiếu chương trình với nhu cầu; cơ quan quản lý nắm thị trường theo vùng.

*Chỉ các con số.* Hơn 66 nghìn tin, 159 kỹ năng, 47 nghề cụ thể, 6 nguồn, trong đó 2 nguồn lấy qua
Internet Archive.

## 5. Kiến trúc: từ crawl tới website (1 phút 15)

Toàn bộ chạy trên một local server, không có backend.

*Chỉ cột trái.* Bọn em crawl trực tiếp 4 trang tuyển dụng. Với các trang chặn crawler như vieclam24h
và topcv, bọn em không gửi request tới trang gốc, chỉ lấy bản lưu công khai trên Internet Archive và
ghi rõ nguồn. Internet Archive cũng cho bọn em lịch sử theo tháng từ 2025.

*Chỉ ô Crawler (daily).* Crawler chạy 7 giờ sáng mỗi ngày, theo năm nguyên tắc ghi ở hàng chip bên
dưới: tôn trọng robots.txt, khai báo danh tính kèm email thật, mỗi trang cách nhau ít nhất 2 giây,
gặp 403 hay CAPTCHA là dừng, và xóa dữ liệu cá nhân trước khi lưu. *Có thể bấm vào từng ô để hiện
giải thích ngay dưới sơ đồ.*

*Chỉ phần giữa và phải.* Dữ liệu vào data warehouse DuckDB qua ba tầng bronze, silver, gold. Trước
khi lên web, bước verify tính lại mọi con số bằng SQL; lệch là dừng, không deploy. Website là JSON
tĩnh trên Cloudflare Pages, lúc demo không có gì phải chạy.

*Chỉ hàng tech stack.* Python, DuckDB, statsmodels cho dự báo, JavaScript thuần. Kỹ năng được trích
bằng rule-based: từ điển 159 kỹ năng song ngữ, không dùng LLM.

## 6. Dữ liệu được xử lý qua từng tầng, sẵn sàng để khai thác (1 phút 15) [4 lần bấm]

Cùng một tin thật trên itviec, Data Engineer của F88, đi qua ba tầng.

*Bấm.* Bronze giữ nguyên như trang gốc: lương còn là chuỗi "800-1300 USD MONTH", địa điểm là "Not
Available, Hà Nội", mô tả còn nguyên phần quảng cáo.
*Bấm.* Silver là một dòng đã chuẩn hóa: lương thành số, tỉnh thành mã Hà Nội, tin được xếp vào nhóm
công nghệ thông tin, nghề Data Engineer, và đánh dấu có phải tin đăng lại không.
*Bấm.* Gold là mỗi dòng một cặp tin và kỹ năng. Tin này có 12 dòng: SQL, Spark, Airflow… Có cả tên
gọi khác, ví dụ "kafka" được hiểu là kỹ năng hàng đợi thông điệp.
*Bấm.* Phía sau là từ điển kỹ năng: 159 kỹ năng với 831 cách gọi tiếng Việt và tiếng Anh, bọn em
duyệt tay từng mục. Ví dụ "pivot table", "vlookup" đều được hiểu là Excel; "IELTS", "TOEIC" là tiếng
Anh giao tiếp. Mỗi dòng gold giữ lại cụm từ đã khớp, nên con số nào trên web cũng truy ngược được
tới câu gốc trong tin.

## 7. Insights · Mỗi nhóm ngành đòi một bộ kỹ năng riêng (1 phút) [4 lần bấm]

4 nhóm ngành nhiều tin đang mở nhất. Mỗi thẻ là 4 kỹ năng được đòi hỏi nhiều nhất, kèm đường xu
hướng 12 tháng.

*Bấm, Kinh doanh.* Chăm sóc khách hàng, đàm phán, tiếng Anh. Lương trung vị 17 triệu; chưa tới 2% tin
nhắc công cụ AI.
*Bấm, Kế toán.* 94% tin đòi nghiệp vụ kế toán, hơn một nửa đòi Excel và phần mềm kế toán.
*Bấm, Công nghệ thông tin.* Tiếng Anh đứng đầu, 53%, nhiều hơn cả SQL. Lương trung vị cao nhất, 22 triệu,
và gần 23% tin nhắc công cụ AI.
*Bấm, Marketing.* Quản lý mạng xã hội gần một nửa số tin, rồi tiếng Anh và vận hành sàn thương mại
điện tử.

Mức ảnh hưởng của AI của cả 4 nhóm đều ở mức trung bình, nhưng tin nhắc công cụ AI chênh nhau
rất xa: IT gần 23%, marketing 12%, kinh doanh và kế toán dưới 2%.

## 8. Insights · Kỹ năng nào đang được yêu cầu nhiều hơn, ít hơn? (1 phút) [3 lần bấm]

*Bấm, cột Nhiều hơn.* Trong tin IT, tỷ lệ đòi biết dùng công cụ AI tăng từ 5,9% lên 20,8% trong 12
tháng; mô hình ngôn ngữ lớn từ 4,7% lên 13,3%. CI/CD, kiểm thử, phân tích nghiệp vụ cũng tăng.
*Bấm, cột Ít hơn.* Cột này chỉ lấy kỹ năng có dự báo ARIMA đáng tin. Đàm phán giảm từ 23,2% xuống
18,8% và mô hình dự báo còn giảm; tiếng Trung giảm 3 điểm rồi đi ngang; bán hàng doanh nghiệp được
dự báo tăng lại.
*Bấm.* Em nói thẳng: ARIMA chỉ thắng cách dự báo đơn giản ở 45 trên 92 kỹ năng, nên chỉ đọc dự báo
ở dòng có nhãn ARIMA. Ở kỹ năng dùng công cụ AI, dự báo giữ quanh 24%, cao hơn
trung bình 3 tháng gần nhất.

## 9. Insights · AI: tin IT nhắc công cụ AI tăng gấp 4 lần (1 phút) [2 lần bấm]

Bọn em đếm tỷ lệ tin tuyển dụng nhắc tới công cụ AI như ChatGPT, Copilot, LLM, trên mẫu bản lưu
Internet Archive từ đầu 2025.

*Bấm.* Ở nhóm công nghệ thông tin, tỷ lệ này tăng từ 5% nửa đầu 2025 lên gần 20% năm 2026, gấp bốn
lần trong 18 tháng. Marketing đi theo sau, từ khoảng 2% lên gần 9%.
*Bấm.* Kế toán, kinh doanh, hành chính vẫn dưới 3%. AI đi vào tin tuyển dụng theo từng nghề, không đều.

Giới hạn: đây là mẫu, khoảng 150 tin mỗi tháng mỗi nguồn. "Nhắc tới công cụ AI" là tín hiệu nhà
tuyển dụng muốn người biết dùng AI, chưa phải số việc làm mất đi.

## 10. Insights · AI: hôm nay, theo từng nghề (1 phút) [2 lần bấm]

*Chỉ bảng.* Tin đang mở ngày 5/11. Cứ 3 tin tuyển Tester thì 1 tin yêu cầu công cụ AI; Business
Analyst 32%, lập trình viên 23%, content marketing gần 17%. Trong khi đó kế toán 2%, logistics hơn
1%, lao động phổ thông gần như không có.

*Bấm.* Tính chung, 5,3% trong 12.359 tin đang mở nhắc tới công cụ AI, gần như toàn bộ ở IT và marketing.
*Bấm.* Với học sinh: nếu muốn làm Tester, BA hay content marketing thì biết dùng công cụ AI đã là kỹ
năng nhà tuyển dụng ghi trong tin. ILO nói 1 trên 5 lao động chịu tác động của AI; dữ liệu này cho
thấy tác động đó đang hiện ra ở nghề nào trước.

## 11. Roadmap 12 tháng: đã làm và sắp làm (1 phút 30) [4 lần bấm]

Cột đầu tiên, tháng 10/2026, là giai đoạn setup đã làm xong; 12 cột sau là kế hoạch tới 10/2027. Đọc
theo bốn làn, mỗi làn nói phần đã làm trước.

*Bấm, Infrastructure.* Đã làm: crawler chạy hằng ngày từ 12/10, 23 ngày dữ liệu, 12.359 tin đang mở;
lịch sử từ Internet Archive; setup local server, xử lý và lưu trữ dữ liệu trong DuckDB. Ba tháng tới: deploy crawler lên server chạy liên tục, gán nhãn 150 tin để công
bố độ chính xác F1, rồi bật chỉ số tháng trên dữ liệu thật. Sau đó mở rộng sang nghề kỹ thuật, sản
xuất, đo tác động AI theo chuỗi, và đủ 12 kỳ thì làm dự báo.
*Bấm, Product.* Đã có bản MVP: web hướng nghiệp cho học sinh, trang báo cáo cho trường đại học và cơ quan
quản lý; từ điển 159 kỹ năng, 47 nghề cụ thể. Sắp tới:
hoàn thiện trang hướng nghiệp, kịp mùa tuyển sinh 2027; so cung với cầu theo chỉ tiêu
tuyển sinh; cuối năm mở dữ liệu CSV theo tỉnh, nghề, kỹ năng.
*Bấm, Partnerships.* Đề xuất hợp tác dữ liệu với các trang tuyển dụng để có ít nhất một nguồn chính
thức; thí điểm với 2–3 trường đại học và THPT; báo
cáo theo quý.
*Bấm, Cost.* Đến nay chi phí là 0 đồng: chạy trên local server, web tĩnh miễn phí. Cả năm đầu khoảng 11 triệu đồng cho server và gán nhãn, vì không có backend và web tĩnh
miễn phí. Đây là giá tham khảo, chưa có báo giá. Chi phí lớn nhất nếu mở rộng là con người, không
phải hạ tầng.

## 12. Demo (3 phút)

*Mời mọi người quét QR của trang hướng nghiệp trên slide.* Nếu mạng yếu, bấm play video demo ở bên
phải (1 phút 49, lời thoại trong `docs/demo-video-script.md`).

**Hướng nghiệp (khoảng 1 phút 30).** *Mở /huong-nghiep/, chọn "Sinh viên", làm nhanh trắc nghiệm.*
Kết quả là mã Holland và các nhóm nghề hợp nhất, mỗi nhóm có số tin đang tuyển và lương phổ biến.
*Mở một nghề, tab Tổng quan, bấm tên một công ty:* tin thật của công ty đó, yêu cầu gì, kỹ năng nào.
*Tab Thị trường, bấm một kỹ năng:* xu hướng 12 tháng; tháng thiếu dữ liệu để trống, không nối cho
đẹp. Biểu đồ AI cho thấy tỷ lệ tin nhắc công cụ AI theo nửa năm. *Tab Kỹ năng & CV:* chọn kỹ năng đã
có hoặc quét CV; CV chỉ đọc trên máy, không gửi đi.

**Nhà trường (khoảng 45 giây).** *Quét QR hoặc mở /nha-truong/.* Nhà trường chọn một nhóm nghề, đánh
dấu kỹ năng đang dạy, rồi xem chương trình phủ được bao nhiêu phần nhu cầu. *Bấm "Tải CSV"* để đối
chiếu với chương trình.

**Cơ quan quản lý (khoảng 30 giây).** *Mở /co-quan/.* Nhu cầu theo tỉnh và nhóm nghề, lương theo nhóm
nghề, kỹ năng biến động mạnh nhất 12 tháng, kèm cột cho biết dự báo có đáng tin không.

**Dữ liệu (15 giây).** *Bấm "Xem dữ liệu đã thu thập".* Còn đây là toàn bộ dữ liệu bọn em đang có, cập
nhật tới hôm nay, để các anh chị tự kiểm tra.

## 13. Tầm nhìn (40 giây)

Thị trường đang thay đổi rất nhanh, vì có sự tham gia của AI. AI không thay thế con người, nhưng con người
phải thay đổi để theo kịp những gì thị trường cần. *Chỉ tiêu đề.* SkillRadar cho biết thị trường đang cần
kỹ năng gì, cập nhật liên tục.

*Chỉ radar.* Với người trẻ: biết mình cần học gì. Với nhà trường: có dữ liệu để cập nhật chương trình.
Với cơ quan quản lý: có công cụ để điều phối thị trường lao động.

Ở slide đầu em nói các bạn trẻ đứng trước ngã rẽ mà không có bản đồ. SkillRadar muốn là tấm bản đồ đó,
và là tấm bản đồ luôn được cập nhật.

Em xin cảm ơn các anh chị và các thầy cô trong Ban giám khảo, và mong nhận góp ý.

## Phụ lục — Trắc nghiệm Holland (chỉ mở khi bị hỏi)

*Bấm → sau slide Tầm nhìn.* Holland chia sở thích nghề thành 6 nhóm: kỹ thuật, nghiên cứu, nghệ thuật,
xã hội, quản lý và nghiệp vụ. Bạn trả lời 24 câu, mỗi nhóm 4 câu, chọn không thích, cũng được hay rất
thích. Ba nhóm điểm cao nhất thành mã Holland, ví dụ I-C-S. Mỗi nghề cũng có một mã như vậy, nhóm gán có
tham khảo O*NET; chữ đầu của mã nghề nặng gấp 3, chữ hai gấp 2, chữ ba gấp 1. Bộ câu hỏi chưa được kiểm
định, nên trang ghi rõ đây chỉ là điểm khởi đầu.

## Phụ lục — Dự báo ARIMA (chỉ mở khi bị hỏi)

Mỗi nguồn, mỗi kỹ năng là một chuỗi tỷ trọng theo tháng trên mẫu Internet Archive. Chỉ dự báo khi có ít nhất
12 tháng dùng được và kỹ năng chiếm từ 2% tin trở lên; tháng thiếu mẫu để trống, không nội suy. Bọn em thử ba
dạng ARIMA, chọn theo AIC, dự báo 6 tháng kèm dải tin cậy 80%. Rồi giữ lại 3 tháng cuối để kiểm tra ngược: chỉ
khi ARIMA sai ít hơn cách dự báo đơn giản (trung bình 3 tháng gần nhất) mới ghi "đáng tin". Kết quả: 80 trên
159 lần, khoảng một nửa. Ví dụ "Sử dụng công cụ AI" trong tin itviec: ARIMA sai 4 điểm %, cách đơn giản sai
6,8 điểm %, nên dự báo này đáng tin.
---

## Nếu bị hỏi

- **Ai chấm điểm "khả năng AI làm thay"?** Hiện là nhóm tự đánh giá, nên trên web ghi rõ "nhóm đánh
  giá". Bước tiếp theo là nhờ người trong ngành chấm lại.
- **Sao không dùng AI để đọc tin?** Từ điển và luật rẻ, nhanh, giải thích được từng kết quả. Nếu sau
  này dùng AI thì cũng phải đo độ chính xác như cách hiện tại.
- **Dữ liệu có đại diện cho cả thị trường không?** Chưa. Đây là tin đang mở trên 4 trang, thiếu tin
  đã đóng và các ngành kỹ thuật, xây dựng, sản xuất. Trang trạng thái ghi rõ điều này.
- **vietnamworks còn cập nhật không?** Trang gỡ sitemap từ 14/10, nên tin của vietnamworks đứng ở ngày
  13/10 và vẫn được tính trong số tin đang mở. Đây là giới hạn đã biết.
- **Lương công bố từ bao nhiêu tin?** Từ 10 tin có ghi lương trở lên; trang ghi rõ tính trên bao
  nhiêu tin.
- **Có thu thập dữ liệu cá nhân không?** Không. Tên, số điện thoại, email người đăng bị xóa trước khi
  ghi xuống đĩa. CV trên trang hướng nghiệp chỉ đọc trên máy người dùng.
