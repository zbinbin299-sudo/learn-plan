import unittest
from datetime import date, timedelta

from pydantic import ValidationError

from app.models.schemas import GoalAnalysis, PlanRequest


class SchemaTests(unittest.TestCase):
    def test_past_deadline_is_rejected(self):
        with self.assertRaises(ValidationError):
            PlanRequest(goal="学习 Objective-C", deadline=date.today() - timedelta(days=1))

    def test_empty_milestones_are_rejected(self):
        with self.assertRaises(ValidationError):
            GoalAnalysis(clarified_goal="学习 Objective-C", milestones=[], estimated_weeks=8)