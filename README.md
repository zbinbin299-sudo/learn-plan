# 知序 · 学习规划助手

在 `learn-plan` 下与旅游助手并列运行的学习规划应用。近期按学习日生成逐项任务，远期按周生成阶段目标；任务状态和计划写入 SQLite，下一次规划时会读取未完成任务、提升优先级并迁移到新周期。

## 架构

- **目标解析 Agent**：整理目标、学习假设与里程碑。
- **资料搜索 Agent**：通过 MCP stdio 客户端连接外部资料搜索工具；未配置时显示可点击的搜索入口。
- **经验整合 Agent**：结合学习背景、历史任务与资料生成学习策略。
- **规划协调 Agent**：近期逐日排任务、远期按阶段规划，保留未完成任务 ID 与状态并重新安排。
- **统一数据契约**：后端 Pydantic 模型定义请求、计划、任务和 Agent 运行记录；前端 `src/types.ts` 按同一 JSON 字段建模。
- **模型服务**：可选 OpenAI 兼容 API。未配置模型 Key 时使用确定性规则，方便本地先运行和演示。

## 运行

终端一启动后端：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

终端二启动前端：

```bash
cd frontend
npm install
npm run dev
```

前端地址为 `http://localhost:5173`，API 文档为 `http://localhost:8000/docs`。没有 API Key 时也能生成和保存计划；要启用模型生成，把 `LLM_API_KEY`、`LLM_BASE_URL` 和 `LLM_MODEL` 填入 `backend/.env`。

## MCP 配置

在 `backend/.env` 设置 `MCP_COMMAND`、JSON 字符串数组 `MCP_ARGS` 和 `MCP_TOOL_NAME`。工具调用通过 MCP Python SDK 的 stdio transport 完成，传入 `{ "query": "学习主题和级别" }`；连接工具返回的文本和 URL 会整理为学习资料。不同 MCP 服务的工具参数不同时，可在 MCP 服务端增加适配工具，使其接受 `query` 参数。

## API

- `POST /api/plans/generate`：生成计划并读取、迁移历史未完成任务。
- `GET /api/plans/current?learner_id=...`：读取最近计划。
- `PATCH /api/tasks/{task_id}`：更新任务状态（`todo`、`in_progress`、`completed`）。
- `GET /api/health`：健康检查。

SQLite 默认保存在 `backend/data/study_planner.db`，可用 `DATABASE_PATH` 更改。
