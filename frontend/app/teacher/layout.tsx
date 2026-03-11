"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/teacher/students", label: "学生管理" },
  { href: "/teacher/records",  label: "课程记录" },
  { href: "/teacher/exams",    label: "考试成绩" },
  { href: "/teacher/homework", label: "作业记录" },
];

export default function TeacherLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="flex h-screen">
      {/* 侧边栏 */}
      <aside className="w-44 bg-white border-r flex flex-col py-6 px-3 gap-1 shrink-0">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2">
          教师端
        </p>
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              pathname.startsWith(item.href)
                ? "bg-blue-50 text-blue-700"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            {item.label}
          </Link>
        ))}
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
