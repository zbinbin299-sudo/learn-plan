from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ..agents.orchestrator import StudyPlanningOrchestrator
from ..config import settings
from ..models.schemas import PlanRequest, StudyPlan, StudyTask, TaskStatusUpdate
from ..services.context_memory import ContextMemory

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "study-planner"}


@app.post("/api/plans/generate", response_model=StudyPlan)
async def generate_plan(request: PlanRequest) -> StudyPlan:
    return await StudyPlanningOrchestrator().create_plan(request)


@app.get("/api/plans/current", response_model=StudyPlan | None)
async def get_current_plan(learner_id: str = "default-learner") -> StudyPlan | None:
    return ContextMemory().latest_plan(learner_id)


@app.patch("/api/tasks/{task_id}", response_model=StudyTask)
async def update_task(task_id: str, update: TaskStatusUpdate) -> StudyTask:
    task = ContextMemory().update_task(task_id, update.status)
    if task is None:
        raise HTTPException(status_code=404, detail="找不到该学习任务")
    return task