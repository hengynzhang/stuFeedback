"""
教师端 API v3
所有接口均需要 JWT 教师身份验证
功能：班级管理 / 学生管理 / 课程记录 / 考试记录 / 作业记录
"""

import random
import string
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Teacher, Class, Student, LessonRecord, LessonPerformance, ExamRecord, HomeworkAssignment, HomeworkCompletion
from schemas import (
    ClassCreate, ClassUpdate, ClassResponse,
    StudentCreate, StudentUpdate, StudentResponse,
    LessonRecordCreate, LessonRecordUpdate, LessonRecordResponse,
    LessonPerformanceUpdate, LessonPerformanceResponse,
    ExamRecordCreate, ExamRecordUpdate, ExamRecordResponse,
    HomeworkAssignmentCreate, HomeworkAssignmentUpdate, HomeworkAssignmentResponse,
    HomeworkCompletionUpdate, HomeworkCompletionResponse,
)
from api.deps import get_current_teacher

router = APIRouter(prefix="/teacher", tags=["teacher"])


# ── 工具函数 ──────────────────────────────────

def _generate_student_id(db: Session) -> str:
    """生成唯一 8 位数字学号"""
    while True:
        sid = "".join(random.choices(string.digits, k=8))
        if not db.query(Student).filter(Student.student_id == sid).first():
            return sid


def _build_class_response(c: Class) -> ClassResponse:
    """构建包含计算字段的班级响应"""
    completed = sum(1 for lr in c.lesson_records if lr.status == "completed")
    remaining = max(0, c.total_lessons - completed)
    return ClassResponse(
        id               = c.id,
        name             = c.name,
        subject          = c.subject,
        teacher_id       = c.teacher_id,
        start_date       = c.start_date,
        end_date         = c.end_date,
        total_lessons    = c.total_lessons,
        status           = c.status,
        completed_lessons= completed,
        remaining_lessons= remaining,
        student_count    = len(c.students),
        created_at       = c.created_at,
    )


def _assert_class_owner(class_id: int, teacher_id: int, db: Session) -> Class:
    """验证班级属于当前教师，不存在或无权则抛 404"""
    c = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="班级不存在或无权操作")
    return c


def _assert_student_owner(student_id: int, teacher_id: int, db: Session) -> Student:
    """验证学生属于当前教师名下班级"""
    s = (db.query(Student)
         .join(Class, Student.class_id == Class.id)
         .filter(Student.id == student_id, Class.teacher_id == teacher_id)
         .first())
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在或无权操作")
    return s


# ── 班级管理 ──────────────────────────────────

@router.get("/classes", response_model=List[ClassResponse])
def list_classes(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    classes = db.query(Class).filter(Class.teacher_id == current_teacher.id).all()
    return [_build_class_response(c) for c in classes]


@router.post("/classes", response_model=ClassResponse)
def create_class(
    body: ClassCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    c = Class(
        name          = body.name,
        subject       = body.subject,
        teacher_id    = current_teacher.id,
        start_date    = body.start_date,
        end_date      = body.end_date,
        total_lessons = body.total_lessons,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _build_class_response(c)


@router.get("/classes/{class_id}", response_model=ClassResponse)
def get_class(
    class_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    return _build_class_response(_assert_class_owner(class_id, current_teacher.id, db))


@router.put("/classes/{class_id}", response_model=ClassResponse)
def update_class(
    class_id: int,
    body: ClassUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    c = _assert_class_owner(class_id, current_teacher.id, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(c, field, value)
    db.commit()
    db.refresh(c)
    return _build_class_response(c)


@router.delete("/classes/{class_id}")
def delete_class(
    class_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    c = _assert_class_owner(class_id, current_teacher.id, db)
    db.delete(c)
    db.commit()
    return {"success": True}


# ── 学生管理 ──────────────────────────────────

@router.get("/students", response_model=List[StudentResponse])
def list_students(
    class_id: Optional[int] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """获取当前教师名下的学生，可按班级筛选"""
    q = (db.query(Student)
         .join(Class, Student.class_id == Class.id)
         .filter(Class.teacher_id == current_teacher.id))
    if class_id:
        q = q.filter(Student.class_id == class_id)
    return q.order_by(Student.chinese_name).all()


@router.post("/students", response_model=StudentResponse)
def create_student(
    body: StudentCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    _assert_class_owner(body.class_id, current_teacher.id, db)
    student = Student(
        student_id   = _generate_student_id(db),
        chinese_name = body.chinese_name,
        english_name = body.english_name,
        class_id     = body.class_id,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    return _assert_student_owner(student_id, current_teacher.id, db)


@router.put("/students/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    body: StudentUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    student = _assert_student_owner(student_id, current_teacher.id, db)
    if body.class_id is not None:
        _assert_class_owner(body.class_id, current_teacher.id, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    student = _assert_student_owner(student_id, current_teacher.id, db)
    db.delete(student)
    db.commit()
    return {"success": True}


# ── 课程记录（单节课） ─────────────────────────

@router.get("/lessons", response_model=List[LessonRecordResponse])
def list_lessons(
    class_id: Optional[int] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    q = (db.query(LessonRecord)
         .join(Class, LessonRecord.class_id == Class.id)
         .filter(Class.teacher_id == current_teacher.id))
    if class_id:
        q = q.filter(LessonRecord.class_id == class_id)
    return q.order_by(LessonRecord.lesson_date.desc()).all()


@router.post("/lessons", response_model=LessonRecordResponse)
def create_lesson(
    body: LessonRecordCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    _assert_class_owner(body.class_id, current_teacher.id, db)
    lesson = LessonRecord(
        class_id          = body.class_id,
        lesson_date       = body.lesson_date,
        lesson_start_time = body.lesson_start_time,
        lesson_end_time   = body.lesson_end_time,
        topic             = body.topic,
        content_notes     = body.content_notes,
        status            = body.status,
    )
    db.add(lesson)
    db.flush()

    for p in body.performances:
        db.add(LessonPerformance(
            lesson_record_id = lesson.id,
            student_id       = p.student_id,
            feedback         = p.feedback,
        ))

    db.commit()
    db.refresh(lesson)
    return lesson


@router.put("/lessons/{lesson_id}", response_model=LessonRecordResponse)
def update_lesson(
    lesson_id: int,
    body: LessonRecordUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    lesson = (db.query(LessonRecord)
              .join(Class, LessonRecord.class_id == Class.id)
              .filter(LessonRecord.id == lesson_id, Class.teacher_id == current_teacher.id)
              .first())
    if not lesson:
        raise HTTPException(status_code=404, detail="课程记录不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(lesson, field, value)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.delete("/lessons/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    lesson = (db.query(LessonRecord)
              .join(Class, LessonRecord.class_id == Class.id)
              .filter(LessonRecord.id == lesson_id, Class.teacher_id == current_teacher.id)
              .first())
    if not lesson:
        raise HTTPException(status_code=404, detail="课程记录不存在")
    db.delete(lesson)
    db.commit()
    return {"success": True}


@router.put("/performances/{performance_id}", response_model=LessonPerformanceResponse)
def update_performance(
    performance_id: int,
    body: LessonPerformanceUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """更新单个学生在某节课的反馈（单元格行内编辑，失焦自动保存）"""
    perf = db.query(LessonPerformance).filter(LessonPerformance.id == performance_id).first()
    if not perf:
        raise HTTPException(status_code=404, detail="表现记录不存在")
    perf.feedback = body.feedback
    db.commit()
    db.refresh(perf)
    return perf


# ── 考试记录 ──────────────────────────────────

@router.get("/exams", response_model=List[ExamRecordResponse])
def list_exams(
    class_id: Optional[int] = None,
    student_id: Optional[int] = None,
    subject: Optional[str] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    q = (db.query(ExamRecord)
         .join(Student, ExamRecord.student_id == Student.id)
         .join(Class, Student.class_id == Class.id)
         .filter(Class.teacher_id == current_teacher.id))
    if class_id:
        q = q.filter(Student.class_id == class_id)
    if student_id:
        q = q.filter(ExamRecord.student_id == student_id)
    if subject:
        q = q.filter(ExamRecord.subject == subject)
    return q.order_by(ExamRecord.test_date.desc().nullslast()).all()


@router.post("/exams", response_model=ExamRecordResponse)
def create_exam(
    body: ExamRecordCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    _assert_student_owner(body.student_id, current_teacher.id, db)
    record = ExamRecord(**body.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/exams/{exam_id}", response_model=ExamRecordResponse)
def update_exam(
    exam_id: int,
    body: ExamRecordUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    record = (db.query(ExamRecord)
              .join(Student, ExamRecord.student_id == Student.id)
              .join(Class, Student.class_id == Class.id)
              .filter(ExamRecord.id == exam_id, Class.teacher_id == current_teacher.id)
              .first())
    if not record:
        raise HTTPException(status_code=404, detail="考试记录不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/exams/{exam_id}")
def delete_exam(
    exam_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    record = (db.query(ExamRecord)
              .join(Student, ExamRecord.student_id == Student.id)
              .join(Class, Student.class_id == Class.id)
              .filter(ExamRecord.id == exam_id, Class.teacher_id == current_teacher.id)
              .first())
    if not record:
        raise HTTPException(status_code=404, detail="考试记录不存在")
    db.delete(record)
    db.commit()
    return {"success": True}


# ── 作业记录 ──────────────────────────────────

@router.get("/homework", response_model=List[HomeworkAssignmentResponse])
def list_homework(
    class_id: Optional[int] = None,
    subject: Optional[str] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    q = (db.query(HomeworkAssignment)
         .join(Class, HomeworkAssignment.class_id == Class.id)
         .filter(Class.teacher_id == current_teacher.id))
    if class_id:
        q = q.filter(HomeworkAssignment.class_id == class_id)
    if subject:
        q = q.filter(HomeworkAssignment.subject == subject)
    return q.order_by(HomeworkAssignment.date.desc()).all()


@router.post("/homework", response_model=HomeworkAssignmentResponse)
def create_homework(
    body: HomeworkAssignmentCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    _assert_class_owner(body.class_id, current_teacher.id, db)
    assignment = HomeworkAssignment(
        class_id = body.class_id,
        date     = body.date,
        subject  = body.subject,
        homework = body.homework,
    )
    db.add(assignment)
    db.flush()

    for c in body.completions:
        db.add(HomeworkCompletion(
            homework_assignment_id = assignment.id,
            student_id             = c.student_id,
            completion_status      = c.completion_status,
        ))

    db.commit()
    db.refresh(assignment)
    return assignment


@router.put("/homework/{assignment_id}", response_model=HomeworkAssignmentResponse)
def update_homework(
    assignment_id: int,
    body: HomeworkAssignmentUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    assignment = (db.query(HomeworkAssignment)
                  .join(Class, HomeworkAssignment.class_id == Class.id)
                  .filter(HomeworkAssignment.id == assignment_id, Class.teacher_id == current_teacher.id)
                  .first())
    if not assignment:
        raise HTTPException(status_code=404, detail="作业记录不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(assignment, field, value)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/homework/{assignment_id}")
def delete_homework(
    assignment_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    assignment = (db.query(HomeworkAssignment)
                  .join(Class, HomeworkAssignment.class_id == Class.id)
                  .filter(HomeworkAssignment.id == assignment_id, Class.teacher_id == current_teacher.id)
                  .first())
    if not assignment:
        raise HTTPException(status_code=404, detail="作业记录不存在")
    db.delete(assignment)
    db.commit()
    return {"success": True}


@router.put("/completions/{completion_id}", response_model=HomeworkCompletionResponse)
def update_completion(
    completion_id: int,
    body: HomeworkCompletionUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """更新单个学生的作业完成情况（单元格点击切换）"""
    completion = db.query(HomeworkCompletion).filter(HomeworkCompletion.id == completion_id).first()
    if not completion:
        raise HTTPException(status_code=404, detail="完成记录不存在")
    completion.completion_status = body.completion_status
    db.commit()
    db.refresh(completion)
    return completion
