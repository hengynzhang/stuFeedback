"""
认证模块 v3
- 教师端：手机号 + 短信验证码注册（Mock 模式），设置密码，手机号+密码登录，JWT
- 家长/学生端：8 位学号登录，session_token
"""

import secrets
import random
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext
import os

from database import get_db
from models import Teacher, SMSVerification, Student, Parent
from schemas import (
    SendCodeRequest, SendCodeResponse,
    RegisterRequest, TeacherLoginRequest, TeacherLoginResponse,
    ParentLoginRequest, ParentLoginResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# ── 密码与 JWT 配置 ───────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7   # 7 天

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def generate_session_token() -> str:
    return secrets.token_hex(32)


# ── 教师端：发送验证码 ────────────────────────

@router.post("/teacher/send-code", response_model=SendCodeResponse)
def send_verification_code(body: SendCodeRequest, db: Session = Depends(get_db)):
    """
    发送短信验证码（当前为 Mock 模式，直接返回验证码）
    生产环境接入阿里云/腾讯云短信后去掉 response 中的 code 字段
    """
    code = "".join(random.choices(string.digits, k=6))
    expires_at = datetime.now() + timedelta(minutes=10)

    # 废止该手机号之前未使用的验证码
    db.query(SMSVerification).filter(
        SMSVerification.phone == body.phone,
        SMSVerification.is_used == False,
    ).update({"is_used": True})

    db.add(SMSVerification(phone=body.phone, code=code, expires_at=expires_at))
    db.commit()

    return SendCodeResponse(message="验证码已发送（Mock 模式）", code=code)


# ── 教师端：注册 ─────────────────────────────

@router.post("/teacher/register", response_model=TeacherLoginResponse)
def register_teacher(body: RegisterRequest, db: Session = Depends(get_db)):
    """教师注册：验证短信验证码 → 创建账号 → 返回 JWT"""
    if db.query(Teacher).filter(Teacher.phone == body.phone).first():
        raise HTTPException(status_code=400, detail="该手机号已注册")

    sms = db.query(SMSVerification).filter(
        SMSVerification.phone   == body.phone,
        SMSVerification.code    == body.code,
        SMSVerification.is_used == False,
        SMSVerification.expires_at > datetime.now(),
    ).order_by(SMSVerification.created_at.desc()).first()

    if not sms:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")

    sms.is_used = True

    teacher = Teacher(
        phone         = body.phone,
        name          = body.name,
        password_hash = hash_password(body.password),
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    token = create_access_token({"sub": str(teacher.id), "role": "teacher"})
    return TeacherLoginResponse(access_token=token, teacher_id=teacher.id, name=teacher.name)


# ── 教师端：登录 ─────────────────────────────

@router.post("/teacher/login", response_model=TeacherLoginResponse)
def login_teacher(body: TeacherLoginRequest, db: Session = Depends(get_db)):
    """教师登录：手机号 + 密码"""
    teacher = db.query(Teacher).filter(Teacher.phone == body.phone).first()
    if not teacher or not verify_password(body.password, teacher.password_hash):
        raise HTTPException(status_code=401, detail="手机号或密码错误")

    token = create_access_token({"sub": str(teacher.id), "role": "teacher"})
    return TeacherLoginResponse(access_token=token, teacher_id=teacher.id, name=teacher.name)


# ── 家长/学生端：登录 ─────────────────────────

@router.post("/login", response_model=ParentLoginResponse)
def login_parent(request: ParentLoginRequest, db: Session = Depends(get_db)):
    """
    家长/学生登录：输入 8 位学号，返回 session_token
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
    parent.last_active   = datetime.now()
    db.commit()
    db.refresh(parent)

    return ParentLoginResponse(
        session_token=parent.session_token,
        student_name =student.full_name,
        student_id   =student.student_id,
    )


@router.post("/logout")
def logout_parent(token: str, db: Session = Depends(get_db)):
    """家长/学生端登出"""
    parent = db.query(Parent).filter(Parent.session_token == token).first()
    if parent:
        parent.session_token = None
        db.commit()
    return {"success": True}
