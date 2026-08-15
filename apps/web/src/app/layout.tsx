import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Điểm 10 Lịch sử | Luyện thi tốt nghiệp THPT",
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
