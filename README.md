# 智面舱 AI Interview Hub (系统开发规划书 V3.0 完整落地工程)

> **AI 驱动的下一代智能面试与人岗精准协同全栈系统**  
> 遵循规划书 V3.0 规范，提供学生端模拟面试与能力雷达诊断、企业端全流程招聘协同、管理后台平台治理与 AI 服务调度、公共门户四端一体化完整闭环。

---

## 一、 系统架构与工程目录

```
ai-interview-hub/
├── .venv/                    # Python 虚拟环境（依赖安装于此，已被 Git 忽略）
├── backend/                  # FastAPI 异步高性能后端
│   ├── app/
│   │   ├── ai/               # AI 引擎 (Mock沙箱 & Real双模式，Pydantic Schema 校验)
│   │   ├── api/v1/           # RESTful API 路由 (公共/认证/个人/企业/后台/文件)
│   │   ├── core/             # 配置、数据库会话、JWT安全与RBAC权限依赖
│   │   ├── models/           # SQLAlchemy 2.0 数据模型 (用户/企业/职位/简历/面试/系统)
│   │   ├── schemas/          # Pydantic v2 输入输出校验与序列化模式
│   │   └── websocket/        # WebSocket 实时交互面试室与流式事件
│   ├── scripts/              # 数据库初始化与全量 Demo 仿真种子数据
│   ├── tests/                # 自动化测试用例 (覆盖认证、API与越权防护)
│   ├── requirements.txt      # Python 依赖清单
│   └── main.py               # 后端服务启动入口 (端口 8000)
│
├── frontend/                 # Vue 3 + TypeScript + Vite + Element Plus 前端应用
│   ├── src/
│   │   ├── api/              # Axios 拦截器与集中式 API 接口调用封装
│   │   ├── components/       # 4态容器 (Loading/Empty/Error/Forbidden)、雷达图与折线图
│   │   ├── layouts/          # 公共/个人求职者/企业协同/平台管理四端独立布局
│   │   ├── router/           # Vue Router 全路由与 RBAC 严格导航守卫
│   │   ├── stores/           # Pinia 状态管理 (Token/UserInfo/权限判断)
│   │   ├── styles/           # 视觉规范附录 A 设计令牌与定制样式
│   │   └── views/            # 全量业务页面 (U01-U16, E01-E15, M01-M10, P01-P07, A01-A06)
│   ├── vite.config.ts        # 代理后端 API、WebSocket 与静态资源
│   └── package.json          # Node 依赖与编译脚本
│
├── uploads/                  # 本地上传目录（内容由 .gitignore 排除）
├── start_all.bat             # Windows 一键启动（后端 .venv + 前端，双窗口）
├── start_backend.bat         # 仅启动后端（使用 .venv 内的 uvicorn，端口 8000）
├── start_frontend.bat        # 仅启动前端（Vite，端口 5173）
├── docker-compose.yml        # 生产容器编排 (MySQL 8 + Redis 7 + Backend + Frontend)
├── .env.example              # 环境变量配置模板
└── .gitignore                # 排除依赖、构建产物、密钥、上传文件与本地数据库
```

---

## 二、 预置测试账号 (密码均为 `123456`)

首次运行种子脚本后，系统会生成完整公司、岗位、简历、投递及已评测面试数据，随后可使用以下账号登录：

| 角色 / 端入口 | 登录账号 | 初始密码 | 角色说明 |
|:---|:---|:---|:---|
| **个人求职者端** | `student@example.com` | `123456` | 拥有简历、模拟面试记录、成长雷达图与待办学习任务 |
| **企业创建人 (Owner)** | `owner@example.com` | `123456` | 华为技术有限公司超级管理员，享全权限 |
| **企业招聘负责人 (HR)** | `hr@example.com` | `123456` | 招聘主管，可发布岗位、推进看板与发送面试邀约 |
| **企业业务面试官** | `interviewer@example.com` | `123456` | 专职面试官，可查阅候选人档案与提交结构化评估 |
| **平台系统管理员** | `admin@example.com` | `123456` | 平台独立管理后台，审核资质、审核岗位与处置投诉 |

---

## 三、 本地极速启动指南（使用虚拟环境）

### 环境准备
- **后端**: Python 3.10+ (已在 3.13 验证)
- **前端**: Node.js 18+ (已在 Node 24 验证)
- 后端依赖统一安装在**项目根目录的 `.venv` 虚拟环境**中，启动脚本（`start_*.bat`）默认调用 `.venv\Scripts\python.exe`。请勿直接使用系统 `python`（可能解析到 Anaconda 等其他环境，导致 `ModuleNotFoundError: No module named 'jose'` 之类缺依赖错误）。

### 首次运行准备

**1) 创建本地环境变量文件**（`.env` 已被 Git 忽略），并将其中的密码与 `SECRET_KEY` 替换为自己的值：

```powershell
# Windows PowerShell
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

**2) 创建虚拟环境并安装后端依赖**（只需执行一次）：

```powershell
# Windows PowerShell（项目根目录）
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

> Windows 若执行 `.venv\Scripts\Activate.ps1` 被执行策略拦截，可先运行
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`；不激活也没关系，
> 直接用 `.venv\Scripts\python.exe` 完整路径调用即可。

**3) 安装前端依赖**（只需执行一次）：

```bash
cd frontend
npm install
cd ..
```

**4) （可选）初始化 Demo 种子数据**：首次运行、或需要重置并重新填充完整演示数据时执行：

```powershell
# Windows
cd backend
..\.venv\Scripts\python.exe scripts\seed_demo.py
cd ..
```

```bash
# macOS / Linux（已激活 .venv）
cd backend && python scripts/seed_demo.py && cd ..
```

### 启动方式一：一键启动（推荐，Windows）

在项目根目录**双击 `start_all.bat`**，会自动分别弹出两个窗口启动后端与前端：
- 前端访问地址：http://localhost:5173
- 后端 Swagger 接口文档：http://127.0.0.1:8000/docs

也可以分开双击 `start_backend.bat`（仅后端）与 `start_frontend.bat`（仅前端）。

### 启动方式二：命令行手动启动

**后端 API 服务**（监听 8000 端口，含热重载）：

```powershell
# Windows PowerShell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

```bash
# macOS / Linux（已激活 .venv）
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**前端页面服务**（新开一个终端，Vite 已配置代理 `/api`、`/ws`、`/uploads` → 127.0.0.1:8000）：

```bash
cd frontend
npm run dev
```

- 后端服务地址：http://127.0.0.1:8000
- 交互式 Swagger API 文档：http://127.0.0.1:8000/docs
- 前端访问地址：http://localhost:5173

### (可选) Docker 一键容器化编排运行
```bash
# 确认已从 .env.example 创建并修改 .env，然后在项目根目录执行
docker-compose up -d --build
```

---

## 四、 核心业务闭环与验证流程

### 闭环 1：求职者端自我诊断与成长闭环
1. 使用 `student@example.com` 登录系统，进入 **个人工作台 (U01)**。
2. 进入 **简历中心 (U04)**，点击 **简历 AI 诊断 (U06)**，系统调用解析引擎生成针对岗位的诊断打分与优化建议。
3. 点击 **创建模拟面试 (U08)**，选择针对岗位，系统自动从题库或 AI 生成多道结构化面试题。
4. 进入 **实时模拟面试间 (U09)**，支持文字/语音输入，答题后实时调用 AI 六维 Rubric 评分引擎打分。
5. 完成面试后自动生成 **面试诊断报告 (U11)**，展示五维胜任力雷达图及雷达短板。
6. 点击进入 **成长中心 (U12)** 与 **AI 学习路线图 (U13)**，完成针对性弱项练习任务并核销进阶。

### 闭环 2：企业端人岗匹配与全流程招聘闭环
1. 使用 `hr@example.com` 登录，进入 **企业工作台 (E01)**。
2. 进入 **职位管理 (E02)** -> **发布新岗位 (E03)**，使用 **AI 智能解析 JD** 自动填充字段并校验五维权重之和为 100%。
3. 进入 **候选人管理 (E06)** 与 **招聘流程看板 (E08)**，查看求职者简历匹配度（AI 打分）。
4. 点击候选人卡片进入 **档案详情 (E07)**，点击 **发起面试邀请** 或 **推进招聘阶段**。
5. 面试结束后，在 **面试管理 (E09)** 中点击 **面试官评价 (E11)**，结构化填写打分、优势分析与录用决策（Offer）。

### 闭环 3：平台管理治理与安全闭环
1. 使用 `admin@example.com` 登录 **管理后台 (/admin/login)**。
2. 在 **企业资质审核 (M05)** 中审核企业提交的营业执照与法人信息，执行通过或驳回。
3. 在 **职位发布审核 (M06)** 中核查企业待发布岗位，执行批准上线或违规强制下架（实时向企业发送站内信通知）。
4. 在 **AI 服务与脱敏日志 (M09)** 中切换沙箱 Mock 与真实大语言模型，查阅脱敏安全调用记录。
5. 验证 **安全防护 (SEC-01 至 SEC-07)**：
   - 越权访问防护：企业账户访问他人模拟面试强制触发 403 Forbidden。
   - 普通管理员试图封禁超级管理员触发 SEC-05 保护拦截。

---

## 五、 规划书功能矩阵对照表

- [x] **公共门户** (P01 首页, P02 职位广场, P03 职位详情, P04 企业主页, P05 核心特性, P06 关于我们, P07 帮助中心)
- [x] **认证流程** (A01 登录, A02 注册选择, A03 个人注册, A04 企业注册, A05 入驻指引, A06 找回密码, M01 后台登录)
- [x] **个人求职者端** (U01 工作台, U02 岗位探索, U03 投递进度, U04 简历列表, U05 简历编辑, U06 简历诊断, U07 胜任力评估, U08 创建面试, U09 实时面试间, U10 模拟面试列表, U11 诊断报告, U12 成长中心, U13 学习路线, U14 消息通知, U15 个人档案, U16 账号安全)
- [x] **企业协作端** (E01 工作台, E02 职位列表, E03 发布岗位, E04 编辑岗位, E06 候选人筛选, E07 档案详情, E08 看板流转, E09 面试管理, E11 面试官打分, E12 人才库, E13 数据中心, E14 成员权限, E15 资质认证)
- [x] **平台管理端** (M02 运营总览, M03 用户治理, M04 企业治理, M05 资质审核, M06 岗位合规, M07 投诉处置, M08 内容配置, M09 AI引擎, M10 审计日志)
- [x] **核心技术规范** (SEC-01~07 安全准则, 4 态统一容器, ECharts 雷达图, 零 mock 动态接口对接, SQLite/MySQL 实体持久化)
