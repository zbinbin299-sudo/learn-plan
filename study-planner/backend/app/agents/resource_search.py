from ..models.schemas import PlanRequest, StudyResource
from ..services.mcp_search import MCPResourceSearch


class ResourceSearchAgent:
    name = "资料搜索 Agent"

    def __init__(self) -> None:
        self.searcher = MCPResourceSearch()

    async def run(self, request: PlanRequest) -> tuple[list[StudyResource], str]:
        topic = request.subject or request.goal
        query = f"{topic} {request.current_level} 学习课程 文档 练习"
        return await self.searcher.search(query)