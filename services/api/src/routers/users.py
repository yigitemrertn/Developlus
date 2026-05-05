"""Developlus API — Users Router"""
from typing import Dict

from cryptography.fernet import Fernet
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.config import settings
from src.dependencies import CurrentUser, DBSession
from src.schemas import SuccessResponse

router = APIRouter(prefix="/users", tags=["Users"])


class HFKeyUpdate(BaseModel):
    hf_api_key: str


class HFKeyStatusResponse(BaseModel):
    has_hf_key: bool


def get_fernet():
    if not settings.hf_encryption_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="HF_ENCRYPTION_KEY ayarlanmamış"
        )
    return Fernet(settings.hf_encryption_key.encode())


@router.post("/me/huggingface-key", response_model=SuccessResponse)
async def update_huggingface_key(data: HFKeyUpdate, current_user: CurrentUser, db: DBSession):
    """
    Kullanıcının HuggingFace API anahtarını şifreleyerek metadata içerisine kaydeder.
    """
    f = get_fernet()
    encrypted_key = f.encrypt(data.hf_api_key.encode()).decode()
    
    # User modelini güncelle
    metadata = dict(current_user.metadata_) if current_user.metadata_ else {}
    metadata["hf_api_key"] = encrypted_key
    
    current_user.metadata_ = metadata
    db.add(current_user)
    await db.commit()
    
    return SuccessResponse(message="HuggingFace API anahtarı başarıyla kaydedildi")


@router.get("/me/huggingface-key-status", response_model=HFKeyStatusResponse)
async def get_huggingface_key_status(current_user: CurrentUser):
    """
    Kullanıcının sistemde kayıtlı bir HuggingFace API anahtarı olup olmadığını döndürür.
    Güvenlik gereği anahtarın kendisi dönülmez.
    """
    metadata = current_user.metadata_ or {}
    has_key = "hf_api_key" in metadata and bool(metadata["hf_api_key"])
    return HFKeyStatusResponse(has_hf_key=has_key)
