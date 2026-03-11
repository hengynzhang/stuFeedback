"""
Pydantic 数据校验模型
分为：Auth / Teacher / Parent / Chat 四组
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    student_id: str  # 8位学号

class LoginResponse(BaseModel):
    session_token: str
    student_name: str
    student_id: str


# ─────────────────────────────────────────────
# Student
# ─────────────────────────────────────────────

class StudentCreate(BaseModel):
    chinese_name: str
    english_name: Optional[str] = None

class StudentUpdate(BaseModel):
    chinese_name: Optional[str] = None
    english_name: Optional[str] = None

class StudentResponse(BaseModel):
    id: int
    student_id: str
    chinese_name: str
    english_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# CourseSession + StudentPerformance
# ─────────────────────────────────────────────

class StudentPerformanceCreate(BaseModel):
    student_id: int
    feedback: Optional[str] = None

class StudentPerformanceUpdate(BaseModel):
    feedback: Optional[str] = None

class StudentPerformanceResponse(BaseModel):
    id: int
    course_session_id: int
    student_id: int
    feedback: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True

class CourseSessionCreate(BaseModel):
    record_type: str = "daily"           # 'daily' | 'weekly'
    date: Optional[date] = None          # 日录入时必填
    day_of_week: Optional[str] = None
    week: Optional[str] = None           # 两种粒度都应填写
    subject: str
    teacher_name: Optional[str] = None
    course_content: Optional[str] = None
    performances: List[StudentPerformanceCreate] = []

class CourseSessionUpdate(BaseModel):
    date: Optional[date] = None
    day_of_week: Optional[str] = None
    week: Optional[str] = None
    subject: Optional[str] = None
    teacher_name: Optional[str] = None
    course_content: Optional[str] = None

class CourseSessionResponse(BaseModel):
    id: int
    record_type: str
    date: Optional[date]
    day_of_week: Optional[str]
    week: Optional[str]
    subject: str
    teacher_name: Optional[str]
    course_content: Optional[str]
    performances: List[StudentPerformanceResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# ExamRecord
# ─────────────────────────────────────────────

class ExamRecordCreate(BaseModel):
    student_id: int
    test_date: Optional[date] = None
    day_of_week: Optional[str] = None
    week: Optional[str] = None
    test_number: Optional[int] = None
    subject: str
    score: Optional[float] = None
    total: Optional[float] = None
    notes: Optional[str] = None

class ExamRecordUpdate(BaseModel):
    test_date: Optional[date] = None
    day_of_week: Optional[str] = None
    week: Optional[str] = None
    test_number: Optional[int] = None
    subject: Optional[str] = None
    score: Optional[float] = None
    total: Optional[float] = None
    notes: Optional[str] = None

class ExamRecordResponse(BaseModel):
    id: int
    student_id: int
    test_date: Optional[date]
    day_of_week: Optional[str]
    week: Optional[str]
    test_number: Optional[int]
    subject: str
    score: Optional[float]
    total: Optional[float]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# HomeworkAssignment + HomeworkCompletion
# ─────────────────────────────────────────────

class HomeworkCompletionCreate(BaseModel):
    student_id: int
    completion_status: str = "not_completed"  # completed / partial / not_completed

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
    record_type: str = "daily"           # 'daily' | 'weekly'
    date: Optional[date] = None
    day_of_week: Optional[str] = None
    week: Optional[str] = None
    subject: str
    homework: Optional[str] = None
    completions: List[HomeworkCompletionCreate] = []

class HomeworkAssignmentUpdate(BaseModel):
    date: Optional[date] = None
    day_of_week: Optional[str] = None
    week: Optional[str] = None
    subject: Optional[str] = None
    homework: Optional[str] = None

class HomeworkAssignmentResponse(BaseModel):
    id: int
    record_type: str
    date: Optional[date]
    day_of_week: Optional[str]
    week: Optional[str]
    subject: str
    homework: Optional[str]
    completions: List[HomeworkCompletionResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# Chat
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
