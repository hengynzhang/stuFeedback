# 学生反馈系统

面向家长/学生的学情查询与 AI 对话平台，同时提供教师端的班级管理、数据录入与 AI 助手功能。

## 功能概览

### 家长/学生端
- 输入 8 位学号登录，查看孩子的学习情况
- 与 AI 助手对话，随时了解课堂表现、考试成绩、作业完成情况
- AI 可根据历史数据提供个性化学习建议
- 支持多轮对话，系统自动记忆家长关注点，跨会话持续生效

### 教师端
- **账号管理**：手机号 + 短信验证码注册（当前为 Mock 模式），手机号 + 密码登录，JWT 认证
- **班级管理**：新建/编辑/删除班级，设置科目、开班/结课日期、总课时数、班级状态
- **学生管理**：在指定班级内新建学生（自动生成 8 位学号），支持中英文姓名
- **课程记录**：以单节课为粒度录入课程，填写日期、时段、主题、内容，并为每位学生填写课堂反馈，支持行内编辑、失焦自动保存
- **考试成绩**：按学生、科目录入每次考试成绩，支持总分与备注
- **作业记录**：以班级为单位布置作业，点击切换每位学生的完成状态（已完成 / 部分完成 / 未完成）
- **教师 AI 助手**：教师端独立 AI 对话入口，可通过对话快速查询和分析班级数据

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python · FastAPI · SQLAlchemy · SQLite |
| 认证 | JWT（教师端）· Session Token（家长端）· passlib bcrypt |
| AI | DeepSeek API（OpenAI 兼容）· Tool Calling · 长期记忆 |
| 前端 | Next.js 14 · TypeScript · Tailwind CSS |

## 项目结构

```
stdFeedback/
├── backend/
│   ├── main.py              # FastAPI 入口（v3.0.0）
│   ├── models.py            # 数据库模型（SQLAlchemy）
│   ├── schemas.py           # Pydantic 校验模型
│   ├── database.py          # 数据库连接
│   ├── api/
│   │   ├── auth.py          # 教师注册/登录 + 家长学号登录
│   │   ├── teacher.py       # 教师端 CRUD 接口（班级/学生/课程/考试/作业）
│   │   ├── parent.py        # 家长端数据查询接口
│   │   ├── chat.py          # 对话管理接口（家长端 + 教师端）
│   │   └── deps.py          # 公共依赖（JWT 与 session 身份验证）
│   └── ai/
│       ├── agent.py         # AI 对话主流程（Tool Calling 循环）
│       ├── tools.py         # 工具定义与数据库查询执行
│       └── memory.py        # 长期记忆读取与更新
└── frontend/
    ├── lib/api.ts           # API 客户端与类型定义
    └── app/
        ├── page.tsx         # 首页（角色选择）
        ├── teacher/         # 教师端页面
        │   ├── login/       # 手机号 + 密码登录
        │   ├── register/    # 手机号 + 验证码注册
        │   ├── classes/     # 班级管理
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
Teacher（教师）
├── SMSVerification（短信验证码）
├── Class（班级）
│   ├── Student（学生）
│   │   ├── LessonPerformance（单节课表现）
│   │   ├── ExamRecord（考试成绩）
│   │   ├── HomeworkCompletion（作业完成情况）
│   │   ├── Parent（家长）
│   │   │   └── Conversation（家长对话）
│   │   │       └── Message（消息）
│   │   └── ConversationMemory（长期记忆）
│   ├── LessonRecord（课程记录）
│   │   └── LessonPerformance（学生课程表现）
│   └── HomeworkAssignment（作业布置）
│       └── HomeworkCompletion（作业完成情况）
└── TeacherConversation（教师 AI 对话）
    └── TeacherMessage（消息）
```

课程记录以**单节课**为粒度（`LessonRecord`），不再区分日粒度与周粒度。作业以班级为单位布置，各学生独立记录完成情况。

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
# 编辑 .env，填入 DEEPSEEK_API_KEY 和 SECRET_KEY

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
| `SECRET_KEY` | JWT 签名密钥（生产环境务必替换） | `dev-secret-key-change-in-production` |

**frontend/.env.local**

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | `http://localhost:8000/api` |

## 认证机制

### 教师端
1. **注册**：输入手机号，获取短信验证码（当前 Mock 模式直接返回验证码），设置密码后创建账号
2. **登录**：手机号 + 密码，成功后返回有效期 7 天的 JWT
3. 后续所有教师端请求携带 `Authorization: Bearer <token>` 请求头

### 家长/学生端
1. **登录**：输入 8 位学号，系统验证后返回 `session_token`
2. 后续请求通过 `session_token` 标识身份，数据严格隔离到当前绑定的学生

## AI 工作机制

### 家长端 AI
家长发送消息后的处理流程：

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

### 教师端 AI
教师登录后可通过 AI 助手对话，查询和分析班级整体或个人的学习数据，对话历史按教师账号独立存储。
