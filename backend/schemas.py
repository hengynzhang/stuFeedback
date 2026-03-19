"""
Pydantic 数据校验模型 v3
分组：Teacher Auth / Class / Student / LessonRecord / ExamRecord / Homework / Parent Auth / Chat
"""

from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, datetime
import re


# ─────────────────────────────────────────────
# 教师认证
# ─────────────────────────────────────────────

class SendCodeRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v

class SendCodeResponse(BaseModel):
    message: str
    code: Optional[str] = None   # Mock 模式下返回，生产环境去掉

class RegisterRequest(BaseModel):
    phone: str
    code: str
    name: str
    password: str

class TeacherLoginRequest(BaseModel):
    phone: str
    password: str

class TeacherLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    teacher_id: int
    name: str

class TeacherResponse(BaseModel):
    id: int
    phone: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# 班级
# ─────────────────────────────────────────────

class ClassCreate(BaseModel):
    name: str
    subject: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_lessons: int = 0

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_lessons: Optional[int] = None
    status: Optional[str] = None

class ClassResponse(BaseModel):
    id: int
    name: str
    subject: str
    teacher_id: int
    start_date: Optional[date]
    end_date: Optional[date]
    total_lessons: int
    status: str
    completed_lessons: int = 0   # 计算字段：已上课时
    remaining_lessons: int = 0   # 计算字段：剩余课时
    student_count: int = 0        # 计算字段：在班学员数
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# 学生
# ─────────────────────────────────────────────

class StudentCreate(BaseModel):
    chinese_name: str
    english_name: Optional[str] = None
    class_id: int

class StudentUpdate(BaseModel):
    chinese_name: Optional[str] = None
    english_name: Optional[str] = None
    class_id: Optional[int] = None

class StudentResponse(BaseModel):
    id: int
    student_id: str
    chinese_name: str
    english_name: Optional[str]
    class_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# 课程记录（单节课）
# ─────────────────────────────────────────────

class LessonPerformanceCreate(BaseModel):
    student_id: int
    feedback: Optional[str] = None

class LessonPerformanceUpdate(BaseModel):
    feedback: Optional[str] = None

class LessonPerformanceResponse(BaseModel):
    id: int
    lesson_record_id: int
    student_id: int
    feedback: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True

class LessonRecordCreate(BaseModel):
    class_id: int
    lesson_date: date
    lesson_start_time: Optional[str] = None   # "14:00"
    lesson_end_time: Optional[str] = None     # "16:00"
    topic: Optional[str] = None
    content_notes: Optional[str] = None
    status: str = "completed"
    performances: List[LessonPerformanceCreate] = []

class LessonRecordUpdate(BaseModel):
    lesson_date: Optional[date] = None
    lesson_start_time: Optional[str] = None
    lesson_end_time: Optional[str] = None
    topic: Optional[str] = None
    content_notes: Optional[str] = None
    status: Optional[str] = None

class LessonRecordResponse(BaseModel):
    id: int
    class_id: int
    lesson_date: date
    lesson_start_time: Optional[str]
    lesson_end_time: Optional[str]
    topic: Optional[str]
    content_notes: Optional[str]
    status: str
    performances: List[LessonPerformanceResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# 考试记录
# ─────────────────────────────────────────────

class ExamRecordCreate(BaseModel):
    student_id: int
    test_date: Optional[date] = None
    test_number: Optional[int] = None
    subject: str
    score: Optional[float] = None
    total: Optional[float] = None
    notes: Optional[str] = None

class ExamRecordUpdate(BaseModel):
    test_date: Optional[date] = None
    test_number: Optional[int] = None
    subject: Optional[str] = None
    score: Optional[float] = None
    total: Optional[float] = None
    notes: Optional[str] = None

class ExamRecordResponse(BaseModel):
    id: int
    student_id: int
    test_date: Optional[date]
    test_number: Optional[int]
    subject: str
    score: Optional[float]
    total: Optional[float]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# 作业（班级维度布置，学生维度完成）
# ─────────────────────────────────────────────

class HomeworkCompletionCreate(BaseModel):
    student_id: int
    completion_status: str = "not_completed"

class HomeworkCompletionUpdate(BaseModel):
    completion_status: str

class HomeworkCompletionResponse(BaseModel):
    id: int
    homework_assignment_id: int
    student_id: int
    completion_status: str
    updated_at: datetime

    class Config:
        from_attributes = True

class HomeworkAssignmentCreate(BaseModel):
    class_id: int
    date: date
    subject: str
    homework: Optional[str] = None
    completions: List[HomeworkCompletionCreate] = []

class HomeworkAssignmentUpdate(BaseModel):
    date: Optional[date] = None
    subject: Optional[str] = None
    homework: Optional[str] = None

class HomeworkAssignmentResponse(BaseModel):
    id: int
    class_id: int
    date: date
    subject: str
    homework: Optional[str]
    completions: List[HomeworkCompletionResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# 家长/学生端认证
# ─────────────────────────────────────────────

class ParentLoginRequest(BaseModel):
    student_id: str   # 8 位学号

class ParentLoginResponse(BaseModel):
    session_token: str
    student_name: str
    student_id: str


# ─────────────────────────────────────────────
# Chat（家长/学生端）
# ─────────────────────────────────────────────

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: int
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    message_id: int
    content: str
    conversation_id: int


# ─────────────────────────────────────────────
# Chat（教师端）
# ─────────────────────────────────────────────

class TeacherConversationResponse(BaseModel):
    id: int
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class TeacherChatResponse(BaseModel):
    message_id: int
    content: str
    conversation_id: int
