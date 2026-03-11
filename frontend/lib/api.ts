/**
 * API 客户端
 * 统一管理后端请求，自动附加 Authorization header（家长端）
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

export interface Student {
  id: number;
  student_id: string;
  chinese_name: string;
  english_name?: string;
  created_at: string;
}

export interface StudentPerformance {
  id: number;
  course_session_id: number;
  student_id: number;
  feedback?: string;
  updated_at: string;
}

export interface CourseSession {
  id: number;
  record_type: "daily" | "weekly";
  date?: string;
  day_of_week?: string;
  week?: string;
  subject: string;
  teacher_name?: string;
  course_content?: string;
  performances: StudentPerformance[];
  created_at: string;
}

export interface ExamRecord {
  id: number;
  student_id: number;
  test_date?: string;
  day_of_week?: string;
  week?: string;
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
  record_type: "daily" | "weekly";
  date?: string;
  day_of_week?: string;
  week?: string;
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

// ── 教师端 API ─────────────────────────────────────────────

export const teacherApi = {
  // 学生
  getStudents: () => request<Student[]>("/teacher/students"),
  createStudent: (data: { chinese_name: string; english_name?: string }) =>
    request<Student>("/teacher/students", { method: "POST", body: JSON.stringify(data) }),
  updateStudent: (id: number, data: { chinese_name?: string; english_name?: string }) =>
    request<Student>(`/teacher/students/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteStudent: (id: number) =>
    request(`/teacher/students/${id}`, { method: "DELETE" }),

  // 课程记录
  getSessions: (params?: { week?: string; subject?: string; record_type?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<CourseSession[]>(`/teacher/sessions${q ? `?${q}` : ""}`);
  },
  createSession: (data: Partial<CourseSession> & { performances: { student_id: number; feedback?: string }[] }) =>
    request<CourseSession>("/teacher/sessions", { method: "POST", body: JSON.stringify(data) }),
  updateSession: (id: number, data: Partial<CourseSession>) =>
    request<CourseSession>(`/teacher/sessions/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteSession: (id: number) =>
    request(`/teacher/sessions/${id}`, { method: "DELETE" }),
  updatePerformance: (id: number, feedback: string) =>
    request<StudentPerformance>(`/teacher/performances/${id}`, {
      method: "PUT",
      body: JSON.stringify({ feedback }),
    }),

  // 考试记录
  getExams: (params?: { student_id?: number; subject?: string; week?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<ExamRecord[]>(`/teacher/exams${q ? `?${q}` : ""}`);
  },
  createExam: (data: Partial<ExamRecord>) =>
    request<ExamRecord>("/teacher/exams", { method: "POST", body: JSON.stringify(data) }),
  updateExam: (id: number, data: Partial<ExamRecord>) =>
    request<ExamRecord>(`/teacher/exams/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteExam: (id: number) =>
    request(`/teacher/exams/${id}`, { method: "DELETE" }),

  // 作业记录
  getHomework: (params?: { week?: string; subject?: string; record_type?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<HomeworkAssignment[]>(`/teacher/homework${q ? `?${q}` : ""}`);
  },
  createHomework: (data: Partial<HomeworkAssignment> & { completions: { student_id: number; completion_status: string }[] }) =>
    request<HomeworkAssignment>("/teacher/homework", { method: "POST", body: JSON.stringify(data) }),
  updateHomework: (id: number, data: Partial<HomeworkAssignment>) =>
    request<HomeworkAssignment>(`/teacher/homework/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteHomework: (id: number) =>
    request(`/teacher/homework/${id}`, { method: "DELETE" }),
  updateCompletion: (id: number, status: string) =>
    request<HomeworkCompletion>(`/teacher/completions/${id}`, {
      method: "PUT",
      body: JSON.stringify({ completion_status: status }),
    }),
};

// ── 家长端 API ─────────────────────────────────────────────

export const authApi = {
  login: (student_id: string) =>
    request<{ session_token: string; student_name: string; student_id: string }>(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ student_id }) }
    ),
};

export const parentApi = {
  getMe: (token: string) => request<Student>("/parent/me", {}, token),
  getPerformance: (token: string, params?: { week?: string; subject?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<CourseSession[]>(`/parent/performance${q ? `?${q}` : ""}`, {}, token);
  },
  getExams: (token: string, params?: { subject?: string; week?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<ExamRecord[]>(`/parent/exams${q ? `?${q}` : ""}`, {}, token);
  },
  getHomework: (token: string, params?: { week?: string; subject?: string }) => {
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
