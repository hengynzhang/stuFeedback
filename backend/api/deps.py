"""
公共依赖项
- get_current_parent：家长/学生端 session_token 验证
- get_current_teacher：教师端 JWT 验证
"""

from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from jose import jwt, JWTError
import os

from database import get_db
from models import Parent, Teacher

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM  = "HS256"


def get_current_parent(
    authorization: str = Header(..., description="Bearer <session_token>"),
    db: Session = Depends(get_db),
) -> Parent:
    """从请求头 Authorization: Bearer <token> 中提取并验证家长身份"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证格式错误，应为 Bearer <token>")

    token  = authorization[len("Bearer "):]
    parent = db.query(Parent).filter(Parent.session_token == token).first()
    if not parent:
        raise HTTPException(status_code=401, detail="无效或已过期的登录凭证，请重新登录")

    parent.last_active = datetime.now()
    db.commit()
    return parent


def get_current_teacher(
    authorization: str = Header(..., description="Bearer <jwt_token>"),
    db: Session = Depends(get_db),
) -> Teacher:
    """从请求头 Authorization: Bearer <JWT> 中解码并验证教师身份"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证格式错误，应为 Bearer <token>")

    token = authorization[len("Bearer "):]
    try:
        payload    = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        teacher_id = int(payload.get("sub", 0))
        role       = payload.get("role", "")
        if role != "teacher":
            raise HTTPException(status_code=403, detail="权限不足")
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="无效或已过期的登录凭证，请重新登录")

    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=401, detail="教师账号不存在")

    return teacher
