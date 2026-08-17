import type { Metadata } from "next";
import Link from "next/link";

import { SiteHeader } from "@/components/site-header";
import { withCanonical } from "@/lib/page-metadata";
import { SITE_NAME } from "@/lib/site";

export const metadata: Metadata = withCanonical("/privacy", {
  title: `Chính sách bảo mật | ${SITE_NAME}`,
  description:
    `Chính sách bảo mật của ${SITE_NAME}: dữ liệu Google tối thiểu, lịch sử làm bài, thời hạn lưu và cách yêu cầu xóa dữ liệu.`,
});

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#f2fbff] text-[#123047]">
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8">
        <p className="text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
          CHÍNH SÁCH BẢO MẬT
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Cách chúng tôi thu thập và bảo vệ dữ liệu của bạn
        </h1>
        <p className="mt-4 text-sm text-[#45667a]">
          Cập nhật lần cuối: 16/08/2026
        </p>
        <div className="mt-8 grid gap-8 rounded-3xl border border-[#bae6fd] bg-white p-6 leading-7 text-[#45667a] sm:p-8">
          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Giới thiệu
            </h2>
            <div className="mt-3 grid gap-3">
              <p>
                Sử Văn Quán là website luyện thi tốt nghiệp THPT môn Lịch
                sử, cung cấp đề thi thử, chấm điểm và lịch sử làm bài để bạn ôn
                tập.
              </p>
              <p>
                Chính sách này giải thích chúng tôi thu thập dữ liệu nào, dùng
                dữ liệu đó để làm gì, lưu trong bao lâu và bạn có quyền gì đối
                với dữ liệu của mình.
              </p>
              <p>
                Chúng tôi chỉ thu thập dữ liệu cần thiết để vận hành website,
                lưu tiến độ học tập và bảo vệ tài khoản của bạn.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Chúng tôi thu thập những loại dữ liệu nào?
            </h2>
            <div className="mt-3 grid gap-4">
              <div>
                <h3 className="font-semibold text-[#123047]">
                  1. Thông tin cá nhân
                </h3>
                <p className="mt-2">
                  Khi bạn đăng nhập bằng Google, website chỉ yêu cầu quyền
                  <code className="mx-1 rounded bg-[#e0f2fe] px-1 py-0.5">
                    openid
                  </code>
                  ,
                  <code className="mx-1 rounded bg-[#e0f2fe] px-1 py-0.5">
                    email
                  </code>
                  và
                  <code className="mx-1 rounded bg-[#e0f2fe] px-1 py-0.5">
                    profile
                  </code>
                  . Từ đó, chúng tôi tạo hồ sơ gồm định danh Google, email đã
                  xác minh, tên hiển thị và ảnh đại diện.
                </p>
                <p className="mt-2">
                  Nếu bạn liên hệ hỗ trợ, chúng tôi cũng lưu thông tin bạn gửi
                  kèm yêu cầu đó.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-[#123047]">
                  2. Dữ liệu học tập
                </h3>
                <p className="mt-2">
                  Ứng dụng lưu lượt làm bài, đáp án đã chọn, thời điểm nộp và
                  điểm để bạn xem lại lịch sử theo từng đề. Dữ liệu này không
                  được dùng để hiển thị đáp án trước khi bạn hoàn thành lượt
                  làm.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-[#123047]">
                  3. Dữ liệu kỹ thuật
                </h3>
                <p className="mt-2">
                  Khi bạn truy cập website, hệ thống có thể ghi nhận địa chỉ IP,
                  trình duyệt, thời điểm truy cập và đường dẫn bạn sử dụng. Các
                  thông tin này phục vụ vận hành, bảo mật và xử lý sự cố.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-[#123047]">
                  4. Cookie phiên đăng nhập
                </h3>
                <p className="mt-2">
                  Website dùng cookie phiên để giữ trạng thái đăng nhập. Cookie
                  này cần thiết để bạn làm đề, nộp bài và xem lịch sử trên tài
                  khoản của mình. Chúng tôi không dùng cookie quảng cáo.
                </p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Chúng tôi sử dụng thông tin của bạn để làm gì?
            </h2>
            <div className="mt-3 grid gap-4">
              <div>
                <h3 className="font-semibold text-[#123047]">
                  1. Vận hành dịch vụ
                </h3>
                <ul className="mt-2 list-disc space-y-2 pl-5">
                  <li>Tạo và quản lý tài khoản sau khi bạn đăng nhập Google</li>
                  <li>
                    Cho phép làm đề, tự lưu bài, nộp bài, chấm điểm và xem lời
                    giải
                  </li>
                  <li>Hiển thị lịch sử làm bài của chính bạn</li>
                  <li>Giữ hệ thống hoạt động ổn định và bảo mật</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-[#123047]">
                  2. Hỗ trợ học tập
                </h3>
                <p className="mt-2">
                  Dữ liệu lượt làm giúp bạn theo dõi tiến độ, xem lại kết quả và
                  làm lại đề. Chúng tôi không dùng dữ liệu này để bán quảng cáo.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-[#123047]">
                  3. Cải thiện website
                </h3>
                <p className="mt-2">
                  Nhật ký kỹ thuật và phản hồi của bạn giúp chúng tôi sửa lỗi,
                  tối ưu giao diện và nâng chất lượng đề thi thử.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-[#123047]">
                  4. Liên lạc khi cần
                </h3>
                <p className="mt-2">
                  Chúng tôi có thể liên hệ về tài khoản, bảo mật hoặc yêu cầu
                  hỗ trợ bạn đã gửi. Website hiện không gửi email quảng cáo.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-[#123047]">
                  5. An toàn và tuân thủ pháp luật
                </h3>
                <ul className="mt-2 list-disc space-y-2 pl-5">
                  <li>
                    Phát hiện và ngăn chặn gian lận, truy cập trái phép hoặc lạm
                    dụng hệ thống
                  </li>
                  <li>
                    Tuân thủ nghĩa vụ pháp lý và yêu cầu hợp lệ từ cơ quan có
                    thẩm quyền
                  </li>
                </ul>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Chúng tôi lưu dữ liệu trong bao lâu?
            </h2>
            <div className="mt-3 grid gap-3">
              <p>
                Chúng tôi lưu dữ liệu trong thời gian cần thiết để cung cấp dịch
                vụ nêu trong Chính sách này, trừ khi pháp luật yêu cầu hoặc cho
                phép lưu lâu hơn.
              </p>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  Dữ liệu tài khoản: lưu khi tài khoản còn hoạt động, gồm định
                  danh Google, email, tên hiển thị và ảnh đại diện
                </li>
                <li>
                  Dữ liệu học tập: lưu để bạn xem lại lịch sử lượt làm, điểm và
                  đáp án đã chọn
                </li>
                <li>
                  Dữ liệu kỹ thuật và cookie phiên: lưu trong thời gian phù hợp
                  để vận hành, bảo mật và xử lý sự cố
                </li>
              </ul>
              <p>
                Khi dữ liệu không còn cần thiết, chúng tôi sẽ xóa hoặc ẩn danh
                theo quy trình nội bộ.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Chúng tôi có chia sẻ dữ liệu ra bên ngoài không?
            </h2>
            <div className="mt-3 grid gap-3">
              <p>
                Chúng tôi không bán, trao đổi hoặc chuyển giao thông tin cá nhân
                của bạn cho bên thứ ba vì mục đích thương mại.
              </p>
              <p>Chúng tôi có thể chia sẻ dữ liệu khi cần để vận hành website:</p>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  Google, để bạn đăng nhập và chúng tôi xác minh tài khoản
                </li>
                <li>
                  Nhà cung cấp hạ tầng như lưu trữ, máy chủ, CDN hoặc nhật ký
                  vận hành, chỉ trong phạm vi cần thiết để chạy website
                </li>
              </ul>
              <p>Chúng tôi cũng có thể tiết lộ dữ liệu khi:</p>
              <ul className="list-disc space-y-2 pl-5">
                <li>Cần tuân thủ pháp luật hoặc yêu cầu của cơ quan có thẩm quyền</li>
                <li>
                  Cần bảo vệ quyền, tài sản hoặc an toàn của website và người
                  dùng
                </li>
                <li>
                  Cần phát hiện, ngăn chặn gian lận, lạm dụng hoặc truy cập trái
                  phép
                </li>
              </ul>
              <p>
                Các bên hỗ trợ vận hành chỉ được dùng dữ liệu trong phạm vi được
                giao và phải bảo mật thông tin.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Bạn có quyền gì đối với dữ liệu của mình?
            </h2>
            <div className="mt-3 grid gap-4">
              <div>
                <h3 className="font-semibold text-[#123047]">
                  1. Quyền truy cập
                </h3>
                <p className="mt-2">
                  Bạn có quyền biết chúng tôi đang lưu những dữ liệu cá nhân nào
                  về bạn.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-[#123047]">
                  2. Quyền chỉnh sửa
                </h3>
                <p className="mt-2">
                  Tên hiển thị và ảnh đại diện lấy từ tài khoản Google. Bạn có
                  thể cập nhật các thông tin đó trên Google, rồi đăng nhập lại,
                  hoặc liên hệ chúng tôi nếu cần chỉnh sửa hồ sơ trên website.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-[#123047]">
                  3. Quyền xóa dữ liệu
                </h3>
                <p className="mt-2">
                  Nếu cần xóa hồ sơ hoặc lịch sử làm bài, hãy liên hệ quản trị
                  viên hệ thống đang vận hành website. Yêu cầu sẽ được xử lý
                  theo phạm vi dữ liệu của tài khoản Google đã xác minh.
                </p>
                <p className="mt-2">
                  Quyền xóa có thể bị hạn chế khi chúng tôi cần giữ dữ liệu để
                  tuân thủ pháp luật, giải quyết tranh chấp hoặc bảo vệ an ninh
                  hệ thống.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-[#123047]">
                  4. Quyền khiếu nại
                </h3>
                <p className="mt-2">
                  Nếu bạn cho rằng dữ liệu của mình bị xử lý không phù hợp, bạn
                  có quyền liên hệ chúng tôi để được xem xét theo pháp luật Việt
                  Nam.
                </p>
              </div>
              <p>
                Để thực hiện các quyền trên, hãy liên hệ quản trị viên hệ thống
                đang vận hành website.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Thay đổi chính sách
            </h2>
            <div className="mt-3 grid gap-3">
              <p>
                Chúng tôi có thể cập nhật Chính sách Bảo mật này khi dịch vụ
                hoặc yêu cầu pháp lý thay đổi.
              </p>
              <p>
                Nếu có thay đổi quan trọng, chúng tôi sẽ thông báo trên website
                và cập nhật ngày hiệu lực của Chính sách.
              </p>
              <p>
                Việc bạn tiếp tục sử dụng website sau khi Chính sách được cập
                nhật đồng nghĩa với việc bạn đồng ý với các thay đổi đó.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">Liên hệ</h2>
            <p className="mt-3">
              Nếu bạn có câu hỏi về Chính sách Bảo mật hoặc muốn yêu cầu xóa dữ
              liệu, hãy liên hệ quản trị viên hệ thống đang vận hành website.
            </p>
          </section>
        </div>
        <Link
          className="mt-8 inline-flex font-semibold text-[#0284c7]"
          href="/login"
        >
          Quay lại đăng nhập
        </Link>
      </main>
    </div>
  );
}
