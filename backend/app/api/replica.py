"""
音色克隆服务 —— vivo 声音复刻接口（已增加用户隔离）
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.models.voice import CustomVoice
from app.middleware.user_identity import get_user_id
from app.services.replica_service import (
    create_vcn_task,
    get_vcn_status,
    list_vcn_tasks,
    delete_vcn,
    convert_audio_to_standard
)
from app.utils.logger import logger


router = APIRouter(prefix="/replica", tags=["音色克隆"])

@router.get("/sample-texts")
async def get_sample_texts():
    """获取推荐的录音样例文本"""
    samples = [
        "我会一直陪着你，无论开心还是难过，我都会在你身边。",
        "今天的天气真好，我们一起去公园散散步吧。",
        "你知道吗，你笑起来的样子特别好看。",
        "谢谢你一直以来的理解和支持，我很感激。",
    ]
    return {"samples": samples}


@router.post("/create")
async def create_replica(
    audio: UploadFile = File(..., description="wav 录音(24kHz, 16bit, 单通道)"),
    text: str = Form(..., description="录音对应文本"),
    user_id: str = Depends(get_user_id),           # ✅ 注入用户身份
):
    """上传录音创建自定义音色，自动生成递增名称并绑定用户"""
    if not audio.filename or not audio.filename.endswith(".wav"):
        raise HTTPException(400, "只支持 wav 格式音频")
    audio_bytes = await audio.read()
    try:
        audio_bytes = convert_audio_to_standard(audio_bytes)
        result = await create_vcn_task(audio_bytes, text)
        vcn = result.get("vcn")
        if vcn:
            async with AsyncSessionLocal() as session:
                # ✅ 查询当前用户已有音色数量，生成名字
                count_stmt = select(func.count(CustomVoice.id)).where(
                    CustomVoice.user_id == user_id
                )
                count = (await session.execute(count_stmt)).scalar() or 0
                name = f"新建音色{count + 1}"

                voice = CustomVoice(
                    name=name,
                    vcn=vcn,
                    status=1,
                    user_id=user_id,
                )
                session.add(voice)
                await session.commit()
                logger.info(f"用户 {user_id} 创建音色: {name} (vcn={vcn})")
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"音色创建失败: {str(e)}")
        raise HTTPException(500, str(e))


@router.get("/status")
async def check_status(vcn: str):
    """查询音色生成状态"""
    try:
        result = await get_vcn_status(vcn)
        return result
    except Exception as e:
        logger.error(f"查询状态失败: {str(e)}")
        raise HTTPException(500, str(e))


@router.get("/list")
async def list_voices(user_id: str = Depends(get_user_id)):   # ✅ 仅返回当前用户的音色
    """获取当前用户的音色列表（含系统音色委托给 /tts/voices，这里仅返回自定义音色）"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CustomVoice)
            .where(CustomVoice.user_id == user_id)
            .order_by(CustomVoice.created_at.desc())
        )
        voices = result.scalars().all()
        return {
            "count": len(voices),
            "items": [
                {
                    "name": v.name,
                    "vcn": v.vcn,
                    "voice_type": v.voice_type,
                    "status": v.status,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in voices
            ]
        }


@router.delete("/{vcn}")
async def remove_voice(vcn: str, user_id: str = Depends(get_user_id)):
    """删除指定音色（仅允许删除自己的）"""
    try:
        # 先检查权限（必须在数据库中存在且属于当前用户）
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CustomVoice).where(
                    CustomVoice.vcn == vcn,
                    CustomVoice.user_id == user_id,
                )
            )
            voice = result.scalar_one_or_none()
            if not voice:
                raise HTTPException(status_code=404, detail="音色不存在或无权操作")

            # 删除 vivo 云端音色
            await delete_vcn(vcn)
            # 删除数据库记录
            await session.delete(voice)
            await session.commit()
            return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除音色失败: {str(e)}")
        raise HTTPException(500, str(e))


@router.put("/rename")
async def rename_voice(
    vcn: str,
    new_name: str,
    user_id: str = Depends(get_user_id),
):
    """重命名自定义音色（仅允许自己的）"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CustomVoice).where(
                CustomVoice.vcn == vcn,
                CustomVoice.user_id == user_id,
            )
        )
        voice = result.scalar_one_or_none()
        if not voice:
            raise HTTPException(404, "音色不存在或无权操作")
        voice.name = new_name
        await session.commit()
        return {"message": "重命名成功", "name": new_name}


@router.post("/sync-status")
async def sync_voice_status(
    vcn: str,
    user_id: str = Depends(get_user_id),
):
    """手动同步音色状态（仅允许自己的）"""
    try:
        vivo_status = await get_vcn_status(vcn)
        status = vivo_status.get("vcn_obj", {}).get("status", 1)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CustomVoice).where(
                    CustomVoice.vcn == vcn,
                    CustomVoice.user_id == user_id,
                )
            )
            voice = result.scalar_one_or_none()
            if voice:
                voice.status = status
                await session.commit()
                return {"vcn": vcn, "status": status, "ready": status == 3}
        raise HTTPException(404, "本地未找到该音色或无权操作")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步状态失败: {str(e)}")
        raise HTTPException(500, str(e))