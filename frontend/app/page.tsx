import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="text-center space-y-6">
        <h1 className="text-3xl font-semibold text-gray-900">学生反馈系统</h1>
        <p className="text-gray-500">请选择你的身份</p>
        <div className="flex gap-4 justify-center">
          <Link href="/teacher/students"
            className="bg-white border rounded-xl px-8 py-5 hover:border-blue-300 hover:shadow-md transition-all">
            <p className="text-lg font-medium text-gray-900">教师端</p>
            <p className="text-sm text-gray-400 mt-1">学生管理 · 数据录入</p>
          </Link>
          <Link href="/parent/login"
            className="bg-blue-600 text-white rounded-xl px-8 py-5 hover:bg-blue-700 transition-all">
            <p className="text-lg font-medium">家长端</p>
            <p className="text-sm text-blue-200 mt-1">学情查询 · AI 对话</p>
          </Link>
        </div>
      </div>
    </div>
  );
}
