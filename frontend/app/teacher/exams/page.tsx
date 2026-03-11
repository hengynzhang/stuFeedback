"use client";
import { useEffect, useState } from "react";
import { teacherApi, ExamRecord, Student } from "@/lib/api";
import { Plus, Trash2, Pencil, Check, X } from "lucide-react";

const SUBJECTS = ["听力", "阅读", "写作", "口语", "数学"];
const DAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];

type FormState = Omit<ExamRecord, "id" | "created_at">;

const EMPTY_FORM: FormState = {
  student_id: 0, test_date: "", day_of_week: "", week: "",
  test_number: undefined, subject: "", score: undefined, total: undefined, notes: "",
};

export default function ExamsPage() {
  const [exams, setExams] = useState<ExamRecord[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<Partial<ExamRecord>>({});
  const [filterStudent, setFilterStudent] = useState("");
  const [filterSubject, setFilterSubject] = useState("");

  useEffect(() => {
    Promise.all([
      teacherApi.getExams().then(setExams),
      teacherApi.getStudents().then(setStudents),
    ]).finally(() => setLoading(false));
  }, []);

  const filtered = exams.filter((e) =>
    (!filterStudent || e.student_id === Number(filterStudent)) &&
    (!filterSubject || e.subject === filterSubject)
  );

  function studentName(id: number) {
    return students.find((s) => s.id === id)?.chinese_name ?? `#${id}`;
  }

  async function handleCreate() {
    if (!form.student_id || !form.subject) return alert("请选择学生和科目");
    try {
      const created = await teacherApi.createExam({
        ...form,
        test_date: form.test_date || undefined,
        day_of_week: form.day_of_week || undefined,
        week: form.week || undefined,
        notes: form.notes || undefined,
      });
      setExams((prev) => [created, ...prev]);
      setForm(EMPTY_FORM); setShowForm(false);
    } catch (e: unknown) { alert(e instanceof Error ? e.message : "创建失败"); }
  }

  async function handleSave(id: number) {
    try {
      const updated = await teacherApi.updateExam(id, editForm);
      setExams((prev) => prev.map((e) => (e.id === id ? updated : e)));
      setEditingId(null);
    } catch (e: unknown) { alert(e instanceof Error ? e.message : "更新失败"); }
  }

  async function handleDelete(id: number) {
    if (!confirm("确认删除？")) return;
    await teacherApi.deleteExam(id);
    setExams((prev) => prev.filter((e) => e.id !== id));
  }

  if (loading) return <p className="text-gray-400">加载中…</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold">考试成绩</h1>
        <button onClick={() => setShowForm(true)}
          className="flex items-center gap-1 bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-blue-700">
          <Plus size={15} /> 新建记录
        </button>
      </div>

      {/* 筛选 */}
      <div className="flex gap-3 mb-4">
        <select value={filterStudent} onChange={(e) => setFilterStudent(e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">全部学生</option>
          {students.map((s) => <option key={s.id} value={s.id}>{s.chinese_name}</option>)}
        </select>
        <select value={filterSubject} onChange={(e) => setFilterSubject(e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">全部科目</option>
          {SUBJECTS.map((s) => <option key={s}>{s}</option>)}
        </select>
      </div>

      {/* 新建表单 */}
      {showForm && (
        <div className="bg-white border rounded-xl p-4 mb-4 shadow-sm">
          <h2 className="font-medium mb-3">新建考试记录</h2>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">学生 *</label>
              <select value={form.student_id} onChange={(e) => setForm({ ...form, student_id: Number(e.target.value) })}
                className="border rounded px-2 py-1.5 text-sm w-full">
                <option value={0}>请选择</option>
                {students.map((s) => <option key={s.id} value={s.id}>{s.chinese_name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">科目 *</label>
              <select value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })}
                className="border rounded px-2 py-1.5 text-sm w-full">
                <option value="">请选择</option>
                {SUBJECTS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">考试日期</label>
              <input type="date" value={form.test_date} onChange={(e) => setForm({ ...form, test_date: e.target.value })}
                className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">星期</label>
              <select value={form.day_of_week} onChange={(e) => setForm({ ...form, day_of_week: e.target.value })}
                className="border rounded px-2 py-1.5 text-sm w-full">
                <option value="">请选择</option>
                {DAYS.map((d) => <option key={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">周次</label>
              <input value={form.week} onChange={(e) => setForm({ ...form, week: e.target.value })}
                placeholder="如 Week 1" className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">第几次考试</label>
              <input type="number" value={form.test_number ?? ""} onChange={(e) => setForm({ ...form, test_number: Number(e.target.value) || undefined })}
                className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">得分</label>
              <input type="number" step="0.5" value={form.score ?? ""} onChange={(e) => setForm({ ...form, score: Number(e.target.value) || undefined })}
                className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">满分</label>
              <input type="number" value={form.total ?? ""} onChange={(e) => setForm({ ...form, total: Number(e.target.value) || undefined })}
                className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">备注</label>
              <input value={form.notes ?? ""} onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleCreate} className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700">保存</button>
            <button onClick={() => { setShowForm(false); setForm(EMPTY_FORM); }} className="text-gray-500 px-4 py-1.5 rounded-lg text-sm hover:bg-gray-100">取消</button>
          </div>
        </div>
      )}

      {/* 表格 */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              {["学生", "科目", "日期", "周次", "得分", "满分", "备注", ""].map((h) => (
                <th key={h} className="text-left px-4 py-2 font-medium text-gray-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((e) => (
              <tr key={e.id} className="border-b hover:bg-gray-50">
                {editingId === e.id ? (
                  <>
                    <td className="px-4 py-2">{studentName(e.student_id)}</td>
                    <td className="px-4 py-2">
                      <select value={editForm.subject ?? e.subject} onChange={(ev) => setEditForm({ ...editForm, subject: ev.target.value })}
                        className="border rounded px-2 py-1 text-sm">
                        {SUBJECTS.map((s) => <option key={s}>{s}</option>)}
                      </select>
                    </td>
                    <td className="px-4 py-2">
                      <input type="date" value={editForm.test_date ?? e.test_date ?? ""} onChange={(ev) => setEditForm({ ...editForm, test_date: ev.target.value })}
                        className="border rounded px-2 py-1 text-sm" />
                    </td>
                    <td className="px-4 py-2">
                      <input value={editForm.week ?? e.week ?? ""} onChange={(ev) => setEditForm({ ...editForm, week: ev.target.value })}
                        className="border rounded px-2 py-1 text-sm w-20" />
                    </td>
                    <td className="px-4 py-2">
                      <input type="number" step="0.5" value={editForm.score ?? e.score ?? ""} onChange={(ev) => setEditForm({ ...editForm, score: Number(ev.target.value) })}
                        className="border rounded px-2 py-1 text-sm w-16" />
                    </td>
                    <td className="px-4 py-2">
                      <input type="number" value={editForm.total ?? e.total ?? ""} onChange={(ev) => setEditForm({ ...editForm, total: Number(ev.target.value) })}
                        className="border rounded px-2 py-1 text-sm w-16" />
                    </td>
                    <td className="px-4 py-2">
                      <input value={editForm.notes ?? e.notes ?? ""} onChange={(ev) => setEditForm({ ...editForm, notes: ev.target.value })}
                        className="border rounded px-2 py-1 text-sm w-32" />
                    </td>
                    <td className="px-4 py-2">
                      <div className="flex gap-1">
                        <button onClick={() => handleSave(e.id)} className="text-green-600"><Check size={15} /></button>
                        <button onClick={() => setEditingId(null)} className="text-gray-400"><X size={15} /></button>
                      </div>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="px-4 py-2">{studentName(e.student_id)}</td>
                    <td className="px-4 py-2">{e.subject}</td>
                    <td className="px-4 py-2 text-gray-500">{e.test_date ?? "—"}</td>
                    <td className="px-4 py-2 text-gray-500">{e.week ?? "—"}</td>
                    <td className="px-4 py-2 font-medium">{e.score ?? "—"}</td>
                    <td className="px-4 py-2 text-gray-500">{e.total ?? "—"}</td>
                    <td className="px-4 py-2 text-gray-500 max-w-xs truncate">{e.notes ?? "—"}</td>
                    <td className="px-4 py-2">
                      <div className="flex gap-2">
                        <button onClick={() => { setEditingId(e.id); setEditForm({}); }} className="text-blue-500"><Pencil size={14} /></button>
                        <button onClick={() => handleDelete(e.id)} className="text-red-400"><Trash2 size={14} /></button>
                      </div>
                    </td>
                  </>
                )}
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">暂无记录</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
