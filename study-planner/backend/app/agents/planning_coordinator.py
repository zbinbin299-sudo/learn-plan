from datetime import date, timedelta

from ..models.schemas import GoalAnalysis, PlanRequest, StudyPhase, StudyTask, TaskStatus
from ..services.llm_client import complete_json


class PlanningCoordinatorAgent:
    name = "规划协调 Agent"

    async def run(
        self,
        request: PlanRequest,
        goal: GoalAnalysis,
        unfinished: list[StudyTask],
    ) -> tuple[list[StudyTask], list[StudyPhase]]:
        today = date.today()
        task_dates = self._study_dates(today, request.study_days_per_week, request.deadline)
        near_tasks: list[StudyTask] = []

        for index, old_task in enumerate(unfinished):
            near_tasks.append(
                old_task.model_copy(
                    update={
                        "due_date": task_dates[min(index, len(task_dates) - 1)],
                        "priority": max(1, old_task.priority - 1),
                        "migrated": True,
                        "migrated_from": old_task.migrated_from or old_task.due_date,
                    }
                )
            )

        planned_sessions = min(14, max(4, request.study_days_per_week * 2))
        new_sessions = max(2, planned_sessions - min(len(unfinished), planned_sessions - 2))
        session_ideas = []
        try:
            result = await complete_json(
                "你是学习计划协调专家。为给定里程碑生成指定数量的近期学习任务，任务要小而具体，包含 title 和 description。只返回 JSON，格式为 {\"sessions\":[{\"title\":\"...\",\"description\":\"...\"}]}。",
                {"milestones": goal.milestones, "count": new_sessions, "minutes_per_session": request.session_minutes},
            )
            raw_session_ideas = result.get("sessions", []) if isinstance(result, dict) else []
            if isinstance(raw_session_ideas, list):
                session_ideas = [
                    {
                        "title": idea.get("title", "") if isinstance(idea.get("title"), str) else "",
                        "description": idea.get("description", "") if isinstance(idea.get("description"), str) else "",
                    }
                    for idea in raw_session_ideas
                    if isinstance(idea, dict)
                ]
        except Exception:
            session_ideas = []
        for index in range(new_sessions):
            milestone = goal.milestones[index % len(goal.milestones)]
            session_number = index + 1
            idea = session_ideas[index] if index < len(session_ideas) else {}
            near_tasks.append(
                StudyTask(
                    title=idea.get("title", "").strip() or f"第 {session_number} 次学习：{milestone}",
                    description=idea.get("description", "").strip() or self._task_detail(milestone, index),
                    due_date=task_dates[min(len(unfinished) + index, len(task_dates) - 1)],
                    duration_minutes=request.session_minutes,
                    priority=2 if index < 2 else 3,
                )
            )

        return near_tasks, self._future_phases(today, request.deadline, goal)

    @staticmethod
    def _study_dates(start: date, study_days_per_week: int, deadline: date | None = None) -> list[date]:
        weekdays = {index * 7 // study_days_per_week for index in range(study_days_per_week)}
        last_day = min(start + timedelta(days=13), deadline) if deadline else start + timedelta(days=13)
        dates = [
            start + timedelta(days=offset)
            for offset in range((last_day - start).days + 1)
            if (start + timedelta(days=offset)).weekday() in weekdays
        ]
        return dates or [start]

    @staticmethod
    def _task_detail(milestone: str, index: int) -> str:
        activities = ["学习核心概念并做笔记", "完成针对性练习并记录错因", "脱离资料复述，再用小任务验证"]
        return f"{activities[index % len(activities)]}：{milestone}。结束时写下一个仍不确定的问题。"

    @staticmethod
    def _future_phases(start: date, deadline: date, goal: GoalAnalysis) -> list[StudyPhase]:
        cursor = start + timedelta(days=14)
        phases = []
        phase_index = 0
        while cursor <= deadline:
            end = min(cursor + timedelta(days=6), deadline)
            focus = goal.milestones[phase_index % len(goal.milestones)]
            phases.append(
                StudyPhase(
                    title=f"第 {phase_index + 3} 周 · {focus}",
                    starts_on=cursor,
                    ends_on=end,
                    focus=focus,
                    outcome=f"完成“{focus}”相关练习，并形成可检查的阶段成果。",
                )
            )
            cursor = end + timedelta(days=1)
            phase_index += 1
        return phases