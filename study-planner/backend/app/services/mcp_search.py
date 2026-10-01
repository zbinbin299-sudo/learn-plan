import json
import os
import re
from urllib.parse import quote_plus

from ..config import settings
from ..models.schemas import StudyResource


class MCPResourceSearch:
    async def search(self, query: str) -> tuple[list[StudyResource], str]:
        if not settings.mcp_command:
            return self._suggested_resources(query), "未配置 MCP 服务，返回可搜索的学习入口"

        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            arguments = json.loads(settings.mcp_args)
            if not isinstance(arguments, list) or not all(isinstance(item, str) for item in arguments):
                raise ValueError("MCP_ARGS 必须是字符串数组")
            server = StdioServerParameters(
                command=settings.mcp_command,
                args=arguments,
                env=os.environ.copy(),
            )
            async with stdio_client(server) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    response = await session.call_tool(settings.mcp_tool_name, {"query": query})
            if response.isError:
                raise RuntimeError("MCP 工具返回错误")
            resources = self._parse_result(response)
            if resources:
                return resources, f"已通过 MCP 工具 {settings.mcp_tool_name} 获取资料"
            return self._suggested_resources(query), "MCP 已响应，但未返回可识别资料"
        except Exception as error:
            return self._suggested_resources(query), f"MCP 调用失败，已提供搜索入口：{error}"

    @staticmethod
    def _parse_result(result: object) -> list[StudyResource]:
        resources: list[StudyResource] = []
        for item in getattr(result, "content", []):
            text = getattr(item, "text", "").strip()
            if not text:
                continue
            urls = re.findall(r"https?://[^\s)\]]+", text)
            resources.append(
                StudyResource(
                    title=text[:72],
                    url=urls[0].rstrip(".,") if urls else None,
                    summary=text[:280],
                    source="MCP",
                )
            )
        return resources[:8]

    @staticmethod
    def _suggested_resources(query: str) -> list[StudyResource]:
        encoded = quote_plus(query)
        return [
            StudyResource(
                title=f"搜索：{query}",
                url=f"https://www.google.com/search?q={encoded}",
                summary="按主题检索课程、文档和练习资料。配置 MCP 搜索服务后可自动获取具体结果。",
            ),
            StudyResource(
                title=f"视频课程：{query}",
                url=f"https://www.bilibili.com/search?keyword={encoded}",
                summary="查找讲解与实操演示，优先选择带章节和练习的系列内容。",
            ),
        ]