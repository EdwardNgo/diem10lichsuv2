# Guideline Chạy Môi Trường Và Migration

## Mục Đích

Tài liệu này mô tả cách chạy ứng dụng Điểm 10 Lịch sử trên local, UAT/VPS và
quy trình bắt buộc khi thay đổi có database migration.

## Môi Trường

### Local Docker Compose

Local Docker là đường chạy gần VPS nhất.

1. Tạo `.env` từ `.env.example` và điền secret thật cho máy local.
2. Khởi động stack:

```shell
docker compose --env-file .env up -d --build
```

3. Chạy migration:

```shell
docker compose --env-file .env exec -T api python -m alembic upgrade head
```

4. Kiểm tra migration hiện tại:

```shell
docker compose --env-file .env exec -T api python -m alembic current
```

5. Nếu cần dữ liệu demo cho UAT local:

```shell
docker compose --env-file .env exec -T api python scripts/seed_demo_exams.py
```

Không chạy seed demo trên production.

### Local Dev Backend

Khi cần chạy API trực tiếp ngoài container, vẫn nên dùng Postgres từ Compose.

```shell
docker compose --env-file .env up -d db
cd services/api
DATABASE_URL="postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:${POSTGRES_PORT:-5432}/$POSTGRES_DB" uvx poetry run uvicorn diem10_api.main:app --reload
```

Trước khi test API trực tiếp, chạy migration bằng cùng `DATABASE_URL`:

```shell
cd services/api
DATABASE_URL="postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:${POSTGRES_PORT:-5432}/$POSTGRES_DB" uvx poetry run alembic upgrade head
```

### Local Dev Frontend

```shell
cd apps/web
pnpm dev
```

Nếu frontend gọi API qua Nginx proxy, dùng Docker Compose stack. Nếu chạy Next dev
riêng, cần đảm bảo request `/v1/...` được proxy đúng tới API.

### UAT/VPS Docker Compose

UAT/VPS dùng cùng `compose.yml`, nhưng `.env` phải là secret của môi trường đó:

- `APP_BASE_URL` là domain thật của môi trường.
- Google OAuth callback phải là `${APP_BASE_URL}/v1/auth/google/callback`.
- `POSTGRES_PASSWORD`, Google OAuth secret và R2 secret không commit vào git.
- `HTTP_PORT` trỏ tới port được reverse proxy/firewall cho phép.

Deploy cơ bản:

```shell
docker compose --env-file .env up -d --build db
docker compose --env-file .env run --rm api python -m alembic upgrade head
docker compose --env-file .env up -d --build
docker compose --env-file .env ps
```

Smoke sau deploy:

```shell
curl -fsS "$APP_BASE_URL/v1/public/exams?page_size=1"
curl -fsS "$APP_BASE_URL/v1/public/exams/filters"
```

Admin đầu tiên vẫn bootstrap bằng SQL thủ công theo quyết định US-03.

## Khi Có Thay Đổi Schema

### Tạo Migration

Khi thay đổi SQLAlchemy models trong `services/api/src/diem10_api/models.py`:

```shell
cd services/api
uvx poetry run alembic revision --autogenerate -m "describe schema change"
uvx poetry run ruff check --fix .
uvx poetry run ruff format .
uvx poetry run pyright
uvx poetry run pytest
```

Sau khi autogenerate, phải review migration thủ công trước khi chạy:

- Kiểm tra `down_revision` đúng migration head hiện tại.
- Kiểm tra index partial PostgreSQL, đặc biệt boolean condition không bị sinh kiểu
  SQLite như `is_primary IS 1`.
- Kiểm tra constraint/check/index có tên ổn định.
- Không để migration xóa dữ liệu hoặc drop cột trong shared/prod nếu chưa có
  recovery plan rõ ràng.
- Không sửa migration đã chạy trên shared/prod; tạo migration mới để sửa tiếp.

### Chạy Migration Local

```shell
docker compose --env-file .env up -d db
docker compose --env-file .env run --rm api python -m alembic upgrade head
docker compose --env-file .env exec -T api python -m alembic current
```

Nếu API container đã chạy image mới, có thể dùng:

```shell
docker compose --env-file .env exec -T api python -m alembic upgrade head
```

### Chạy Migration UAT/Production

Thứ tự an toàn:

1. Backup database hoặc tạo snapshot volume trước migration.
2. Build/pull image mới chứa migration.
3. Chạy `alembic upgrade head` bằng one-off API container.
4. Khởi động/recreate app containers.
5. Smoke public endpoints và flow chính bị ảnh hưởng.
6. Kiểm tra `docker compose ps` và logs nếu healthcheck chưa healthy.

Lệnh mẫu:

```shell
docker compose --env-file .env up -d --build db
docker compose --env-file .env run --rm api python -m alembic upgrade head
docker compose --env-file .env up -d --build api web proxy
docker compose --env-file .env exec -T api python -m alembic current
```

Không chạy `alembic downgrade` trên production nếu chưa có chỉ đạo rollback cụ
thể, backup đã kiểm chứng và hiểu rõ tác động dữ liệu.

### Nếu Migration Fail

1. Dừng deploy app mới nếu migration chưa hoàn tất.
2. Lưu lỗi Alembic/Postgres logs.
3. Không tự ý sửa trực tiếp database production.
4. Nếu migration chưa thay đổi dữ liệu, sửa migration/code và chạy lại trên local
   trước.
5. Nếu migration đã thay đổi một phần dữ liệu, dùng backup/snapshot hoặc migration
   sửa lỗi có kiểm soát.

## Logging Backend

API dùng `structlog` và middleware log request/response đầy đủ (trừ `/healthz`).

Biến môi trường:

- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR` (mặc định `INFO`).
- `LOG_JSON`: `true` để xuất JSON cho production/log aggregator.
- `LOG_REQUEST_BODY`: `true`/`false` — log body request (mặc định `true`).
- `LOG_RESPONSE_BODY`: `true`/`false` — log body response (mặc định `true`).
- `LOG_MAX_BODY_BYTES`: giới hạn bytes body log (mặc định `65536`).

Header nhạy cảm (`cookie`, `authorization`) được redact. Mỗi request có
`x-request-id` trong response để trace log.

Cấu trúc code backend:

- `controllers/`: route HTTP mỏng.
- `services/`: business logic.
- `repositories/`: truy cập database.
- `models/`: SQLAlchemy entities.
- `schemas/`: Pydantic request/response DTO.

## Validation Checklist

Sau mỗi change có migration:

- `uvx poetry run ruff check --fix .`
- `uvx poetry run ruff format .`
- `uvx poetry run pyright`
- `uvx poetry run pytest`
- `pnpm lint && pnpm build` trong `apps/web` nếu UI hoặc API contract ảnh hưởng UI.
- `docker compose --env-file .env up -d --build`
- `docker compose --env-file .env exec -T api python -m alembic current`
- Smoke endpoint liên quan qua Nginx/proxy, không chỉ gọi service nội bộ.
