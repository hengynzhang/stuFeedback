"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [studentId, setStudentId] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (studentId.length !== 8 || !/^\d+$/.test(studentId)) {
      setError("请输入8位数字学号");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await authApi.login(studentId);
      localStorage.setItem("session_token", res.session_token);
      localStorage.setItem("student_name", res.student_name);
      router.push("/parent/chat");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "登录失败，请检查学号");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm">
        <div className="text-center mb-6">
          <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <svg className="w-7 h-7 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold text-gray-900">学情查询</h1>
          <p className="text-sm text-gray-500 mt-1">输入孩子的学号，了解学习情况</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1.5">学号</label>
            <input
              value={studentId}
              onChange={(e) => setStudentId(e.target.value.replace(/\D/g, "").slice(0, 8))}
              placeholder="请输入8位学号"
              className="w-full border rounded-xl px-4 py-2.5 text-center text-2xl font-mono tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-300"
              maxLength={8}
              autoFocus
            />
          </div>

          {error && <p className="text-sm text-red-500 text-center">{error}</p>}

          <button
            type="submit"
            disabled={loading || studentId.length !== 8}
            className="w-full bg-blue-600 text-white py-2.5 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "登录中…" : "进入"}
          </button>
        </form>

        <p className="text-xs text-gray-400 text-center mt-4">
          学号由教师提供，如有疑问请联系班主任
        </p>
      </div>
    </div>
  );
}
