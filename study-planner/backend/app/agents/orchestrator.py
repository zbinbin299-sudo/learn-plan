import json
import logging

from ..models.schemas import AgentTrace, PlanRequest, StudyPlan
from ..services.context_memory import ContextMemory
from .experience_integrator import ExperienceIntegrationAgent
from .goal_parser import GoalParsingAgent
from .planning_coordinator import PlanningCoordinatorAgent
from .resource_search import ResourceSearchAgent


logger = logging.getLogger("uvicorn.error")


class StudyPlanningOrchestrator:
    def __init__(self) -> None:
        self.memory = ContextMemory()
        self.goal_agent = GoalParsingAgent()
        self.resource_agent = ResourceSearchAgent()
        self.experience_agent = ExperienceIntegrationAgent()
        self.coordinator_agent = PlanningCoordinatorAgent()

    async def create_plan(self, request: PlanRequest) -> StudyPlan:
        unfinished = self.memory.unfinished_tasks(request.learner_id)
        goal = await self.goal_agent.run(request)
        logger.info("Agent 输出 | %s | %s", self.goal_agent.name, json.dumps(goal.model_dump(mode="json"), ensure_ascii=False))
        resources, search_detail = await self.resource_agent.run(request)
        logger.info(
            "Agent 输出 | %s | %s",
            self.resource_agent.name,
            json.dumps(
                {
                    "detail": search_detail,
                    "resources": [resource.model_dump(mode="json") for resource in resources],
                },
                ensure_ascii=False,
            ),
        )
        experience = await self.experience_agent.run(request, goal, resources, unfinished)
        logger.info(
            "Agent 输出 | %s | %s",
            self.experience_agent.name,
            json.dumps(experience.model_dump(mode="json"), ensure_ascii=False),
        )
        tasks, phases = await self.coordinator_agent.run(request, goal, unfinished)
        logger.info(
            "Agent 输出 | %s | %s",
            self.coordinator_agent.name,
            json.dumps(
                {
                    "near_term_tasks": [task.model_dump(mode="json") for task in tasks],
                    "future_phases": [phase.model_dump(mode="json") for phase in phases],
                },
                ensure_ascii=False,
            ),
        )
        plan = StudyPlan(
            learner_id=request.learner_id,
            goal=goal,
            experience=experience,
            resources=resources,
            near_term_tasks=tasks,
            future_phases=phases,
            migrated_tasks_count=len(unfinished),
            agents=[
                AgentTrace(name=self.goal_agent.name, status="完成", detail="已拆解目标、前提和阶段里程碑。"),
                AgentTrace(name=self.resource_agent.name, status="完成", detail=search_detail),
                AgentTrace(name=self.experience_agent.name, status="完成", detail="已结合学习背景与历史任务整理策略。"),
                AgentTrace(name=self.coordinator_agent.name, status="完成", detail=f"近期安排 {len(tasks)} 项，远期划分 {len(phases)} 个阶段；迁移 {len(unfinished)} 项未完成任务。"),
            ],
        )
        self.memory.save_plan(plan)
        return plan