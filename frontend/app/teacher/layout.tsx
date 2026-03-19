"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const AUTH_FREE = ["/teacher/login", "/teacher/register"];

const NAV = [
  { href: "/teacher/classes",  label: "班级管理" },
  { href: "/teacher/students", label: "学生管理" },
  { href: "/teacher/records",  label: "课程记录" },
  { href: "/teacher/exams",    label: "考试成绩" },
  { href: "/teacher/homework", label: "作业记录" },
];

export default function TeacherLayout({ children }: { children: React.ReactNode }) {
  const pathname    = usePathname();
  const router      = useRouter();
  const isAuthFree  = AUTH_FREE.includes(pathname);
  const [teacherName, setTeacherName] = useState("");

  useEffect(() => {
    if (isAuthFree) return;
    const token = localStorage.getItem("teacher_token");
    if (!token) { router.push("/teacher/login"); return; }
    setTeacherName(localStorage.getItem("teacher_name") ?? "");
  }, [pathname, isAuthFree, router]);

  // 登录/注册页不渲染侧边栏
  if (isAuthFree) return <>{children}</>;

  function handleLogout() {
    localStorage.removeItem("teacher_token");
    localStorage.removeItem("teacher_name");
    localStorage.removeItem("teacher_id");
    router.push("/teacher/login");
  }

  return (
    <div className="flex h-screen">
      {/* 侧边栏 */}
      <aside className="w-44 bg-white border-r flex flex-col py-6 px-3 gap-1 shrink-0">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1 px-2">
          教师端
        </p>
        {teacherName && (
          <p className="text-xs text-gray-500 px-2 mb-3 truncate">{teacherName}</p>
        )}
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
        <div className="mt-auto">
          <button
            onClick={handleLogout}
            className="w-full text-left rounded-lg px-3 py-2 text-sm text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
          >
            退出登录
          </button>
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 overflow-auto p-6 bg-gray-50">{children}</main>
    </div>
  );
}
