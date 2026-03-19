"use client";
import { useEffect, useState } from "react";
import { teacherApi, Student, Class } from "@/lib/api";
import { Trash2, Plus, Pencil, Check, X } from "lucide-react";

function getToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("teacher_token") ?? "";
}

export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [classes, setClasses]   = useState<Class[]>([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState("");
  const [filterClass, setFilterClass] = useState<number | "">("");

  const [creating, setCreating]   = useState(false);
  const [newChinese, setNewChinese] = useState("");
  const [newEnglish, setNewEnglish] = useState("");
  const [newClassId, setNewClassId] = useState<number | "">("");

  const [editingId, setEditingId]   = useState<number | null>(null);
  const [editChinese, setEditChinese] = useState("");
  const [editEnglish, setEditEnglish] = useState("");
  const [editClassId, setEditClassId] = useState<number | "">("");

  useEffect(() => { load(); }, []);

  async function load() {
    try {
      const [studs, cls] = await Promise.all([
        teacherApi.getStudents(getToken()),
        teacherApi.getClasses(getToken()),
      ]);
      setStudents(studs);
      setClasses(cls);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  const filtered = filterClass
    ? students.filter((s) => s.class_id === filterClass)
    : students;

  function className(class_id: number) {
    return classes.find((c) => c.id === class_id)?.name ?? `班级#${class_id}`;
  }

  async function handleCreate() {
    if (!newChinese.trim()) return;
    if (!newClassId) return alert("请选择班级");
    try {
      const s = await teacherApi.createStudent(getToken(), {
        chinese_name: newChinese,
        english_name: newEnglish || undefined,
        class_id:     Number(newClassId),
      });
      setStudents((prev) => [...prev, s]);
      setNewChinese(""); setNewEnglish(""); setNewClassId(""); setCreating(false);
    } catch (e: unknown) { alert(e instanceof Error ? e.message : "创建失败"); }
  }

  async function handleSave(id: number) {
    try {
      const s = await teacherApi.updateStudent(getToken(), id, {
        chinese_name: editChinese,
        english_name: editEnglish || undefined,
        class_id:     editClassId ? Number(editClassId) : undefined,
      });
      setStudents((prev) => prev.map((x) => (x.id === id ? s : x)));
      setEditingId(null);
    } catch (e: unknown) { alert(e instanceof Error ? e.message : "更新失败"); }
  }

  async function handleDelete(id: number) {
    if (!confirm("确认删除该学生？相关记录也会一并删除。")) return;
    try {
      await teacherApi.deleteStudent(getToken(), id);
      setStudents((prev) => prev.filter((x) => x.id !== id));
    } catch (e: unknown) { alert(e instanceof Error ? e.message : "删除失败"); }
  }

  if (loading) return <p className="text-gray-400">加载中…</p>;
  if (error) return <p className="text-red-500">{error}</p>;

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold">学生管理</h1>
        <div className="flex gap-2">
          <select
            value={filterClass}
            onChange={(e) => setFilterClass(e.target.value ? Number(e.target.value) : "")}
            className="border rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="">全部班级</option>
            {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-1 bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-blue-700"
          >
            <Plus size={15} /> 新建学生
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium text-gray-500">中文名</th>
              <th className="text-left px-4 py-2.5 font-medium text-gray-500">英文名</th>
              <th className="text-left px-4 py-2.5 font-medium text-gray-500">学号</th>
              <th className="text-left px-4 py-2.5 font-medium text-gray-500">班级</th>
              <th className="px-4 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {/* 新建行 */}
            {creating && (
              <tr className="border-b bg-blue-50">
                <td className="px-4 py-2">
                  <input autoFocus value={newChinese} onChange={(e) => setNewChinese(e.target.value)}
                    placeholder="中文名" className="border rounded px-2 py-1 w-full text-sm" />
                </td>
                <td className="px-4 py-2">
                  <input value={newEnglish} onChange={(e) => setNewEnglish(e.target.value)}
                    placeholder="英文名（选填）" className="border rounded px-2 py-1 w-full text-sm" />
                </td>
                <td className="px-4 py-2 text-gray-400 text-xs">自动生成</td>
                <td className="px-4 py-2">
                  <select value={newClassId} onChange={(e) => setNewClassId(Number(e.target.value))}
                    className="border rounded px-2 py-1 text-sm w-full">
                    <option value="">选择班级</option>
                    {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </td>
                <td className="px-4 py-2">
                  <div className="flex gap-1">
                    <button onClick={handleCreate} className="text-green-600 hover:text-green-800"><Check size={15} /></button>
                    <button onClick={() => { setCreating(false); setNewChinese(""); setNewEnglish(""); setNewClassId(""); }}
                      className="text-gray-400 hover:text-gray-600"><X size={15} /></button>
                  </div>
                </td>
              </tr>
            )}

            {filtered.map((s) => (
              <tr key={s.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-2">
                  {editingId === s.id
                    ? <input autoFocus value={editChinese} onChange={(e) => setEditChinese(e.target.value)}
                        className="border rounded px-2 py-1 w-full text-sm" />
                    : s.chinese_name}
                </td>
                <td className="px-4 py-2">
                  {editingId === s.id
                    ? <input value={editEnglish} onChange={(e) => setEditEnglish(e.target.value)}
                        className="border rounded px-2 py-1 w-full text-sm" />
                    : (s.english_name ?? "—")}
                </td>
                <td className="px-4 py-2 font-mono text-gray-500">{s.student_id}</td>
                <td className="px-4 py-2">
                  {editingId === s.id
                    ? <select value={editClassId || s.class_id} onChange={(e) => setEditClassId(Number(e.target.value))}
                        className="border rounded px-2 py-1 text-sm">
                        {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                      </select>
                    : <span className="text-xs text-gray-500">{className(s.class_id)}</span>}
                </td>
                <td className="px-4 py-2">
                  <div className="flex gap-2 justify-end">
                    {editingId === s.id ? (
                      <>
                        <button onClick={() => handleSave(s.id)} className="text-green-600 hover:text-green-800"><Check size={15} /></button>
                        <button onClick={() => setEditingId(null)} className="text-gray-400 hover:text-gray-600"><X size={15} /></button>
                      </>
                    ) : (
                      <>
                        <button onClick={() => { setEditingId(s.id); setEditChinese(s.chinese_name); setEditEnglish(s.english_name ?? ""); setEditClassId(s.class_id); }}
                          className="text-blue-500 hover:text-blue-700"><Pencil size={14} /></button>
                        <button onClick={() => handleDelete(s.id)} className="text-red-400 hover:text-red-600"><Trash2 size={14} /></button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}

            {filtered.length === 0 && !creating && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                {classes.length === 0 ? "请先在「班级管理」中创建班级" : "暂无学生，点击右上角新建"}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
