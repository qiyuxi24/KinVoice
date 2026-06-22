"""
KinVoice 后端 —— FastAPI 入口
"""
# main.py主要负责将用户的CRUD请求进行路由分发(分发后各部分分别执行各自的任务)

from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.utils.logger import logger
from app.api.convert import router as convert_router
from app.api.chat import router as chat_router 
from app.api.memory import router as memory_router
from app.api.tts import router as tts_router
from app.api.replica import router as replica_router

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

# TTS:文本->音频生成
app.include_router(tts_router)

# 音色克隆功能(自定义音色)
app.include_router(replica_router)

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """所有未捕获异常的兜底处理"""
    logger.error(f"未捕获异常: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"},
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """参数校验错误"""
    logger.warning(f"参数错误: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )