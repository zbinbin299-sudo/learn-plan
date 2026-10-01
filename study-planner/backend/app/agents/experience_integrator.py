from ..models.schemas import ExperienceBrief, GoalAnalysis, PlanRequest, StudyResource, StudyTask
from ..services.llm_client import complete_json


class ExperienceIntegrationAgent:
    name = "经验整合 Agent"

    async def run(
        self,
        request: PlanRequest,
        goal: GoalAnalysis,
        resources: list[StudyResource],
        unfinished: list[StudyTask],
    ) -> ExperienceBrief:
        context = [line.strip() for line in request.context_notes.splitlines() if line.strip()]
        if unfinished:
            context.append(f"识别到 {len(unfinished)} 项尚未完成的历史任务")
        try:
            result = await complete_json(
                "你是学习策略顾问。结合目标、历史任务与资料，给出可执行的学习策略、风险和已使用上下文。只返回 JSON，字段为 strategy（字符串）、risks（字符串数组）、context_used（字符串数组）。",
                {
                    "goal": goal.clarified_goal,
                    "milestones": goal.milestones,
                    "context": context,
                    "resources": [resource.title for resource in resources],
                    "weekly_hours": request.weekly_hours,
                },
            )
            if result:
                return ExperienceBrief(
                    strategy=result["strategy"],
                    risks=result.get("risks", []),
                    context_used=result.get("context_used", context[:6]),
                )
        except Exception:
            pass
        strategy = "采用主动回忆、间隔复习与小项目交替推进；每周留出一次复盘，按阶段产出检验掌握度。"
        if len(resources) > 0:
            strategy += " 资料先选一条主线，练习优先于囤积课程。"
        risks = []
        if request.weekly_hours < 3:
            risks.append("每周可用时间较少，优先保持稳定频率并缩小单次目标。")
        if goal.estimated_weeks <= 2:
            risks.append("目标周期较短，建议尽早做一次真实任务或模拟测验。")
        if unfinished:
            risks.append("先消化迁移任务，再增加新任务，避免计划持续堆积。")
        return ExperienceBrief(strategy=strategy, risks=risks, context_used=context[:6])