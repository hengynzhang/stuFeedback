"""
AI 对话 Agent
核心流程：
1. 加载长期记忆 → 注入 system prompt
2. 将历史消息 + 新消息发给 DeepSeek
3. 若返回 tool_calls → 执行对应 DB 查询 → 将结果回传 → 继续对话
4. 直到返回纯文字回复为止
5. 异步更新长期记忆
"""

import json
import os
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from models import Student
from ai.tools import TOOL_SCHEMAS, ToolExecutor
from ai.memory import load_memory, extract_and_update_memory

CHAT_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

_api_key = os.getenv("DEEPSEEK_API_KEY")
client = AsyncOpenAI(api_key=_api_key, base_url="https://api.deepseek.com") if _api_key else None

MAX_TOOL_ROUNDS = 5  # 最多连续调用工具的轮数，防止无限循环


class ChatAgent:

    def __init__(self, db: Session, student_id: int):
        """
        student_id: ORM Student.id（整数主键，非8位学号）
        """
        self.db = db
        self.student_id = student_id
        self.executor = ToolExecutor(db=db, student_id=student_id)

    def _build_system_prompt(self, student_name: str, memory_text: str) -> str:
        base = f"""你是一位专业、亲切的学生学习情况助手，帮助家长实时了解孩子（{student_name}）的学习状态。

你的职责：
1. 根据家长的问题，调用工具查询孩子的课堂表现、考试成绩、作业情况等真实数据
2. 用简洁、温暖的语言将数据整理成家长易于理解的回答
3. 当家长询问建议时，结合孩子的真实数据给出有针对性的、实际可操作的建议
4. 只能访问 {student_name} 的数据，不可讨论其他学生的情况

注意事项：
- 回答基于真实数据，不要编造数据
- 如果数据库中暂无相关记录，如实告知家长
- 语气专业但不生硬，体现对孩子的关注"""

        if memory_text:
            base += f"\n\n{memory_text}"

        return base

    async def chat(
        self,
        history: List[Dict[str, str]],
        student_id: int,
    ) -> str:
        """
        主对话方法
        history: 本次对话的完整历史（含刚刚存入DB的用户消息）
        返回：AI 回复的文字内容
        """
        # 1. 获取学生姓名
        student = self.db.query(Student).filter(Student.id == self.student_id).first()
        student_name = student.full_name if student else "该学生"

        # 2. 加载长期记忆
        memory_text = load_memory(self.db, self.student_id)

        # 3. 构建消息列表
        system_prompt = self._build_system_prompt(student_name, memory_text)
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *history,
        ]

        # 4. Tool Calling 循环
        if client is None:
            return "AI 功能暂未配置，请联系管理员设置 DEEPSEEK_API_KEY。"

        for _ in range(MAX_TOOL_ROUNDS):
            response = await client.chat.completions.create(
                model=CHAT_MODEL,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.7,
            )

            choice = response.choices[0]

            # 没有 tool call → 直接返回最终回复
            if choice.finish_reason != "tool_calls":
                return choice.message.content

            # 有 tool call → 执行并将结果追加到 messages
            assistant_msg = choice.message
            messages.append(assistant_msg.model_dump(exclude_unset=True))

            for tool_call in assistant_msg.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                result = self.executor.execute(tool_name, arguments)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        # 超过最大轮数，强制请求纯文字回复
        messages.append({
            "role": "user",
            "content": "请直接用中文给出最终回答，不要再调用工具。"
        })
        final = await client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.7,
        )
        return final.choices[0].message.content

    async def update_memory_async(
        self,
        history: List[Dict[str, str]],
        student_id: int,
    ) -> None:
        """
        在 chat() 返回后异步调用，提取记忆并更新数据库
        失败不影响主流程
        """
        await extract_and_update_memory(
            db=self.db,
            student_id=self.student_id,
            conversation_history=history,
        )
