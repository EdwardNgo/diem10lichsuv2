# Quản trị nội dung

## Vòng đời đề

Đề chuyển qua các trạng thái `draft`, `in_review`, `published` và `archived`.
Chỉ phiên bản đã xuất bản mới mở lượt làm mới cho học sinh. Xuất bản thay đổi
trên đề hiện có tạo phiên bản mới thay vì sửa lượt làm lịch sử.

Đề chỉ được xuất bản khi có metadata hợp lệ, thời lượng hợp lệ, ít nhất một câu
và mỗi câu có nội dung, ít nhất hai lựa chọn, đúng một đáp án đúng và lời giải.

## Soạn đề thủ công

Admin tạo bản nháp với tiêu đề, mô tả, chủ đề lịch sử, năm, mức độ, thời lượng,
câu hỏi, lựa chọn, đáp án đúng, lời giải và ảnh. Admin có thể sửa và sắp xếp các
trường này trước khi xuất bản.

## Tài sản

Tài liệu nguồn và ảnh nằm trong object storage tương thích S3. Database lưu
object key, MIME type, kích thước, checksum và metadata ứng dụng, không lưu blob
tệp.

Định dạng được hỗ trợ ở phiên bản đầu:

- Tài liệu nguồn: DOCX và PDF có lớp chữ.
- Ảnh câu hỏi: JPEG, PNG và WebP.

Tệp nguồn chỉ dành cho admin. Kiểm tra tệp xác thực loại được phép, phần mở rộng,
kích thước và checksum trước khi liên kết tài sản với đề.

## Nhập và rà soát đồng bộ

Admin có thể tải tài liệu nguồn hợp lệ và yêu cầu parser đồng bộ. Parser cố gắng
trích xuất tiêu đề, câu hỏi, lựa chọn, đáp án đúng và lời giải. Trường mơ hồ được
đánh dấu cảnh báo thay vì tự suy diễn.

Tệp lớn hơn 20 MB, xử lý quá 120 giây và PDF scan/chỉ có ảnh bị từ chối an toàn
với phản hồi có thể xử lý. Kết quả nhập chỉ tạo hoặc cập nhật bản nháp. Admin rà
soát nguồn, dữ liệu trích xuất và cảnh báo, sau đó sửa mọi lỗi validation trước
khi xuất bản.
