import unittest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from app.agents.planning_coordinator import PlanningCoordinatorAgent
from app.models.schemas import GoalAnalysis, PlanRequest, StudyTask, TaskStatus


class PlanningCoordinatorTests(unittest.IsolatedAsyncioTestCase):
    def test_study_dates_are_spread_across_the_week(self):
        monday = date.today() - timedelta(days=date.today().weekday())

        dates = PlanningCoordinatorAgent._study_dates(monday, 3)

        self.assertEqual([day.weekday() for day in dates], [0, 2, 4, 0, 2, 4])

    @patch("app.agents.planning_coordinator.complete_json", new_callable=AsyncMock)
    async def test_near_term_tasks_do_not_exceed_deadline(self, complete_json):
        complete_json.return_value = None
        request = PlanRequest(
            goal="学习 Objective-C 基础",
            deadline=date.today() + timedelta(days=3),
            study_days_per_week=3,
        )
        goal = GoalAnalysis(
            clarified_goal=request.goal,
            milestones=["语法基础", "完成练习"],
            estimated_weeks=1,
        )

        tasks, _ = await PlanningCoordinatorAgent().run(request, goal, [])

        self.assertTrue(tasks)
        self.assertTrue(all(task.due_date <= request.deadline for task in tasks))

    @patch("app.agents.planning_coordinator.complete_json", new_callable=AsyncMock)
    async def test_malformed_model_sessions_fall_back_to_template(self, complete_json):
        complete_json.return_value = {"sessions": ["not-an-object"]}
        request = PlanRequest(
            goal="学习 Objective-C 基础",
            deadline=date.today() + timedelta(days=45),
            study_days_per_week=3,
        )
        goal = GoalAnalysis(
            clarified_goal=request.goal,
            milestones=["语法基础", "完成练习"],
            estimated_weeks=7,
        )

        tasks, _ = await PlanningCoordinatorAgent().run(request, goal, [])

        self.assertEqual(len(tasks), 6)
        self.assertTrue(all(task.title and task.description for task in tasks))

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