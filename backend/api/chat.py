"""
对话管理 API
家长发起对话、发送消息、查看历史
AI 回复的生成逻辑在 ai/agent.py，此模块只负责会话管理和消息存取
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Parent, Conversation, Message
from schemas import MessageCreate, MessageResponse, ConversationResponse, ChatResponse
from api.deps import get_current_parent
from ai.agent import ChatAgent

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversations", response_model=ConversationResponse)
def new_conversation(
    current_parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """发起新对话"""
    conversation = Conversation(parent_id=current_parent.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    limit: int = 20,
    current_parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """获取历史对话列表（不含消息内容，用于侧边栏展示）"""
    return (
        db.query(Conversation)
        .filter(Conversation.parent_id == current_parent.id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    current_parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """获取某次对话的完整消息记录"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.parent_id == current_parent.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: int,
    body: MessageCreate,
    current_parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """
    发送消息并获取 AI 回复
    流程：
    1. 存储用户消息
    2. 读取对话历史 + 长期记忆
    3. 调用 ChatAgent 生成回复（含 Tool Calling）
    4. 存储 AI 回复
    5. 异步更新长期记忆
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.parent_id == current_parent.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    # 1. 存储用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=body.content,
    )
    db.add(user_message)
    db.commit()

    # 2. 构建历史消息列表
    history = [
        {"role": m.role, "content": m.content}
        for m in conversation.messages
    ]

    # 3. 调用 AI Agent
    agent = ChatAgent(db=db, student_id=current_parent.student_id)
    reply_content = await agent.chat(
        history=history,
        student_id=current_parent.student_id,
    )

    # 4. 存储 AI 回复
    ai_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=reply_content,
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)

    # 5. 异步更新长期记忆（不阻塞响应）
    await agent.update_memory_async(
        history=history + [
            {"role": "user", "content": body.content},
            {"role": "assistant", "content": reply_content},
        ],
        student_id=current_parent.student_id,
    )

    return ChatResponse(
        message_id=ai_message.id,
        content=reply_content,
        conversation_id=conversation_id,
    )
