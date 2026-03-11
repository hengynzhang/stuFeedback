"use client";
import { useEffect, useState, useCallback } from "react";
import { teacherApi, CourseSession, Student } from "@/lib/api";
import { Plus, Trash2, ChevronDown, ChevronUp } from "lucide-react";

const SUBJECTS = ["听力", "阅读", "写作", "口语", "数学", "早读"];
const DAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];

export default function RecordsPage() {
  const [sessions, setSessions] = useState<CourseSession[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  // 筛选
  const [filterWeek, setFilterWeek] = useState("");
  const [filterSubject, setFilterSubject] = useState("");
  const [filterType, setFilterType] = useState("");

  // 新建表单
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    record_type: "daily",
    date: "",
    day_of_week: "",
    week: "",
    subject: "",
    teacher_name: "",
    course_content: "",
  });
  const [performances, setPerformances] = useState<Record<number, string>>({});

  useEffect(() => {
    Promise.all([loadSessions(), teacherApi.getStudents().then(setStudents)]);
  }, []);

  const loadSessions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await teacherApi.getSessions({
        week: filterWeek || undefined,
        subject: filterSubject || undefined,
        record_type: filterType || undefined,
      });
      setSessions(data);
    } finally {
      setLoading(false);
    }
  }, [filterWeek, filterSubject, filterType]);

  useEffect(() => { loadSessions(); }, [loadSessions]);

  async function handleCreate() {
    if (!form.subject) return alert("请填写科目");
    try {
      const payload = {
        ...form,
        date: form.date || undefined,
        day_of_week: form.day_of_week || undefined,
        week: form.week || undefined,
        teacher_name: form.teacher_name || undefined,
        course_content: form.course_content || undefined,
        performances: students.map((s) => ({
          student_id: s.id,
          feedback: performances[s.id] || undefined,
        })),
      };
      const created = await teacherApi.createSession(payload);
      setSessions((prev) => [created, ...prev]);
      setShowForm(false);
      setForm({ record_type: "daily", date: "", day_of_week: "", week: "", subject: "", teacher_name: "", course_content: "" });
      setPerformances({});
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "创建失败");
    }
  }

  async function handleDeleteSession(id: number) {
    if (!confirm("确认删除该课程记录？")) return;
    await teacherApi.deleteSession(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
  }

  // 单元格失焦后自动保存
  async function handleFeedbackBlur(performanceId: number, value: string) {
    try {
      await teacherApi.updatePerformance(performanceId, value);
    } catch (e: unknown) {
      console.error("保存失败", e);
    }
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

      {/* 筛选栏 */}
      <div className="flex gap-3 mb-4">
        <input value={filterWeek} onChange={(e) => setFilterWeek(e.target.value)}
          placeholder="周次（如 Week 1）" className="border rounded-lg px-3 py-1.5 text-sm w-40" />
        <select value={filterSubject} onChange={(e) => setFilterSubject(e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">全部科目</option>
          {SUBJECTS.map((s) => <option key={s}>{s}</option>)}
        </select>
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">日/周均显示</option>
          <option value="daily">仅日录入</option>
          <option value="weekly">仅周录入</option>
        </select>
      </div>

      {/* 新建表单 */}
      {showForm && (
        <div className="bg-white border rounded-xl p-4 mb-4 shadow-sm">
          <h2 className="font-medium mb-3">新建课程记录</h2>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">录入粒度</label>
              <select value={form.record_type} onChange={(e) => setForm({ ...form, record_type: e.target.value })}
                className="border rounded px-2 py-1.5 text-sm w-full">
                <option value="daily">日录入</option>
                <option value="weekly">周录入</option>
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
              <label className="text-xs text-gray-500 mb-1 block">周次</label>
              <input value={form.week} onChange={(e) => setForm({ ...form, week: e.target.value })}
                placeholder="如 Week 1" className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
            {form.record_type === "daily" && (
              <>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">日期</label>
                  <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })}
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
              </>
            )}
            <div>
              <label className="text-xs text-gray-500 mb-1 block">授课教师</label>
              <input value={form.teacher_name} onChange={(e) => setForm({ ...form, teacher_name: e.target.value })}
                placeholder="教师姓名" className="border rounded px-2 py-1.5 text-sm w-full" />
            </div>
          </div>
          <div className="mb-3">
            <label className="text-xs text-gray-500 mb-1 block">课程内容</label>
            <textarea value={form.course_content} onChange={(e) => setForm({ ...form, course_content: e.target.value })}
              rows={2} className="border rounded px-2 py-1.5 text-sm w-full resize-none" />
          </div>

          {/* 各学生反馈 */}
          {students.length > 0 && (
            <div className="mb-3">
              <label className="text-xs text-gray-500 mb-2 block">各学生表现</label>
              <div className="grid gap-2">
                {students.map((s) => (
                  <div key={s.id} className="flex items-start gap-2">
                    <span className="text-sm w-24 pt-1.5 shrink-0 text-gray-700">{s.chinese_name}</span>
                    <textarea
                      rows={1}
                      value={performances[s.id] ?? ""}
                      onChange={(e) => setPerformances({ ...performances, [s.id]: e.target.value })}
                      className="border rounded px-2 py-1.5 text-sm flex-1 resize-none"
                      placeholder={`${s.chinese_name} 的课堂表现`}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <button onClick={handleCreate} className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700">
              保存
            </button>
            <button onClick={() => setShowForm(false)} className="text-gray-500 px-4 py-1.5 rounded-lg text-sm hover:bg-gray-100">
              取消
            </button>
          </div>
        </div>
      )}

      {/* 记录列表（折叠展开） */}
      {loading ? (
        <p className="text-gray-400">加载中…</p>
      ) : sessions.length === 0 ? (
        <p className="text-gray-400 py-8 text-center">暂无记录</p>
      ) : (
        <div className="space-y-2">
          {sessions.map((session) => (
            <div key={session.id} className="bg-white border rounded-xl overflow-hidden">
              {/* 行头：点击折叠/展开 */}
              <div
                className="flex items-center px-4 py-3 cursor-pointer hover:bg-gray-50 select-none"
                onClick={() => setExpandedId(expandedId === session.id ? null : session.id)}
              >
                <div className="flex-1 flex items-center gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    session.record_type === "daily" ? "bg-blue-50 text-blue-700" : "bg-purple-50 text-purple-700"
                  }`}>
                    {session.record_type === "daily" ? "日" : "周"}
                  </span>
                  <span className="font-medium">{session.subject}</span>
                  <span className="text-sm text-gray-500">
                    {session.date ?? session.week ?? "—"}
                    {session.day_of_week ? ` ${session.day_of_week}` : ""}
                  </span>
                  {session.teacher_name && (
                    <span className="text-sm text-gray-400">{session.teacher_name}</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={(e) => { e.stopPropagation(); handleDeleteSession(session.id); }}
                    className="text-red-400 hover:text-red-600 p-1">
                    <Trash2 size={14} />
                  </button>
                  {expandedId === session.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>
              </div>

              {/* 展开内容：学生反馈表格（行内编辑） */}
              {expandedId === session.id && (
                <div className="border-t px-4 py-3">
                  {session.course_content && (
                    <p className="text-sm text-gray-600 mb-3">
                      <span className="font-medium text-gray-500">课程内容：</span>{session.course_content}
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
                      {session.performances.map((p) => {
                        const stu = students.find((s) => s.id === p.student_id);
                        return (
                          <tr key={p.id} className="border-b last:border-0">
                            <td className="py-1.5 pr-3 text-gray-700 align-top pt-2.5">
                              {stu?.chinese_name ?? `#${p.student_id}`}
                            </td>
                            <td className="py-1.5">
                              <textarea
                                defaultValue={p.feedback ?? ""}
                                onBlur={(e) => handleFeedbackBlur(p.id, e.target.value)}
                                rows={2}
                                className="w-full border rounded px-2 py-1.5 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-300"
                                placeholder="暂无记录，点击填写"
                              />
                            </td>
                          </tr>
                        );
                      })}
                      {session.performances.length === 0 && (
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
