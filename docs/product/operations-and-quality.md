# Vận hành và chất lượng

## Ranh giới kiến trúc

Repository là monorepo:

```text
apps/web/          frontend Next.js App Router
services/api/      FastAPI, SQLAlchemy, Alembic, parser đồng bộ
infra/caddy/       cấu hình reverse proxy và TLS
compose.yml        topology dịch vụ VPS
```

Docker Compose chạy `proxy`, `web`, `api` và `db` trên VPS. Nginx route `/v1/*`
tới FastAPI và mọi đường dẫn còn lại tới Next.js. Điều này giữ trải nghiệm trình
duyệt cùng origin và tránh cấu hình CORS công khai.

FastAPI xử lý REST/OpenAPI, Google OAuth callback, xác thực session nội bộ,
RBAC, chấm điểm và đồng hồ. PostgreSQL là nguồn dữ liệu duy nhất, migration được
áp dụng qua Alembic. Cloudflare R2 và Seq là dịch vụ ngoài.

## Mục tiêu dịch vụ

- Ít nhất 95% request API đọc/ghi thông thường hoàn thành trong một giây khi
  không có tiến trình nhập.
- Lượt nhập đồng bộ hợp lệ bị giới hạn 20 MB và 120 giây.
- Lỗi nhập không được cản học sinh bắt đầu, trả lời, nộp hoặc xem lại lượt làm.
- Health check báo khả năng truy cập PostgreSQL và object storage.
- Baseline Ubuntu 24.04, 1 vCPU và 2 GB RAM chỉ dành cho lưu lượng thấp; các
  container cần giới hạn bộ nhớ và cảnh báo khi có áp lực tài nguyên.

## Bảo mật và bảo vệ dữ liệu

- TLS là bắt buộc; secret không được có trong source control hoặc application
  log.
- Dùng presigned URL ngắn hạn và phân quyền phía server cho tài sản.
- Rate limit các route đăng nhập, bắt đầu lượt làm, lưu đáp án, nộp và nhập đề.
- Backup PostgreSQL hằng ngày và diễn tập khôi phục ở staging.
- Bật versioning và lifecycle policy phù hợp cho object storage.
- Trước production, công bố Điều khoản sử dụng và Chính sách bảo mật bao gồm dữ
  liệu Google tối thiểu, thời hạn lưu và yêu cầu xóa dữ liệu.

## Điều kiện phát hành

Mọi acceptance criteria trong `docs/story-packet.md` cần bằng chứng tự động
hoặc UAT được ghi lại. Chặn phát hành nếu có lộ đáp án trước khi nộp, vượt quyền,
điểm không đúng hoặc mất/hỏng lịch sử lượt làm.
