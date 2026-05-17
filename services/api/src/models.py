"""
Developlus API — SQLAlchemy ORM Modelleri
=========================================
Her model bir PostgreSQL tablosuna karşılık gelir.
İlişkiler relationship() ile tanımlanır; cascade="all, delete-orphan"
Python tarafında da ON DELETE CASCADE mantığını yansıtır.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, 
    Boolean, Float, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.database import Base


# ══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 1: KULLANICI VE KİMLİK YÖNETİMİ
# ══════════════════════════════════════════════════════════════════════════════

class User(Base):
    """
    Tüm varlıkların kök sahibi.
    is_active=False ile soft-delete yapılır; kayıt fiziksel olarak silinmez.
    """
    __tablename__ = "users"

    # Birincil anahtar: UUID4 ile çarpışma riski sıfır, sıra bağımsız
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    username        = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=False)         # bcrypt/argon2 hash; asla düz metin
    full_name       = Column(String(255))
    # Abonelik katmanı: ücretsiz, profesyonel veya kurumsal
    tier            = Column(String(20), default="free")
    is_active       = Column(Boolean, default=True)        # FALSE = soft-delete
    is_verified     = Column(Boolean, default=False)       # E-posta doğrulama durumu
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # Genişletilebilir ek alan (avatar_url, locale, notification prefs vb.)
    metadata_       = Column("metadata", JSONB, default=dict)

    # ── İlişkiler ──────────────────────────────────────────────────────────
    # Kullanıcı silindiğinde tüm bağlı kayıtlar Python ORM katmanında da temizlenir
    projects        = relationship("Project",      back_populates="user",   cascade="all, delete-orphan")
    sessions        = relationship("ChatSession",  back_populates="user",   cascade="all, delete-orphan")
    documents       = relationship("Document",     back_populates="user",   cascade="all, delete-orphan")
    refresh_tokens  = relationship("RefreshToken", back_populates="user",   cascade="all, delete-orphan")


class RefreshToken(Base):
    """
    JWT refresh tokenlarını saklar.
    Token rotation'da eski satır silinip yenisi eklenir.
    Ham token istemcide; DB'de yalnızca SHA-256 hash tutulur.
    """
    __tablename__ = "refresh_tokens"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash  = Column(Text, unique=True, nullable=False)  # Güvenlik: raw token DB'de saklanmaz
    expires_at  = Column(DateTime(timezone=True), nullable=False)  # Süresi dolanlara cron ile temizlenir
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="refresh_tokens")


# ══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 2: DEVELOPLUS ÇEKIRDEK TABLOLARI
# ══════════════════════════════════════════════════════════════════════════════

class Project(Base):
    """
    Sol çubukta listelenen proje kartlarının ORM karşılığı.
    Her kullanıcı birden fazla projeye sahip olabilir (1-to-many).
    status='archived' olan projeler salt-okunur mod için işaretlenir.
    """
    __tablename__ = "projects"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_name = Column(String(255), nullable=False)    # Kullanıcının verdiği proje adı
    description  = Column(Text)                           # Opsiyonel kısa açıklama
    # Durum: active = aktif geliştirme, archived = arşivlenmiş
    status       = Column(String(20), default="active")
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ── İlişkiler ──────────────────────────────────────────────────────────
    user               = relationship("User",                back_populates="projects")
    # Proje silindiğinde bağlı tüm veriler Python katmanında da temizlenir
    survey_data        = relationship("ProjectSurveyData",   back_populates="project",
                                      uselist=False,         cascade="all, delete-orphan")
    chat_history       = relationship("ChatHistory",         back_populates="project",
                                      cascade="all, delete-orphan",
                                      order_by="ChatHistory.created_at")
    stack_recommendations = relationship("StackRecommendation", back_populates="project",
                                         cascade="all, delete-orphan",
                                         order_by="StackRecommendation.version.desc()")


class ProjectSurveyData(Base):
    """
    Proje oluşturma sihirbazından gelen teknik kısıt verileri.

    JSONB SEÇİMİNİN GEREKÇESİ:
      Anket soruları değişkendir; her değişiklikte ALTER TABLE yerine
      JSONB schema-less esneklik + GIN indeks + @> operatörü ile
      güçlü sorgulama imkânı sunar.

    Bir projeye ait yalnızca bir anket seti vardır (1-to-1 → uselist=False).
    """
    __tablename__ = "project_survey_data"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # UNIQUE kısıtı 1-to-1 ilişkiyi DB seviyesinde garanti eder
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
                        nullable=False, unique=True)
    # Tüm anket yanıtları esnek JSONB yapısında (traffic, budget, skills vb.)
    responses  = Column(JSONB, nullable=False, default=dict)
    question   = Column(String(30))
    survey_complete = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="survey_data")


class ChatHistory(Base):
    """
    Sağdaki 'Chat' sekmesine ait proje bazlı mesaj geçmişi.

    Genel chatbot (ChatSession/Message) ile paralel çalışır; ikisi birbirinden bağımsız.
    Bu tablo stack danışmanı akışına özeldir: her mesaj bir projeye aittir.
    """
    __tablename__ = "chat_history"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id        = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
                               nullable=False)
    # Aktör: 'user' = kullanıcı girişi, 'assistant' = LLM yanıtı, 'system' = sistem talimatı
    role              = Column(String(20), nullable=False)
    message_content   = Column(Text, nullable=False)      # Markdown destekli ham içerik
    # Token sayaçları: maliyet takibi ve rate-limit hesapları için
    prompt_tokens     = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens      = Column(Integer)
    # Uçtan uca yanıt süresi: performans izleme için
    latency_ms        = Column(Integer)
    # Hangi model kullanıldı: A/B test ve model geçişlerinde izlenebilirlik sağlar
    model_used        = Column(String(100))
    created_at        = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="chat_history")


class StackRecommendation(Base):
    """
    Sağdaki 'Stack' sekmesindeki 4 kutunun (Frontend/Backend/DB/DevOps) veri kaynağı.

    VERSİYONLAMA MANTIĞI:
      Her yeni LLM önerisi mevcut satırı güncellemez; yeni bir satır ekler.
      Bu sayede 'öneri geçmişi' korunur ve kullanıcı önceki versiyonlara
      geri dönebilir. En güncel öneri max(version) ile bulunur.

    UNIQUE(project_id, version) → aynı projede aynı versiyon numarası olamaz.
    """
    __tablename__ = "stack_recommendations"
    __table_args__ = (
        # Bütünlük kuralı: bir projeye ait her versiyon benzersiz olmalı
        UniqueConstraint("project_id", "version", name="uq_stack_project_version"),
    )

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id       = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
                              nullable=False)
    # Versiyon numarası: 1, 2, 3 ... her yeni öneri +1 artar
    version          = Column(Integer, nullable=False, default=1)
    # ── 4 Ana Kutu ─────────────────────────────────────────────────────────
    frontend_content = Column(Text)    # Framework, kütüphane ve rationale
    backend_content  = Column(Text)    # API framework, dil ve mimari
    database_content = Column(Text)    # Primary/secondary DB seçimi + gerekçe
    devops_content   = Column(Text)    # CI/CD, container, cloud provider
    # Öneriyi üreten survey_responses'ın anlık kopyası; geriye dönük analiz için
    generated_from   = Column(JSONB, default=dict)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="stack_recommendations")


# ══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 3: GENEL AMAÇLI CHATBOT ALTYAPISI
# ══════════════════════════════════════════════════════════════════════════════

class ChatSession(Base):
    """
    Genel chatbot oturumu (GPT/Claude tarzı çoklu oturum yönetimi).
    Proje bazlı ChatHistory ile paralel; birbirini etkilemez.
    """
    __tablename__ = "chat_sessions"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title           = Column(Text, default="Yeni Sohbet")           # İlk mesajdan türetilebilir
    model_used      = Column(String(100), default="qwen2.5-72b-instruct")
    system_prompt   = Column(Text)                                  # Oturuma özel sistem talimatı
    temperature     = Column(Float, default=0.7)                    # LLM yaratıcılık [0-2]
    max_tokens      = Column(Integer, default=4096)                 # Tek yanıt token üst sınırı
    use_rag         = Column(Boolean, default=False)                # RAG modu açık mı
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    session_metadata = Column("metadata", JSONB, default=dict)      # Pinned, tags vb. ek ayarlar

    user     = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan",
                            order_by="Message.created_at")


class Message(Base):
    """
    Genel chatbot mesajları; chat_sessions'a bağlı.
    'tool' rolü function calling / tool use yanıtları için ayrılmıştır.
    """
    __tablename__ = "messages"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id        = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"),
                               nullable=False)
    # Aktör: user / assistant / system / tool (function calling)
    role              = Column(String(20), nullable=False)
    content           = Column(Text, nullable=False)
    prompt_tokens     = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens      = Column(Integer)
    latency_ms        = Column(Integer)
    # Override: oturum modelinden farklı bir model kullanıldıysa kaydedilir
    model             = Column(String(100))
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    message_metadata  = Column("metadata", JSONB, default=dict)  # Tool call detayları, citations vb.

    session = relationship("ChatSession", back_populates="messages")


# ══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 4: RAG (RETRIEVAL AUGMENTED GENERATION) ALTYAPISI
# ══════════════════════════════════════════════════════════════════════════════

class Document(Base):
    """
    Kullanıcının yüklediği belgeler.
    Celery worker, status'u pending → processing → ready/failed şeklinde günceller.
    """
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(50))               # 'pdf', 'txt', 'md' vb.
    file_size: Mapped[Optional[int]] = mapped_column(Integer)                  # Bayt cinsinden boyut
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)       # Oluşturulan chunk sayısı
    # Celery pipeline durumu; işlem adımları bu sütunla izlenir
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    doc_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)  # Yazar, sayfa sayısı, kaynak URL vb.

    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """
    Belge parçaları + pgvector embedding.
    HNSW indeksi cosine similarity ile ANN araması yapar (init.sql'de tanımlı).
    embedding boyutu 384: MiniLM-L6 (384)
    """
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)   # Belge içindeki sıra numarası (0-based)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)      # Ham metin parçası
    embedding = mapped_column(Vector(384))              # MiniLM-L6 (384)
    token_count: Mapped[Optional[int]] = mapped_column(Integer)                  # Context penceresi yönetimi için token sayısı
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    chunk_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)  # Sayfa no, başlık, kaynak bölüm vb.

    document = relationship("Document", back_populates="chunks")


# ══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 5: İZLEME VE ANALİTİK
# ══════════════════════════════════════════════════════════════════════════════

class ApiUsage(Base):
    """
    Her LLM çağrısının token tüketimi ve maliyeti.
    user_id NULL olabilir: anonim istekler veya kullanıcı silindikten sonra da
    kayıtlar korunur (ON DELETE SET NULL).
    """
    __tablename__ = "api_usage"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id           = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
                               nullable=True)                    # Anonim istek desteği
    model             = Column(String(100))                      # Çağrılan model adı
    endpoint          = Column(String(200))                      # API endpoint
    prompt_tokens     = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens      = Column(Integer, default=0)
    cost_usd          = Column(Float, default=0.0)               # Hesaplanan tahmini maliyet
    latency_ms        = Column(Integer)                          # Uçtan uca yanıt süresi
    status_code       = Column(Integer)                          # HTTP durum kodu
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
