import type { Metadata } from "next";
import Link from "next/link";

import { SiteHeader } from "@/components/site-header";
import { SITE_NAME } from "@/lib/site";

export const metadata: Metadata = {
  title: `Điều khoản sử dụng | ${SITE_NAME}`,
  description:
    `Điều khoản sử dụng website ${SITE_NAME}, quy định quyền, nghĩa vụ và trách nhiệm khi truy cập hoặc sử dụng nền tảng.`,
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[#f2fbff] text-[#123047]">
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8">
        <p className="text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
          ĐIỀU KHOẢN SỬ DỤNG
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Quy định khi truy cập và sử dụng website
        </h1>
        <p className="mt-4 text-sm text-[#45667a]">
          Cập nhật lần cuối: 16/08/2026
        </p>
        <div className="mt-8 grid gap-8 rounded-3xl border border-[#bae6fd] bg-white p-6 leading-7 text-[#45667a] sm:p-8">
          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Giới thiệu chung
            </h2>
            <div className="mt-3 grid gap-3">
              <p>
                Các Điều khoản Sử dụng này quy định cách bạn truy cập và sử dụng
                website Sử Văn Quán.
              </p>
              <p>
                Website là nền tảng trực tuyến cung cấp các giải pháp luyện thi
                THPT và đánh giá năng lực, bao gồm nhưng không giới hạn ở: bài
                học, tài liệu, bài luyện, bài kiểm tra, phân tích kết quả và các
                công cụ hỗ trợ học tập khác.
              </p>
              <p>
                Khi truy cập hoặc sử dụng website, bạn xác nhận rằng bạn đã đọc,
                hiểu và đồng ý bị ràng buộc bởi các Điều khoản này.
              </p>
              <p>
                Nếu bạn không đồng ý với bất kỳ nội dung nào, vui lòng ngừng sử
                dụng website.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">Định nghĩa</h2>
            <p className="mt-3">
              Trong Điều khoản này, các thuật ngữ dưới đây được hiểu như sau:
            </p>
            <dl className="mt-4 grid gap-4">
              <div>
                <dt className="font-semibold text-[#123047]">
                  Chúng tôi
                </dt>
                <dd className="mt-1">
                  Sử Văn Quán, đơn vị vận hành website.
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-[#123047]">
                  Bạn / Người dùng
                </dt>
                <dd className="mt-1">
                  Cá nhân hoặc tổ chức truy cập hoặc sử dụng website, bao gồm cả
                  người đã đăng ký tài khoản.
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-[#123047]">Website</dt>
                <dd className="mt-1">
                  Nền tảng trực tuyến Sử Văn Quán, bao gồm toàn bộ nội dung,
                  tính năng và dịch vụ được cung cấp.
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-[#123047]">Tài khoản</dt>
                <dd className="mt-1">
                  Thông tin đăng nhập (bao gồm email, mật khẩu hoặc phương thức
                  xác thực khác) được tạo để truy cập và sử dụng các tính năng
                  của website.
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-[#123047]">Nội dung</dt>
                <dd className="mt-1">
                  Toàn bộ tài liệu, bài viết, đề thi, video, hình ảnh, dữ liệu,
                  phần mềm và các tài nguyên học tập khác được cung cấp trên
                  website.
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-[#123047]">Dịch vụ</dt>
                <dd className="mt-1">
                  Các sản phẩm và tính năng do chúng tôi cung cấp, bao gồm nhưng
                  không giới hạn ở khóa học, bài luyện, bài kiểm tra, phân tích
                  kết quả và các công cụ hỗ trợ học tập.
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-[#123047]">Thiết bị</dt>
                <dd className="mt-1">
                  Điện thoại, máy tính hoặc bất kỳ thiết bị nào có thể truy cập
                  website.
                </dd>
              </div>
            </dl>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Tài khoản người dùng
            </h2>
            <div className="mt-3 grid gap-3">
              <p>
                Để sử dụng một số tính năng của website, bạn có thể cần đăng ký
                tài khoản. Hiện tại, website hỗ trợ đăng nhập bằng tài khoản
                Google có email đã xác minh.
              </p>
              <p>Khi tạo tài khoản, bạn đồng ý rằng:</p>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  Cung cấp thông tin chính xác, đầy đủ và luôn được cập nhật
                </li>
                <li>
                  Chịu trách nhiệm bảo mật thông tin đăng nhập, bao gồm email
                  và mật khẩu
                </li>
                <li>
                  Thông báo kịp thời cho chúng tôi nếu phát hiện tài khoản bị
                  truy cập trái phép hoặc có dấu hiệu bị xâm phạm
                </li>
              </ul>
              <p>
                Bạn chịu trách nhiệm cho mọi hoạt động diễn ra dưới tài khoản
                của mình. Chúng tôi có thể chấm dứt quyền truy cập mà không cần
                thông báo trước.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Quyền và nghĩa vụ của người dùng
            </h2>
            <div className="mt-3 grid gap-3">
              <p>Khi sử dụng website, bạn đồng ý:</p>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  Sử dụng website và nội dung cho mục đích học tập cá nhân, hợp
                  pháp
                </li>
                <li>
                  Tuân thủ các quy định của pháp luật và Điều khoản Sử dụng này
                </li>
                <li>
                  Không sao chép, phân phối, phát tán hoặc khai thác nội dung
                  cho mục đích thương mại khi chưa được cho phép
                </li>
                <li>
                  Không sử dụng website để thực hiện các hành vi gian lận thi cử
                  hoặc làm sai lệch kết quả học tập
                </li>
                <li>
                  Không can thiệp, phá hoại, làm gián đoạn hoặc gây ảnh hưởng
                  đến hoạt động của hệ thống website
                </li>
                <li>
                  Không phát tán mã độc, virus hoặc thực hiện các hành vi gây
                  hại đến hệ thống hoặc người dùng khác
                </li>
              </ul>
              <p>
                Bạn cam kết chịu trách nhiệm đối với mọi hành vi sử dụng website
                của mình.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Nội dung và quyền sở hữu trí tuệ
            </h2>
            <div className="mt-3 grid gap-3">
              <p>
                Toàn bộ nội dung trên website thuộc quyền sở hữu của chúng tôi
                hoặc các bên cấp phép hợp pháp. Kho đề gồm đề thi thử do chúng
                tôi biên soạn và đề tham khảo từ nguồn khác, chỉ dùng để ôn tập,
                không phải đề thi chính thức.
              </p>
              <p className="font-semibold text-[#123047]">Bạn được phép:</p>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  Sử dụng nội dung cho mục đích học tập cá nhân, không nhằm mục
                  đích thương mại
                </li>
              </ul>
              <p className="font-semibold text-[#123047]">Bạn không được phép:</p>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  Sao chép, chỉnh sửa, tái xuất bản hoặc phân phối nội dung dưới
                  bất kỳ hình thức nào cho mục đích thương mại
                </li>
                <li>
                  Khai thác nội dung theo cách gây ảnh hưởng đến quyền và lợi
                  ích hợp pháp của chúng tôi
                </li>
              </ul>
              <p>
                Mọi hành vi vi phạm có thể dẫn đến việc bị xử lý theo quy định
                của pháp luật và/hoặc bị chấm dứt quyền sử dụng website.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Liên kết bên thứ ba
            </h2>
            <div className="mt-3 grid gap-3">
              <p>
                Website có thể chứa liên kết đến các website hoặc dịch vụ của
                bên thứ ba nhằm cung cấp thêm thông tin hoặc tiện ích cho người
                dùng.
              </p>
              <p>Chúng tôi:</p>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  Không kiểm soát và không đảm bảo tính chính xác, đầy đủ hoặc
                  an toàn của các website bên thứ ba
                </li>
                <li>
                  Không chịu trách nhiệm đối với bất kỳ thiệt hại hoặc rủi ro
                  nào phát sinh từ việc bạn truy cập hoặc sử dụng các website đó
                </li>
              </ul>
              <p>
                Bạn nên xem xét kỹ điều khoản sử dụng và chính sách quyền riêng
                tư của các website đó trước khi sử dụng.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Tuyên bố miễn trừ trách nhiệm
            </h2>
            <div className="mt-3 grid gap-3">
              <p>
                Chúng tôi không đưa ra bất kỳ cam kết hoặc đảm bảo nào, bao gồm
                nhưng không giới hạn:
              </p>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  Website sẽ luôn hoạt động liên tục, không bị gián đoạn hoặc
                  không có lỗi
                </li>
                <li>
                  Nội dung luôn chính xác, đầy đủ hoặc phù hợp với mọi đối tượng
                  người dùng
                </li>
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Luật áp dụng
            </h2>
            <div className="mt-3 grid gap-3">
              <p>
                Các Điều khoản Sử dụng này được điều chỉnh và giải thích theo
                pháp luật của nước Cộng hòa Xã hội Chủ nghĩa Việt Nam.
              </p>
              <p>
                Mọi vấn đề phát sinh liên quan đến việc truy cập hoặc sử dụng
                website sẽ được xử lý theo quy định của pháp luật Việt Nam hiện
                hành.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Giải quyết tranh chấp
            </h2>
            <div className="mt-3 grid gap-3">
              <p>
                Trong trường hợp phát sinh tranh chấp liên quan đến việc sử dụng
                website hoặc Điều khoản Sử dụng này, các bên sẽ ưu tiên giải
                quyết thông qua thương lượng và trao đổi thiện chí.
              </p>
              <p>
                Nếu không thể giải quyết thông qua thương lượng trong thời gian
                hợp lý, tranh chấp sẽ được đưa ra cơ quan có thẩm quyền tại Việt
                Nam để giải quyết theo quy định pháp luật.
              </p>
              <p>
                Trong quá trình giải quyết tranh chấp, các bên vẫn có trách
                nhiệm tiếp tục thực hiện các nghĩa vụ không bị ảnh hưởng bởi
                tranh chấp.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Hiệu lực từng phần
            </h2>
            <div className="mt-3 grid gap-3">
              <p>
                Nếu bất kỳ điều khoản nào trong Điều khoản Sử dụng này bị tuyên
                bố là vô hiệu, không hợp pháp hoặc không thể thực thi theo quy
                định của pháp luật, điều khoản đó sẽ được tách khỏi phần còn
                lại.
              </p>
              <p>
                Các điều khoản còn lại vẫn giữ nguyên hiệu lực và giá trị pháp
                lý đầy đủ.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Thay đổi điều khoản
            </h2>
            <div className="mt-3 grid gap-3">
              <p>Chúng tôi có thể cập nhật điều khoản bất kỳ lúc nào.</p>
              <p>Nếu có thay đổi quan trọng, chúng tôi sẽ thông báo trước.</p>
              <p>
                Việc bạn tiếp tục sử dụng website đồng nghĩa với việc bạn chấp
                nhận các thay đổi đó.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#123047]">Liên hệ</h2>
            <p className="mt-3">
              Nếu bạn có câu hỏi về Điều khoản Sử dụng, hãy liên hệ quản trị
              viên hệ thống đang vận hành website.
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
