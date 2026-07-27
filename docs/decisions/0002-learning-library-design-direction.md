# 0002 Hướng thiết kế Thư viện học tập

Ngày: 2026-07-26

## Trạng thái

Đã chấp nhận

## Bối cảnh

US-01 cần một design template nhất quán cho landing page, màn hình làm đề và
trang quản trị. Sản phẩm hướng tới học sinh THPT, cần hỗ trợ đọc đề dài, ôn tập
tập trung và lời giải chi tiết.

## Quyết định

Chọn hướng **Thư viện học tập**:

- Giao diện sáng, điềm tĩnh, ưu tiên khả năng đọc và tập trung.
- Font sans hiện đại, màu nhấn xanh ngọc trầm duy nhất trên nền trung tính.
- Landing page dùng bố cục biên tập: thông điệp rõ, đề nổi bật và gợi ý chủ đề.
- Hero có dòng thời gian ôn tập với các mốc lịch sử; khối “Đề hôm nay” là điểm
  neo thị giác và CTA thực dụng chính.
- Có thể dùng texture tư liệu nhẹ từ CSS/SVG, không dùng ảnh lịch sử chưa rõ
  quyền sử dụng.
- Màn hình làm bài dành phần lớn diện tích cho câu hỏi; điều hướng câu và trạng
  thái đáp án có mật độ thấp, không gây áp lực thị giác.
- Admin dùng cấu trúc dữ liệu thực dụng, trạng thái xuất bản rõ ràng.
- Chuyển động timeline/đề nổi bật được tiết chế và luôn tôn trọng
  `prefers-reduced-motion`.

## Các phương án đã cân nhắc

1. Phòng thi kỷ luật: phù hợp mô phỏng buổi thi nhưng quá khô cứng cho trải
   nghiệm ôn tập thường xuyên.
2. Lịch sử kể chuyện: có bản sắc mạnh ở landing page nhưng có nguy cơ làm nội
   dung học tập nặng và phân mảnh hệ thống giao diện.

## Hệ quả

Tích cực:

- Có hệ thống trực quan bền vững cho cả ba bề mặt khách/học sinh/admin.
- Độ tương phản, typographic hierarchy và keyboard navigation là ưu tiên ngay
  từ US-01.

Đánh đổi:

- Landing page ít tính trình diễn hơn hướng kể chuyện.
- Cần dùng hình/tư liệu lịch sử chọn lọc để tránh trở thành giao diện chung
  chung.

## Công việc tiếp theo

- Triển khai US-01 theo hướng này và kiểm tra bằng Vercel UI guidelines cùng
  WCAG 2.2.
