from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "学习规划助手"
    host: str = "0.0.0.0"
    port: int = 8000
    mcp_command: str = ""
    mcp_args: str = "[]"
    mcp_tool_name: str = "search"
    database_path: str = "data/study_planner.db"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def resolved_database_path(self) -> Path:
        path = Path(self.database_path)
        return path if path.is_absolute() else Path(__file__).resolve().parents[1] / path


settings = Settings()