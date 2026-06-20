"""
KinVoice 后端 —— FastAPI 入口
"""
# main.py主要负责将用户的CRUD请求进行路由分发(分发后各部分分别执行各自的任务)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.utils.logger import logger
from app.api.convert import router as convert_router
from app.api.memory import router as memory_router
from app.api.chat import router as chat_router 

app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS(用来放行合法的跨域请求)
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动事件
@app.on_event("startup")
async def startup():
    logger.info(f"应用 {settings.APP_NAME} 启动成功")

# 运行状态测试
@app.get("/ping")
async def ping():
    return {"status": "ok"}


# NVC非暴力沟通转换功能
app.include_router(convert_router)

# 与AI(cloudie)聊天的接口
app.include_router(chat_router)

# 记忆卡片功能
app.include_router(memory_router)