import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

import { SITE_NAME, SITE_TAGLINE } from "@/lib/site";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  applicationName: SITE_NAME,
  title: `${SITE_NAME} | ${SITE_TAGLINE}`,
  description:
    "Tổng hợp đề thi thử môn Lịch sử: đề tự biên soạn và đề tham khảo từ các nguồn khác, theo cấu trúc kỳ thi tốt nghiệp THPT, có chấm điểm và lời giải chi tiết.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className={`${geistSans.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">{children}</body>
    </html>
  );
}
