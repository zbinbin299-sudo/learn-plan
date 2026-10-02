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
        logger.info(
            "Agent 输出 | %s | milestones=%d estimated_weeks=%d",
            self.goal_agent.name,
            len(goal.milestones),
            goal.estimated_weeks,
        )
        resources, search_detail = await self.resource_agent.run(request)
        logger.info(
            "Agent 输出 | %s | resources=%d",
            self.resource_agent.name,
            len(resources),
        )
        experience = await self.experience_agent.run(request, goal, resources, unfinished)
        logger.info(
            "Agent 输出 | %s | risks=%d context_items=%d",
            self.experience_agent.name,
            len(experience.risks),
            len(experience.context_used),
        )
        tasks, phases = await self.coordinator_agent.run(request, goal, unfinished)
        logger.info(
            "Agent 输出 | %s | near_term_tasks=%d future_phases=%d migrated_tasks=%d",
            self.coordinator_agent.name,
            len(tasks),
            len(phases),
            len(unfinished),
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