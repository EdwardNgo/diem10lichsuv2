# Tổng quan sản phẩm

## Kết quả mong muốn

Điểm 10 Lịch sử giúp học sinh THPT Việt Nam ôn thi Lịch sử qua đề trắc nghiệm
có giới hạn thời gian, lời giải ngay sau khi làm và lịch sử bài làm bền vững.
Quản trị viên kiểm soát mọi nội dung đề trước khi học sinh nhìn thấy.

Kho đề công khai gồm đề thi thử tự biên soạn và đề tham khảo từ các nguồn khác,
dùng để ôn tập kỳ thi tốt nghiệp THPT quốc gia môn Lịch sử. Nội dung này không
phải đề thi chính thức của Bộ GDĐT.

## Người dùng

- Khách: khám phá sản phẩm và các đề đã xuất bản.
- Học sinh: xác thực bằng Google, làm đề và xem kết quả.
- Admin: tài khoản Google có trong allowlist, có quyền soạn, nhập, rà soát và
  xuất bản đề.

## Phạm vi bản phát hành

Bản phát hành đầu tiên gồm:

- Landing page responsive và tính năng khám phá đề đã xuất bản.
- Xác thực Google và vai trò học sinh/admin được server thực thi.
- Lượt làm trắc nghiệm có thời gian, tự lưu, nộp bài, chấm tự động và lời giải
  theo từng câu.
- Lịch sử làm bài cá nhân và làm lại không giới hạn.
- Admin tải tài liệu nguồn lên storage tương thích S3, nhập DOCX/PDF có lớp chữ
  đồng bộ, rà soát/xuất bản và có thể tạo draft thủ công khi cần.

## Ngoài phạm vi

- Thanh toán, lớp học, tài khoản giáo viên và thi đấu thời gian thực.
- Chấm tự luận và AI tạo nội dung đề.
- Ứng dụng mobile native.
- OCR cho PDF scan/chỉ có ảnh.
- Redis, RabbitMQ và worker nền.

## Nguyên tắc sản phẩm

- Không bao giờ lộ đáp án hoặc lời giải trước khi lượt làm hoàn thành.
- Server, không phải trình duyệt, quyết định hết hạn, phân quyền và điểm.
- Nội dung nhập vào luôn là bản nháp cần rà soát; parser không bao giờ tự xuất
  bản.
- Thay đổi đề giữ nguyên kết quả lịch sử nhờ phiên bản hóa.
