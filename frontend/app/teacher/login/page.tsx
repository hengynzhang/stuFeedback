"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { teacherAuthApi } from "@/lib/api";

export default function TeacherLoginPage() {
  const router = useRouter();
  const [phone, setPhone]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await teacherAuthApi.login(phone, password);
      localStorage.setItem("teacher_token", res.access_token);
      localStorage.setItem("teacher_name",  res.name);
      localStorage.setItem("teacher_id",    String(res.teacher_id));
      router.push("/teacher/classes");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "登录失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm">
        <div className="text-center mb-6">
          <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <svg className="w-7 h-7 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold text-gray-900">教师登录</h1>
          <p className="text-sm text-gray-500 mt-1">手机号 + 密码</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1.5">手机号</label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value.replace(/\D/g, "").slice(0, 11))}
              placeholder="请输入手机号"
              className="w-full border rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
              maxLength={11}
              autoFocus
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1.5">密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
              className="w-full border rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
          </div>

          {error && <p className="text-sm text-red-500 text-center">{error}</p>}

          <button
            type="submit"
            disabled={loading || phone.length !== 11 || !password}
            className="w-full bg-blue-600 text-white py-2.5 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "登录中…" : "登录"}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-5">
          还没有账号？{" "}
          <Link href="/teacher/register" className="text-blue-600 hover:underline font-medium">
            立即注册
          </Link>
        </p>
      </div>
    </div>
  );
}
