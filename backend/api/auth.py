"""
认证模块
家长通过8位学号登录，获取 session_token
"""

import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Student, Parent
from schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def generate_session_token() -> str:
    return secrets.token_hex(32)  # 64位十六进制字符串


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    家长登录：输入8位学号，返回 session_token
    若该学号尚无 Parent 记录，自动创建
    """
    student = db.query(Student).filter(Student.student_id == request.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学号不存在，请联系教师确认")

    parent = db.query(Parent).filter(Parent.student_id == student.id).first()
    if not parent:
        parent = Parent(student_id=student.id)
        db.add(parent)

    parent.session_token = generate_session_token()
    parent.last_active = datetime.now()
    db.commit()
    db.refresh(parent)

    return LoginResponse(
        session_token=parent.session_token,
        student_name=student.full_name,
        student_id=student.student_id,
    )


@router.post("/logout")
def logout(token: str, db: Session = Depends(get_db)):
    """使 session_token 失效"""
    parent = db.query(Parent).filter(Parent.session_token == token).first()
    if parent:
        parent.session_token = None
        db.commit()
    return {"success": True}
