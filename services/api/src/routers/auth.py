"""Developlus API — Auth Router"""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.dependencies import CurrentUser, DBSession
from src.schemas import (
    RefreshRequest, TokenResponse, UserLogin,
    UserRegister, UserResponse, SuccessResponse
)
from src.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: DBSession):
    """Yeni kullanıcı kaydı."""
    try:
        user = await auth_service.register_user(
            db=db,
            email=data.email,
            username=data.username,
            password=data.password,
            full_name=data.full_name,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Kullanıcı zaten mevcut")


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: DBSession):
    """Email/şifre ile giriş yapar, JWT token döner."""
    user = await auth_service.authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı",
        )

    access_token, expires_in = auth_service.create_access_token(str(user.id), user.email)
    refresh_token = auth_service.create_refresh_token()
    await auth_service.save_refresh_token(db, str(user.id), refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: DBSession):
    """Refresh token ile yeni access token alır."""
    user = await auth_service.validate_refresh_token(db, data.refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token geçersiz veya süresi dolmuş",
        )

    # Eski token'ı iptal et, yeni oluştur
    await auth_service.revoke_refresh_token(db, data.refresh_token)
    access_token, expires_in = auth_service.create_access_token(str(user.id), user.email)
    new_refresh = auth_service.create_refresh_token()
    await auth_service.save_refresh_token(db, str(user.id), new_refresh)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=expires_in,
    )


@router.post("/logout", response_model=SuccessResponse)
async def logout(data: RefreshRequest, db: DBSession):
    """Refresh token'ı geçersiz kılar."""
    await auth_service.revoke_refresh_token(db, data.refresh_token)
    return SuccessResponse(message="Başarıyla çıkış yapıldı")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Giriş yapmış kullanıcının profilini döner."""
    return current_user
