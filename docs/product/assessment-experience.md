# Trải nghiệm làm bài

## Khám phá đề đã xuất bản

Học sinh có thể tìm và lọc đề đã xuất bản hiện hành theo tiêu đề, chủ đề/giai
đoạn lịch sử, năm và mức độ. Thẻ đề hiển thị tiêu đề, mô tả ngắn, chủ đề, cấu
trúc đề, thời lượng và trạng thái đã làm.

## Vòng đời lượt làm

Bắt đầu đề tạo một lượt làm `in_progress` cho học sinh và đề đó. Hệ thống lưu
snapshot phiên bản đề hiện hành cùng `started_at`, `expires_at` và mốc
`paused_at` khi tạm dừng. Học sinh tiếp tục lượt làm chưa hết hạn thay vì tạo
lượt mới cho cùng đề.

Lượt làm chuyển thành:

- `submitted` khi học sinh nộp trước hạn.
- `expired_and_submitted` khi server đóng và chấm lúc hết hạn.

Chỉ lượt làm `in_progress`, đang hoạt động và chưa hết hạn mới nhận thay đổi đáp
án. Khi học sinh rời màn hình làm bài, server ghi mốc tạm dừng. Khi mở lại,
server dời `expires_at` theo đúng thời gian đã tạm dừng để giữ nguyên số giây còn
lại.

## Cấu trúc đề

Đề thi Lịch sử chuẩn gồm hai phần cố định:

- Phần I có 24 câu trắc nghiệm ABCD. Mỗi câu có bốn lựa chọn, đúng một đáp án và
  tối đa 0,25 điểm.
- Phần II có 4 câu tư liệu. Mỗi câu có một đoạn tư liệu và đúng bốn phát biểu;
  học sinh chọn Đúng hoặc Sai cho từng phát biểu. Mỗi câu tối đa 1,00 điểm.

Đề cũ chỉ có câu trắc nghiệm được giữ tương thích bằng cách coi toàn bộ câu là
Phần I, nhưng đề xuất bản mới phải theo cấu trúc 24 + 4.

## Hoàn thành đề

UI hỗ trợ điều hướng theo hai phần, tiến độ, đánh dấu xem lại, đếm ngược và tự
lưu. Câu Phần I được tính đã trả lời khi có một lựa chọn ABCD. Câu Phần II được
tính đã hoàn tất khi cả bốn phát biểu đã được chọn Đúng hoặc Sai. Khi lưu đáp án
thất bại, UI phải cho biết trạng thái chưa lưu và cho phép thử lại.

Tiến độ được thu gọn thành một bảng điều hướng mở theo yêu cầu để dành phần lớn
chiều rộng cho câu hỏi và đáp án. Khi học sinh bấm liên kết rời khỏi lượt làm
đang diễn ra, UI phải yêu cầu xác nhận rồi tạm dừng lượt làm trên server; thao
tác đóng hoặc tải lại trang dùng cảnh báo rời trang của trình duyệt và gửi yêu
cầu tạm dừng dạng `keepalive`.

Đồng hồ phía client chỉ để hiển thị. Khi lượt làm đang hoạt động, server từ chối
thay đổi đáp án sau `expires_at`. Thời gian lượt làm ở trạng thái tạm dừng không
được trừ vào thời gian còn lại.

Trước khi tự nộp, hệ thống hiển thị số câu chưa trả lời và yêu cầu xác nhận. Thao
tác nộp có tính idempotent.

## Chấm điểm và xem lại

Điểm tối đa là 10. Phần I tối đa 6 điểm: mỗi câu ABCD đúng được 0,25 điểm, sai
hoặc bỏ trống được 0 điểm.

Phần II tối đa 4 điểm. Với mỗi câu tư liệu, số phát biểu học sinh chọn đúng được
quy đổi như sau:

- 0 phát biểu đúng: 0 điểm.
- 1 phát biểu đúng: 0,10 điểm.
- 2 phát biểu đúng: 0,25 điểm.
- 3 phát biểu đúng: 0,50 điểm.
- 4 phát biểu đúng: 1,00 điểm.

Phát biểu bỏ trống tính là sai; không có điểm âm. Điểm tổng được tính bằng tổng
điểm các câu và làm tròn 2 chữ số thập phân. Kết quả hoàn thành gồm tổng điểm,
breakdown theo phần, thời gian sử dụng, đáp án học sinh chọn, đáp án đúng, điểm
từng câu và lời giải.

Điểm hiển thị tối đa 2 chữ số thập phân và bỏ các số 0 không có ý nghĩa ở cuối,
ví dụ `3.1` và `10`. Trong phần xem lại, đáp án đúng dùng dấu tích xanh và lựa
chọn sai của học sinh dùng dấu X đỏ thay cho nhãn chữ lặp lại.

Lịch sử làm bài chỉ hiển thị các lượt đã nộp hoặc đã hết giờ của học sinh hiện
tại, gom theo từng đề thi. Danh sách đề được sắp theo lần làm mới nhất; khi chọn
một đề, học sinh xem các lượt làm hoàn thành của đề đó, mới nhất trước. Mở một
lượt trong lịch sử luôn xem lại kết quả, đáp án và lời giải theo phiên bản đề
gốc của lượt đó.

Học sinh có thể làm lại không giới hạn khi đề còn phiên bản xuất bản hiện hành.
Mỗi lần làm lại tạo lượt làm mới theo phiên bản đang xuất bản. Kết quả có sẵn
gắn với phiên bản gốc và không bao giờ được chấm lại sau khi admin sửa hoặc
archive câu hỏi.
