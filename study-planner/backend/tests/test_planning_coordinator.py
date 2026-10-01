import unittest
from datetime import date, timedelta

from app.agents.planning_coordinator import PlanningCoordinatorAgent
from app.models.schemas import GoalAnalysis, PlanRequest, StudyTask, TaskStatus


class PlanningCoordinatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_unfinished_task_is_migrated_and_prioritized(self):
        old_due_date = date.today() - timedelta(days=3)
        old_task = StudyTask(
            id="unfinished-1",
            title="复习函数基础",
            description="补完练习",
            due_date=old_due_date,
            duration_minutes=45,
            priority=4,
            status=TaskStatus.in_progress,
        )
        request = PlanRequest(
            goal="掌握 Python 并完成项目",
            deadline=date.today() + timedelta(days=45),
            study_days_per_week=5,
        )
        goal = GoalAnalysis(
            clarified_goal=request.goal,
            milestones=["函数", "数据处理"],
            estimated_weeks=7,
        )

        tasks, phases = await PlanningCoordinatorAgent().run(request, goal, [old_task])

        migrated = next(task for task in tasks if task.id == old_task.id)
        self.assertTrue(migrated.migrated)
        self.assertEqual(migrated.migrated_from, old_due_date)
        self.assertGreaterEqual(migrated.due_date, date.today())
        self.assertEqual(migrated.priority, 3)
        self.assertEqual(migrated.status, TaskStatus.in_progress)
        self.assertTrue(phases)


if __name__ == "__main__":
    unittest.main()