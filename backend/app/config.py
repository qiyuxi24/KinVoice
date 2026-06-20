"""
应用配置管理 —— 从 .env 读取所有环境变量
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
<<<<<<< Updated upstream
    # 大模型配置
    llm_api_key: str = "sk-your-key-here"
    llm_api_base: str = "https://your-endpoint.com/v1"
    llm_model: str = "qwen-plus"
=======
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用基础配置
    APP_NAME: str = "KinVoice"
    DEBUG: str = "true"  # str 类型避免与系统环境变量 DEBUG=release 冲突

    # CORS 允许的前端地址
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # 大模型配置 
    llm_api_key: str = "no"       # 模型接口密钥
    llm_api_base: str = "no"  # 模型接口根地址
    llm_model: str = "Volc-DeepSeek-V3.2"    # 模型名称
>>>>>>> Stashed changes

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./data/kinvoice.db"

    # 日志
    log_level: str = "info"

    # Azure TTS（后期可选）
    azure_speech_key: str = ""
    azure_speech_region: str = ""

    model_config = dict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
