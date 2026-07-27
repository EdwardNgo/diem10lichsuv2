# Định danh và truy cập

## Xác thực

Người dùng đăng nhập và đăng xuất qua Google OAuth/OIDC. FastAPI xử lý OAuth
callback, tạo hồ sơ nội bộ và phát session duy nhất của ứng dụng. Định danh hồ
sơ là Google `sub`; email chỉ là thuộc tính, không phải khóa định danh chính.

Session cookie dùng `HttpOnly`, `Secure` và `SameSite=Lax`. Session hết hạn
hoặc không hợp lệ không được truy cập API cần xác thực.

## Vai trò

- `student` là vai trò mặc định sau khi đăng nhập Google thành công.
- `admin` chỉ được gán khi email tài khoản có trong admin allowlist lúc đăng
  nhập.

Backend kiểm tra vai trò trên mọi API đặc quyền. Việc hiển thị trên UI không
thay thế cho phân quyền.

## Quy tắc phân quyền

- Khách chỉ đọc metadata công khai của đề đã xuất bản.
- Học sinh chỉ truy cập lượt làm, đáp án và kết quả của chính mình.
- Học sinh không thể lấy đáp án đúng, lời giải, tệp nguồn hoặc nội dung đề nháp
  trước khi nộp.
- Admin có thể tạo và quản lý nội dung, tài sản, lượt nhập, rà soát và xuất bản.

## Yêu cầu nhật ký kiểm toán

Ghi nhận actor, thời điểm, đối tượng và thao tác cho việc cập nhật allowlist,
nhập đề, xuất bản, thay đổi đáp án đúng và archive.
