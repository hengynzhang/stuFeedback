"""
家长端数据查询 API
所有接口强制通过 get_current_parent 依赖，数据严格隔离至当前学生
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Parent, Student, CourseSession, StudentPerformance, ExamRecord, HomeworkAssignment, HomeworkCompletion
from schemas import StudentResponse, CourseSessionResponse, ExamRecordResponse, HomeworkAssignmentResponse
from api.deps import get_current_parent

router = APIRouter(prefix="/parent", tags=["parent"])


@router.get("/me", response_model=StudentResponse)
def get_my_student(
    current_parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """获取当前家长绑定的学生信息"""
    return current_parent.student


@router.get("/performance", response_model=List[CourseSessionResponse])
def get_performance(
    week: Optional[str] = None,
    subject: Optional[str] = None,
    record_type: Optional[str] = None,
    current_parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """
    获取孩子的课程表现记录
    返回 CourseSession 列表，每条记录中 performances 仅含当前学生
    """
    student_id = current_parent.student_id

    # 找到包含该学生反馈的课程单元
    q = db.query(CourseSession).join(
        StudentPerformance,
        StudentPerformance.course_session_id == CourseSession.id
    ).filter(StudentPerformance.student_id == student_id)

    if week:
        q = q.filter(CourseSession.week == week)
    if subject:
        q = q.filter(CourseSession.subject == subject)
    if record_type:
        q = q.filter(CourseSession.record_type == record_type)

    sessions = q.order_by(CourseSession.date.desc().nullslast()).all()

    # 只保留当前学生的 performance 记录
    result = []
    for session in sessions:
        session.performances = [
            p for p in session.performances if p.student_id == student_id
        ]
        result.append(session)

    return result


@router.get("/exams", response_model=List[ExamRecordResponse])
def get_exams(
    subject: Optional[str] = None,
    week: Optional[str] = None,
    limit: int = 20,
    current_parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """获取孩子的考试成绩记录"""
    student_id = current_parent.student_id

    q = db.query(ExamRecord).filter(ExamRecord.student_id == student_id)
    if subject:
        q = q.filter(ExamRecord.subject == subject)
    if week:
        q = q.filter(ExamRecord.week == week)

    return q.order_by(ExamRecord.test_date.desc().nullslast()).limit(limit).all()


@router.get("/homework", response_model=List[HomeworkAssignmentResponse])
def get_homework(
    week: Optional[str] = None,
    subject: Optional[str] = None,
    current_parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """
    获取孩子的作业记录
    返回 HomeworkAssignment 列表，每条记录中 completions 仅含当前学生
    """
    student_id = current_parent.student_id

    q = db.query(HomeworkAssignment).join(
        HomeworkCompletion,
        HomeworkCompletion.homework_assignment_id == HomeworkAssignment.id
    ).filter(HomeworkCompletion.student_id == student_id)

    if week:
        q = q.filter(HomeworkAssignment.week == week)
    if subject:
        q = q.filter(HomeworkAssignment.subject == subject)

    assignments = q.order_by(HomeworkAssignment.date.desc().nullslast()).all()

    result = []
    for assignment in assignments:
        assignment.completions = [
            c for c in assignment.completions if c.student_id == student_id
        ]
        result.append(assignment)

    return result
