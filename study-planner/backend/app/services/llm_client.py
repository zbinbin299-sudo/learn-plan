import json

import httpx

from ..config import settings


async def complete_json(system_prompt: str, user_payload: dict) -> dict | None:
    if not settings.llm_api_key:
        return None
    async with httpx.AsyncClient(timeout=35) as client:
        response = await client.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json={
                "model": settings.llm_model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
                ],
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content)
        content = content.strip().removeprefix("```json").removesuffix("```").strip()
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None