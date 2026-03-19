"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { teacherAuthApi } from "@/lib/api";

type Step = "phone" | "verify";

export default function TeacherRegisterPage() {
  const router = useRouter();
  const [step, setStep]                     = useState<Step>("phone");
  const [phone, setPhone]                   = useState("");
  const [code, setCode]                     = useState("");
  const [mockCode, setMockCode]             = useState("");
  const [name, setName]                     = useState("");
  const [password, setPassword]             = useState("");
  const [confirmPassword, setConfirm]       = useState("");
  const [error, setError]                   = useState("");
  const [loading, setLoading]               = useState(false);

  async function handleSendCode() {
    if (phone.length !== 11) { setError("请输入 11 位手机号"); return; }
    setLoading(true);
    setError("");
    try {
      const res = await teacherAuthApi.sendCode(phone);
      if (res.code) setMockCode(res.code);
      setStep("verify");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "发送失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirmPassword) { setError("两次密码不一致"); return; }
    if (password.length < 6) { setError("密码长度至少 6 位"); return; }
    setLoading(true);
    setError("");
    try {
      const res = await teacherAuthApi.register({ phone, code, name, password });
      localStorage.setItem("teacher_token", res.access_token);
      localStorage.setItem("teacher_name",  res.name);
      localStorage.setItem("teacher_id",    String(res.teacher_id));
      router.push("/teacher/classes");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "注册失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm">
        <div className="text-center mb-6">
          <h1 className="text-xl font-semibold text-gray-900">教师注册</h1>
          <p className="text-sm text-gray-500 mt-1">
            {step === "phone" ? "输入手机号获取验证码" : "填写验证码和账号信息"}
          </p>
        </div>

        {step === "phone" ? (
          <div className="space-y-4">
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
            {error && <p className="text-sm text-red-500 text-center">{error}</p>}
            <button
              onClick={handleSendCode}
              disabled={loading || phone.length !== 11}
              className="w-full bg-blue-600 text-white py-2.5 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? "发送中…" : "获取验证码"}
            </button>
          </div>
        ) : (
          <form onSubmit={handleRegister} className="space-y-4">
            {/* Mock 模式：展示验证码 */}
            {mockCode && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-3 text-center">
                <p className="text-xs text-yellow-600 font-medium mb-1">Mock 模式 · 验证码</p>
                <p className="text-2xl font-mono font-bold text-yellow-700 tracking-[0.3em]">
                  {mockCode}
                </p>
              </div>
            )}
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1.5">验证码</label>
              <input
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="6 位验证码"
                className="w-full border rounded-xl px-4 py-2.5 text-center text-xl font-mono tracking-[0.3em] focus:outline-none focus:ring-2 focus:ring-blue-300"
                maxLength={6}
                autoFocus
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1.5">姓名</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="请输入姓名"
                className="w-full border rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1.5">设置密码</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="至少 6 位"
                className="w-full border rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1.5">确认密码</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="再次输入密码"
                className="w-full border rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
            </div>

            {error && <p className="text-sm text-red-500 text-center">{error}</p>}

            <button
              type="submit"
              disabled={loading || !code || !name || !password || !confirmPassword}
              className="w-full bg-blue-600 text-white py-2.5 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? "注册中…" : "完成注册"}
            </button>
          </form>
        )}

        <p className="text-center text-sm text-gray-500 mt-5">
          已有账号？{" "}
          <Link href="/teacher/login" className="text-blue-600 hover:underline font-medium">
            去登录
          </Link>
        </p>
      </div>
    </div>
  );
}
