"""
教师端 API
学生管理 + 课程记录录入 + 考试记录录入 + 作业记录录入
所有写操作均在此模块，不需要身份验证（MVP阶段，后续可加教师Auth）
"""

import random
import string
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Student, CourseSession, StudentPerformance, ExamRecord, HomeworkAssignment, HomeworkCompletion
from schemas import (
    StudentCreate, StudentUpdate, StudentResponse,
    CourseSessionCreate, CourseSessionUpdate, CourseSessionResponse,
    StudentPerformanceUpdate, StudentPerformanceResponse,
    ExamRecordCreate, ExamRecordUpdate, ExamRecordResponse,
    HomeworkAssignmentCreate, HomeworkAssignmentUpdate, HomeworkAssignmentResponse,
    HomeworkCompletionUpdate, HomeworkCompletionResponse,
)

router = APIRouter(prefix="/teacher", tags=["teacher"])


# ── 工具函数 ──────────────────────────────────

def _generate_student_id(db: Session) -> str:
    """生成唯一8位数字学号"""
    while True:
        sid = ''.join(random.choices(string.digits, k=8))
        if not db.query(Student).filter(Student.student_id == sid).first():
            return sid


# ── 学生管理 ──────────────────────────────────

@router.get("/students", response_model=List[StudentResponse])
def list_students(db: Session = Depends(get_db)):
    return db.query(Student).order_by(Student.chinese_name).all()


@router.post("/students", response_model=StudentResponse)
def create_student(body: StudentCreate, db: Session = Depends(get_db)):
    """新建学生，自动生成8位学号"""
    student = Student(
        student_id=_generate_student_id(db),
        chinese_name=body.chinese_name,
        english_name=body.english_name,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    return student


@router.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, body: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    if body.chinese_name is not None:
        student.chinese_name = body.chinese_name
    if body.english_name is not None:
        student.english_name = body.english_name
    db.commit()
    db.refresh(student)
    return student


@router.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    db.delete(student)
    db.commit()
    return {"success": True}


# ── 课程记录 ──────────────────────────────────

@router.get("/sessions", response_model=List[CourseSessionResponse])
def list_sessions(
    week: Optional[str] = None,
    subject: Optional[str] = None,
    record_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(CourseSession)
    if week:
        q = q.filter(CourseSession.week == week)
    if subject:
        q = q.filter(CourseSession.subject == subject)
    if record_type:
        q = q.filter(CourseSession.record_type == record_type)
    return q.order_by(CourseSession.date.desc().nullslast(), CourseSession.week.desc()).all()


@router.post("/sessions", response_model=CourseSessionResponse)
def create_session(body: CourseSessionCreate, db: Session = Depends(get_db)):
    """
    创建课程单元，同时批量创建各学生的表现记录
    适合 Airtable 风格的一次性录入：教师填完一行课程信息 + 每列学生反馈后提交
    """
    session = CourseSession(
        record_type=body.record_type,
        date=body.date,
        day_of_week=body.day_of_week,
        week=body.week,
        subject=body.subject,
        teacher_name=body.teacher_name,
        course_content=body.course_content,
    )
    db.add(session)
    db.flush()  # 获取 session.id

    for p in body.performances:
        db.add(StudentPerformance(
            course_session_id=session.id,
            student_id=p.student_id,
            feedback=p.feedback,
        ))

    db.commit()
    db.refresh(session)
    return session


@router.put("/sessions/{session_id}", response_model=CourseSessionResponse)
def update_session(session_id: int, body: CourseSessionUpdate, db: Session = Depends(get_db)):
    """更新课程单元的基本信息（不含各学生反馈，反馈通过 /performances/{id} 单独更新）"""
    session = db.query(CourseSession).filter(CourseSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="课程记录不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(session, field, value)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(CourseSession).filter(CourseSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="课程记录不存在")
    db.delete(session)
    db.commit()
    return {"success": True}


@router.put("/performances/{performance_id}", response_model=StudentPerformanceResponse)
def update_performance(performance_id: int, body: StudentPerformanceUpdate, db: Session = Depends(get_db)):
    """更新单个学生在某节课的反馈（对应 Airtable 中单元格编辑）"""
    perf = db.query(StudentPerformance).filter(StudentPerformance.id == performance_id).first()
    if not perf:
        raise HTTPException(status_code=404, detail="表现记录不存在")
    perf.feedback = body.feedback
    db.commit()
    db.refresh(perf)
    return perf


# ── 考试记录 ──────────────────────────────────

@router.get("/exams", response_model=List[ExamRecordResponse])
def list_exams(
    student_id: Optional[int] = None,
    subject: Optional[str] = None,
    week: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(ExamRecord)
    if student_id:
        q = q.filter(ExamRecord.student_id == student_id)
    if subject:
        q = q.filter(ExamRecord.subject == subject)
    if week:
        q = q.filter(ExamRecord.week == week)
    return q.order_by(ExamRecord.test_date.desc().nullslast()).all()


@router.post("/exams", response_model=ExamRecordResponse)
def create_exam(body: ExamRecordCreate, db: Session = Depends(get_db)):
    record = ExamRecord(**body.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/exams/{exam_id}", response_model=ExamRecordResponse)
def update_exam(exam_id: int, body: ExamRecordUpdate, db: Session = Depends(get_db)):
    record = db.query(ExamRecord).filter(ExamRecord.id == exam_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="考试记录不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/exams/{exam_id}")
def delete_exam(exam_id: int, db: Session = Depends(get_db)):
    record = db.query(ExamRecord).filter(ExamRecord.id == exam_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="考试记录不存在")
    db.delete(record)
    db.commit()
    return {"success": True}


# ── 作业记录 ──────────────────────────────────

@router.get("/homework", response_model=List[HomeworkAssignmentResponse])
def list_homework(
    week: Optional[str] = None,
    subject: Optional[str] = None,
    record_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(HomeworkAssignment)
    if week:
        q = q.filter(HomeworkAssignment.week == week)
    if subject:
        q = q.filter(HomeworkAssignment.subject == subject)
    if record_type:
        q = q.filter(HomeworkAssignment.record_type == record_type)
    return q.order_by(HomeworkAssignment.date.desc().nullslast(), HomeworkAssignment.week.desc()).all()


@router.post("/homework", response_model=HomeworkAssignmentResponse)
def create_homework(body: HomeworkAssignmentCreate, db: Session = Depends(get_db)):
    """
    创建作业布置，同时批量创建各学生的完成情况记录
    """
    assignment = HomeworkAssignment(
        record_type=body.record_type,
        date=body.date,
        day_of_week=body.day_of_week,
        week=body.week,
        subject=body.subject,
        homework=body.homework,
    )
    db.add(assignment)
    db.flush()

    for c in body.completions:
        db.add(HomeworkCompletion(
            homework_assignment_id=assignment.id,
            student_id=c.student_id,
            completion_status=c.completion_status,
        ))

    db.commit()
    db.refresh(assignment)
    return assignment


@router.put("/homework/{assignment_id}", response_model=HomeworkAssignmentResponse)
def update_homework(assignment_id: int, body: HomeworkAssignmentUpdate, db: Session = Depends(get_db)):
    assignment = db.query(HomeworkAssignment).filter(HomeworkAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="作业记录不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(assignment, field, value)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/homework/{assignment_id}")
def delete_homework(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(HomeworkAssignment).filter(HomeworkAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="作业记录不存在")
    db.delete(assignment)
    db.commit()
    return {"success": True}


@router.put("/completions/{completion_id}", response_model=HomeworkCompletionResponse)
def update_completion(completion_id: int, body: HomeworkCompletionUpdate, db: Session = Depends(get_db)):
    """更新单个学生的作业完成情况（对应 Airtable 中单元格编辑）"""
    completion = db.query(HomeworkCompletion).filter(HomeworkCompletion.id == completion_id).first()
    if not completion:
        raise HTTPException(status_code=404, detail="完成记录不存在")
    completion.completion_status = body.completion_status
    db.commit()
    db.refresh(completion)
    return completion
