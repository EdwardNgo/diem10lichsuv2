# 0001 Kiến trúc monorepo trên VPS

Ngày: 2026-07-24

## Trạng thái

Đã chấp nhận

## Bối cảnh

Ứng dụng cần trải nghiệm học công khai, domain đề thi do server quyết định, xác
thực Google, parser tài liệu và vận hành đơn giản trên VPS. Bản phát hành đầu
phải tránh độ phức tạp vận hành chưa cần thiết cho phạm vi sản phẩm đã chấp nhận.

## Quyết định

Dùng monorepo gồm:

- Frontend Next.js App Router tại `apps/web`.
- Backend FastAPI tại `services/api`.
- PostgreSQL là nguồn dữ liệu chính, truy cập qua SQLAlchemy và migration qua
  Alembic.
- Docker Compose cho reverse proxy, web, API và database.
- Nginx route `/v1/*` tới FastAPI và đường dẫn còn lại tới Next.js.
- FastAPI sở hữu Google OAuth/session/RBAC và parser tài liệu đồng bộ.
- Cloudflare R2 là object storage tương thích S3; Seq nằm ngoài.
- Baseline VPS là Ubuntu 24.04, 1 vCPU, 2 GB RAM. Đây chỉ phù hợp lưu lượng thấp;
  service phải có giới hạn tài nguyên, health check và giám sát bộ nhớ.
- Domain chưa được chọn; ứng dụng dùng biến `APP_BASE_URL` cho tới staging.

Không đưa Redis, RabbitMQ hoặc worker vào bản phát hành đầu.

## Các phương án đã cân nhắc

1. Go backend: runtime nhẹ hơn nhưng kém phù hợp parser DOCX/PDF và chậm hơn cho
   stack đội ngũ đã chọn.
2. Java/Spring Boot: nền tảng enterprise trưởng thành nhưng tốn chi phí phát
   triển/vận hành hơn cho VPS ban đầu.
3. Chỉ dùng Next.js backend: làm trùng hoặc suy yếu ranh giới FastAPI,
   SQLAlchemy, Alembic và parser đã chọn.
4. Parser qua queue ngay từ đầu: phức tạp không cần thiết khi parser bị giới hạn
   20 MB và 120 giây.

## Hệ quả

Tích cực:

- Ranh giới frontend/backend rõ ràng với một server có thẩm quyền cho bảo mật và
  quy tắc làm bài.
- Route cùng origin đơn giản hóa xác thực trình duyệt và CORS.
- Thư viện Python đáp ứng yêu cầu parser ban đầu.
- Docker Compose là topology VPS có thể deploy và tái lập.

Đánh đổi:

- Parser đồng bộ tiêu thụ năng lực request API và có giới hạn tệp/thời gian rõ
  ràng.
- Hai runtime ứng dụng yêu cầu pipeline build/test frontend và backend riêng.
- Tải trong tương lai có thể cần chuyển import sang worker bất đồng bộ.
- VPS 2 GB RAM có rủi ro thiếu bộ nhớ khi parser hoặc PostgreSQL tăng tải; cần
  nâng ít nhất 4 GB RAM hoặc tách workload khi số liệu vận hành cho thấy áp lực.

## Công việc tiếp theo

- Giữ interface parser độc lập với request handling để có thể chuyển sang dịch
  vụ nền sau này.
- Cấu hình domain staging/production, Google OAuth redirect URI và quản lý
  secret production trước khi deploy.
