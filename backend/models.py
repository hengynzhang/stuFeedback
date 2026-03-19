"""
数据库模型模块 v3
包含：
  认证层：Teacher / SMSVerification
  核心数据：Class / Student / LessonRecord / LessonPerformance
  考试/作业：ExamRecord / HomeworkAssignment / HomeworkCompletion
  家长对话：Parent / Conversation / Message / ConversationMemory
  教师对话：TeacherConversation / TeacherMessage
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


# ─────────────────────────────────────────────
# 教师认证
# ─────────────────────────────────────────────

class Teacher(Base):
    """教师表 - 通过手机号+密码登录，JWT 认证"""
    __tablename__ = "teachers"

    id             = Column(Integer, primary_key=True, index=True)
    phone          = Column(String(11), nullable=False, unique=True, index=True)
    password_hash  = Column(String(256), nullable=False)
    name           = Column(String(50), nullable=False)
    created_at     = Column(DateTime, default=datetime.now)

    classes        = relationship("Class", back_populates="teacher")
    conversations  = relationship("TeacherConversation", back_populates="teacher", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Teacher(id={self.id}, phone={self.phone}, name={self.name})>"


class SMSVerification(Base):
    """短信验证码表 - 当前为 Mock 模式"""
    __tablename__ = "sms_verifications"

    id         = Column(Integer, primary_key=True, index=True)
    phone      = Column(String(11), nullable=False, index=True)
    code       = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used    = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<SMSVerification(phone={self.phone}, code={self.code})>"


# ─────────────────────────────────────────────
# 班级
# ─────────────────────────────────────────────

class Class(Base):
    """
    班级表
    - total_lessons：开班时预设，各班可不同
    - completed_lessons / remaining_lessons 为计算字段，由 LessonRecord 数量派生，不存储
    """
    __tablename__ = "classes"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    subject       = Column(String(50), nullable=False)
    teacher_id    = Column(Integer, ForeignKey("teachers.id"), nullable=False, index=True)
    start_date    = Column(Date, nullable=True)
    end_date      = Column(Date, nullable=True)
    total_lessons = Column(Integer, nullable=False, default=0)
    status        = Column(String(20), nullable=False, default="active")  # active / completed
    created_at    = Column(DateTime, default=datetime.now)
    updated_at    = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    teacher              = relationship("Teacher", back_populates="classes")
    students             = relationship("Student", back_populates="class_", cascade="all, delete-orphan")
    lesson_records       = relationship("LessonRecord", back_populates="class_", cascade="all, delete-orphan")
    homework_assignments = relationship("HomeworkAssignment", back_populates="class_", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Class(id={self.id}, name={self.name}, subject={self.subject})>"


# ─────────────────────────────────────────────
# 学生
# ─────────────────────────────────────────────

class Student(Base):
    """
    学生表
    - student_id：系统自动生成的 8 位学号，供家长/学生登录使用
    - class_id：必须归属一个班级（强绑定，一生一班）
    """
    __tablename__ = "students"

    id           = Column(Integer, primary_key=True, index=True)
    student_id   = Column(String(8), nullable=False, unique=True, index=True)
    chinese_name = Column(String(50), nullable=False, index=True)
    english_name = Column(String(50), nullable=True)
    class_id     = Column(Integer, ForeignKey("classes.id"), nullable=False, index=True)
    created_at   = Column(DateTime, default=datetime.now)
    updated_at   = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    class_               = relationship("Class", back_populates="students")
    exam_records         = relationship("ExamRecord", back_populates="student", cascade="all, delete-orphan")
    homework_completions = relationship("HomeworkCompletion", back_populates="student", cascade="all, delete-orphan")
    lesson_performances  = relationship("LessonPerformance", back_populates="student", cascade="all, delete-orphan")
    parent               = relationship("Parent", back_populates="student", uselist=False, cascade="all, delete-orphan")
    conversation_memory  = relationship("ConversationMemory", back_populates="student", uselist=False, cascade="all, delete-orphan")

    @property
    def full_name(self):
        if self.english_name:
            return f"{self.chinese_name} {self.english_name}"
        return self.chinese_name

    def __repr__(self):
        return f"<Student(student_id={self.student_id}, name={self.chinese_name})>"


# ─────────────────────────────────────────────
# 课程记录（单节课粒度，取代原 CourseSession）
# ─────────────────────────────────────────────

class LessonRecord(Base):
    """
    单节课程记录表 - 每行对应一次实际上课
    所有记录以单节课为粒度，不再区分 daily/weekly
    """
    __tablename__ = "lesson_records"

    id                = Column(Integer, primary_key=True, index=True)
    class_id          = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_date       = Column(Date, nullable=False, index=True)
    lesson_start_time = Column(String(10), nullable=True)   # 如 "14:00"
    lesson_end_time   = Column(String(10), nullable=True)   # 如 "16:00"
    topic             = Column(String(200), nullable=True)
    content_notes     = Column(Text, nullable=True)
    status            = Column(String(20), nullable=False, default="completed")  # completed / cancelled / makeup
    created_at        = Column(DateTime, default=datetime.now)
    updated_at        = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    class_       = relationship("Class", back_populates="lesson_records")
    performances = relationship("LessonPerformance", back_populates="lesson_record", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LessonRecord(id={self.id}, class_id={self.class_id}, date={self.lesson_date})>"


class LessonPerformance(Base):
    """学生单节课表现反馈表 - 每位学生每节课一行"""
    __tablename__ = "lesson_performances"

    id               = Column(Integer, primary_key=True, index=True)
    lesson_record_id = Column(Integer, ForeignKey("lesson_records.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id       = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    feedback         = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=datetime.now)
    updated_at       = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    lesson_record = relationship("LessonRecord", back_populates="performances")
    student       = relationship("Student", back_populates="lesson_performances")

    def __repr__(self):
        return f"<LessonPerformance(lesson_record_id={self.lesson_record_id}, student_id={self.student_id})>"


# ─────────────────────────────────────────────
# 考试记录
# ─────────────────────────────────────────────

class ExamRecord(Base):
    """考试记录表 - 每行对应一位学生一次考试的单科成绩"""
    __tablename__ = "exam_records"

    id          = Column(Integer, primary_key=True, index=True)
    student_id  = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    test_date   = Column(Date, nullable=True, index=True)
    test_number = Column(Integer, nullable=True)
    subject     = Column(String(50), nullable=False)
    score       = Column(Float, nullable=True)
    total       = Column(Float, nullable=True)
    notes       = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=datetime.now)
    updated_at  = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    student = relationship("Student", back_populates="exam_records")

    def __repr__(self):
        return f"<ExamRecord(id={self.id}, student_id={self.student_id}, subject={self.subject})>"


# ─────────────────────────────────────────────
# 作业相关（班级维度布置，学生维度完成）
# ─────────────────────────────────────────────

class HomeworkAssignment(Base):
    """作业布置表 - 以班级为单位布置"""
    __tablename__ = "homework_assignments"

    id         = Column(Integer, primary_key=True, index=True)
    class_id   = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    date       = Column(Date, nullable=False, index=True)
    subject    = Column(String(50), nullable=False)
    homework   = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    class_      = relationship("Class", back_populates="homework_assignments")
    completions = relationship("HomeworkCompletion", back_populates="homework_assignment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<HomeworkAssignment(id={self.id}, class_id={self.class_id}, date={self.date})>"


class HomeworkCompletion(Base):
    """
    作业完成情况表 - 每位学生对每次作业的完成情况
    completion_status: completed / partial / not_completed
    """
    __tablename__ = "homework_completions"

    id                     = Column(Integer, primary_key=True, index=True)
    homework_assignment_id = Column(Integer, ForeignKey("homework_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id             = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    completion_status      = Column(String(20), nullable=False, default="not_completed")
    created_at             = Column(DateTime, default=datetime.now)
    updated_at             = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    homework_assignment = relationship("HomeworkAssignment", back_populates="completions")
    student             = relationship("Student", back_populates="homework_completions")

    def __repr__(self):
        return f"<HomeworkCompletion(id={self.id}, assignment_id={self.homework_assignment_id}, student_id={self.student_id})>"


# ─────────────────────────────────────────────
# 家长认证与对话（学生/家长端）
# ─────────────────────────────────────────────

class Parent(Base):
    """家长表 - 通过 8 位学号绑定学生，登录后获得 session_token"""
    __tablename__ = "parents"

    id            = Column(Integer, primary_key=True, index=True)
    student_id    = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    session_token = Column(String(64), nullable=True, index=True)
    last_active   = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, default=datetime.now)

    student       = relationship("Student", back_populates="parent")
    conversations = relationship("Conversation", back_populates="parent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Parent(id={self.id}, student_id={self.student_id})>"


class Conversation(Base):
    """家长/学生对话 Session 表"""
    __tablename__ = "conversations"

    id         = Column(Integer, primary_key=True, index=True)
    parent_id  = Column(Integer, ForeignKey("parents.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    parent   = relationship("Parent", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

    def __repr__(self):
        return f"<Conversation(id={self.id}, parent_id={self.parent_id})>"


class Message(Base):
    """家长/学生对话消息表  role: 'user' | 'assistant'"""
    __tablename__ = "messages"

    id              = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role            = Column(String(10), nullable=False)
    content         = Column(Text, nullable=False)
    created_at      = Column(DateTime, default=datetime.now)

    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role})>"


class ConversationMemory(Base):
    """长期记忆表 - 每位学生对应一条记录，跨会话持久化家长关注点和孩子特征"""
    __tablename__ = "conversation_memories"

    id             = Column(Integer, primary_key=True, index=True)
    student_id     = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    memory_content = Column(JSON, nullable=True, default=dict)
    updated_at     = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    student = relationship("Student", back_populates="conversation_memory")

    def __repr__(self):
        return f"<ConversationMemory(id={self.id}, student_id={self.student_id})>"


# ─────────────────────────────────────────────
# 教师端对话（教师 AI Chatbot）
# ─────────────────────────────────────────────

class TeacherConversation(Base):
    """教师对话 Session 表"""
    __tablename__ = "teacher_conversations"

    id         = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    teacher  = relationship("Teacher", back_populates="conversations")
    messages = relationship("TeacherMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="TeacherMessage.created_at")

    def __repr__(self):
        return f"<TeacherConversation(id={self.id}, teacher_id={self.teacher_id})>"


class TeacherMessage(Base):
    """教师对话消息表  role: 'user' | 'assistant'"""
    __tablename__ = "teacher_messages"

    id              = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("teacher_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role            = Column(String(10), nullable=False)
    content         = Column(Text, nullable=False)
    created_at      = Column(DateTime, default=datetime.now)

    conversation = relationship("TeacherConversation", back_populates="messages")

    def __repr__(self):
        return f"<TeacherMessage(id={self.id}, conversation_id={self.conversation_id}, role={self.role})>"
