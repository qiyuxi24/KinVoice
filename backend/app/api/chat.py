"""
Chat 接口( 先占位，后期完善 )
"""
from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import chat as llm_chat

router = APIRouter(tags=["陪伴对话"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    reply = await llm_chat(prompt=request.message)
    return ChatResponse(reply=reply, tokens_used=0)