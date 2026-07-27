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
  cố định.
- Server tính hạn, chống thay đổi đồng hồ client.
- Mở lại đề chưa hết hạn tiếp tục lượt làm có sẵn.
- Xác nhận bắt đầu hiển thị số câu và thời lượng.

Luồng thuận:

1. Học sinh mở đề đã xuất bản và xem xác nhận số câu/thời lượng.
2. Bấm bắt đầu; backend tạo attempt kèm snapshot phiên bản, `started_at` và
   `expires_at`.
3. Frontend mở câu đầu, hiển thị đồng hồ dựa trên `expires_at`.
4. Học sinh quay lại trước hạn được tiếp tục đúng attempt đó.

Ngoại lệ:

- Request bắt đầu được gửi lặp do mạng: backend trả attempt đang mở, không tạo
  hai attempt.
- Đề bị archive hoặc không còn published trước khi bắt đầu: từ chối tạo attempt.
- Session hết hạn khi bắt đầu: chuyển login; chỉ tạo attempt sau khi xác thực lại.

## US-06 — Trả lời không mất tiến độ

Là học sinh, tôi muốn đáp án được lưu khi điều hướng đề.

Tiêu chí chấp nhận:

- Một câu chọn tối đa một lựa chọn và có thể hiển thị ảnh liên kết.
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
- UI và backend đều chặn thay đổi đáp án sau khi hết hạn.
- Server đóng và chấm bằng đáp án lưu gần nhất.
- Hết giờ được hiển thị như trạng thái hoàn thành, không phải lỗi hệ thống.

Luồng thuận:

1. UI cập nhật đếm ngược từ `expires_at`.
2. Khi đồng hồ về 0, UI dừng chỉnh sửa và yêu cầu tải kết quả.
3. Backend đóng attempt, chấm bằng đáp án đã lưu gần nhất và trả kết quả.

Ngoại lệ:

- Tab bị ngủ hoặc đồng hồ client chậm: request tiếp theo vẫn bị backend kiểm tra
  `expires_at` và từ chối sửa đáp án.
- Học sinh offline khi hết giờ: lần kết nối lại đầu tiên nhận trạng thái đã hết
  giờ và kết quả đã chấm.
- Tác vụ đóng bị gửi lặp: chấm điểm idempotent, không thay đổi kết quả.

## US-08 — Nộp và xem kết quả

Là học sinh, tôi muốn điểm và lời giải từng câu sau khi nộp.

Tiêu chí chấp nhận:

- Nộp bài yêu cầu xác nhận và chỉ ra câu chưa trả lời.
- Nộp lặp trả cùng kết quả, không tạo lượt làm mới hoặc thay đổi điểm.
- Kết quả hiển thị tổng, điểm thang 10 và thời gian dùng.
- Mỗi câu có đáp án đã chọn, đáp án đúng, trạng thái và lời giải.

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

- Lịch sử chỉ có lượt hoàn thành của học sinh hiện tại, mới nhất trước.
- Chi tiết lượt làm không đổi sau khi đề được sửa.
- Làm lại tạo lượt mới theo phiên bản đã xuất bản hiện hành.

Luồng thuận:

1. Học sinh mở lịch sử; hệ thống trả các attempt hoàn thành mới nhất trước.
2. Học sinh chọn một attempt để xem kết quả snapshot và lời giải.
3. Học sinh bấm làm lại, xác nhận và bắt đầu attempt mới theo phiên bản hiện
   hành.

Ngoại lệ:

- Không có lịch sử: hiển thị trạng thái trống kèm CTA tìm đề.
- Attempt cũ tham chiếu đề đã archive: vẫn mở được kết quả snapshot, nhưng làm
  lại bị từ chối nếu không còn phiên bản published.
- URL attempt của người khác: trả `404` hoặc `403` mà không tiết lộ sự tồn tại
  hay nội dung.

## US-10 — Soạn đề thủ công

Là admin, tôi muốn tạo bản nháp đề tin cậy mà không cần nhập tệp.

Tiêu chí chấp nhận:

- Bản nháp hỗ trợ metadata bắt buộc, câu hỏi, lựa chọn, đáp án đúng và lời giải.
- Validation xuất bản yêu cầu mỗi câu có ít nhất hai lựa chọn và đúng một đáp án
  đúng.
- Admin có thể thêm, sửa, xóa mềm và sắp xếp câu hỏi/lựa chọn nháp.
- Sửa nội dung đã xuất bản tạo phiên bản nháp mới.

Luồng thuận:

1. Admin tạo đề nháp, nhập metadata và thời lượng.
2. Admin thêm câu, lựa chọn, đáp án đúng, lời giải và ảnh nếu cần.
3. Admin lưu nháp, xem validation theo từng câu, chỉnh sửa đến khi hợp lệ.
4. Với đề published, admin tạo phiên bản nháp mới rồi sửa trên phiên bản này.

Ngoại lệ:

- Lưu khi thiếu trường bắt buộc: trả validation theo trường, vẫn giữ dữ liệu đã
  nhập trong form.
- Một câu có không/multiple đáp án đúng: chặn publish và chỉ rõ câu lỗi.
- Hai admin sửa cùng nháp: phát hiện version conflict và yêu cầu tải lại/giải
  quyết thay đổi, không ghi đè im lặng.
- Admin cố sửa trực tiếp phiên bản đã dùng cho attempt: backend từ chối và yêu
  cầu tạo phiên bản nháp.

## US-11 — Quản lý tài sản đề

Là admin, tôi muốn đính kèm tệp nguồn và ảnh vào nội dung đề.

Tiêu chí chấp nhận:

- Tải tệp nguồn nhận DOCX/PDF có lớp chữ; ảnh nhận JPEG, PNG và WebP.
- Upload xác thực MIME type, phần mở rộng, kích thước và checksum.
- Tệp nằm trong storage tương thích S3, chỉ metadata nằm trong PostgreSQL.
- Tài liệu nguồn chỉ dành cho admin.

Luồng thuận:

1. Admin chọn tệp và yêu cầu upload.
2. Backend kiểm tra quyền/metadata, cấp presigned URL ngắn hạn.
3. Client tải tệp lên object storage, xác nhận hoàn tất với backend.
4. Backend lưu metadata/checksum và liên kết asset với bản nháp.

Ngoại lệ:

- MIME type, phần mở rộng hoặc checksum không hợp lệ: từ chối liên kết asset.
- Tệp vượt giới hạn: chặn trước upload nếu biết kích thước; nếu storage từ chối,
  hiển thị lỗi và không tạo asset hoàn chỉnh.
- Presigned URL hết hạn: yêu cầu URL mới; không retry bằng URL cũ.
- Học sinh yêu cầu source document: backend trả `403` và không phát presigned
  URL.

## US-12 — Nhập bản nháp đồng bộ

Là admin, tôi muốn parse tài liệu được hỗ trợ thành bản nháp có thể rà soát.

Tiêu chí chấp nhận:

- Chỉ admin gọi được import.
- DOCX và PDF có lớp chữ hoạt động; PDF scan báo OCR chưa được hỗ trợ.
- Đầu ra parser đánh dấu trường trích xuất mơ hồ là cảnh báo.
- Tệp trên 20 MB hoặc xử lý quá 120 giây thất bại an toàn.
- Import không bao giờ xuất bản đề.

Luồng thuận:

1. Admin tải DOCX/PDF có lớp chữ lên và chọn “Nhập đề”.
2. Backend kiểm tra quyền, loại tệp và kích thước, sau đó parser chạy trong
   request với timeout.
3. Hệ thống tạo/cập nhật draft, lưu findings và trả màn hình rà soát.
4. Admin chỉnh sửa mọi trường bị thiếu/cảnh báo trước khi yêu cầu xuất bản.

Ngoại lệ:

- PDF scan hoặc chỉ có ảnh: trả lỗi OCR chưa hỗ trợ; không tạo draft rỗng.
- Parser không nhận diện được cấu trúc: tạo draft chỉ khi có dữ liệu an toàn,
  kèm cảnh báo; nếu không có dữ liệu thì báo thất bại và giữ tệp nguồn.
- Timeout/lỗi parser: hủy an toàn transaction dữ liệu trích xuất, lưu trạng
  thái lỗi/audit và cho phép chạy lại.
- Request bị retry: dùng import idempotency key hoặc nhận diện checksum để không
  tạo các draft trùng.

## US-13 — Rà soát và xuất bản nội dung

Là admin, tôi muốn sửa đầu ra parser trước khi học sinh nhìn thấy.

Tiêu chí chấp nhận:

- Rà soát hiển thị nguồn, dữ liệu trích xuất và mọi cảnh báo parser.
- Admin sửa được mọi trường có thể xuất bản.
- Lỗi xuất bản nêu rõ trường hoặc câu không hợp lệ.
- Phiên bản xuất bản có sẵn cho học sinh, lượt cũ giữ phiên bản gốc.
- Import, publish, đổi đáp án đúng và archive được audit log.

Luồng thuận:

1. Admin mở bản nháp, so sánh tệp nguồn với dữ liệu parser và warnings.
2. Admin sửa metadata/câu hỏi/đáp án/lời giải, rồi yêu cầu validation.
3. Khi validation đạt, admin bấm xuất bản.
4. Backend tạo/đánh dấu phiên bản published, ghi audit log và công khai phiên bản
   mới cho lượt làm mới.

Ngoại lệ:

- Còn warning hoặc lỗi validation bắt buộc: chặn publish, điều hướng đến trường
  hoặc câu lỗi; warning không bắt buộc cần được admin xác nhận rõ.
- Hai admin publish đồng thời: chỉ một phiên bản thắng theo optimistic lock;
  yêu cầu còn lại nhận conflict và tải lại.
- Publish thành công nhưng cache danh sách chưa cập nhật: cache phải được
  invalidate trước khi phản hồi thành công.
- Lỗi giữa publish: transaction rollback, phiên bản cũ vẫn published và audit
  log ghi sự cố.

## Kỳ vọng bằng chứng

- Unit test chứng minh chấm điểm, chuyển trạng thái, kiểm tra phân quyền, phiên
  bản hóa và validation parser.
- Integration test chứng minh persistence API, vòng đời session, truy cập storage
  và giới hạn import đồng bộ.
- End-to-end test chứng minh luồng Google login, làm bài có thời gian,
  refresh/tiếp tục, nộp/kết quả/lịch sử và admin import/rà soát/publish.
