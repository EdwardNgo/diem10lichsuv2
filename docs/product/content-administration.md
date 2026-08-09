# Quản trị nội dung

## Vòng đời đề

Đề chuyển qua các trạng thái `draft`, `in_review`, `published` và `archived`.
Chỉ phiên bản đã xuất bản mới mở lượt làm mới cho học sinh. Xuất bản thay đổi
trên đề hiện có tạo phiên bản mới thay vì sửa lượt làm lịch sử.

Đề chỉ được xuất bản khi có metadata hợp lệ, thời lượng hợp lệ và đúng cấu trúc
24 câu Phần I + 4 câu Phần II. Câu Phần I phải có nội dung, bốn lựa chọn ABCD,
đúng một đáp án đúng và lời giải. Câu Phần II phải có đoạn tư liệu, đúng bốn
phát biểu, mỗi phát biểu có đáp án Đúng/Sai và lời giải.

## Tài sản và nhập đề

Tài liệu nguồn và ảnh nằm trong object storage tương thích S3. Database lưu
object key, MIME type, kích thước, checksum và metadata ứng dụng, không lưu blob
tệp.

Định dạng được hỗ trợ ở phiên bản đầu:

- Tài liệu nguồn: DOCX và PDF có lớp chữ.
- Ảnh câu hỏi: JPEG, PNG và WebP.

Tệp nguồn chỉ dành cho admin. Kiểm tra tệp xác thực loại được phép, phần mở rộng,
kích thước và checksum trước khi hoàn tất upload. Tài liệu nguồn có thể tồn tại
độc lập trước khi import; ảnh câu hỏi chỉ được liên kết trong editor của bản
nháp.

Admin có thể tải tài liệu nguồn hợp lệ và yêu cầu parser đồng bộ. Parser cố gắng
trích xuất tiêu đề, câu hỏi Phần I, lựa chọn ABCD, câu tư liệu Phần II, phát
biểu Đúng/Sai, đáp án đúng và lời giải. Trường mơ hồ được đánh dấu cảnh báo thay
vì tự suy diễn.

Tệp lớn hơn 20 MB, xử lý quá 120 giây và PDF scan/chỉ có ảnh bị từ chối an toàn
với phản hồi có thể xử lý. Import thành công tạo hoặc cập nhật bản nháp và liên
kết tài liệu nguồn; import thất bại không tạo bản nháp rỗng. Kết quả nhập không
bao giờ tự xuất bản.

## Rà soát, xuất bản và soạn thủ công

Admin rà soát nguồn, dữ liệu trích xuất và cảnh báo, sau đó sửa mọi lỗi
validation trước khi xuất bản. Editor bản nháp là nơi quản lý metadata, chủ đề,
thời lượng, câu hỏi Phần I, câu tư liệu Phần II, lựa chọn, phát biểu, đáp án
đúng, lời giải và ảnh.

Soạn đề thủ công là entry point thay thế khi admin không có tài liệu nguồn. Hệ
thống tạo draft trống hoặc draft mới từ phiên bản đã xuất bản hiện hành, rồi dùng
cùng editor, validation, versioning, audit và publish contract với draft được
nhập từ parser.
