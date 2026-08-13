# Execution Plan: US-12 — Rà soát, chỉnh sửa và xuất bản

Date: 2026-08-10

## Status

Completed

## Outcome

Admin mở bản nháp (thường từ import US-11), rà soát nguồn/cảnh báo parser, chỉnh metadata và
28 câu hỏi trong editor chung, chạy validation, xuất bản — đề xuất hiện ngay cho học sinh làm
mới; attempt cũ giữ snapshot phiên bản gốc. Publish, đổi đáp án, archive và gắn ảnh câu hỏi
được audit log.

## Context

- Story: `docs/story-packet.md` — US-12 (rà soát/xuất bản); US-13 (soạn thủ công, entry point
  tạo draft — **ngoài phạm vi US-12**)
- Product: `docs/product/content-administration.md`
- Schema: `docs/database-schema.md` — `exam_versions`, `questions`, `asset_links`, `import_findings`
- US-11 đã xong: import tạo `exam_versions` status `draft` + findings; UI chỉ hiển thị draft id
- Hiện trạng code:
  - **Backend**: chỉ có admin upload/import/allowlist; chưa có API draft CRUD, validation, publish,
    archive, question image
  - **Frontend**: `/admin` có upload + import; chưa có editor hay danh sách draft
  - **DB**: `questions`/`question_options`/`question_statements` chưa có `deleted_at` (story yêu cầu
    xóa mềm)

## Phân tích gap so với acceptance criteria

| Tiêu chí US-12 | Hiện trạng | Cần làm |
| -------------- | ---------- | ------- |
| Editor metadata + 24 MC + 4 TF | Draft tồn tại sau import, không API/UI sửa | Admin draft API + editor UI |
| Rà soát import: nguồn, findings | Findings trong DB, không màn rà soát | GET import-context + panel Review |
| Thêm/sửa/xóa mềm/sắp xếp câu | Không | CRUD questions + reorder + migration soft delete |
| Validation publish có lỗi theo trường/câu | Không | `PublishValidationService` |
| Publish → học sinh thấy, attempt cũ giữ version | Chỉ có published query cho public | Publish transaction + archive |
| Optimistic lock 2 admin | Không | `If-Match: updated_at` → 409 |
| Từ chối sửa version đã published | Không guard | Chỉ cho PATCH draft/in_review |
| Audit publish/đáp án/archive/ảnh | Có pattern audit (allowlist, import) | Mở rộng audit actions |
| Cache invalidate trước response publish | Client fetch trực tiếp API, không Redis | Commit DB trước 200; ghi note revalidate nếu thêm cache sau |

### Quyết định authority (story packet)

- **Lời giải tuỳ chọn khi publish** — story packet US-12 ngoại lệ: *“Chỉ cần có đáp án là được,
  lời giải là tuỳ chọn”*. Finding `questions.*.explanation` từ import là **warning**, không chặn
  publish; admin có thể bỏ qua sau khi xác nhận.
- **Warning parser**: publish chặn nếu còn finding `error` chưa resolved; finding `warning` yêu cầu
  `acknowledge_warnings: true` trong body publish (hoặc resolve từng finding khi admin sửa field).

## Scope

In scope:

- Migration `deleted_at` cho `questions`, `question_options`, `question_statements` (xóa mềm nháp)
- `DraftRepository` + `PublishValidationService` + `DraftService` / `PublishService`
- Admin API: list/get/update draft, CRUD/reorder câu hỏi, validate, publish, archive
- Admin API: import context (source asset presigned download URL + findings)
- Admin API: upload ảnh câu hỏi (JPEG/PNG/WebP) + liên kết `asset_links` trên `questions`
- Frontend: danh sách draft, editor `/admin/drafts/[versionId]`, panel rà soát, luồng publish
- Link từ kết quả import US-11 → mở editor
- Unit test validation; integration test publish/archive/conflict/403

Out of scope (US-13):

- Tạo draft trống hoặc draft mới từ đề published (clone)
- Entry point “Soạn đề thủ công”
- Sửa trực tiếp phiên bản published → tạo draft kế tiếp (US-13)

## Approach

### 1. Migration — soft delete câu hỏi nháp

```sql
ALTER TABLE questions ADD COLUMN deleted_at timestamptz NULL;
ALTER TABLE question_options ADD COLUMN deleted_at timestamptz NULL;
ALTER TABLE question_statements ADD COLUMN deleted_at timestamptz NULL;
```

- Query draft editor/publish chỉ load `deleted_at IS NULL`.
- Publish validation đếm câu active; không cho publish nếu ≠ 24 + 4.
- Hard delete không dùng — giữ lịch sử nháp an toàn.

### 2. Publish validation (`services/publish_validation.py`)

Trả `ValidationResult` gồm `errors[]` và `warnings[]`, mỗi item có `field_path`, `message`,
`question_id?`, `part_number?`, `part_position?`.

**Metadata bắt buộc (errors):**

| Trường | Rule |
| ------ | ---- |
| `title` | non-empty, ≤ 255 |
| `summary` | non-empty (import có thể rỗng → admin bổ sung) |
| `duration_minutes` | > 0 |
| `difficulty` | một trong enum đã dùng (`de`, `trung-binh`, `kho` hoặc slug hiện có) |
| `primary_topic_id` | phải có topic active |

**Cấu trúc câu (errors):**

- Phần I: đúng 24 câu `multiple_choice`, `body` non-empty
- Mỗi câu Phần I: đúng 4 options, đúng **một** `is_correct=true`, mỗi option `body` non-empty
- Phần II: đúng 4 câu `true_false_group`, `source_text` non-empty
- Mỗi câu Phần II: đúng 4 statements, mỗi statement `body` non-empty, `is_correct` not null

**Tuỳ chọn (warnings — không chặn nếu `acknowledge_warnings`):**

- `explanation` rỗng
- `year` null
- Import findings chưa `resolved_at`

**Không validate:** ảnh câu hỏi (tuỳ chọn v1).

### 3. Backend services

```
services/api/src/diem10_api/
  repositories/draft_repository.py
  services/publish_validation.py
  services/draft_service.py      # read/update draft, questions CRUD, reorder
  services/publish_service.py     # validate, publish, archive
  schemas/admin_draft.py          # request/response models
```

**Optimistic lock:** mọi PATCH/PUT draft gửi `expected_updated_at` (ISO 8601). Backend so với
`exam_versions.updated_at`; mismatch → `409 Conflict` + draft hiện tại.

**Publish transaction** (`PublishService.publish_draft`):

1. Kiểm tra admin; version status ∈ `{draft, in_review}`
2. Chạy validation; nếu errors → `422` + chi tiết; nếu warnings và không acknowledge → `422`
3. Trong transaction:
   - Nếu exam chưa có published: set version `published`, `published_at=now`
   - Nếu exam đã có published (edge: draft version_number > 1 từ flow sau): archive bản published
     cũ, promote draft
   - Ghi `audit_logs` action `exam.publish`
   - Resolve import findings tương ứng field đã sửa (tuỳ chọn v1: mark all unresolved warnings
     resolved khi acknowledge)
4. Commit **trước** trả response 200

**Archive** (`POST /v1/admin/exams/{exam_id}/archive`):

- Chỉ khi có version `published`; set `archived`, xóa khỏi public list
- Audit `exam.archive`
- Attempt cũ vẫn đọc được snapshot

**Guard published:**

- PATCH/DELETE trên version `published`/`archived` → `409` “Tạo bản nháp mới để chỉnh sửa”
  (US-13 sẽ implement tạo draft; US-12 chỉ từ chối)

### 4. Admin API surface

```
GET    /v1/admin/drafts
       ?status=draft|in_review&page=&page_size=
GET    /v1/admin/drafts/{version_id}
PATCH  /v1/admin/drafts/{version_id}
       Body: { expected_updated_at, title?, summary?, year?, difficulty?,
               duration_minutes?, primary_topic_id? }

GET    /v1/admin/drafts/{version_id}/import-context
       → { source_asset, download_url?, findings[] }

PUT    /v1/admin/drafts/{version_id}/questions
       Body: { expected_updated_at, questions: [ full snapshot 28 câu ] }
       # v1: full replace snapshot — đơn giản, tránh partial orphan; UI autosave gửi cả tree

POST   /v1/admin/drafts/{version_id}/validate
       → ValidationResult (dry-run, không đổi DB)

POST   /v1/admin/drafts/{version_id}/publish
       Body: { expected_updated_at, acknowledge_warnings?: bool }
       → { exam_slug, version_id, published_at }

POST   /v1/admin/exams/{exam_id}/archive

POST   /v1/admin/assets/question-images/upload-url   # mirror source-doc pattern
POST   /v1/admin/assets/question-images              # confirm
POST   /v1/admin/drafts/{version_id}/questions/{question_id}/image
       Body: { asset_id }
DELETE /v1/admin/drafts/{version_id}/questions/{question_id}/image
```

Response `GET draft` gồm:

- Metadata + `updated_at` + `status` + `exam_slug`
- `questions[]` với nested options/statements + optional `image` metadata
- `import_summary?` (warnings count, source filename) nếu có `asset_links`

### 5. Frontend

**Routes:**

- `/admin/drafts` — bảng draft (title, trạng thái, ngày, nút “Rà soát”)
- `/admin/drafts/[versionId]` — editor chính

**Layout editor** (3 vùng):

1. **Metadata** — title, summary, topic (select từ `GET /v1/public/exams/filters` hoặc admin
   topics endpoint), year, difficulty, duration
2. **Câu hỏi** — tab Phần I (24) / Phần II (4); accordion từng câu; inline edit stem, options,
   statements, đáp án đúng, explanation (optional); nút thêm/xóa mềm/reorder (↑↓)
3. **Rà soát** (chỉ khi có import context) — tên file nguồn, link tải, bảng findings filter theo
   severity; click finding → scroll tới field/câu

**Luồng publish:**

1. Nút “Kiểm tra” → `POST validate` → hiển thị lỗi/cảnh báo inline + summary
2. Nếu chỉ warnings → checkbox “Tôi đã rà soát các cảnh báo”
3. Nút “Xuất bản” → `POST publish` → redirect `/exams/{slug}` hoặc toast + link

**Cập nhật US-11 UI:** sau import thành công, nút **“Mở bản nháp”** → `/admin/drafts/{id}`

**Autosave:** debounce 2s gửi `PUT questions` + `PATCH metadata` khi dirty; hiển thị trạng thái
saved/conflict; 409 → modal “Có người khác đã lưu — tải lại?”

### 6. Test plan

**Unit** (`tests/test_publish_validation.py`):

- Draft đủ 28 câu hợp lệ → pass
- Thiếu topic / 23 câu Phần I / 2 đáp án đúng / thiếu source_text Phần II → errors đúng
  `field_path`
- Explanation rỗng → warning only
- Import finding unresolved → warning

**Integration** (`tests/test_admin_draft_publish.py`):

- Admin GET/PATCH draft từ import fixture
- Student → 403 trên mọi admin draft routes
- Publish draft → `GET /v1/public/exams` có đề mới
- Publish lặp idempotent → cùng kết quả, không duplicate published
- PATCH với stale `expected_updated_at` → 409
- PATCH published version → 409
- Archive → public list không còn; attempt cũ vẫn đọc được
- Publish failure giữa transaction → version cũ vẫn published
- Audit log có `exam.publish`, `exam.archive`

**Manual UAT:**

1. Upload + import `ĐỀ SỐ 1.docx`
2. Mở editor → bổ sung topic, summary, year
3. Validate → sửa warnings còn lại hoặc acknowledge
4. Publish → học sinh thấy đề, làm bài được
5. Archive → đề biến mất khỏi kho; lịch sử attempt vẫn xem được

## Risks And Recovery

- **Editor UI lớn**: chia deliverable — backend + validation trước, frontend metadata + read-only
  questions trước, rồi edit/publish. Có thể publish qua API test trước khi UI hoàn chỉnh.
- **Full-replace questions payload lớn**: 28 câu ~ vài chục KB JSON — chấp nhận được; nếu chậm
  thì tách PATCH từng câu ở follow-up.
- **Conflict product doc vs story (explanation)**: follow story packet; cập nhật
  `content-administration.md` khi US-12 done nếu cần đồng bộ.
- **Soft delete + unique position**: khi xóa mềm, giữ `position` cũ; reorder chỉ trên câu active;
  publish validation đếm active rows.
- **Rollback publish**: toàn bộ publish trong một transaction; lỗi → rollback, audit
  `exam.publish.failed`.

## Progress

- [x] Migration soft delete questions/options/statements
- [x] `PublishValidationService` + unit tests
- [x] `DraftRepository`, `DraftService`, admin draft schemas
- [x] API draft CRUD + import-context + topics
- [x] `PublishService` publish/archive + integration tests
- [x] Question image upload + link API
- [x] Frontend draft list + editor + review panel
- [x] Link import → editor; cập nhật `/admin` navigation
- [x] Validation end-to-end; cập nhật `initial-delivery.md`

## Result

US-12 đã triển khai end-to-end:

- Admin mở draft (từ import), sửa metadata + 28 câu, xem import context/findings
- `POST validate` + `POST publish` với optimistic lock và `acknowledge_warnings`
- Publish làm đề xuất hiện trên `GET /v1/public/exams`; audit `exam.publish`
- Archive qua `POST /v1/admin/exams/{exam_id}/archive`
- UI: `/admin/drafts`, `/admin/drafts/[versionId]`, nút **Mở bản nháp** sau import

Validation: 40 pytest API pass, ruff clean, `pnpm lint`, `pnpm build`.

## Decisions

- 2026-08-10: **Lời giải không bắt buộc khi publish** — theo story packet US-12 ngoại lệ; import
  warnings explanation không chặn publish sau acknowledge.
- 2026-08-10: **Optimistic lock dùng `exam_versions.updated_at`** — không thêm cột `lock_version`.
- 2026-08-10: **v1 lưu câu hỏi bằng PUT full snapshot** — đơn giản hóa reorder và tránh orphan;
  granular PATCH từng câu là follow-up nếu autosave quá nặng.
- 2026-08-10: **US-12 không implement tạo draft thủ công** — entry point để US-13; US-12 chỉ
  editor + publish cho draft đã có (import hoặc seed).
- 2026-08-10: **Cache invalidation** — v1 không có cache layer; đảm bảo DB commit trước response;
  document hook `revalidateTag('public-exams')` cho Next nếu bật ISR sau.

## Validation

- Focused: `pytest tests/test_publish_validation.py`
- Integration: `pytest tests/test_admin_draft_publish.py` + regression 30+ test API hiện có
- Frontend: `pnpm lint`, `pnpm build`
- Backend: `ruff check .`
- Manual UAT: import → edit → publish → student attempt

## Result

_(Chưa triển khai — cập nhật khi hoàn thành.)_

Moved to completed section above.
