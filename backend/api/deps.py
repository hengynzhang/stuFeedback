"""
公共依赖项
"""

from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Parent


def get_current_parent(
    authorization: str = Header(..., description="Bearer <session_token>"),
    db: Session = Depends(get_db),
) -> Parent:
    """
    从请求头 Authorization: Bearer <token> 中提取并验证家长身份
    所有家长端接口均依赖此函数，确保数据隔离
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证格式错误，应为 Bearer <token>")

    token = authorization[len("Bearer "):]
    parent = db.query(Parent).filter(Parent.session_token == token).first()
    if not parent:
        raise HTTPException(status_code=401, detail="无效或已过期的登录凭证，请重新登录")

    # 更新最后活跃时间
    parent.last_active = datetime.now()
    db.commit()

    return parent
