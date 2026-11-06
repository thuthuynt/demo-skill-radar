# Câu hỏi giám khảo có thể hỏi, và gợi ý trả lời

Số liệu theo bản build ngày 5/11/2026. Mỗi câu trả lời nói trong khoảng 20–40 giây. Nguyên tắc chung:
nói thẳng giới hạn trước khi bị hỏi dồn, rồi nói bước tiếp theo đã có trong roadmap.

---

## A. Dữ liệu và độ tin cậy

**1. Dữ liệu của em có đại diện cho thị trường lao động Việt Nam không?**

Chưa, và bọn em ghi rõ điều này trên trang trạng thái. Đây là tin đang mở trên 4 trang tuyển dụng,
thiếu tin đã đóng, thiếu việc tuyển qua người quen, và chưa có ngành kỹ thuật, xây dựng, sản xuất
chuyên môn. Cái SkillRadar đo được là: trong những tin đăng công khai, kỹ năng nào được đòi hỏi nhiều
và thay đổi ra sao. Để rộng hơn, roadmap có hai việc: mở rộng phạm vi nghề, và hợp tác để có ít nhất
một nguồn dữ liệu chính thức.

**2. Độ chính xác của việc trích kỹ năng là bao nhiêu?**

Em nói thật: chưa đo xong. Bọn em đã chọn 150 tin để gán nhãn tay, chia đều tin tiếng Việt, tiếng Anh
và tin trộn, nhưng mới gán xong vài tin. Vì vậy trang trạng thái đang ghi "chưa đo", không ghi một con
số cho đẹp. Công bố F1 trên 150 tin là việc đầu tiên trong roadmap 3 tháng. Điểm mạnh của cách làm
hiện tại là mỗi kết quả giữ lại cụm từ đã khớp, nên ai cũng kiểm tra lại được từng dòng.

**3. Một tin đăng lại nhiều lần thì có bị đếm trùng không?**

Không. Ở tầng silver, tin cùng công ty, tiêu đề gần giống nhau và đăng cách nhau dưới 30 ngày, kể cả
trên hai trang khác nhau, bị đánh dấu là tin đăng lại. Mọi chỉ số chỉ tính trên tin gốc.

**4. vietnamworks dừng cập nhật từ 13/10, sao vẫn tính?**

vietnamworks gỡ sitemap từ 14/10, nên crawler không còn thấy tin mới. Với mỗi nguồn, "tin đang mở" là
tin có trong ảnh chụp gần nhất của nguồn đó, nên phần vietnamworks là ảnh chụp ngày 13/10. Trang trạng
thái ghi ngày chụp của từng nguồn. Đây là giới hạn đã biết; hướng xử lý là bỏ nguồn khỏi số đang mở khi
ảnh chụp quá cũ, và tìm cách lấy lại nguồn này một cách hợp lệ.

**5. Lương công bố từ ít tin như vậy có đáng tin không?**

Bọn em công bố khoảng lương khi có từ 10 tin ghi lương trở lên, và trang ghi rõ tính trên bao nhiêu
tin. Con số là trung vị và khoảng giữa 25% đến 75%, nên ít bị kéo lệch bởi vài tin lương rất cao. Với
nghề ít tin, người dùng thấy ngay cỡ mẫu nhỏ để tự cân nhắc.

**6. Dự báo chỉ đúng 50% thì dùng làm gì?**

Đó chính là lý do bọn em không khoe đường dự báo. Mỗi dự báo được so với một cách dự báo đơn giản (trung
bình 3 tháng gần nhất) trên dữ liệu quá khứ. Hiện mô hình chỉ thắng trong 80 trên 159 lần, nên trên web
có cột "dự báo đáng tin?" và khuyến nghị không dùng để ra quyết định. Khi đủ 12 tháng dữ liệu hằng ngày,
bọn em sẽ đo lại.

## B. Pháp lý, đạo đức, dữ liệu cá nhân

**7. Crawl dữ liệu của các trang tuyển dụng có hợp pháp không?**

Bọn em chỉ lấy tin do doanh nghiệp đăng công khai, theo năm nguyên tắc đã viết trong hồ sơ dự thi:
tôn trọng robots.txt, khai báo danh tính kèm email liên hệ thật, mỗi request cách nhau ít nhất 2 giây,
gặp 403 hay CAPTCHA là dừng, không vượt rào chống bot. Năm trang đã từ chối crawler, bọn em đã loại
khỏi danh sách nguồn. Lâu dài, bọn em muốn chuyển sang hợp tác dữ liệu chính thức với các trang này.

**8. Vậy lấy bản lưu Internet Archive của trang đã chặn crawler có phải là lách không?**

Bọn em không gửi request nào tới trang gốc. Chỉ đọc bản lưu công khai trên web.archive.org, vẫn theo
robots.txt của Internet Archive, cách 4 giây mỗi request, lọc dữ liệu cá nhân như dữ liệu crawl, và
mọi số từ nguồn này đều ghi nhãn "Internet Archive". Dữ liệu này chỉ dùng cho tỷ trọng theo tháng, không
dùng số đếm. Quyết định này bọn em chốt sau buổi coaching 27/10 và ghi rõ trong tài liệu dự án.

**9. Có thu thập dữ liệu cá nhân không? CV người dùng đi đâu?**

Không. Tên, số điện thoại, email, Zalo của người đăng tin bị cắt ngay ở tầng bronze, trước khi ghi
xuống đĩa. Bọn em không bao giờ chạm vào hồ sơ ứng viên. CV trên trang hướng nghiệp được đọc ngay trong
trình duyệt của người dùng, không gửi lên máy chủ nào; website cũng không có máy chủ xử lý để gửi tới.

**10. Hệ thống có an toàn trước tấn công không?**

Bề mặt tấn công rất nhỏ: website là file tĩnh trên Cloudflare Pages, không có backend, không có cơ sở
dữ liệu trực tuyến, không có tài khoản người dùng. Crawler và kho dữ liệu chạy trên máy nội bộ, không
mở cổng ra ngoài. Dữ liệu công bố chỉ là số tổng hợp và trích đoạn tin tuyển dụng công khai.

## C. Phương pháp

**11. "Mức ảnh hưởng của AI" tính thế nào? Ai chấm?**

Công thức là 0,65 nhân khả năng AI làm thay, cộng 0,35 nhân mức kỹ năng đó đi cùng công cụ AI trong
tin tuyển dụng. Phần đầu hiện do nhóm tự đánh giá, nên trên web ghi rõ "nhóm đánh giá". Phần sau đo
được từ dữ liệu. Trọng số là lựa chọn của nhóm, chưa được kiểm định. Bước tiếp theo là nhờ người trong
ngành chấm lại, và khi có đủ chuỗi thời gian thì đo trực tiếp thay vì đánh giá.

**12. Sao không dùng AI, LLM để đọc tin cho chính xác hơn?**

Từ điển và luật rẻ, nhanh, chạy offline, và giải thích được từng kết quả: tin nào, câu nào, cụm từ nào.
Với một công cụ có thể ảnh hưởng tới quyết định chọn nghề, khả năng giải thích quan trọng hơn vài phần
trăm độ chính xác. Nếu sau này dùng LLM, bọn em vẫn sẽ đo trên cùng tập 150 tin để so.

**13. Trắc nghiệm Holland trên trang có khoa học không?**

24 câu do nhóm tự soạn theo lý thuyết RIASEC của Holland, không lấy từ bộ công cụ có bản quyền nào. Mã
Holland của từng nghề là nhận định của nhóm, tham khảo hồ sơ sở thích nghề của O*NET. Bọn em chưa kiểm
định bộ câu hỏi, nên trang ghi rõ đây chỉ là điểm khởi đầu, không quyết định thay người dùng. Thí điểm
với trường THPT trong roadmap là để có người làm nghề tư vấn góp ý.

**14. "Tin nhắc tới công cụ AI tăng gấp 4" có nghĩa là AI lấy mất việc không?**

Không. Đó là tín hiệu nhà tuyển dụng muốn người biết dùng AI, không phải số việc làm mất đi. Số liệu
lấy từ mẫu khoảng 150 tin mỗi tháng mỗi nguồn trên Internet Archive, kỳ nào dưới 80 tin thì không công
bố. Muốn đo việc làm mất đi cần dữ liệu khác, ví dụ số tin theo thời gian của cả thị trường.

## D. Sản phẩm và tính bền vững

**15. Khác gì báo cáo thị trường của các trang tuyển dụng hay số liệu của cơ quan thống kê?**

Báo cáo của trang tuyển dụng thường theo quý, chỉ dữ liệu của trang đó, không công bố phương pháp. Số
liệu thống kê chính thức nói về việc làm, thất nghiệp, chưa đi tới mức kỹ năng. SkillRadar gộp nhiều
nguồn, cập nhật hằng ngày, xuống tới từng kỹ năng và từng nghề, và mọi con số truy ngược được tới câu
gốc. Ba trang cho ba nhóm người dùng khác nhau.

**16. Ai sẽ duy trì sau cuộc thi? Chi phí bao nhiêu?**

Hệ thống được thiết kế để một người vận hành: không backend, web tĩnh miễn phí. Chi phí năm đầu khoảng
11 triệu đồng cho máy chủ crawler và gán nhãn, theo giá tham khảo. Chi phí lớn nhất khi mở rộng là
người làm, khoảng 8–10 triệu một tháng cho một cộng tác viên bán thời gian. Hướng bền vững là hợp tác
với trường học và trang tuyển dụng, như trong roadmap.

**17. Nhà trường dùng cụ thể thế nào?**

Nhà trường chọn nhóm nghề đầu ra, đánh dấu kỹ năng chương trình đang dạy, trang tính mức đáp ứng theo
nhu cầu thật và liệt kê kỹ năng còn thiếu, kèm xu hướng 12 tháng. Có nút tải CSV để đưa vào hồ sơ rà
soát chương trình. Roadmap có thí điểm với 2–3 trường đại học và THPT để kiểm tra cách dùng này.

**18. Nếu một trang tuyển dụng đổi giao diện hoặc chặn crawler thì sao?**

Crawler ghi log mỗi ngày, trang trạng thái hiện độ phủ theo ngày nên thấy ngay khi một nguồn tụt. Bộ
đọc dùng dữ liệu có cấu trúc JSON-LD trước, HTML sau, nên ít vỡ khi đổi giao diện. Nếu trang chặn, bọn
em dừng nguồn đó, không vượt rào; có nhiều nguồn nên hệ thống vẫn chạy.

---

## Câu nên tránh nói

- Không nói "chính xác 90%" hay bất kỳ con số độ chính xác nào: F1 chưa đo.
- Không nói "dự báo nhu cầu kỹ năng": chỉ nói "có thử dự báo và công bố kết quả kiểm tra".
- Không nói "đại diện cho cả thị trường" hay "AI làm mất X việc làm".
