# 0004 Production delivery qua GHCR, CD thủ công và R2 backup

Date: 2026-08-15

## Status

Accepted

## Context

Ứng dụng chạy trên VPS bằng Docker Compose. CI hiện có chỉ lint/test/build, còn
VPS đang build image tại chỗ theo runbook cũ. Với baseline VPS nhỏ, build trên
server vừa tốn tài nguyên vừa khó rollback vì không có image tag bất biến.

Product yêu cầu TLS, secret không nằm trong source control và backup PostgreSQL
hằng ngày. Ứng dụng đã dùng Cloudflare R2 cho tài liệu nguồn/ảnh, còn database
vẫn là nguồn dữ liệu chính cần dump riêng.

## Decision

GitHub Actions publish hai image `diem10lichsu-web` và `diem10lichsu-api` lên
GitHub Container Registry (`ghcr.io`) sau khi kiểm tra web/API xanh. Image được
tag bằng `sha-<short-sha>`, `latest` trên `main`, và tag version khi push git
tag `v*`.

Production deploy là thao tác thủ công trên VPS: operator chọn `IMAGE_TAG`, pull
image, chạy Alembic migration bằng one-off API container, recreate service và
smoke endpoint công khai. Rollback release dùng lại image tag cũ; không chạy
`alembic downgrade` nếu chưa có chỉ đạo phục hồi dữ liệu rõ ràng.

Backup PostgreSQL chạy hằng ngày bằng cron trên VPS, tạo `pg_dump -Fc` từ
container database và upload lên R2 bucket backup riêng. Bucket chứa tài liệu
nguồn/ảnh bật object versioning/lifecycle riêng, không thay thế backup database.

TLS mặc định đi qua Cloudflare trước VPS. Giai đoạn ổn định production dùng
Cloudflare Full (strict) với origin certificate hoặc certificate tương đương.

## Alternatives Considered

1. Build image trực tiếp trên VPS: đơn giản hơn lúc đầu nhưng tốn RAM/CPU, khó
   pin release và rollback.
2. Auto-deploy SSH từ GitHub Actions: giảm thao tác tay nhưng tăng quyền CI và
   rủi ro thay đổi production khi quy trình vận hành chưa diễn tập đủ.
3. Worker/queue backup trong ứng dụng: không phù hợp phạm vi bản đầu vì product
   đang loại Redis, RabbitMQ và worker nền.
4. Docker Hub: quen thuộc nhưng giới hạn private repository không phù hợp khi
   cần tách private image web và API.

## Consequences

Positive:

- Mỗi release có image tag có thể pull lại và rollback.
- VPS không cần build application image.
- Migration và smoke vẫn nằm trong quyền kiểm soát của operator.
- Backup database và object storage có ranh giới rõ.

Tradeoffs:

- Deploy vẫn cần thao tác thủ công và kỷ luật ghi nhận image tag.
- Cron backup cần theo dõi log và diễn tập restore định kỳ.
- Cloudflare Flexible chỉ nên là bước tạm; production ổn định cần Full (strict).

## Follow-Up

- Cấu hình quyền package trên GitHub Container Registry và đảm bảo VPS có quyền
  pull private images nếu repository/package đang private.
- Cấu hình Cloudflare DNS/TLS và Google OAuth callback production.
- Thiết lập R2 lifecycle cho backup bucket và diễn tập restore ở staging.
- Thêm monitoring/rate limit production trong luồng vận hành riêng.
