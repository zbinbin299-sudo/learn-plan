from datetime import date, timedelta
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    completed = "completed"


class PlanRequest(BaseModel):
    learner_id: str = Field(default="default-learner", min_length=1, max_length=80)
    goal: str = Field(min_length=4, max_length=500)
    subject: str = Field(default="", max_length=100)
    current_level: str = Field(default="初学者", max_length=100)
    weekly_hours: float = Field(default=6, gt=0, le=60)
    study_days_per_week: int = Field(default=5, ge=1, le=7)
    session_minutes: int = Field(default=60, ge=15, le=240)
    deadline: date = Field(default_factory=lambda: date.today() + timedelta(days=60))
    context_notes: str = Field(default="", max_length=2000)

    @field_validator("deadline")
    @classmethod
    def deadline_must_not_be_in_the_past(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("目标日期不能早于今天")
        return value


class GoalAnalysis(BaseModel):
    clarified_goal: str
    assumptions: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(min_length=1, max_length=5)
    estimated_weeks: int = Field(ge=1)


class StudyResource(BaseModel):
    title: str
    url: Optional[str] = None
    summary: str = ""
    source: str = "建议入口"


class ExperienceBrief(BaseModel):
    strategy: str
    risks: list[str] = Field(default_factory=list)
    context_used: list[str] = Field(default_factory=list)


class StudyTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    due_date: date
    duration_minutes: int = Field(ge=5)
    priority: int = Field(ge=1, le=5)
    status: TaskStatus = TaskStatus.todo
    migrated: bool = False
    migrated_from: Optional[date] = None


class StudyPhase(BaseModel):
    title: str
    starts_on: date
    ends_on: date
    focus: str
    outcome: str


class AgentTrace(BaseModel):
    name: str
    status: str
    detail: str


class StudyPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    learner_id: str
    goal: GoalAnalysis
    experience: ExperienceBrief
    resources: list[StudyResource] = Field(default_factory=list)
    near_term_tasks: list[StudyTask] = Field(default_factory=list)
    future_phases: list[StudyPhase] = Field(default_factory=list)
    migrated_tasks_count: int = 0
    agents: list[AgentTrace] = Field(default_factory=list)
    generated_at: date = Field(default_factory=date.today)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus