"""
FastAPI 主入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from database import engine
import models

# 创建所有数据库表
models.Base.metadata.create_all(bind=engine)

# 导入路由
from api.auth import router as auth_router
from api.teacher import router as teacher_router
from api.parent import router as parent_router
from api.chat import router as chat_router

app = FastAPI(
    title="学生反馈系统",
    description="面向家长的学生情况查询与 AI 对话系统",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,    prefix="/api")
app.include_router(teacher_router, prefix="/api")
app.include_router(parent_router,  prefix="/api")
app.include_router(chat_router,    prefix="/api")


@app.get("/")
def root():
    return {"message": "学生反馈系统 API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
