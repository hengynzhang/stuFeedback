"use client";
import { useEffect, useState, useCallback } from "react";
import { teacherApi, LessonRecord, Student, Class } from "@/lib/api";
import { Plus, Trash2, ChevronDown, ChevronUp } from "lucide-react";

const STATUS_LABELS = { completed: "已上课", cancelled: "已取消", makeup: "补课" };
const STATUS_COLORS = {
  completed: "bg-green-50 text-green-700",
  cancelled: "bg-red-50 text-red-600",
  makeup:    "bg-yellow-50 text-yellow-700",
};

function getToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("teacher_token") ?? "";
}

export default function RecordsPage() {
  const [lessons, setLessons]   = useState<LessonRecord[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [classes, setClasses]   = useState<Class[]>([]);
  const [loading, setLoading]   = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const [filterClass, setFilterClass] = useState<number | "">("");

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    class_id: "" as number | "",
    lesson_date: "",
    lesson_start_time: "",
    lesson_end_time: "",
    topic: "",
    content_notes: "",
    status: "completed",
  });
  const [performances, setPerformances] = useState<Record<number, string>>({});

  useEffect(() => {
    Promise.all([
      teacherApi.getClasses(getToken()).then(setClasses),
      teacherApi.getStudents(getToken()).then(setStudents),
    ]);
  }, []);

  const loadLessons = useCallback(async () => {
    setLoading(true);
    try {
      const data = await teacherApi.getLessons(
        getToken(),
        filterClass ? { class_id: filterClass as number } : undefined
      );
      setLessons(data);
    } finally { setLoading(false); }
  }, [filterClass]);

  useEffect(() => { loadLessons(); }, [loadLessons]);

  // 当前班级下的学生
  const classStudents = form.class_id
    ? students.filter((s) => s.class_id === form.class_id)
    : [];

  function className(class_id: number) {
    return classes.find((c) => c.id === class_id)?.name ?? `班级#${class_id}`;
  }
  function subjectName(class_id: number) {
    return classes.find((c) => c.id === class_id)?.subject ?? "";
  }

  async function handleCreate() {
    if (!form.class_id) return alert("请选择班级");
    if (!form.lesson_date) return alert("请填写上课日期");
    try {
      const created = await teacherApi.createLesson(getToken(), {
        class_id:          Number(form.class_id),
        lesson_date:       form.lesson_date,
        lesson_start_time: form.lesson_start_time || undefined,
        lesson_end_time:   form.lesson_end_time   || undefined,
        topic:             form.topic             || undefined,
        content_notes:     form.content_notes     || undefined,
        status:            form.status as LessonRecord["status"],
        performances: classStudents.map((s) => ({
          student_id: s.id,
          feedback:   performances[s.id] || undefined,
        })),
      });
      setLessons((prev) => [created, ...prev]);
      setShowForm(false);
      setForm({ class_id: "", lesson_date: "", lesson_start_time: "", lesson_end_time: "", topic: "", content_notes: "", status: "completed" });
      setPerformances({});
    } catch (e: unknown) { alert(e instanceof Error ? e.message : "创建失败"); }
  }

  async function handleDeleteLesson(id: number) {
    if (!confirm("确认删除该课程记录？")) return;
    await teacherApi.deleteLesson(getToken(), id);
    setLessons((prev) => prev.filter((l) => l.id !== id));
  }

  async function handleFeedbackBlur(performanceId: number, value: string) {
    try { await teacherApi.updatePerformance(getToken(), performanceId, value); }
    catch (e) { console.error("保存失败", e); }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold">课程记录</h1>
        <button onClick={() => setShowForm(true)}
          className="flex items-center gap-1 bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-blue-700">
          <Plus size={15} /> 新建课程记录
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
          <h2 className="font-medium mb-3">新建课程记录</h2>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">班级 *</label>
              <select value={form.class_id}
                onChange={(e) => { setForm({ ...form, class_id: Number(e.target.value) }); setPerformances({}); }}
                className="border rounded px-2 py-1.5 text-sm w-full">
                <option value="">请选择</option>
                {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">上课日期 *</label>
              <input type="date" value={form.lesson_date}
                onChange={(e) => setForm({ ...form, lesson_date: e.target.value })}
                className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">状态</label>
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}
                className="border rounded px-2 py-1.5 text-sm w-full">
                <option value="completed">已上课</option>
                <option value="cancelled">已取消</option>
                <option value="makeup">补课</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">上课时间（开始）</label>
              <input type="time" value={form.lesson_start_time}
                onChange={(e) => setForm({ ...form, lesson_start_time: e.target.value })}
                className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">上课时间（结束）</label>
              <input type="time" value={form.lesson_end_time}
                onChange={(e) => setForm({ ...form, lesson_end_time: e.target.value })}
                className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">课程主题</label>
              <input value={form.topic} onChange={(e) => setForm({ ...form, topic: e.target.value })}
                placeholder="本节课主题" className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
          </div>
          <div className="mb-3">
            <label className="text-xs text-gray-500 mb-1 block">课程内容</label>
            <textarea value={form.content_notes} onChange={(e) => setForm({ ...form, content_notes: e.target.value })}
              rows={2} className="border rounded px-2 py-1.5 text-sm w-full resize-none" />
          </div>

          {classStudents.length > 0 && (
            <div className="mb-3">
              <label className="text-xs text-gray-500 mb-2 block">各学生课堂表现</label>
              <div className="grid gap-2">
                {classStudents.map((s) => (
                  <div key={s.id} className="flex items-start gap-2">
                    <span className="text-sm w-24 pt-1.5 shrink-0 text-gray-700">{s.chinese_name}</span>
                    <textarea rows={1} value={performances[s.id] ?? ""}
                      onChange={(e) => setPerformances({ ...performances, [s.id]: e.target.value })}
                      className="border rounded px-2 py-1.5 text-sm flex-1 resize-none"
                      placeholder={`${s.chinese_name} 的课堂表现`} />
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

      {/* 记录列表 */}
      {loading ? <p className="text-gray-400">加载中…</p>
        : lessons.length === 0 ? <p className="text-gray-400 py-8 text-center">暂无记录</p>
        : (
          <div className="space-y-2">
            {lessons.map((lesson) => (
              <div key={lesson.id} className="bg-white border rounded-xl overflow-hidden">
                <div className="flex items-center px-4 py-3 cursor-pointer hover:bg-gray-50 select-none"
                  onClick={() => setExpandedId(expandedId === lesson.id ? null : lesson.id)}>
                  <div className="flex-1 flex items-center gap-3 flex-wrap">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[lesson.status]}`}>
                      {STATUS_LABELS[lesson.status]}
                    </span>
                    <span className="font-medium">{subjectName(lesson.class_id)}</span>
                    <span className="text-sm text-gray-500">{className(lesson.class_id)}</span>
                    <span className="text-sm text-gray-500">
                      {lesson.lesson_date}
                      {lesson.lesson_start_time && ` ${lesson.lesson_start_time}`}
                      {lesson.lesson_end_time && `–${lesson.lesson_end_time}`}
                    </span>
                    {lesson.topic && <span className="text-sm text-gray-400 truncate max-w-xs">{lesson.topic}</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={(e) => { e.stopPropagation(); handleDeleteLesson(lesson.id); }}
                      className="text-red-400 hover:text-red-600 p-1"><Trash2 size={14} /></button>
                    {expandedId === lesson.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </div>
                </div>

                {expandedId === lesson.id && (
                  <div className="border-t px-4 py-3">
                    {lesson.content_notes && (
                      <p className="text-sm text-gray-600 mb-3">
                        <span className="font-medium text-gray-500">课程内容：</span>{lesson.content_notes}
                      </p>
                    )}
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left border-b">
                          <th className="pb-1 font-medium text-gray-500 w-24">学生</th>
                          <th className="pb-1 font-medium text-gray-500">课堂表现（点击编辑，失焦自动保存）</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lesson.performances.map((p) => {
                          const stu = students.find((s) => s.id === p.student_id);
                          return (
                            <tr key={p.id} className="border-b last:border-0">
                              <td className="py-1.5 pr-3 text-gray-700 align-top pt-2.5">
                                {stu?.chinese_name ?? `#${p.student_id}`}
                              </td>
                              <td className="py-1.5">
                                <textarea defaultValue={p.feedback ?? ""}
                                  onBlur={(e) => handleFeedbackBlur(p.id, e.target.value)}
                                  rows={2}
                                  className="w-full border rounded px-2 py-1.5 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-300"
                                  placeholder="暂无记录，点击填写" />
                              </td>
                            </tr>
                          );
                        })}
                        {lesson.performances.length === 0 && (
                          <tr><td colSpan={2} className="py-3 text-gray-400 text-center">无学生反馈记录</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
    </div>
  );
}
