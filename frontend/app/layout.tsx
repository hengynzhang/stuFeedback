import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "学生反馈系统",
  description: "家长学情查询与 AI 对话系统",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
