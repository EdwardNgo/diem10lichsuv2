# Gói user story cho bản phát hành đầu

## Mục đích

Gói này chuyển product contract đã chấp nhận thành các user story có thể xác
minh độc lập. Đây là tài liệu thực thi bổ trợ cho `docs/product/`, không thay
thế các product docs đó.

## Thứ tự thực hiện

1. US-01 đến US-03: điểm vào công khai, xác thực và phân quyền.
2. US-04 đến US-09: khám phá đề, làm bài, chấm điểm và lịch sử của học sinh.
3. US-10 đến US-13: quản trị, tài sản, nhập, rà soát và xuất bản.

## US-01 — Khám phá sản phẩm

Là khách, tôi muốn xem sản phẩm và đề nổi bật trước khi xác thực.

Tiêu chí chấp nhận:

- Landing page có mục đích sản phẩm, CTA “Làm đề ngay”, khám phá đề và điều
  hướng đăng nhập Google.
- Chỉ metadata của đề đã xuất bản được công khai.
- Khách chọn đề sẽ xác thực rồi quay lại đúng đích đó.
- Trang hoạt động trên mobile và desktop.

Luồng thuận:

1. Khách mở trang chủ, đọc giới thiệu và xem danh sách đề nổi bật.
2. Khách bấm “Làm đề ngay” hoặc chọn một đề.
3. Nếu chưa đăng nhập, hệ thống lưu đường dẫn đích và chuyển tới đăng nhập Google.
4. Đăng nhập thành công đưa người dùng tới trang chi tiết đề hoặc dashboard.

Ngoại lệ:

- Danh sách đề trống: hiển thị trạng thái “Chưa có đề để làm”, không hiển thị
  placeholder đề.
- Tải danh sách lỗi: hiển thị lỗi có nút thử lại; CTA đăng nhập vẫn hoạt động.
- `return_to` không hợp lệ hoặc trỏ domain ngoài: bỏ qua và đưa người dùng về
  dashboard để tránh open redirect.

## US-02 — Đăng nhập bằng Google

Là học sinh, tôi muốn đăng nhập Google để bài làm được lưu.

Tiêu chí chấp nhận:

- Google OAuth/OIDC hỗ trợ đăng nhập và đăng xuất.
- Lần đăng nhập đầu tạo đúng một hồ sơ nội bộ theo Google `sub`.
- Lỗi xác thực không tạo session và không lộ secret kỹ thuật.
- Session hết hạn không gọi được API được bảo vệ.

Luồng thuận:

1. Người dùng bấm “Đăng nhập Google”.
2. Hệ thống chuyển tới Google với `state` và PKCE phù hợp.
3. Google trả callback hợp lệ; FastAPI xác minh token, tìm/tạo hồ sơ theo `sub`
   và xác định role.
4. FastAPI đặt session cookie rồi chuyển về đích đã lưu.

Ngoại lệ:

- Người dùng hủy ở Google: quay lại trang trước đó với thông báo hủy đăng nhập.
- Callback thiếu/sai `state`, token không hợp lệ hoặc hết hạn: từ chối callback,
  không tạo session và ghi log bảo mật.
- Google hoặc mạng không phản hồi: thông báo có thể thử lại; không tạo hồ sơ
  nửa chừng.

## US-03 — Thực thi quyền admin

Là chủ hệ thống, tôi muốn chỉ tài khoản Google trong allowlist là admin.

Tiêu chí chấp nhận:

- Email trong allowlist nhận `admin`; tài khoản xác thực khác nhận `student`.
- Backend chặn non-admin truy cập admin endpoint.
- Thay đổi allowlist được audit log với actor, đối tượng, thời gian và hành động.

Luồng thuận:

1. Chủ hệ thống thêm email vào allowlist qua cơ chế quản trị được bảo vệ.
2. Người dùng đăng nhập Google; backend đối chiếu email với allowlist.
3. Backend gán `admin`, hiển thị điều hướng quản trị và kiểm tra role ở mọi API.

Ngoại lệ:

- Học sinh gọi trực tiếp API admin: trả `403`, không tiết lộ dữ liệu nháp.
- Email bị xóa khỏi allowlist: lần session tiếp theo hoặc lần kiểm tra role tiếp
  theo mất quyền admin; thao tác đang thực hiện bị từ chối an toàn.
- Admin cố xóa quyền admin cuối cùng: hệ thống chặn để tránh mất quyền quản trị.

## US-04 — Tìm đề đã xuất bản

Là học sinh, tôi muốn tìm và lọc đề phù hợp với việc ôn tập.

Tiêu chí chấp nhận:

- Kết quả chỉ có đề đã xuất bản hiện hành.
- Tìm theo tiêu đề; lọc theo chủ đề/giai đoạn, năm và mức độ.
- Thẻ hiển thị tiêu đề, mô tả, số câu, thời lượng, chủ đề và trạng thái hoàn
  thành.
- Phản hồi chi tiết không có đáp án đúng hoặc lời giải trước khi hoàn thành.

Luồng thuận:

1. Học sinh mở danh sách đề.
2. Nhập từ khóa hoặc chọn bộ lọc; hệ thống tải trang kết quả tương ứng.
3. Học sinh mở thẻ đề để xem metadata và bấm bắt đầu.

Ngoại lệ:

- Bộ lọc không có kết quả: hiển thị trạng thái trống và nút xóa bộ lọc.
- Tham số lọc/phân trang không hợp lệ: dùng giá trị mặc định an toàn hoặc trả
  lỗi validation, không lỗi máy chủ.
- Đề vừa bị archive giữa lúc xem: trang chi tiết báo đề không còn khả dụng và
  quay về danh sách.

## US-05 — Bắt đầu và tiếp tục lượt làm

Là học sinh, tôi muốn lượt làm có thời gian và nhất quán trong khi làm.

Tiêu chí chấp nhận:

- Bắt đầu tạo lượt làm với phiên bản đề, thời gian bắt đầu và thời điểm hết hạn
  do server quản lý.
- Server tính hạn, chống thay đổi đồng hồ client.
- Rời màn hình làm bài tạm dừng đồng hồ trên server; mở lại tiếp tục lượt làm có
  sẵn với đúng thời gian còn lại.
- Xác nhận bắt đầu hiển thị cấu trúc 24 câu Phần I, 4 câu Phần II và thời lượng.

Luồng thuận:

1. Học sinh mở đề đã xuất bản và xem xác nhận số câu/thời lượng.
2. Bấm bắt đầu; backend tạo attempt kèm snapshot phiên bản, `started_at` và
   `expires_at`.
3. Frontend mở câu đầu, hiển thị đồng hồ dựa trên `expires_at`.
4. Khi học sinh rời bài, backend ghi `paused_at`.
5. Học sinh quay lại được tiếp tục đúng attempt đó; backend dời `expires_at`
   theo thời gian tạm dừng và xóa `paused_at`.

Ngoại lệ:

- Request bắt đầu được gửi lặp do mạng: backend trả attempt đang mở, không tạo
  hai attempt.
- Đề bị archive hoặc không còn published trước khi bắt đầu: từ chối tạo attempt.
- Session hết hạn khi bắt đầu: chuyển login; chỉ tạo attempt sau khi xác thực lại.

## US-06 — Trả lời không mất tiến độ

Là học sinh, tôi muốn đáp án được lưu khi điều hướng đề.

Tiêu chí chấp nhận:

- Câu Phần I chọn tối đa một lựa chọn ABCD; câu Phần II chọn Đúng/Sai cho từng
  phát biểu và có thể hiển thị ảnh liên kết.
- UI hiển thị tiến độ, điều hướng và dấu xem lại.
- Đáp án đã lưu được khôi phục sau refresh hoặc đổi thiết bị khi lượt làm còn
  hiệu lực.
- Tự lưu thất bại hiển thị rõ chưa lưu và có thể thử lại.
- Tài khoản không truy cập được lượt làm của học sinh khác.

Luồng thuận:

1. Học sinh chọn đáp án; UI đánh dấu câu đã trả lời.
2. Frontend tự lưu đáp án và hiển thị trạng thái đã lưu sau khi backend xác nhận.
3. Học sinh chuyển câu/đánh dấu xem lại; tiến độ cập nhật.
4. Refresh hoặc mở thiết bị khác tải lại đáp án đã lưu của attempt còn hạn.

Ngoại lệ:

- Mất mạng lúc tự lưu: giữ đáp án trong UI, hiển thị chưa lưu và retry khi người
  dùng yêu cầu/kết nối trở lại; không giả báo thành công.
- Lượt làm đã hết hạn trong lúc lưu: backend trả trạng thái hết hạn, UI khóa
  chỉnh sửa và chuyển sang nộp/kết quả.
- `question_id` không thuộc snapshot attempt: trả `400`/`404`, không tạo đáp án.

## US-07 — Hoàn thành đúng khi hết giờ

Là học sinh, tôi muốn đếm ngược chính xác và xử lý đúng khi hết giờ.

Tiêu chí chấp nhận:

- Đồng hồ hiển thị lấy từ thời điểm hết hạn do server trả về.
- Thời gian không giảm khi lượt làm đã được tạm dừng do người dùng rời bài.
- UI và backend đều chặn thay đổi đáp án sau khi hết hạn.
- Server đóng và chấm bằng đáp án lưu gần nhất.
- Hết giờ được hiển thị như trạng thái hoàn thành, không phải lỗi hệ thống.

Luồng thuận:

1. UI cập nhật đếm ngược từ `expires_at`.
2. Khi rời bài, UI yêu cầu server tạm dừng; khi mở lại, UI yêu cầu server tiếp
   tục và nhận `expires_at` mới.
3. Khi đồng hồ về 0, UI dừng chỉnh sửa và yêu cầu tải kết quả.
4. Backend đóng attempt, chấm bằng đáp án đã lưu gần nhất và trả kết quả.

Ngoại lệ:

- Tab bị ngủ hoặc đồng hồ client chậm: request tiếp theo vẫn bị backend kiểm tra
  `expires_at` và từ chối sửa đáp án.
- Mất kết nối khi yêu cầu tạm dừng: UI báo chưa tạm dừng và không tự điều hướng;
  đóng tab dùng yêu cầu `keepalive` theo khả năng của trình duyệt.
- Tác vụ đóng bị gửi lặp: chấm điểm idempotent, không thay đổi kết quả.

## US-08 — Nộp và xem kết quả

Là học sinh, tôi muốn điểm và lời giải từng câu sau khi nộp.

Tiêu chí chấp nhận:

- Nộp bài yêu cầu xác nhận và chỉ ra câu chưa trả lời.
- Nộp lặp trả cùng kết quả, không tạo lượt làm mới hoặc thay đổi điểm.
- Kết quả hiển thị tổng, điểm thang 10 và thời gian dùng.
- Mỗi câu có đáp án đã chọn, đáp án đúng, trạng thái, điểm đạt được và lời giải;
  câu Phần II hiển thị trạng thái từng phát biểu.

Luồng thuận:

1. Học sinh bấm nộp; UI hiển thị số câu bỏ trống.
2. Học sinh xác nhận; backend khóa attempt, chấm snapshot và lưu kết quả.
3. Frontend mở trang kết quả với tổng điểm và lời giải từng câu.

Ngoại lệ:

- Học sinh hủy hộp xác nhận: quay về làm bài, không thay đổi attempt.
- Nộp đúng thời điểm hết hạn: backend chấp nhận/chuyển sang hết giờ theo thời
  điểm server, không dựa vào thời gian client.
- Client retry submit sau timeout: backend trả lại kết quả đã có, không chấm lại.

## US-09 — Xem lịch sử và làm lại

Là học sinh, tôi muốn theo dõi bài đã hoàn thành và làm lại đề.

Tiêu chí chấp nhận:

- Lịch sử chỉ có lượt hoàn thành của học sinh hiện tại, gom theo đề thi và sắp
  xếp theo đề có lần làm mới nhất trước.
- Khi chọn một đề trong lịch sử, hệ thống hiển thị các lượt làm hoàn thành của
  đề đó, mới nhất trước.
- Chi tiết lượt làm không đổi sau khi đề được sửa.
- Làm lại tạo lượt mới theo phiên bản đã xuất bản hiện hành.

Luồng thuận:

1. Học sinh mở lịch sử; hệ thống trả các đề đã có lượt làm hoàn thành, mới nhất
   trước.
2. Học sinh chọn một đề; UI mở danh sách các lượt làm hoàn thành của đề đó.
3. Học sinh chọn một lượt làm để xem kết quả snapshot và lời giải.
4. Học sinh bấm làm lại, xác nhận và bắt đầu attempt mới theo phiên bản hiện
   hành.

Ngoại lệ:

- Không có lịch sử: hiển thị trạng thái trống kèm CTA tìm đề.
- Attempt cũ tham chiếu đề đã archive: vẫn mở được kết quả snapshot, nhưng làm
  lại bị từ chối nếu không còn phiên bản published.
- URL attempt của người khác: trả `404` hoặc `403` mà không tiết lộ sự tồn tại
  hay nội dung.

## US-10 — Tải tài liệu nguồn

Là admin, tôi muốn tải tài liệu đề gốc để hệ thống có thể nhập thành bản nháp.

Tiêu chí chấp nhận:

- Tải tài liệu nguồn nhận DOCX và PDF có lớp chữ.
- Upload xác thực MIME type, phần mở rộng, kích thước và checksum.
- Tệp nằm trong storage tương thích R2, chỉ metadata nằm trong PostgreSQL.
- Tài liệu nguồn chỉ dành cho admin.
- Upload tài liệu nguồn không tạo bản nháp và không yêu cầu bản nháp có sẵn.

Luồng thuận:

1. Admin chọn tài liệu nguồn và yêu cầu upload.
2. Backend kiểm tra quyền/metadata, cấp presigned URL ngắn hạn.
3. Client tải tệp lên object storage, xác nhận hoàn tất với backend.
4. Backend lưu metadata/checksum của source asset để admin có thể nhập hoặc
   chạy lại import sau đó.

Ngoại lệ:

- MIME type, phần mở rộng hoặc checksum không hợp lệ: từ chối hoàn tất asset.
- Tệp vượt giới hạn: chặn trước upload nếu biết kích thước; nếu storage từ chối,
  hiển thị lỗi và không tạo asset hoàn chỉnh.
- Presigned URL hết hạn: yêu cầu URL mới; không retry bằng URL cũ.
- Học sinh yêu cầu source document: backend trả `403` và không phát presigned
  URL.

## US-11 — Nhập tài liệu thành bản nháp

Là admin, tôi muốn parse tài liệu được hỗ trợ thành bản nháp có thể rà soát.

Tiêu chí chấp nhận:

- Chỉ admin gọi được import.
- Import chạy từ source asset đã upload; DOCX và PDF có lớp chữ hoạt động; PDF
  scan báo OCR chưa được hỗ trợ.
- Đầu ra parser đánh dấu trường trích xuất mơ hồ là cảnh báo.
- Tệp trên 20 MB hoặc xử lý quá 120 giây thất bại an toàn.
- Import không bao giờ xuất bản đề.
- Import thành công tạo hoặc cập nhật draft và liên kết source asset với draft
  đó; import thất bại không tạo draft rỗng.

Luồng thuận:

1. Admin chọn source asset đã upload và chọn “Nhập đề”.
2. Backend kiểm tra quyền, loại tệp và kích thước, sau đó parser chạy trong
   request với timeout.
3. Hệ thống tạo/cập nhật draft, liên kết source asset, lưu findings và trả màn
   hình rà soát.
4. Admin chuyển sang editor để sửa mọi trường bị thiếu/cảnh báo trước khi yêu
   cầu xuất bản.

Ngoại lệ:

- PDF scan hoặc chỉ có ảnh: trả lỗi OCR chưa hỗ trợ; không tạo draft rỗng.
- Parser không nhận diện được cấu trúc: tạo draft chỉ khi có dữ liệu an toàn,
  kèm cảnh báo; nếu không có dữ liệu thì báo thất bại và giữ tệp nguồn.
- Timeout/lỗi parser: hủy an toàn transaction dữ liệu trích xuất, lưu trạng
  thái lỗi/audit và cho phép chạy lại.
- Request bị retry: dùng import idempotency key hoặc nhận diện checksum để không
  tạo các draft trùng.

## US-12 — Rà soát, chỉnh sửa và xuất bản

Là admin, tôi muốn rà soát và chỉnh sửa bản nháp trước khi học sinh nhìn thấy.

Tiêu chí chấp nhận:

- Draft hỗ trợ metadata bắt buộc, 24 câu ABCD Phần I, 4 câu tư liệu Phần II,
  lựa chọn, phát biểu, đáp án đúng, lời giải và ảnh.
- Rà soát draft import hiển thị nguồn, dữ liệu trích xuất và mọi cảnh báo
  parser; draft thủ công không cần nguồn parser.
- Admin có thể thêm, sửa, xóa mềm và sắp xếp câu hỏi/lựa chọn/phát biểu nháp.
- Lỗi xuất bản nêu rõ trường hoặc câu không hợp lệ.
- Validation xuất bản yêu cầu đúng 24 câu Phần I có bốn lựa chọn và đúng một đáp
  án đúng; đúng 4 câu Phần II có đoạn tư liệu và bốn phát biểu Đúng/Sai.
- Phiên bản xuất bản có sẵn cho học sinh, lượt cũ giữ phiên bản gốc.
- Publish, đổi đáp án đúng, archive và gắn ảnh câu hỏi được audit log.

Luồng thuận:

1. Admin mở bản nháp; nếu draft đến từ import, UI hiển thị tệp nguồn, dữ liệu
   parser và warnings để đối chiếu.
2. Admin sửa metadata/câu hỏi/đáp án/lời giải, sắp xếp nội dung và gắn ảnh nếu
   cần, rồi yêu cầu validation.
3. Khi validation đạt, admin bấm xuất bản.
4. Backend tạo/đánh dấu phiên bản published, ghi audit log và công khai phiên bản
   mới cho lượt làm mới.

Ngoại lệ:

- Lưu khi thiếu trường bắt buộc: trả validation theo trường, vẫn giữ dữ liệu đã
  nhập trong form.
- Một câu ABCD có không/multiple đáp án đúng hoặc câu tư liệu thiếu bốn phát
  biểu Đúng/Sai: chặn publish và chỉ rõ câu lỗi.
- Còn warning hoặc lỗi validation bắt buộc: chặn publish, điều hướng đến trường
  hoặc câu lỗi; warning không bắt buộc cần được admin xác nhận rõ.
  Chỉ cần có đáp án là được, lời giải là tuỳ chọn
- Hai admin sửa cùng nháp: phát hiện version conflict và yêu cầu tải lại/giải
  quyết thay đổi, không ghi đè im lặng.
- Hai admin publish đồng thời: chỉ một phiên bản thắng theo optimistic lock;
  yêu cầu còn lại nhận conflict và tải lại.
- Admin cố sửa trực tiếp phiên bản đã dùng cho attempt: backend từ chối và yêu
  cầu tạo phiên bản nháp.
- Publish thành công nhưng cache danh sách chưa cập nhật: cache phải được
  invalidate trước khi phản hồi thành công.
- Lỗi giữa publish: transaction rollback, phiên bản cũ vẫn published và audit
  log ghi sự cố.

## US-13 — Soạn đề thủ công

Là admin, tôi muốn tạo bản nháp đề tin cậy khi không có tài liệu nguồn.

Tiêu chí chấp nhận:

- Admin có thể tạo draft trống bằng metadata tối thiểu hoặc từ một đề published
  hiện có.
- Draft thủ công dùng cùng editor, validation, optimistic lock, versioning,
  audit và publish contract với draft nhập từ parser.
- Draft thủ công không yêu cầu source asset hoặc import findings.
- Sửa nội dung đã xuất bản tạo phiên bản nháp mới, không sửa phiên bản đã có lượt
  làm.

Luồng thuận:

1. Admin chọn tạo đề thủ công hoặc tạo bản nháp mới từ đề published.
2. Hệ thống tạo draft trống hoặc sao chép nội dung hiện hành sang phiên bản nháp.
3. Admin nhập/sửa nội dung bằng editor chung của US-12.
4. Admin validation và xuất bản qua cùng luồng rà soát/xuất bản.

Ngoại lệ:

- Admin bỏ dở draft trống: draft vẫn ở trạng thái nháp và không xuất hiện cho học
  sinh.
- Tạo draft từ đề không còn quyền chỉnh sửa hoặc đã bị archive: backend từ chối
  và không tạo phiên bản mới.
- Hai admin cùng tạo draft kế tiếp từ một đề published: backend chỉ cho phép một
  draft chỉnh sửa hiện hành hoặc trả conflict để admin mở draft đang có.

## Kỳ vọng bằng chứng

- Unit test chứng minh chấm điểm, chuyển trạng thái, kiểm tra phân quyền, phiên
  bản hóa và validation parser.
- Integration test chứng minh persistence API, vòng đời session, truy cập storage
  và giới hạn import đồng bộ.
- End-to-end test chứng minh luồng Google login, làm bài có thời gian,
  refresh/tiếp tục, nộp/kết quả/lịch sử, admin upload/import/rà soát/publish và
  tạo draft thủ công bằng editor chung.
