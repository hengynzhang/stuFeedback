"use client";
import { useEffect, useState } from "react";
import { teacherApi, Class } from "@/lib/api";
import { Plus, Trash2, Pencil, Check, X, BookOpen } from "lucide-react";

const SUBJECTS = ["英语", "数学", "语文", "物理", "化学", "生物", "历史", "地理", "政治", "其他"];
const STATUS_MAP = { active: "进行中", completed: "已结课" };

const EMPTY_FORM = {
  name: "", subject: "", start_date: "", end_date: "", total_lessons: 20,
};

function getToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("teacher_token") ?? "";
}

export default function ClassesPage() {
  const [classes, setClasses]   = useState<Class[]>([]);
  const [loading, setLoading]   = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm]         = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm]   = useState<Partial<Class>>({});

  useEffect(() => { load(); }, []);

  async function load() {
    try {
      setClasses(await teacherApi.getClasses(getToken()));
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!form.name.trim() || !form.subject) return alert("请填写班级名称和科目");
    try {
      const created = await teacherApi.createClass(getToken(), {
        name:          form.name,
        subject:       form.subject,
        start_date:    form.start_date || undefined,
        end_date:      form.end_date   || undefined,
        total_lessons: form.total_lessons,
      });
      setClasses((prev) => [created, ...prev]);
      setForm(EMPTY_FORM);
      setShowForm(false);
    } catch (e: unknown) { alert(e instanceof Error ? e.message : "创建失败"); }
  }

  async function handleSave(id: number) {
    try {
      const updated = await teacherApi.updateClass(getToken(), id, editForm);
      setClasses((prev) => prev.map((c) => (c.id === id ? updated : c)));
      setEditingId(null);
    } catch (e: unknown) { alert(e instanceof Error ? e.message : "更新失败"); }
  }

  async function handleDelete(id: number) {
    if (!confirm("确认删除该班级？班级下的所有学生和记录也会一并删除。")) return;
    try {
      await teacherApi.deleteClass(getToken(), id);
      setClasses((prev) => prev.filter((c) => c.id !== id));
    } catch (e: unknown) { alert(e instanceof Error ? e.message : "删除失败"); }
  }

  if (loading) return <p className="text-gray-400">加载中…</p>;

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-xl font-semibold">班级管理</h1>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-blue-700"
        >
          <Plus size={15} /> 新建班级
        </button>
      </div>

      {/* 新建表单 */}
      {showForm && (
        <div className="bg-white border rounded-xl p-5 mb-5 shadow-sm">
          <h2 className="font-medium mb-4">新建班级</h2>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">班级名称 *</label>
              <input
                autoFocus
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="如：2025春季英语A班"
                className="border rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">科目 *</label>
              <select
                value={form.subject}
                onChange={(e) => setForm({ ...form, subject: e.target.value })}
                className="border rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-300"
              >
                <option value="">请选择</option>
                {SUBJECTS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">开班日期</label>
              <input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                className="border rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">结课日期</label>
              <input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                className="border rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">总课时</label>
              <input
                type="number"
                min={1}
                value={form.total_lessons}
                onChange={(e) => setForm({ ...form, total_lessons: Number(e.target.value) })}
                className="border rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleCreate} className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700">
              创建
            </button>
            <button onClick={() => { setShowForm(false); setForm(EMPTY_FORM); }} className="text-gray-500 px-4 py-1.5 rounded-lg text-sm hover:bg-gray-100">
              取消
            </button>
          </div>
        </div>
      )}

      {/* 班级列表 */}
      {classes.length === 0 && !showForm ? (
        <div className="bg-white border rounded-xl p-12 text-center text-gray-400">
          <BookOpen size={40} className="mx-auto mb-3 opacity-30" />
          <p>暂无班级，点击右上角新建</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {classes.map((c) => (
            <div key={c.id} className="bg-white border rounded-xl p-4 hover:shadow-sm transition-shadow">
              {editingId === c.id ? (
                /* 行内编辑 */
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">班级名称</label>
                    <input
                      autoFocus
                      value={editForm.name ?? c.name}
                      onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                      className="border rounded px-2 py-1.5 text-sm w-full"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">科目</label>
                    <select
                      value={editForm.subject ?? c.subject}
                      onChange={(e) => setEditForm({ ...editForm, subject: e.target.value })}
                      className="border rounded px-2 py-1.5 text-sm w-full"
                    >
                      {SUBJECTS.map((s) => <option key={s}>{s}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">总课时</label>
                    <input
                      type="number"
                      value={editForm.total_lessons ?? c.total_lessons}
                      onChange={(e) => setEditForm({ ...editForm, total_lessons: Number(e.target.value) })}
                      className="border rounded px-2 py-1.5 text-sm w-full"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">开班日期</label>
                    <input
                      type="date"
                      value={editForm.start_date ?? c.start_date ?? ""}
                      onChange={(e) => setEditForm({ ...editForm, start_date: e.target.value })}
                      className="border rounded px-2 py-1.5 text-sm w-full"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">结课日期</label>
                    <input
                      type="date"
                      value={editForm.end_date ?? c.end_date ?? ""}
                      onChange={(e) => setEditForm({ ...editForm, end_date: e.target.value })}
                      className="border rounded px-2 py-1.5 text-sm w-full"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">状态</label>
                    <select
                      value={editForm.status ?? c.status}
                      onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                      className="border rounded px-2 py-1.5 text-sm w-full"
                    >
                      <option value="active">进行中</option>
                      <option value="completed">已结课</option>
                    </select>
                  </div>
                  <div className="col-span-3 flex gap-2 mt-1">
                    <button onClick={() => handleSave(c.id)} className="flex items-center gap-1 text-green-600 hover:text-green-800 text-sm">
                      <Check size={14} /> 保存
                    </button>
                    <button onClick={() => setEditingId(null)} className="flex items-center gap-1 text-gray-400 hover:text-gray-600 text-sm">
                      <X size={14} /> 取消
                    </button>
                  </div>
                </div>
              ) : (
                /* 展示视图 */
                <div className="flex items-center">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900">{c.name}</span>
                      <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full">{c.subject}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        c.status === "active" ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"
                      }`}>
                        {STATUS_MAP[c.status]}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-400">
                      <span>开班：{c.start_date ?? "—"}</span>
                      <span>结课：{c.end_date ?? "—"}</span>
                      <span>在班学员：{c.student_count} 人</span>
                      <span>
                        课时：{c.completed_lessons}/{c.total_lessons}
                        （剩余 {c.remaining_lessons}）
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => { setEditingId(c.id); setEditForm({}); }}
                      className="text-blue-400 hover:text-blue-600 p-1"
                    >
                      <Pencil size={14} />
                    </button>
                    <button
                      onClick={() => handleDelete(c.id)}
                      className="text-red-400 hover:text-red-600 p-1"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
