# 学生反馈系统

面向家长的学情查询与 AI 对话平台，同时提供教师端的数据录入管理功能。

## 功能概览

### 家长端
- 输入 8 位学号登录，查看孩子的学习情况
- 与 AI 助手对话，随时了解课堂表现、考试成绩、作业完成情况
- AI 可根据历史数据提供个性化学习建议
- 支持多轮对话，系统自动记忆家长关注点，跨会话持续生效

### 教师端
- 学生管理：新建学生，自动生成 8 位学号
- 课程记录：录入每节课（或每周）的课程内容与各学生表现，支持行内编辑、失焦自动保存
- 考试成绩：按学生、科目录入每次考试成绩
- 作业记录：录入作业内容，点击切换每位学生的完成状态（已完成 / 部分完成 / 未完成）

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python · FastAPI · SQLAlchemy · SQLite |
| AI | DeepSeek API（OpenAI 兼容）· Tool Calling · 长期记忆 |
| 前端 | Next.js 14 · TypeScript · Tailwind CSS |

## 项目结构

```
stdFeedback/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── models.py            # 数据库模型（SQLAlchemy）
│   ├── schemas.py           # Pydantic 校验模型
│   ├── database.py          # 数据库连接
│   ├── api/
│   │   ├── auth.py          # 家长登录认证
│   │   ├── teacher.py       # 教师端 CRUD 接口
│   │   ├── parent.py        # 家长端数据查询接口
│   │   ├── chat.py          # 对话管理接口
│   │   └── deps.py          # 公共依赖（身份验证）
│   └── ai/
│       ├── agent.py         # AI 对话主流程（Tool Calling 循环）
│       ├── tools.py         # 工具定义与数据库查询执行
│       └── memory.py        # 长期记忆读取与更新
└── frontend/
    ├── lib/api.ts           # API 客户端与类型定义
    └── app/
        ├── page.tsx         # 首页（角色选择）
        ├── teacher/         # 教师端页面
        │   ├── students/    # 学生管理
        │   ├── records/     # 课程记录
        │   ├── exams/       # 考试成绩
        │   └── homework/    # 作业记录
        └── parent/          # 家长端页面
            ├── login/       # 学号登录
            └── chat/        # AI 对话
```

## 数据模型

```
Student（学生）
├── CourseSession（课程单元）
│   └── StudentPerformance（学生课程反馈）
├── ExamRecord（考试成绩）
├── HomeworkAssignment（作业布置）
│   └── HomeworkCompletion（作业完成情况）
└── Parent（家长）
    └── Conversation（对话）
        └── Message（消息）
```

数据录入支持**日粒度**（具体某一天的课程）和**周粒度**（每周综合总结）两种模式，由教师根据实际情况灵活选择。

## 本地运行

### 前置要求

- Python 3.11+
- Node.js 18+
- DeepSeek API Key（[申请地址](https://platform.deepseek.com/)）

### 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 启动（数据库文件会自动创建）
python main.py
```

后端默认运行在 `http://localhost:8000`，API 文档见 `http://localhost:8000/docs`。

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动
npm run dev
```

前端默认运行在 `http://localhost:3000`。

## 环境变量

**backend/.env**

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接地址 | `sqlite:///./student_records.db` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 必填 |
| `DEEPSEEK_MODEL` | 使用的模型 | `deepseek-chat` |

**frontend/.env.local**

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | `http://localhost:8000/api` |

## AI 工作机制

家长发送消息后，AI 的处理流程如下：

```
家长提问
  ↓
加载长期记忆（该学生的历史关注点）
  ↓
DeepSeek 判断意图，选择调用工具：
  ├── get_performance()     → 查询课堂表现
  ├── get_exam_records()    → 查询考试成绩
  ├── get_homework_stats()  → 查询作业完成率
  └── get_recent_overview() → 综合近期概览
  ↓
基于真实数据生成自然语言回复
  ↓（异步）
提取关键信息，更新长期记忆
```

所有数据查询均严格限定在当前家长绑定的学生范围内，不同家长之间数据完全隔离。
