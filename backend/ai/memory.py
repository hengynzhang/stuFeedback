"""
长期记忆模块
- load_memory：读取该学生的历史记忆，格式化为 system prompt 注入字符串
- extract_and_update_memory：会话结束后，用 LLM 提取新记忆点并合并更新
"""

import json
import os
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from models import ConversationMemory

client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

MEMORY_MODEL = "deepseek-chat"


def load_memory(db: Session, student_id: int) -> str:
    """
    读取该学生的长期记忆，返回可直接注入 system prompt 的字符串
    若无记忆记录则返回空字符串
    """
    memory = db.query(ConversationMemory).filter(
        ConversationMemory.student_id == student_id
    ).first()

    if not memory or not memory.memory_content:
        return ""

    content: Dict[str, List[str]] = memory.memory_content
    parts = []

    if content.get("concerns"):
        parts.append("家长关注点：" + "；".join(content["concerns"]))
    if content.get("child_traits"):
        parts.append("孩子特点：" + "；".join(content["child_traits"]))
    if content.get("preferences"):
        parts.append("沟通偏好：" + "；".join(content["preferences"]))

    if not parts:
        return ""

    return "【关于这位家长和孩子的历史记忆】\n" + "\n".join(parts)


async def extract_and_update_memory(
    db: Session,
    student_id: int,
    conversation_history: List[Dict[str, str]],
) -> None:
    """
    从本次完整对话中提取关键记忆点，合并到该学生的长期记忆中
    在会话结束后异步调用，不阻塞主响应

    记忆结构：
    {
        "concerns":     [...],  # 家长关注的问题/话题
        "child_traits": [...],  # 孩子的学习特点/规律
        "preferences":  [...],  # 家长的沟通偏好/风格
    }
    """
    # 读取现有记忆
    existing_record = db.query(ConversationMemory).filter(
        ConversationMemory.student_id == student_id
    ).first()
    existing: Dict[str, List] = existing_record.memory_content if existing_record else {}

    # 构建提取 prompt
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in conversation_history
    )
    existing_text = json.dumps(existing, ensure_ascii=False)

    prompt = f"""你是一个记忆提取助手。请从以下对话中提取值得长期记忆的关键信息，并以 JSON 格式返回。

【现有记忆】
{existing_text}

【本次对话】
{history_text}

请提取或更新以下三类信息（每类最多保留5条最重要的，去除重复或过时的）：
- concerns: 家长在本次对话中关注的问题或话题（如"关注写作成绩"、"询问专注力问题"）
- child_traits: 孩子的学习特点或规律（如"听力基础较好"、"数学有进步趋势"）
- preferences: 家长的沟通偏好（如"偏好详细建议"、"希望对比历次成绩"）

只返回 JSON，格式如下，不要加任何其他文字：
{{"concerns": [...], "child_traits": [...], "preferences": [...]}}"""

    try:
        response = await client.chat.completions.create(
            model=MEMORY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()

        # 解析 JSON（防止 LLM 返回带 markdown 代码块）
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        new_memory: Dict[str, List] = json.loads(raw.strip())

        # 写回数据库
        if existing_record:
            existing_record.memory_content = new_memory
        else:
            db.add(ConversationMemory(
                student_id=student_id,
                memory_content=new_memory,
            ))
        db.commit()

    except Exception as e:
        # 记忆更新失败不影响主流程
        print(f"[memory] 更新失败：{e}")
