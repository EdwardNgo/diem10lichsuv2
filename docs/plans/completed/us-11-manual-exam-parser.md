# Execution Plan: US-11 — Parser đề thủ công (manual-exams)

Date: 2026-08-10

## Status

Completed

## Outcome

Admin chọn source asset DOCX đã upload (định dạng như `parser-source/manual-exams/ĐỀ SỐ 1.docx`),
bấm **Nhập đề**, backend parse đồng bộ thành `exam_versions` draft kèm 24 câu Phần I + 4 câu
Phần II, lưu `import_jobs`/`import_findings`, liên kết source asset — **không** tự xuất bản.

## Context

- Story: `docs/story-packet.md` — US-11 (import), US-12 (rà soát sau import)
- Product: `docs/product/content-administration.md`
- Schema: `docs/database-schema.md` — `import_jobs`, `import_findings`, `asset_links`
- Mẫu chuẩn admin upload: `parser-source/manual-exams/ĐỀ SỐ 1.docx`
- US-10 đã xong: upload source document → `assets` (chưa có draft)
- `parser-source/raw/` chứa đề nguồn bên thứ ba (Thuvienhoclieu…) — **ngoài phạm vi v1**;
  format khác, có lời giải dài, cấu trúc không đồng nhất

## Phân tích định dạng manual-exams

Mẫu `ĐỀ SỐ 1.docx` (~202 đoạn văn bản) có cấu trúc cố định:

```
ĐỀ SỐ 1
PHẦN I: Thí sinh trả lời từ câu 1 đến câu 24...
Câu 1. <stem>
A. <option>
B. <option>
C. <option>
D. <option>
...
Câu 24. <stem>
A. ...
PHẦN II: Thí sinh trả lời từ câu 1 đến câu 4...
Câu 1. Cho đoạn tư liệu sau đây:
“<đoạn trích>”
(Nguồn trích, NXB..., tr. XX)
a) <phát biểu>
b) <phát biểu>
c) <phát biểu>
d) <phát biểu>
...
Câu 4. ...
Đáp án
Phần I
1.A
2.D
...
24.B
Phần II
a / b / c / d          ← header cột (tuỳ chọn)
Câu 1
Đúng / Sai / Sai / Đúng   ← 4 dòng theo thứ tự a→d
Câu 2
...
```

Quy ước map sang DB:

| Trường DOCX | Model DB | Ghi chú |
|-------------|----------|---------|
| Dòng tiêu đề đầu | `exam_versions.title` | Fallback tên file nếu thiếu |
| Stem `Câu N.` Phần I | `questions.body` | `part_number=1`, `question_type=multiple_choice` |
| `A.`–`D.` | `question_options` ×4 | `is_correct` từ đáp án |
| Intro + trích dẫn Phần II | `questions.source_text` | Gộp đoạn `"..."` + dòng nguồn |
| `a)`–`d)` | `question_statements` ×4 | `is_correct` từ Đúng/Sai |
| — | `questions.explanation` | Luôn rỗng → **warning** bắt buộc sửa ở US-12 |
| — | metadata `year`, `difficulty`, topic | Không có trong file → default + **warning** |

Không có trong file manual: thời lượng, chủ đề, mô tả, lời giải. Parser đặt default an toàn
(`duration_minutes=50`, `summary=""`, topic chưa gán) và gắn finding để admin bổ sung trước
publish.

## Scope

In scope:

- Migration + model: `import_jobs`, `import_findings`, `asset_links`
- Module parser độc lập request (`diem10_api/parsers/`) cho **manual DOCX**
- PDF có lớp chữ: cùng pipeline sau bước extract text (pypdf/pdfplumber)
- `ImportService`: timeout 120s, giới hạn 20 MB, transaction an toàn
- API admin `POST /v1/admin/assets/{asset_id}/import`
- Unit test parser với fixture `ĐỀ SỐ 1.docx`
- Integration test import end-to-end (mock storage download)
- Nút **Nhập đề** tối thiểu trên UI admin (gọi API, hiển thị findings)

Out of scope (v1):

- Parser cho `parser-source/raw/` (Thuvienhoclieu, lời giải chi tiết, đề thi thử nhiều header)
- OCR / PDF scan
- Worker bất đồng bộ
- Editor rà soát đầy đủ (US-12) — chỉ trả draft id + findings để bước sau mở editor
- Ảnh trong câu hỏi (manual format hiện không có ảnh)

## Approach

### 1. Persistence (migration)

Thêm bảng theo `docs/database-schema.md`:

- `import_jobs`: `source_asset_id`, `exam_version_id` nullable, `status`, `error_code`,
  `idempotency_key` (nullable, unique per asset+key), timestamps
- `import_findings`: `severity` (`warning`|`error`), `field_path`, `message`, `raw_value`
- `asset_links`: liên kết `source_document` → `exam_versions` sau import thành công

Ràng buộc application: mỗi `asset_links` row chỉ có `exam_version_id` **hoặc** `question_id`.

### 2. Parser architecture

```
services/api/src/diem10_api/parsers/
  types.py           # ParsedExamDraft, ParsedMcQuestion, ParsedTfQuestion, ParserFinding
  text_lines.py      # normalize whitespace, unicode NFC, strip soft hyphen
  docx_reader.py     # đọc paragraph list từ DOCX (stdlib zip+xml)
  pdf_reader.py      # extract text layer; detect scan → raise OcrNotSupported
  manual_exam.py     # state machine parse manual-exams format
  __init__.py        # parse_source(bytes, mime_type) → ParsedExamDraft
```

**State machine** (`manual_exam.py`):

1. `METADATA` — dòng đầu không khớp `PHẦN`/`Câu` → title
2. `PART1` — sau `PHẦN I`; đọc `Câu N.` + 4 option `^[A-D]\.`
3. `PART2` — sau `PHẦN II`; đọc `Câu N.` + block tư liệu + `a)`–`d)`
4. `ANSWERS` — sau `Đáp án`; parse Phần I (`N.L`) và Phần II (4× Đúng/Sai/câu)

Regex cốt lõi (case-insensitive cho `PHẦN`, `Câu`, `Đáp án`):

- Question start: `^Câu\s+(\d+)\.\s*(.*)$`
- MC option: `^([A-D])\.\s*(.+)$`
- TF statement: `^([a-d])\)\s*(.+)$`
- MC answer: `^(\d+)\.\s*([A-D])\s*$`
- TF answer: `^(Đúng|Sai)\s*$` (sau header `Câu N` trong khối Phần II)

**Findings** (không suy diễn im lặng):

| Điều kiện | Severity | field_path ví dụ |
|-----------|----------|------------------|
| ≠ 24 câu Phần I | warning | `questions.part1.count` |
| ≠ 4 câu Phần II | warning | `questions.part2.count` |
| Thiếu/không khớp đáp án | warning | `questions.part1[3].correct_option` |
| Nhiều hơn 4 phát biểu | error | `questions.part2[1].statements` |
| Không trích được title | warning | `metadata.title` |
| Không có explanation | warning | `questions.part1[0].explanation` (lặp 28 câu) |
| Không extract được topic/year | warning | `metadata.topic`, `metadata.year` |
| Cấu trúc hoàn toàn không nhận diện | error | `_document` → fail job, không tạo draft |

Ngưỡng **dữ liệu an toàn** (US-11): ≥1 câu hỏi hợp lệ **và** không có finding `error` cấp
document → mới persist draft; ngược lại rollback + job `failed`.

### 3. Import service & API

Luồng `ImportService.import_source_document(asset_id, actor, idempotency_key?)`:

1. Kiểm tra admin, asset tồn tại, `asset_kind=source_document`, chưa xóa
2. Idempotency: nếu job `succeeded` cùng `source_asset_id` + key → trả draft hiện có
3. Tải object từ R2 (hoặc local fixture trong test)
4. `asyncio.wait_for` / `signal.alarm` — timeout 120s
5. Gọi `parse_source()`
6. Trong transaction:
   - Tạo `import_jobs` status `running`
   - Nếu pass safe threshold: upsert `Exam` + `ExamVersion` draft, questions/options/statements
   - Ghi `import_findings`, `asset_links`, cập nhật job `succeeded`
   - Audit log `admin.import.succeeded`
7. Lỗi: job `failed`/`timed_out`, **không** draft rỗng, giữ source asset

API:

```
POST /v1/admin/assets/{asset_id}/import
Body: { "idempotency_key"?: string }
Response: {
  "import_job_id", "exam_version_id", "status",
  "findings": [{ "severity", "field_path", "message" }],
  "summary": { "part1_count", "part2_count", "warnings", "errors" }
}
```

Schemas bổ sung trong `schemas/admin.py`.

### 4. Dependencies

Thêm vào `pyproject.toml`:

- `pypdf` hoặc `pdfplumber` — PDF text layer (ưu tiên nhẹ: `pypdf` nếu đủ)
- DOCX: **không** cần `python-docx` v1 — stdlib đủ cho paragraph text

### 5. Frontend (tối thiểu US-11)

Mở rộng `admin-source-documents.tsx` hoặc component mới:

- Liệt kê source assets đã confirm (GET list endpoint nếu chưa có)
- Nút **Nhập đề** → POST import → hiển thị findings + link draft id
- Trạng thái loading/error/timeout rõ ràng

GET list assets có thể là follow-up nhỏ trong cùng PR nếu UI cần chọn asset.

### 6. Test plan

**Unit** (`tests/parsers/test_manual_exam.py`):

- Parse `parser-source/manual-exams/ĐỀ SỐ 1.docx` → đúng 24+4 câu
- Đáp án câu 1 Phần I = A, câu 24 = B, câu 1 Phần II = `[True,False,False,True]`
- Title = `ĐỀ SỐ 1`
- Có warnings explanation/metadata, không có errors

**Unit edge cases**:

- Thiếu Phần II → fail safe / không draft
- Đáp án thiếu câu 15 → warning, vẫn draft nếu còn safe
- File rỗng → failed

**Integration** (`tests/test_admin_import.py`):

- Admin import asset DOCX → draft + job succeeded + asset_link
- Student → 403
- Retry idempotency → cùng draft
- PDF scan mock → 422 OCR unsupported
- Timeout mock → job timed_out, không draft

## Risks And Recovery

- **Biến thể format admin**: admin soạn Word khác spacing (option cùng dòng, `Câu 1:` thay
  `Câu 1.`). Mitigation: fixture thêm + regex tolerant; finding thay vì crash.
- **PDF layout phức tạp**: text layer có thể mất thứ tự cột. v1: chỉ hỗ trợ PDF đơn cột giống
  DOCX; layout lỗi → warning/fail.
- **Parser >120s trên VPS 2GB**: giữ sync; log duration; nếu vượt ngưỡng thực tế thì tách
  worker sau (decision 0001).
- **Rollback**: import transaction bọc toàn bộ draft; failed job không để orphan questions.

## Progress

- [x] Migration `import_jobs`, `import_findings`, `asset_links` + SQLAlchemy models
- [x] `parsers/types.py`, `docx_reader.py`, `manual_exam.py`
- [x] Unit tests parser với `ĐỀ SỐ 1.docx`
- [x] `pdf_reader.py` + detect scan/OCR unsupported
- [x] `ImportService` + repository methods
- [x] API `POST .../import` + admin schemas
- [x] Integration tests (mock R2 download)
- [x] UI admin: nút Nhập đề + hiển thị findings
- [x] Cập nhật `initial-delivery.md` khi validation xong

## Decisions

- 2026-08-10: **v1 parser chỉ nhắm `manual-exams` format** do admin kiểm soát nội dung upload;
  không parse `parser-source/raw/` ở bản đầu.
- 2026-08-10: DOCX đọc bằng stdlib (zip + XML) thay vì thêm `python-docx` — đủ cho text-only.
- 2026-08-10: Explanation luôn rỗng với manual format; mọi câu sinh finding warning — admin
  bắt buộc bổ sung trước publish (US-12).
- 2026-08-10: Idempotency theo `(source_asset_id, idempotency_key)`; mặc định key = checksum
  nếu client không gửi.

## Validation

- Focused: `pytest tests/parsers/` — parse fixture, counts, answers, findings
- Integration: `pytest tests/test_admin_import.py` — full import lifecycle
- Regression: toàn bộ test API hiện có + `ruff check .`
- Manual UAT: upload `ĐỀ SỐ 1.docx` → import → kiểm tra draft 28 câu trong DB/admin UI

## Result

US-11 đã triển khai end-to-end:

- Parser manual-exams (`ĐỀ SỐ 1.docx`) → 24 câu Phần I + 4 câu Phần II + đáp án
- API `GET /v1/admin/assets/source-documents`, `POST /v1/admin/assets/{id}/import`
- Draft `exam_versions` + `import_jobs`/`import_findings`/`asset_links`
- Idempotent retry theo checksum; không auto-publish

Validation: 30 pytest API pass, ruff clean, pnpm lint pass.
