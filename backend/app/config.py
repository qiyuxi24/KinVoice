"""
应用配置管理 —— 从 .env 读取所有环境变量
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  
    )

    # 应用基础配置
    APP_NAME: str = "KinVoice"
    DEBUG: bool = True

    # CORS 允许的前端地址
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # 大模型配置 
    llm_api_key: str = "sk-your-key-here"
    llm_api_base: str = "https://your-endpoint.com/v1"
    llm_model: str = "qwen-plus"

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./data/kinvoice.db"

    # 日志 
    LOG_LEVEL: str = "INFO"

    # Azure TTS（后期可选）
    azure_speech_key: str = ""
    azure_speech_region: str = ""

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()