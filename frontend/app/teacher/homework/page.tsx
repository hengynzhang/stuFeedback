"use client";
import { useEffect, useState } from "react";
import { teacherApi, HomeworkAssignment, Student, Class } from "@/lib/api";
import { Plus, Trash2, ChevronDown, ChevronUp } from "lucide-react";

const SUBJECTS = ["听力", "阅读", "写作", "口语", "数学", "语文", "物理", "化学", "其他"];
const STATUS_OPTIONS = [
  { value: "completed",     label: "已完成" },
  { value: "partial",       label: "部分完成" },
  { value: "not_completed", label: "未完成" },
];
const STATUS_COLORS: Record<string, string> = {
  completed:     "bg-green-50 text-green-700",
  partial:       "bg-yellow-50 text-yellow-700",
  not_completed: "bg-red-50 text-red-600",
};

function getToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("teacher_token") ?? "";
}

export default function HomeworkPage() {
  const [assignments, setAssignments] = useState<HomeworkAssignment[]>([]);
  const [students, setStudents]       = useState<Student[]>([]);
  const [classes, setClasses]         = useState<Class[]>([]);
  const [loading, setLoading]         = useState(true);
  const [expandedId, setExpandedId]   = useState<number | null>(null);
  const [showForm, setShowForm]       = useState(false);
  const [filterClass, setFilterClass] = useState<number | "">("");

  const [form, setForm] = useState({
    class_id: "" as number | "", date: "", subject: "", homework: "",
  });
  const [completions, setCompletions] = useState<Record<number, string>>({});

  useEffect(() => {
    Promise.all([
      teacherApi.getHomework(getToken()).then(setAssignments),
      teacherApi.getStudents(getToken()).then(setStudents),
      teacherApi.getClasses(getToken()).then(setClasses),
    ]).finally(() => setLoading(false));
  }, []);

  const filtered = filterClass
    ? assignments.filter((a) => a.class_id === filterClass)
    : assignments;

  const classStudents = form.class_id
    ? students.filter((s) => s.class_id === form.class_id)
    : [];

  function studentName(id: number) {
    return students.find((s) => s.id === id)?.chinese_name ?? `#${id}`;
  }
  function className(class_id: number) {
    return classes.find((c) => c.id === class_id)?.name ?? `班级#${class_id}`;
  }

  async function handleCreate() {
    if (!form.class_id) return alert("请选择班级");
    if (!form.date)     return alert("请填写布置日期");
    if (!form.subject)  return alert("请选择科目");
    try {
      const created = await teacherApi.createHomework(getToken(), {
        class_id:    Number(form.class_id),
        date:        form.date,
        subject:     form.subject,
        homework:    form.homework || undefined,
        completions: classStudents.map((s) => ({
          student_id:        s.id,
          completion_status: completions[s.id] ?? "not_completed",
        })),
      });
      setAssignments((prev) => [created, ...prev]);
      setForm({ class_id: "", date: "", subject: "", homework: "" });
      setCompletions({});
      setShowForm(false);
    } catch (e: unknown) { alert(e instanceof Error ? e.message : "创建失败"); }
  }

  async function handleCompletionChange(completionId: number, status: string) {
    try {
      await teacherApi.updateCompletion(getToken(), completionId, status);
      setAssignments((prev) =>
        prev.map((a) => ({
          ...a,
          completions: a.completions.map((c) =>
            c.id === completionId
              ? { ...c, completion_status: status as HomeworkAssignment["completions"][0]["completion_status"] }
              : c
          ),
        }))
      );
    } catch (e) { console.error(e); }
  }

  async function handleDelete(id: number) {
    if (!confirm("确认删除？")) return;
    await teacherApi.deleteHomework(getToken(), id);
    setAssignments((prev) => prev.filter((a) => a.id !== id));
  }

  if (loading) return <p className="text-gray-400">加载中…</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold">作业记录</h1>
        <button onClick={() => setShowForm(true)}
          className="flex items-center gap-1 bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-blue-700">
          <Plus size={15} /> 新建作业
        </button>
      </div>

      {/* 筛选 */}
      <div className="flex gap-3 mb-4">
        <select value={filterClass} onChange={(e) => setFilterClass(e.target.value ? Number(e.target.value) : "")}
          className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">全部班级</option>
          {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>

      {/* 新建表单 */}
      {showForm && (
        <div className="bg-white border rounded-xl p-4 mb-4 shadow-sm">
          <h2 className="font-medium mb-3">新建作业记录</h2>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">班级 *</label>
              <select value={form.class_id}
                onChange={(e) => { setForm({ ...form, class_id: Number(e.target.value) }); setCompletions({}); }}
                className="border rounded px-2 py-1.5 text-sm w-full">
                <option value="">请选择</option>
                {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">布置日期 *</label>
              <input type="date" value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
                className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">科目 *</label>
              <select value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })}
                className="border rounded px-2 py-1.5 text-sm w-full">
                <option value="">请选择</option>
                {SUBJECTS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>
          </div>
          <div className="mb-3">
            <label className="text-xs text-gray-500 mb-1 block">作业内容</label>
            <textarea value={form.homework} onChange={(e) => setForm({ ...form, homework: e.target.value })}
              rows={2} className="border rounded px-2 py-1.5 text-sm w-full resize-none" />
          </div>

          {classStudents.length > 0 && (
            <div className="mb-3">
              <label className="text-xs text-gray-500 mb-2 block">各学生完成情况</label>
              <div className="grid gap-1.5">
                {classStudents.map((s) => (
                  <div key={s.id} className="flex items-center gap-3">
                    <span className="text-sm w-24 shrink-0">{s.chinese_name}</span>
                    <div className="flex gap-2">
                      {STATUS_OPTIONS.map((opt) => (
                        <button key={opt.value}
                          onClick={() => setCompletions({ ...completions, [s.id]: opt.value })}
                          className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                            (completions[s.id] ?? "not_completed") === opt.value
                              ? STATUS_COLORS[opt.value] + " border-transparent font-medium"
                              : "border-gray-200 text-gray-500 hover:border-gray-300"
                          }`}>
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <button onClick={handleCreate} className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700">保存</button>
            <button onClick={() => setShowForm(false)} className="text-gray-500 px-4 py-1.5 rounded-lg text-sm hover:bg-gray-100">取消</button>
          </div>
        </div>
      )}

      {/* 列表 */}
      <div className="space-y-2">
        {filtered.map((a) => (
          <div key={a.id} className="bg-white border rounded-xl overflow-hidden">
            <div className="flex items-center px-4 py-3 cursor-pointer hover:bg-gray-50 select-none"
              onClick={() => setExpandedId(expandedId === a.id ? null : a.id)}>
              <div className="flex-1 flex items-center gap-3 flex-wrap">
                <span className="font-medium">{a.subject}</span>
                <span className="text-sm text-gray-500">{className(a.class_id)}</span>
                <span className="text-sm text-gray-500">{a.date}</span>
                {a.homework && <span className="text-sm text-gray-400 truncate max-w-xs">{a.homework}</span>}
              </div>
              <div className="flex items-center gap-2">
                <button onClick={(e) => { e.stopPropagation(); handleDelete(a.id); }} className="text-red-400 hover:text-red-600 p-1">
                  <Trash2 size={14} />
                </button>
                {expandedId === a.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </div>
            </div>

            {expandedId === a.id && (
              <div className="border-t px-4 py-3">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left border-b">
                      <th className="pb-1 font-medium text-gray-500 w-28">学生</th>
                      <th className="pb-1 font-medium text-gray-500">完成情况（点击切换，自动保存）</th>
                    </tr>
                  </thead>
                  <tbody>
                    {a.completions.map((c) => (
                      <tr key={c.id} className="border-b last:border-0">
                        <td className="py-2 pr-3">{studentName(c.student_id)}</td>
                        <td className="py-2">
                          <div className="flex gap-2">
                            {STATUS_OPTIONS.map((opt) => (
                              <button key={opt.value}
                                onClick={() => handleCompletionChange(c.id, opt.value)}
                                className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                                  c.completion_status === opt.value
                                    ? STATUS_COLORS[opt.value] + " border-transparent font-medium"
                                    : "border-gray-200 text-gray-500 hover:border-gray-300"
                                }`}>
                                {opt.label}
                              </button>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
        {filtered.length === 0 && <p className="text-gray-400 py-8 text-center">暂无记录</p>}
      </div>
    </div>
  );
}
