# 🚀 Developlus

**Yanlış teknoloji seçimi yüzünden batan projeleri engelleyen akıllı danışman.**

Developlus, yazılım geliştirme aşamasında yapılan hatalı teknoloji tercihlerinin önüne geçmek için tasarlanmış, RAG (Retrieval-Augmented Generation) destekli bir LLM chatbot uygulamasıdır. Kullanıcıdan alınan 9 kritik anket sorusu ve genel proje açıklaması ile projenin ihtiyacına en uygun teknoloji yığınını (tech stack) önerir.

---

## 🎯 Projenin Amacı

Yazılım dünyasında birçok proje, teknik gereksinimlerle örtüşmeyen araçlar seçildiği için geliştirme sürecinde tıkanmakta veya başarısız olmaktadır. Developlus:
- Projenin ölçeğini, bütçesini, performans beklentisini ve ekip yetkinliğini analiz eder.
- 9 soruluk anket ile teknik detayları netleştirir.
- RAG desteği sayesinde güncel teknoloji trendlerini ve en iyi pratikleri kullanarak kişiselleştirilmiş öneriler sunar.

---

## 🚀 Kurulum (Installation Setup)

Projeyi Docker kullanarak hızlıca ayağa kaldırabilirsiniz.

### 1. Hazırlık
`.env.example` dosyasını `.env` olarak kopyalayın ve gerekli API anahtarlarını girin:

```bash
cp .env.example .env
```

`.env` dosyasındaki temel alanlar:
```env
# LLM Sağlayıcısı (Alibaba Dashscope / OpenAI vb.)
DASHSCOPE_API_KEY=your_api_key_here

# Veritabanı Şifreleri
POSTGRES_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_secret_key

# LiteLLM
LITELLM_MASTER_KEY=sk-developlus-master
```

### 2. Docker ile Çalıştırma
Tüm servisleri başlatmak için:

```bash
docker compose up -d
```

Bu komut şunları ayağa kaldırır:
- **Frontend (React + Vite)**: Kullanıcı arayüzü ve anket formu.
- **FastAPI Backend**: Mantıksal işlemler ve LLM entegrasyonu.
- **PostgreSQL (pgvector)**: Veri saklama ve vektör tabanlı arama.
- **Redis**: Önbellekleme ve görev kuyruğu.
- **LiteLLM Proxy**: LLM modellerine erişim.
- **Celery Worker**: RAG indeksleme ve uzun süreli işlemler.

### 3. Erişim

| Servis | URL |
|--------|-----|
| **Kullanıcı Arayüzü** | [http://localhost](http://localhost) |
| **API Dokümantasyonu** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **LiteLLM Yönetimi** | [http://localhost:4000](http://localhost:4000) |

---

## 🛠️ Teknoloji Yığını

- **Frontend**: React 19, Vite, Lucide React, Tailwind-like Glassmorphism CSS.
- **Backend**: FastAPI (Async Python), SQLAlchemy, Alembic.
- **AI/LLM**: Qwen 2.5 via LiteLLM Proxy, RAG (Retrieval-Augmented Generation).
- **Veritabanı**: PostgreSQL 16 + pgvector.
- **Altyapı**: Docker & Docker Compose, Nginx, Redis.

---

*© 2026 Developlus — Yazılım projelerinizin temeli sağlam olsun.*
