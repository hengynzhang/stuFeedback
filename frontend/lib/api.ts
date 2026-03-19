/**
 * API 客户端 v3
 * - 教师端：JWT Bearer token（localStorage: teacher_token）
 * - 家长/学生端：session_token（localStorage: session_token）
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

// ── 通用请求 ────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "请求失败");
  }
  return res.json();
}

// ── 类型定义 ────────────────────────────────────────────────

export interface Teacher {
  id: number;
  phone: string;
  name: string;
  created_at: string;
}

export interface Class {
  id: number;
  name: string;
  subject: string;
  teacher_id: number;
  start_date?: string;
  end_date?: string;
  total_lessons: number;
  status: "active" | "completed";
  completed_lessons: number;
  remaining_lessons: number;
  student_count: number;
  created_at: string;
}

export interface Student {
  id: number;
  student_id: string;
  chinese_name: string;
  english_name?: string;
  class_id: number;
  created_at: string;
}

export interface LessonPerformance {
  id: number;
  lesson_record_id: number;
  student_id: number;
  feedback?: string;
  updated_at: string;
}

export interface LessonRecord {
  id: number;
  class_id: number;
  lesson_date: string;
  lesson_start_time?: string;
  lesson_end_time?: string;
  topic?: string;
  content_notes?: string;
  status: "completed" | "cancelled" | "makeup";
  performances: LessonPerformance[];
  created_at: string;
}

export interface ExamRecord {
  id: number;
  student_id: number;
  test_date?: string;
  test_number?: number;
  subject: string;
  score?: number;
  total?: number;
  notes?: string;
  created_at: string;
}

export interface HomeworkCompletion {
  id: number;
  homework_assignment_id: number;
  student_id: number;
  completion_status: "completed" | "partial" | "not_completed";
  updated_at: string;
}

export interface HomeworkAssignment {
  id: number;
  class_id: number;
  date: string;
  subject: string;
  homework?: string;
  completions: HomeworkCompletion[];
  created_at: string;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  created_at: string;
  messages: Message[];
}

// ── 教师认证 API ─────────────────────────────────────────────

export const teacherAuthApi = {
  sendCode: (phone: string) =>
    request<{ message: string; code?: string }>("/auth/teacher/send-code", {
      method: "POST",
      body: JSON.stringify({ phone }),
    }),

  register: (data: { phone: string; code: string; name: string; password: string }) =>
    request<{ access_token: string; token_type: string; teacher_id: number; name: string }>(
      "/auth/teacher/register",
      { method: "POST", body: JSON.stringify(data) }
    ),

  login: (phone: string, password: string) =>
    request<{ access_token: string; token_type: string; teacher_id: number; name: string }>(
      "/auth/teacher/login",
      { method: "POST", body: JSON.stringify({ phone, password }) }
    ),
};

// ── 教师端 API ─────────────────────────────────────────────

export const teacherApi = {
  // 班级
  getClasses: (token: string) =>
    request<Class[]>("/teacher/classes", {}, token),
  createClass: (token: string, data: Partial<Class>) =>
    request<Class>("/teacher/classes", { method: "POST", body: JSON.stringify(data) }, token),
  updateClass: (token: string, id: number, data: Partial<Class>) =>
    request<Class>(`/teacher/classes/${id}`, { method: "PUT", body: JSON.stringify(data) }, token),
  deleteClass: (token: string, id: number) =>
    request(`/teacher/classes/${id}`, { method: "DELETE" }, token),

  // 学生
  getStudents: (token: string, params?: { class_id?: number }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<Student[]>(`/teacher/students${q ? `?${q}` : ""}`, {}, token);
  },
  createStudent: (token: string, data: { chinese_name: string; english_name?: string; class_id: number }) =>
    request<Student>("/teacher/students", { method: "POST", body: JSON.stringify(data) }, token),
  updateStudent: (token: string, id: number, data: Partial<Student>) =>
    request<Student>(`/teacher/students/${id}`, { method: "PUT", body: JSON.stringify(data) }, token),
  deleteStudent: (token: string, id: number) =>
    request(`/teacher/students/${id}`, { method: "DELETE" }, token),

  // 课程记录
  getLessons: (token: string, params?: { class_id?: number }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<LessonRecord[]>(`/teacher/lessons${q ? `?${q}` : ""}`, {}, token);
  },
  createLesson: (
    token: string,
    data: Partial<LessonRecord> & { class_id: number; lesson_date: string; performances: { student_id: number; feedback?: string }[] }
  ) => request<LessonRecord>("/teacher/lessons", { method: "POST", body: JSON.stringify(data) }, token),
  updateLesson: (token: string, id: number, data: Partial<LessonRecord>) =>
    request<LessonRecord>(`/teacher/lessons/${id}`, { method: "PUT", body: JSON.stringify(data) }, token),
  deleteLesson: (token: string, id: number) =>
    request(`/teacher/lessons/${id}`, { method: "DELETE" }, token),
  updatePerformance: (token: string, id: number, feedback: string) =>
    request<LessonPerformance>(`/teacher/performances/${id}`, {
      method: "PUT",
      body: JSON.stringify({ feedback }),
    }, token),

  // 考试记录
  getExams: (token: string, params?: { class_id?: number; student_id?: number; subject?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<ExamRecord[]>(`/teacher/exams${q ? `?${q}` : ""}`, {}, token);
  },
  createExam: (token: string, data: Partial<ExamRecord>) =>
    request<ExamRecord>("/teacher/exams", { method: "POST", body: JSON.stringify(data) }, token),
  updateExam: (token: string, id: number, data: Partial<ExamRecord>) =>
    request<ExamRecord>(`/teacher/exams/${id}`, { method: "PUT", body: JSON.stringify(data) }, token),
  deleteExam: (token: string, id: number) =>
    request(`/teacher/exams/${id}`, { method: "DELETE" }, token),

  // 作业记录
  getHomework: (token: string, params?: { class_id?: number; subject?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<HomeworkAssignment[]>(`/teacher/homework${q ? `?${q}` : ""}`, {}, token);
  },
  createHomework: (
    token: string,
    data: { class_id: number; date: string; subject: string; homework?: string; completions: { student_id: number; completion_status: string }[] }
  ) => request<HomeworkAssignment>("/teacher/homework", { method: "POST", body: JSON.stringify(data) }, token),
  updateHomework: (token: string, id: number, data: Partial<HomeworkAssignment>) =>
    request<HomeworkAssignment>(`/teacher/homework/${id}`, { method: "PUT", body: JSON.stringify(data) }, token),
  deleteHomework: (token: string, id: number) =>
    request(`/teacher/homework/${id}`, { method: "DELETE" }, token),
  updateCompletion: (token: string, id: number, status: string) =>
    request<HomeworkCompletion>(`/teacher/completions/${id}`, {
      method: "PUT",
      body: JSON.stringify({ completion_status: status }),
    }, token),
};

// ── 家长/学生端 API ─────────────────────────────────────────

export const authApi = {
  login: (student_id: string) =>
    request<{ session_token: string; student_name: string; student_id: string }>(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ student_id }) }
    ),
};

export const parentApi = {
  getMe: (token: string) => request<Student>("/parent/me", {}, token),
  getPerformance: (token: string, params?: { subject?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<LessonRecord[]>(`/parent/performance${q ? `?${q}` : ""}`, {}, token);
  },
  getExams: (token: string, params?: { subject?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<ExamRecord[]>(`/parent/exams${q ? `?${q}` : ""}`, {}, token);
  },
  getHomework: (token: string, params?: { subject?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<HomeworkAssignment[]>(`/parent/homework${q ? `?${q}` : ""}`, {}, token);
  },
};

export const chatApi = {
  newConversation: (token: string) =>
    request<Conversation>("/chat/conversations", { method: "POST" }, token),
  getConversations: (token: string) =>
    request<Conversation[]>("/chat/conversations", {}, token),
  getConversation: (token: string, id: number) =>
    request<Conversation>(`/chat/conversations/${id}`, {}, token),
  sendMessage: (token: string, conversationId: number, content: string) =>
    request<{ message_id: number; content: string; conversation_id: number }>(
      `/chat/conversations/${conversationId}/messages`,
      { method: "POST", body: JSON.stringify({ content }) },
      token
    ),
};
