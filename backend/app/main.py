"""
KinVoice 后端 —— FastAPI 入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.convert import router as convert_router
from app.api.chat import router as chat_router
from app.api.memory import router as memory_router
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info("KinVoice 后端启动中...")
    yield
    logger.info("KinVoice 后端已关闭")


app = FastAPI(
    title="KinVoice API",
    description="亲子破冰 · NVC 非暴力沟通智能助手",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS —— 允许快应用前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(convert_router)
app.include_router(chat_router)
app.include_router(memory_router)


@app.get("/", tags=["健康检查"])
async def root():
    return {"status": "ok", "service": "KinVoice", "version": "0.1.0"}
