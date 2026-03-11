"""
数据库模型模块
包含：学生、课程单元、学生课程反馈、考试记录、作业布置、作业完成情况、
      家长认证、对话、消息、长期记忆
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


# ─────────────────────────────────────────────
# 学生
# ─────────────────────────────────────────────

class Student(Base):
    """
    学生表
    student_id: 系统自动生成的8位学号，供家长登录使用
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(8), nullable=False, unique=True, index=True)
    chinese_name = Column(String(50), nullable=False, index=True)
    english_name = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    performances = relationship("StudentPerformance", back_populates="student", cascade="all, delete-orphan")
    exam_records = relationship("ExamRecord", back_populates="student", cascade="all, delete-orphan")
    homework_completions = relationship("HomeworkCompletion", back_populates="student", cascade="all, delete-orphan")
    parent = relationship("Parent", back_populates="student", uselist=False, cascade="all, delete-orphan")
    conversation_memory = relationship("ConversationMemory", back_populates="student", uselist=False, cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.chinese_name} {self.english_name}"

    def __repr__(self):
        return f"<Student(student_id={self.student_id}, name={self.chinese_name})>"


# ─────────────────────────────────────────────
# 课程相关
# ─────────────────────────────────────────────

class CourseSession(Base):
    """
    课程单元表 - 一节课一行，存储课程级别的共享信息
    """
    __tablename__ = "course_sessions"

    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String(10), nullable=False, default="daily")  # 'daily' | 'weekly'
    date = Column(Date, nullable=True, index=True)         # 日录入时填写，周录入时留 null
    day_of_week = Column(String(10), nullable=True)        # 周一 / 周二 等，日录入时填写
    week = Column(String(20), nullable=True, index=True)   # Week 1 等，两种粒度都填
    subject = Column(String(50), nullable=False)
    teacher_name = Column(String(50), nullable=True)
    course_content = Column(Text, nullable=True)           # 本节课/本周重点内容
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    performances = relationship("StudentPerformance", back_populates="course_session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CourseSession(id={self.id}, date={self.date}, subject={self.subject})>"


class StudentPerformance(Base):
    """
    学生课程反馈表 - 每位学生在每节课的表现反馈，一行对应一个学生一节课
    """
    __tablename__ = "student_performances"

    id = Column(Integer, primary_key=True, index=True)
    course_session_id = Column(Integer, ForeignKey("course_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    feedback = Column(Text, nullable=True)                # 该学生本节课的表现反馈
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    course_session = relationship("CourseSession", back_populates="performances")
    student = relationship("Student", back_populates="performances")

    def __repr__(self):
        return f"<StudentPerformance(id={self.id}, course_session_id={self.course_session_id}, student_id={self.student_id})>"


# ─────────────────────────────────────────────
# 考试相关
# ─────────────────────────────────────────────

class ExamRecord(Base):
    """
    考试记录表 - 每行对应一位学生一次考试的单科成绩
    """
    __tablename__ = "exam_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    test_date = Column(Date, nullable=True, index=True)
    day_of_week = Column(String(10), nullable=True)
    week = Column(String(20), nullable=True, index=True)
    test_number = Column(Integer, nullable=True)          # 第几次考试（可选）
    subject = Column(String(50), nullable=False)          # 考试科目
    score = Column(Float, nullable=True)                  # 得分
    total = Column(Float, nullable=True)                  # 满分
    notes = Column(Text, nullable=True)                   # 备注
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    student = relationship("Student", back_populates="exam_records")

    def __repr__(self):
        return f"<ExamRecord(id={self.id}, student_id={self.student_id}, subject={self.subject}, date={self.test_date})>"


# ─────────────────────────────────────────────
# 作业相关
# ─────────────────────────────────────────────

class HomeworkAssignment(Base):
    """
    作业布置表 - 一次作业布置一行，存储作业级别的共享信息
    """
    __tablename__ = "homework_assignments"

    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String(10), nullable=False, default="daily")  # 'daily' | 'weekly'
    date = Column(Date, nullable=True, index=True)         # 日录入时填写，周录入时留 null
    day_of_week = Column(String(10), nullable=True)        # 日录入时填写
    week = Column(String(20), nullable=True, index=True)   # 两种粒度都填
    subject = Column(String(50), nullable=False)
    homework = Column(Text, nullable=True)                 # 作业内容
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    completions = relationship("HomeworkCompletion", back_populates="homework_assignment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<HomeworkAssignment(id={self.id}, date={self.date}, subject={self.subject})>"


class HomeworkCompletion(Base):
    """
    作业完成情况表 - 每位学生对每次作业的完成情况，一行对应一个学生一次作业
    completion_status: completed / partial / not_completed
    """
    __tablename__ = "homework_completions"

    id = Column(Integer, primary_key=True, index=True)
    homework_assignment_id = Column(Integer, ForeignKey("homework_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    completion_status = Column(String(20), nullable=False, default="not_completed")  # completed / partial / not_completed
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    homework_assignment = relationship("HomeworkAssignment", back_populates="completions")
    student = relationship("Student", back_populates="homework_completions")

    def __repr__(self):
        return f"<HomeworkCompletion(id={self.id}, homework_assignment_id={self.homework_assignment_id}, student_id={self.student_id})>"


# ─────────────────────────────────────────────
# 家长认证与对话
# ─────────────────────────────────────────────

class Parent(Base):
    """
    家长表 - 通过8位学号绑定学生，登录后获得 session_token
    """
    __tablename__ = "parents"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    session_token = Column(String(64), nullable=True, index=True)
    last_active = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # 关联关系
    student = relationship("Student", back_populates="parent")
    conversations = relationship("Conversation", back_populates="parent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Parent(id={self.id}, student_id={self.student_id})>"


class Conversation(Base):
    """
    对话 Session 表 - 每次家长发起新对话对应一条记录
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("parents.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    parent = relationship("Parent", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

    def __repr__(self):
        return f"<Conversation(id={self.id}, parent_id={self.parent_id})>"


class Message(Base):
    """
    消息表
    role: 'user' | 'assistant'
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(10), nullable=False)   # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 关联关系
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role})>"


class ConversationMemory(Base):
    """
    长期记忆表 - 每位学生对应一条记录，跨会话持久化家长关注点和孩子特征
    memory_content 示例：
    {
        "concerns": ["家长关注写作成绩", "孩子听力有明显进步"],
        "preferences": ["家长偏好详细建议"],
        "child_traits": ["专注力不稳定", "数学基础较好"]
    }
    """
    __tablename__ = "conversation_memories"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    memory_content = Column(JSON, nullable=True, default=dict)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    student = relationship("Student", back_populates="conversation_memory")

    def __repr__(self):
        return f"<ConversationMemory(id={self.id}, student_id={self.student_id})>"
