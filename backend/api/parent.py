"""
家长/学生端数据查询 API v3
所有接口强制通过 get_current_parent 依赖，数据严格隔离至当前学生
课程记录已改为 LessonRecord（单节课粒度）
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Parent, Student, Class, LessonRecord, LessonPerformance, ExamRecord, HomeworkAssignment, HomeworkCompletion
from schemas import StudentResponse, LessonRecordResponse, ExamRecordResponse, HomeworkAssignmentResponse
from api.deps import get_current_parent

router = APIRouter(prefix="/parent", tags=["parent"])


@router.get("/me", response_model=StudentResponse)
def get_my_student(
    current_parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """获取当前家长/学生绑定的学生信息"""
    return current_parent.student


@router.get("/performance", response_model=List[LessonRecordResponse])
def get_performance(
    subject: Optional[str] = None,
    current_parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """
    获取孩子的课程表现记录（单节课粒度）
    返回 LessonRecord 列表，每条记录中 performances 仅含当前学生
    """
    student_id = current_parent.student_id

    q = (db.query(LessonRecord)
         .join(LessonPerformance, LessonPerformance.lesson_record_id == LessonRecord.id)
         .filter(LessonPerformance.student_id == student_id))

    if subject:
        q = q.join(Class, LessonRecord.class_id == Class.id).filter(Class.subject == subject)

    lessons = q.order_by(LessonRecord.lesson_date.desc()).all()

    result = []
    for lesson in lessons:
        lesson.performances = [p for p in lesson.performances if p.student_id == student_id]
        result.append(lesson)
    return result


@router.get("/exams", response_model=List[ExamRecordResponse])
def get_exams(
    subject: Optional[str] = None,
    limit: int = 20,
    current_parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """获取孩子的考试成绩记录"""
    student_id = current_parent.student_id
    q = db.query(ExamRecord).filter(ExamRecord.student_id == student_id)
    if subject:
        q = q.filter(ExamRecord.subject == subject)
    return q.order_by(ExamRecord.test_date.desc().nullslast()).limit(limit).all()


@router.get("/homework", response_model=List[HomeworkAssignmentResponse])
def get_homework(
    subject: Optional[str] = None,
    current_parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """
    获取孩子的作业记录
    从班级维度的 HomeworkAssignment 中筛选该学生的完成情况
    """
    student_id = current_parent.student_id
    student    = db.query(Student).filter(Student.id == student_id).first()

    q = (db.query(HomeworkAssignment)
         .join(HomeworkCompletion, HomeworkCompletion.homework_assignment_id == HomeworkAssignment.id)
         .filter(
             HomeworkCompletion.student_id == student_id,
             HomeworkAssignment.class_id   == student.class_id,
         ))
    if subject:
        q = q.filter(HomeworkAssignment.subject == subject)

    assignments = q.order_by(HomeworkAssignment.date.desc()).all()

    result = []
    for assignment in assignments:
        assignment.completions = [c for c in assignment.completions if c.student_id == student_id]
        result.append(assignment)
    return result
