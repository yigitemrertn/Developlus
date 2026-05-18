"""Developlus API — Pydantic Schemas"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
#  AUTH SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Şifre en az bir büyük harf içermelidir")
        if not any(c.isdigit() for c in v):
            raise ValueError("Şifre en az bir rakam içermelidir")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    tier: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
#  CHAT SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    title: str = "Yeni Sohbet"
    model_used: str = "qwen-turbo"
    system_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=32000)
    use_rag: bool = False


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=32000)
    use_rag: Optional[bool] = None


class SessionResponse(BaseModel):
    id: UUID
    title: str
    model_used: str
    system_prompt: Optional[str]
    temperature: float
    max_tokens: int
    use_rag: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    total_tokens: Optional[int]
    latency_ms: Optional[int]
    model: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    session_id: UUID
    message: str = Field(min_length=1, max_length=32000)
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)


# ─────────────────────────────────────────────────────────────────────────────
#  DOCUMENT / RAG SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    chunk_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
#  PROJECT SCHEMAS — Sol çubuk proje listesi + proje CRUD işlemleri
# ─────────────────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    """Yeni proje oluşturma isteği. project_name zorunlu, description opsiyonel."""
    project_name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Kısmi güncelleme: yalnızca gönderilen alanlar değiştirilir (PATCH semantiği)."""
    project_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    # 'archived' → projeyi salt-okunur moda alır; 'active' → tekrar aktif eder
    status: Optional[str] = Field(default=None, pattern=r"^(active|archived)$")


class ProjectResponse(BaseModel):
    """Sol çubuk kart ve proje detay sayfası için API yanıtı."""
    id: UUID
    user_id: UUID
    project_name: str
    description: Optional[str]
    status: str
    survey_complete: Optional[bool] = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
#  SURVEY SCHEMAS — Proje oluşturma sihirbazı teknik kısıt verileri
# ─────────────────────────────────────────────────────────────────────────────

class SurveySubmit(BaseModel):
    """
    Anket yanıtlarını gönderir. responses dict JSONB sütununa yazılır.
    Örnek responses:
      {
        "expected_traffic": "high",
        "monthly_budget_usd": 500,
        "team_size": 3,
        "team_skills": ["Python", "React"],
        "deployment_preference": "cloud",
        "has_mobile": true,
        "compliance_needs": ["GDPR"]
      }
    """
    responses: dict  # Şema-bağımsız; JSONB esnekliğini Python tarafında da korur
    question: Optional[str] = None
    survey_complete: bool = False


class SurveyResponse(BaseModel):
    """Anket verilerini döndürür; frontend sihirbazı son adımı görüntülemek için kullanır."""
    id: UUID
    project_id: UUID
    responses: dict
    question: Optional[str] = None
    survey_complete: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
#  CHAT HISTORY SCHEMAS — Sağ panel "Chat" sekmesi (proje bazlı)
# ─────────────────────────────────────────────────────────────────────────────

class ProjectChatRequest(BaseModel):
    """
    Kullanıcının proje bazlı chat paneline gönderdiği mesaj.
    model override opsiyoneldir; belirtilmezse servis varsayılanı kullanılır.
    """
    message: str = Field(min_length=1, max_length=32000)
    model: Optional[str] = None    # Opsiyonel model override (örn: 'qwen-plus')
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)


class ChatHistoryItemResponse(BaseModel):
    """Tek bir mesaj satırının API yanıtı."""
    id: UUID
    project_id: UUID
    role: str                        # 'user' | 'assistant' | 'system'
    message_content: str
    total_tokens: Optional[int]
    latency_ms: Optional[int]
    model_used: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryListResponse(BaseModel):
    """Projenin tüm mesaj geçmişi; sayfalama bilgisiyle birlikte döner."""
    project_id: UUID
    messages: List[ChatHistoryItemResponse]
    total_count: int = 0


# ─────────────────────────────────────────────────────────────────────────────
#  STACK RECOMMENDATION SCHEMAS — Sağ panel "Stack" sekmesi (4 kutu)
# ─────────────────────────────────────────────────────────────────────────────

class StackRecommendationResponse(BaseModel):
    """
    Stack sekmesindeki dinamik katmanların veri kaynağı.
    version alanı geçmiş versiyonlar arasında gezinmek için kullanılır.
    """
    id: UUID
    project_id: UUID
    version: int                     # 1, 2, 3 ... en yüksek = güncel öneri
    layers: Optional[dict] = None    # Dinamik katmanlar: {"Frontend": "React", "AI Layer": "PyTorch"}
    generated_from: Optional[dict]   # Hangi survey yanıtlarından üretildi
    created_at: datetime

    model_config = {"from_attributes": True}


class StackRecommendationListResponse(BaseModel):
    """Projenin tüm öneri versiyonlarını listeler; geçmiş versiyonlar için kullanılır."""
    project_id: UUID
    recommendations: List[StackRecommendationResponse]
    latest_version: int = 0


# ─────────────────────────────────────────────────────────────────────────────
#  GENERIC
# ─────────────────────────────────────────────────────────────────────────────

class SuccessResponse(BaseModel):
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
