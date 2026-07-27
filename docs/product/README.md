# Tài liệu sản phẩm

Thư mục này chứa hành vi sản phẩm hiện hành được suy ra từ yêu cầu đã chấp nhận.
Harness không tự tạo ra domain sản phẩm giả.

Khi người dùng cung cấp đặc tả sản phẩm, hãy tách thành các tài liệu sống nhỏ
hơn ở đây thay vì duy trì một đặc tả lớn làm tài liệu vận hành. Đặt tên tệp theo
domain sản phẩm thực tế.

## Product contract hiện hành

Product contract của ứng dụng Lịch sử THPT được tách theo domain:

- [Tổng quan](overview.md): kết quả, người dùng, phạm vi và ranh giới phát hành.
- [Định danh và truy cập](identity-and-access.md): Google login, session, vai trò và phân quyền.
- [Trải nghiệm làm bài](assessment-experience.md): khám phá, lượt làm, đồng hồ, chấm điểm, kết quả và lịch sử.
- [Quản trị nội dung](content-administration.md): soạn đề, tài sản, nhập đồng bộ, rà soát và xuất bản.
- [Vận hành và chất lượng](operations-and-quality.md): ranh giới kiến trúc, bảo mật, độ tin cậy và tiêu chí phát hành.

Snapshot yêu cầu ban đầu được giữ ở gốc repository tại [`SPEC.md`](../../SPEC.md).
Các tệp trên là product docs sống có thẩm quyền. User story có thể bàn giao và
acceptance criteria được nhóm trong [`docs/story-packet.md`](../story-packet.md).

## Quy tắc cập nhật

Khi hành vi thay đổi:

1. Cập nhật product document bị ảnh hưởng khi hành vi mong đợi thay đổi.
2. Cập nhật execution plan active khi công việc phức tạp có sử dụng plan.
3. Chỉ thêm lasting decision khi công việc sau cần kế thừa lựa chọn quan trọng
   về sản phẩm, kiến trúc, dữ liệu, bảo mật, tương thích hoặc validation.
4. Thêm hoặc cập nhật bằng chứng thực thi kiểm tra hành vi đó.

Thay đổi có phạm vi hẹp không yêu cầu story packet, proof-matrix hay thay đổi
Harness CLI.
