"""
Tool Calling 定义模块 v3（家长/学生端）
已适配 LessonRecord 新模型（取代原 CourseSession）
"""

import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from models import Student, Class, LessonRecord, LessonPerformance, ExamRecord, HomeworkAssignment, HomeworkCompletion


# ─────────────────────────────────────────────
# 工具 JSON Schema（传给 DeepSeek）
# ─────────────────────────────────────────────

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_performance",
            "description": (
                "查询学生的课堂表现记录，包含课程主题、内容和教师反馈。"
                "可按科目筛选。适用于家长询问孩子课堂情况的问题。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "科目名称，如 '英语'、'数学'。不传则返回所有科目。"
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
                "可按科目筛选，也可查询某科目的历次成绩趋势。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
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
            "name": "get_homework_stats",
            "description": (
                "查询学生的作业布置和完成情况。"
                "可按科目筛选，适用于家长询问孩子作业完成率的问题。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
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
                "获取学生最近的综合概览，涵盖课堂表现、考试成绩和作业情况。"
                "适用于家长询问孩子整体学习状态或寻求综合建议的场景。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "各类记录各返回多少条，默认 5。",
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
        self.db         = db
        self.student_id = student_id  # ORM Student.id（非 8 位学号）

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
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

    def _get_performance(self, subject: Optional[str] = None, limit: int = 10) -> str:
        q = (self.db.query(LessonRecord, LessonPerformance)
             .join(LessonPerformance, LessonPerformance.lesson_record_id == LessonRecord.id)
             .filter(LessonPerformance.student_id == self.student_id))
        if subject:
            q = q.join(Class, LessonRecord.class_id == Class.id).filter(Class.subject == subject)
        rows = q.order_by(LessonRecord.lesson_date.desc()).limit(limit).all()

        if not rows:
            return "暂无课堂表现记录。"

        lines = ["【课堂表现记录】"]
        for lesson, perf in rows:
            time_str = ""
            if lesson.lesson_start_time:
                time_str = f" {lesson.lesson_start_time}"
                if lesson.lesson_end_time:
                    time_str += f"–{lesson.lesson_end_time}"
            lines.append(
                f"- {lesson.lesson_date}{time_str}"
                f"\n  课程主题：{lesson.topic or '未记录'}"
                f"\n  课程内容：{lesson.content_notes or '未记录'}"
                f"\n  学生表现：{perf.feedback or '未记录'}"
            )
        return "\n".join(lines)

    # ── 考试成绩 ────────────────────────────────

    def _get_exam_records(self, subject: Optional[str] = None, limit: int = 10) -> str:
        q = self.db.query(ExamRecord).filter(ExamRecord.student_id == self.student_id)
        if subject:
            q = q.filter(ExamRecord.subject == subject)
        records = q.order_by(ExamRecord.test_date.desc().nullslast()).limit(limit).all()

        if not records:
            return "暂无考试成绩记录。"

        lines = ["【考试成绩记录】"]
        for r in records:
            date_str  = str(r.test_date) if r.test_date else "未知日期"
            score_str = str(r.score) if r.score is not None else "未出分"
            total_str = f"/{r.total}" if r.total else ""
            notes_str = f"（备注：{r.notes}）" if r.notes else ""
            lines.append(f"- {date_str} | {r.subject} | 得分：{score_str}{total_str} {notes_str}")
        return "\n".join(lines)

    # ── 作业完成情况 ────────────────────────────

    def _get_homework_stats(self, subject: Optional[str] = None, limit: int = 10) -> str:
        q = (self.db.query(HomeworkAssignment, HomeworkCompletion)
             .join(HomeworkCompletion, HomeworkCompletion.homework_assignment_id == HomeworkAssignment.id)
             .filter(HomeworkCompletion.student_id == self.student_id))
        if subject:
            q = q.filter(HomeworkAssignment.subject == subject)
        rows = q.order_by(HomeworkAssignment.date.desc()).limit(limit).all()

        if not rows:
            return "暂无作业记录。"

        status_map = {
            "completed":     "✓ 已完成",
            "partial":       "△ 部分完成",
            "not_completed": "✗ 未完成",
        }
        lines = ["【作业完成情况】"]
        for assignment, completion in rows:
            status = status_map.get(completion.completion_status, completion.completion_status)
            lines.append(
                f"- {assignment.date} | {assignment.subject} | {status}"
                f"\n  作业内容：{assignment.homework or '未记录'}"
            )
        return "\n".join(lines)

    # ── 综合概览 ────────────────────────────────

    def _get_recent_overview(self, limit: int = 5) -> str:
        perf = self._get_performance(limit=limit)
        exam = self._get_exam_records(limit=limit)
        hw   = self._get_homework_stats(limit=limit)
        return f"{perf}\n\n{exam}\n\n{hw}"
