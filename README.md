# 🚀 Developlus

**LLM tabanlı akıllı chatbot platformu** — Qwen 2.5 · RAG · PostgreSQL · Redis · Docker

---

## Hızlı Başlangıç

### 1. Ortam Değişkenlerini Ayarla

```bash
cp .env.example .env
```

`.env` dosyasını düzenle:

```env
POSTGRES_PASSWORD=güvenli_şifre
JWT_SECRET_KEY=en_az_32_karakter_uzun_bir_secret
DASHSCOPE_API_KEY=sk-xxxxx   # Alibaba Dashscope API key
LITELLM_MASTER_KEY=sk-developlus-master
```

### 2. Docker Compose ile Başlat

```bash
docker compose up -d
```

İlk başlatmada tüm imajlar indirilir (~3-5 dakika).

### 3. Servislere Eriş

| Servis | URL |
|--------|-----|
| **Frontend** | http://localhost |
| **API Docs** | http://localhost:8000/docs |
| **API Health** | http://localhost:8000/health |
| **LiteLLM Proxy** | http://localhost:4000 |
| **Flower (Celery)** | http://localhost:5555 |
| **PgAdmin** | `docker compose --profile tools up pgadmin` → http://localhost:5050 |

---

## Mimari

```
Nginx (80)
  ├── /        → Frontend (static files)
  └── /api/    → FastAPI (8000)
                    ├── PostgreSQL + pgvector (5432)
                    ├── Redis           (6379)
                    ├── LiteLLM Proxy  (4000)
                    └── Celery Worker
```

## API Endpoints

### Auth
| Method | Path | Açıklama |
|--------|------|----------|
| POST | `/auth/register` | Yeni kullanıcı |
| POST | `/auth/login` | Giriş yap |
| POST | `/auth/refresh` | Token yenile |
| POST | `/auth/logout` | Çıkış yap |
| GET  | `/auth/me` | Profil bilgisi |

### Chat
| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/chat/sessions` | Oturum listesi |
| POST | `/chat/sessions` | Yeni oturum |
| PATCH | `/chat/sessions/{id}` | Oturum güncelle |
| DELETE | `/chat/sessions/{id}` | Oturum sil |
| GET | `/chat/sessions/{id}/messages` | Mesajlar |
| **POST** | **`/chat/stream`** | **SSE Streaming Chat** |

### RAG
| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/rag/documents` | Belge listesi |
| POST | `/rag/documents` | Belge yükle |
| DELETE | `/rag/documents/{id}` | Belge sil |

---

## Geliştirme

```bash
# Logları izle
docker compose logs -f api

# Worker logları
docker compose logs -f worker

# Sadece veritabanlarını başlat (lokal geliştirme için)
docker compose up -d postgres redis

# Yeni migration
cd services/api && alembic revision --autogenerate -m "açıklama"
alembic upgrade head
```

## Dashscope API Key Almak

1. https://dashscope.aliyuncs.com adresine git
2. Alibaba Cloud hesabı oluştur
3. API Key'i `.env` dosyasına `DASHSCOPE_API_KEY` olarak ekle

---

## Teknoloji Yığını

- **Backend**: FastAPI + asyncpg + SQLAlchemy (async)
- **Database**: PostgreSQL 16 + pgvector (RAG)
- **Cache**: Redis 7 (LLM cache + session + Celery broker)
- **LLM**: Qwen 2.5 via LiteLLM Proxy (OpenAI uyumlu)
- **RAG**: pgvector HNSW cosine similarity
- **Tasks**: Celery + Redis (belge indexleme)
- **Frontend**: Vanilla HTML/CSS/JS (dark glassmorphism)
- **Proxy**: Nginx (rate limiting + SSE support)
- **Container**: Docker Compose

---

*© 2026 Developlus — Qwen LLM ile güçlendirilmiştir*
