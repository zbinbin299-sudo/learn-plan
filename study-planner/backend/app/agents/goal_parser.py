import math
import re
from datetime import date

from ..models.schemas import GoalAnalysis, PlanRequest
from ..services.llm_client import complete_json


class GoalParsingAgent:
    name = "目标解析 Agent"

    async def run(self, request: PlanRequest) -> GoalAnalysis:
        try:
            result = await complete_json(
                "你是学习目标分析专家。把目标转成清晰可执行的结果和 2-5 个不重复的阶段里程碑。里程碑应是具体学习成果，不要重复目标原文。只返回 JSON，字段为 clarified_goal、assumptions（字符串数组）、milestones（字符串数组）。",
                request.model_dump(mode="json"),
            )
            clarified_goal = result.get("clarified_goal") if isinstance(result, dict) else None
            milestones = self._clean_strings(result.get("milestones")) if isinstance(result, dict) else []
            assumptions = self._clean_strings(result.get("assumptions")) if isinstance(result, dict) else []
            if isinstance(clarified_goal, str) and clarified_goal.strip() and len(milestones) >= 2:
                return GoalAnalysis(
                    clarified_goal=clarified_goal.strip(),
                    assumptions=assumptions,
                    milestones=milestones[:5],
                    estimated_weeks=max(1, math.ceil((request.deadline - date.today()).days / 7)),
                )
        except Exception:
            pass
        return self._fallback(request)

    def _fallback(self, request: PlanRequest) -> GoalAnalysis:
        subject = request.subject.strip()
        clarified = request.goal.strip()
        if subject:
            clarified = f"围绕{subject}，{clarified}"
        parts = [part.strip() for part in re.split(r"[，,；;。\n]+", request.goal) if part.strip()]
        milestones = self._clean_strings(parts)[:4]
        if len(milestones) < 2:
            milestones = [
                f"建立{subject or '目标主题'}的核心知识框架",
                f"完成{subject or '目标主题'}的阶段练习",
                f"独立完成与“{request.goal[:24]}”相关的成果",
            ]
        estimated_weeks = max(1, math.ceil((request.deadline - date.today()).days / 7))
        return GoalAnalysis(
            clarified_goal=clarified,
            assumptions=[f"按每周约 {request.weekly_hours:g} 小时安排", f"当前水平：{request.current_level}"],
            milestones=milestones,
            estimated_weeks=estimated_weeks,
        )

    @staticmethod
    def _clean_strings(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        cleaned = []
        seen = set()
        for item in value:
            if not isinstance(item, str):
                continue
            text = re.sub(r"\s+", " ", item).strip()
            key = text.casefold()
            if text and key not in seen:
                cleaned.append(text)
                seen.add(key)
        return cleaned