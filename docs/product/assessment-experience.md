# Trải nghiệm làm bài

## Khám phá đề đã xuất bản

Học sinh có thể tìm và lọc đề đã xuất bản hiện hành theo tiêu đề, chủ đề/giai
đoạn lịch sử, năm và mức độ. Thẻ đề hiển thị tiêu đề, mô tả ngắn, chủ đề, số
câu, thời lượng và trạng thái đã làm.

## Vòng đời lượt làm

Bắt đầu đề tạo một lượt làm `in_progress` cho học sinh và đề đó. Hệ thống lưu
snapshot phiên bản đề hiện hành cùng `started_at` và `expires_at`. Học sinh tiếp
tục lượt làm chưa hết hạn thay vì tạo lượt mới cho cùng đề.

Lượt làm chuyển thành:

- `submitted` khi học sinh nộp trước hạn.
- `expired_and_submitted` khi server đóng và chấm lúc hết hạn.

Chỉ lượt làm `in_progress` chưa hết hạn mới nhận thay đổi đáp án.

## Hoàn thành đề

Mỗi câu có đúng một đáp án có thể chọn. UI hỗ trợ điều hướng câu, tiến độ, đánh
dấu xem lại, đếm ngược và tự lưu. Khi lưu đáp án thất bại, UI phải cho biết trạng
thái chưa lưu và cho phép thử lại.

Đồng hồ phía client chỉ để hiển thị. Server từ chối thay đổi đáp án sau
`expires_at`, kể cả khi người dùng kết nối lại sau thời gian offline.

Trước khi tự nộp, hệ thống hiển thị số câu chưa trả lời và yêu cầu xác nhận. Thao
tác nộp có tính idempotent.

## Chấm điểm và xem lại

Mỗi câu có trọng số bằng nhau. Điểm được tính:

`round(correct_answers / total_questions × 10, 2)`

Câu sai và bỏ trống nhận 0 điểm; không có điểm âm. Kết quả hoàn thành gồm tổng
đúng/sai/bỏ trống, điểm, thời gian sử dụng, đáp án học sinh chọn, đáp án đúng và
lời giải cho từng câu.

Học sinh có thể làm lại không giới hạn. Mỗi lần làm lại tạo lượt làm mới theo
phiên bản đề đã xuất bản hiện hành. Kết quả có sẵn gắn với phiên bản gốc và không
bao giờ được chấm lại sau khi admin sửa câu hỏi.
