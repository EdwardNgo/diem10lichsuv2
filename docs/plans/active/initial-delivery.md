# Kế hoạch thực thi: Nền tảng học tập bản đầu

Ngày: 2026-07-24

## Trạng thái

Đang thực hiện

## Kết quả mong muốn

Hoàn thành nền tảng học Lịch sử THPT bản đầu theo product docs và story packet
đã chấp nhận, với hành vi xác thực, làm bài, quản trị và triển khai VPS có thể
xác minh.

## Bối cảnh

- Product contract: `docs/product/`
- Story packet: `docs/story-packet.md`
- Quyết định kiến trúc: `docs/decisions/0001-vps-monorepo-architecture.md`
- Snapshot nguồn ban đầu: `SPEC.md`

## Phạm vi

Trong phạm vi:

- Nền tảng monorepo cho Next.js, FastAPI, PostgreSQL và Docker Compose.
- Google authentication, admin allowlist, session/RBAC và audit logging.
- Khám phá đề, lượt làm, tự lưu, đồng hồ, chấm điểm, kết quả và lịch sử của học
  sinh.
- Tải tài liệu nguồn, import đồng bộ, rà soát/xuất bản và tạo draft thủ công của
  admin.
- Test và tài liệu vận hành chứng minh các story đã chấp nhận.

Ngoài phạm vi:

- Tính năng bị loại trừ trong `docs/product/overview.md`.
- OCR, worker bất đồng bộ, Redis, RabbitMQ và deploy production trước khi có
  quyết định hạ tầng cần thiết.

## Cách tiếp cận

1. Scaffold topology repository và môi trường compose local.
2. Thiết lập ranh giới persistence, migration, định danh, phân quyền và audit.
3. Hoàn thành luồng làm bài của học sinh theo thứ tự story.
4. Hoàn thành luồng quản trị nội dung theo thứ tự upload tài liệu nguồn, import
   đồng bộ, rà soát/xuất bản và entry point thủ công dùng editor chung.
5. Thêm bằng chứng focused, integration và end-to-end trước staging.

## Rủi ro và khôi phục

- Parser đồng bộ có thể vượt năng lực request. Thực thi giới hạn đã ghi và chỉ
  chuyển sang dịch vụ nền sau khi có nhu cầu quan sát được.
- Phiên bản hóa sai có thể đổi điểm lịch sử. Xác thực snapshot lượt làm bất biến
  trước khi xuất bản quản trị nội dung.
- Cấu hình auth/cookie sai có thể làm hỏng session cùng origin. Test proxy route
  và vòng đời session trong Docker trước khi mở rộng tính năng.
- Rollback release qua image bất biến và duy trì backup/recovery migration trước
  production.

## Tiến độ

- [x] Tách product docs, story packet, quyết định kiến trúc và plan từ SPEC đã
  chấp nhận.
- [x] Scaffold monorepo và runtime local.
- [x] Chốt US-01: landing page, metadata đề published, CTA đăng nhập an toàn,
  trạng thái loading/empty/error và giao diện kho đề theo gam xanh nước biển.
- [x] Tạo migration nền và API công khai chỉ đọc đề `published` cho US-01.
- [x] Đồng bộ migration nền với UUID native, taxonomy chuẩn hóa và ràng buộc
  version/status theo decision 0003.
- [ ] Triển khai US-02 đến US-03.
- [ ] Triển khai US-04 đến US-09.
- [x] Sửa vòng đời US-05/US-07 để lượt làm tạm dừng trên server khi học sinh
  rời bài và tiếp tục với đúng thời gian còn lại.
- [x] Triển khai US-09: lịch sử gom theo đề thi, mở từng đề để xem các lượt làm
  hoàn thành, xem lại snapshot kết quả và làm lại theo phiên bản đề đang xuất
  bản.
- [x] Triển khai US-10: admin lấy presigned URL R2 cho DOCX/PDF nguồn, upload
  trực tiếp lên storage và confirm metadata/checksum thành `source_document`
  asset riêng tư mà chưa tạo draft.
- [ ] Triển khai US-10 đến US-13: upload tài liệu nguồn, import thành draft, rà
  soát/xuất bản và tạo draft thủ công bằng editor chung.
- [ ] Hoàn thành validation và bằng chứng sẵn sàng staging.

## Quyết định

- 2026-07-24: Tài liệu được tách theo product domain; `SPEC.md` là snapshot ban
  đầu.
- 2026-07-24: Kiến trúc monorepo VPS trong decision 0001 đã được chấp nhận.
- 2026-07-26: Dùng Cloudflare R2, Nginx và baseline VPS Ubuntu 24.04 1 vCPU/2 GB
  RAM; domain và OAuth credential được cung cấp qua biến môi trường trước staging.
- 2026-07-26: Frontend dùng Next.js 16, React 19, Tailwind CSS 4 và pnpm;
  backend dùng Python 3.11-compatible FastAPI với Poetry.
- 2026-07-26: US-01 dùng hướng thiết kế Thư viện học tập theo decision 0002.
- 2026-07-26: US-01 hiển thị trạng thái chưa có đề; danh sách đề published và
  Google login redirect được hoàn tất sau khi API công khai/xác thực tồn tại.
- 2026-07-26: API `GET /v1/public/exams` chỉ trả metadata của phiên bản
  `published`; không trả đáp án, lời giải hoặc tệp nguồn.
- 2026-07-26: Database dùng UUID native PostgreSQL và taxonomy `topics` chuẩn
  hóa theo decision 0003; migration đầu chưa áp dụng môi trường dùng chung sẽ
  được điều chỉnh trước khi tiếp tục.
- 2026-07-26: Migration gốc đã được tái tạo theo decision 0003; API public lấy
  tên chủ đề qua liên kết primary topic.
- 2026-07-27: US-01 chuyển từ hướng Thư viện học tập sang hướng kho đề luyện
  thi trực quan hơn, dùng palette xanh nước biển, hero animation nhẹ và không
  hiển thị đáp án/lời giải trước khi người dùng nộp bài.
- 2026-08-06: Đề thi Lịch sử chuyển sang cấu trúc 24 câu ABCD Phần I và 4 câu
  tư liệu Đúng/Sai Phần II. Phần I mỗi câu 0,25 điểm; Phần II mỗi câu quy đổi
  theo số phát biểu đúng 0/1/2/3/4 thành 0/0,10/0,25/0,50/1,00 điểm.
- 2026-08-08: Đồng hồ lượt làm tạm dừng khi học sinh rời màn hình. Backend lưu
  `paused_at` và dời `expires_at` theo khoảng tạm dừng khi tiếp tục, nên client
  không thể tự sửa thời gian còn lại.
- 2026-08-08: Lịch sử học sinh gom theo đề thi và chỉ hiển thị lượt `submitted`
  hoặc `expired_and_submitted` của chính người dùng trong từng đề. Kết quả cũ
  đọc từ version gốc; làm lại luôn tạo attempt theo version `published` hiện
  hành nếu còn.
- 2026-08-09: Luồng admin US-10 đến US-13 ưu tiên upload tài liệu nguồn, import
  parser thành draft, rà soát/xuất bản bằng editor chung; soạn đề thủ công là
  entry point cuối cùng tạo draft trống hoặc draft mới từ đề published.

## Validation

- Bằng chứng focused: ánh xạ mọi acceptance criteria trong story packet đến test
  hoặc bằng chứng UAT khi nhóm triển khai hoàn thành.
- Bằng chứng integration/end-to-end: chạy luồng học sinh và admin qua topology
  Docker Compose, gồm upload/import/rà soát/publish và tạo draft thủ công dùng
  chung editor.
- Kiểm tra bắt buộc repository: định nghĩa format, lint, type-check, test,
  security scan và dependency audit khi scaffold tooling dự án.
- Scaffold đã xác minh: `pnpm lint`, `pnpm build`, Ruff, Pyright, Pytest và
  `docker compose --env-file .env.example config --quiet`.
- US-01 đã xác minh: `pnpm lint`, `pnpm build`, Ruff, Pyright, Pytest,
  `docker compose --env-file .env.example build --pull=false` và Docker web
  image build sau chỉnh UI.
- Tạm dừng/tiếp tục lượt làm đã xác minh bằng `ruff check .`, toàn bộ 20 test
  API, migration chain `alembic upgrade head`, cùng `pnpm lint` và `pnpm build`.
- US-09 đã xác minh bằng test ownership/history/archive/current-version, toàn bộ
  21 test API, migration chain `alembic upgrade head`, cùng `pnpm lint` và
  `pnpm build`. Cập nhật lịch sử nhóm theo đề đã chạy lại `ruff check .`, toàn
  bộ 21 test API, `pnpm lint` và `pnpm build`.
- US-10 đã xác minh bằng test admin upload URL/confirm/permission/validation,
  toàn bộ 24 test API, `ruff check .`, migration chain `alembic upgrade head`,
  `pnpm lint` và `pnpm build`. `pyright` bị treo không có output trong hơn 4
  phút ở môi trường local nên đã dừng và chưa có kết quả type-check mới.

## Kết quả

US-01 đã chốt. Các US tiếp theo bắt đầu bằng US-02 Google authentication/session.
