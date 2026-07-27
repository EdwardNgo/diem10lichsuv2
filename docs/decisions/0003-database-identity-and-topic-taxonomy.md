# 0003 Định danh database và taxonomy chủ đề

Ngày: 2026-07-26

## Trạng thái

Đã chấp nhận

## Bối cảnh

Migration đầu tiên đã tạo schema tối thiểu cho API public. Trước khi schema được
dùng lâu dài, cần chốt kiểu khóa chính và mô hình chủ đề để hỗ trợ lọc đề, báo
cáo tiến độ và các ràng buộc phiên bản.

## Quyết định

- Dùng UUID native PostgreSQL làm khóa chính cho các thực thể domain.
- Chuẩn hóa chủ đề qua bảng `topics`; `exam_versions` liên kết với chủ đề thay
  vì lưu text tự do.
- Thực thi ràng buộc database: unique `(exam_id, version_number)`, tối đa một
  version `published` cho một exam, và kiểm tra hợp lệ cho status/duration/
  position.

## Các phương án đã cân nhắc

1. UUID dạng `String(36)`: đơn giản cho SQLite nhưng không tận dụng native type
   và validation của PostgreSQL.
2. `topic` text tự do: nhanh ở bản đầu nhưng làm filter/báo cáo không nhất quán
   và dễ tạo dữ liệu trùng nghĩa.

## Hệ quả

Tích cực:

- Dữ liệu có ràng buộc chặt hơn tại tầng PostgreSQL.
- Topic filter và phân tích tiến độ dùng cùng một taxonomy.

Đánh đổi:

- Migration ban đầu và test SQLite cần được điều chỉnh để tương thích UUID native.
- Admin cần chọn topic từ taxonomy hoặc được cấp quyền tạo topic mới.

## Công việc tiếp theo

- Sửa migration đầu tiên trước khi môi trường dùng chung áp dụng nó.
- Bổ sung bảng `topics`, FK từ `exam_versions`, index/ràng buộc P0 và seed
  taxonomy ban đầu.
