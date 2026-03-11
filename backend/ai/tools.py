"""
Tool Calling 定义模块
包含两部分：
1. TOOL_SCHEMAS  — 传给 DeepSeek API 的 JSON 描述，告诉模型有哪些工具可用
2. ToolExecutor  — 实际执行 DB 查询的 Python 函数，结果以自然语言字符串返回供 LLM 使用
"""

import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from models import Student, CourseSession, StudentPerformance, ExamRecord, HomeworkAssignment, HomeworkCompletion


# ─────────────────────────────────────────────
# 工具 JSON Schema（传给 DeepSeek）
# ─────────────────────────────────────────────

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_performance",
            "description": (
                "查询学生的课堂表现记录，包含科目、课程内容和教师反馈。"
                "可按周次和科目筛选。适用于家长询问孩子课堂情况的问题。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "week": {
                        "type": "string",
                        "description": "周次，如 'Week 1'。不传则返回最近记录。"
                    },
                    "subject": {
                        "type": "string",
                        "description": "科目名称，如 '听力'、'数学'、'写作'。不传则返回所有科目。"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数上限，默认 10。",
                        "default": 10
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exam_records",
            "description": (
                "查询学生的考试成绩记录。"
                "可按科目和周次筛选，也可查询某科目的历次成绩趋势。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "科目名称，如 '听力'、'阅读'。不传则返回所有科目。"
                    },
                    "week": {
                        "type": "string",
                        "description": "周次，如 'Week 2'。不传则不按周过滤。"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数上限，默认 10。",
                        "default": 10
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_homework_stats",
            "description": (
                "查询学生的作业布置和完成情况。"
                "可按周次和科目筛选，适用于家长询问孩子作业完成率的问题。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "week": {
                        "type": "string",
                        "description": "周次，如 'Week 1'。不传则返回最近记录。"
                    },
                    "subject": {
                        "type": "string",
                        "description": "科目名称。不传则返回所有科目。"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数上限，默认 10。",
                        "default": 10
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_overview",
            "description": (
                "获取学生最近几周的综合概览，涵盖课堂表现、考试成绩和作业情况。"
                "适用于家长询问孩子整体学习状态或寻求综合建议的场景。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "weeks": {
                        "type": "integer",
                        "description": "查询最近几条记录（按时间倒序），默认 5。",
                        "default": 5
                    },
                },
                "required": [],
            },
        },
    },
]


# ─────────────────────────────────────────────
# 工具执行器
# ─────────────────────────────────────────────

class ToolExecutor:
    """
    执行 DeepSeek 选择的工具，返回自然语言格式的结果字符串
    所有查询均严格限定在 student_id 范围内
    """

    def __init__(self, db: Session, student_id: int):
        self.db = db
        self.student_id = student_id  # ORM Student.id（非8位学号）

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """统一入口，根据工具名分发"""
        dispatch = {
            "get_performance":     self._get_performance,
            "get_exam_records":    self._get_exam_records,
            "get_homework_stats":  self._get_homework_stats,
            "get_recent_overview": self._get_recent_overview,
        }
        func = dispatch.get(tool_name)
        if not func:
            return f"未知工具：{tool_name}"
        return func(**arguments)

    # ── 课堂表现 ────────────────────────────────

    def _get_performance(
        self,
        week: Optional[str] = None,
        subject: Optional[str] = None,
        limit: int = 10,
    ) -> str:
        q = (
            self.db.query(CourseSession, StudentPerformance)
            .join(StudentPerformance, StudentPerformance.course_session_id == CourseSession.id)
            .filter(StudentPerformance.student_id == self.student_id)
        )
        if week:
            q = q.filter(CourseSession.week == week)
        if subject:
            q = q.filter(CourseSession.subject == subject)

        rows = q.order_by(CourseSession.date.desc().nullslast()).limit(limit).all()

        if not rows:
            return "暂无课堂表现记录。"

        lines = ["【课堂表现记录】"]
        for session, perf in rows:
            date_str = str(session.date) if session.date else session.week or "未知日期"
            lines.append(
                f"- {date_str} {session.day_of_week or ''} | {session.subject}"
                f" | 授课教师：{session.teacher_name or '未记录'}"
                f"\n  课程内容：{session.course_content or '未记录'}"
                f"\n  学生表现：{perf.feedback or '未记录'}"
            )
        return "\n".join(lines)

    # ── 考试成绩 ────────────────────────────────

    def _get_exam_records(
        self,
        subject: Optional[str] = None,
        week: Optional[str] = None,
        limit: int = 10,
    ) -> str:
        q = self.db.query(ExamRecord).filter(ExamRecord.student_id == self.student_id)
        if subject:
            q = q.filter(ExamRecord.subject == subject)
        if week:
            q = q.filter(ExamRecord.week == week)

        records = q.order_by(ExamRecord.test_date.desc().nullslast()).limit(limit).all()

        if not records:
            return "暂无考试成绩记录。"

        lines = ["【考试成绩记录】"]
        for r in records:
            date_str = str(r.test_date) if r.test_date else r.week or "未知日期"
            score_str = f"{r.score}" if r.score is not None else "未出分"
            total_str = f"/{r.total}" if r.total else ""
            notes_str = f"（备注：{r.notes}）" if r.notes else ""
            lines.append(
                f"- {date_str} | {r.subject} | 得分：{score_str}{total_str} {notes_str}"
            )
        return "\n".join(lines)

    # ── 作业完成情况 ────────────────────────────

    def _get_homework_stats(
        self,
        week: Optional[str] = None,
        subject: Optional[str] = None,
        limit: int = 10,
    ) -> str:
        q = (
            self.db.query(HomeworkAssignment, HomeworkCompletion)
            .join(HomeworkCompletion, HomeworkCompletion.homework_assignment_id == HomeworkAssignment.id)
            .filter(HomeworkCompletion.student_id == self.student_id)
        )
        if week:
            q = q.filter(HomeworkAssignment.week == week)
        if subject:
            q = q.filter(HomeworkAssignment.subject == subject)

        rows = q.order_by(HomeworkAssignment.date.desc().nullslast()).limit(limit).all()

        if not rows:
            return "暂无作业记录。"

        status_map = {
            "completed":     "✓ 已完成",
            "partial":       "△ 部分完成",
            "not_completed": "✗ 未完成",
        }
        lines = ["【作业完成情况】"]
        for assignment, completion in rows:
            date_str = str(assignment.date) if assignment.date else assignment.week or "未知日期"
            status = status_map.get(completion.completion_status, completion.completion_status)
            lines.append(
                f"- {date_str} | {assignment.subject} | {status}"
                f"\n  作业内容：{assignment.homework or '未记录'}"
            )
        return "\n".join(lines)

    # ── 综合概览 ────────────────────────────────

    def _get_recent_overview(self, weeks: int = 5) -> str:
        perf = self._get_performance(limit=weeks)
        exam = self._get_exam_records(limit=weeks)
        hw   = self._get_homework_stats(limit=weeks)
        return f"{perf}\n\n{exam}\n\n{hw}"
