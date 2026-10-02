import unittest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from app.agents.goal_parser import GoalParsingAgent
from app.models.schemas import PlanRequest


class GoalParsingTests(unittest.IsolatedAsyncioTestCase):
    @patch("app.agents.goal_parser.complete_json", new_callable=AsyncMock)
    async def test_duplicate_milestones_are_removed(self, complete_json):
        complete_json.return_value = {
            "clarified_goal": "三个月内掌握 Objective-C 并完成小项目",
            "milestones": ["Objective-C 基础", "Objective-C 基础", "完成小项目"],
        }
        request = PlanRequest(
            goal="三个月内掌握 Objective-C 并完成小项目",
            deadline=date.today() + timedelta(days=90),
        )

        result = await GoalParsingAgent().run(request)

        self.assertEqual(result.milestones, ["Objective-C 基础", "完成小项目"])

    @patch("app.agents.goal_parser.complete_json", new_callable=AsyncMock)
    async def test_repeated_only_milestone_uses_rule_fallback(self, complete_json):
        complete_json.return_value = {
            "clarified_goal": "学习 Objective-C",
            "milestones": ["Objective-C", "Objective-C", "Objective-C"],
        }
        request = PlanRequest(
            goal="学习 Objective-C",
            subject="Objective-C",
            deadline=date.today() + timedelta(days=60),
        )

        result = await GoalParsingAgent().run(request)

        self.assertGreaterEqual(len(result.milestones), 2)
        self.assertEqual(len(result.milestones), len({item.casefold() for item in result.milestones}))