-- ══════════════════════════════════════════════════════════════════════════════
--  Developlus — PostgreSQL Init Script
--  İlk konteyner başlatmasında otomatik çalışır (docker-compose init volume).
--
--  TABLO HİYERARŞİSİ:
--    users  ──┬──▶  projects  ──┬──▶  project_survey_data  (1-to-1)
--             │                 ├──▶  chat_history          (1-to-many)
--             │                 └──▶  stack_recommendations (1-to-many, versioned)
--             ├──▶  refresh_tokens
--             ├──▶  chat_sessions ──▶ messages
--             ├──▶  documents    ──▶ document_chunks
--             └──▶  api_usage
-- ══════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────────
--  EXTENSIONS
--  pgvector : RAG embedding aramalarını (HNSW/IVFFlat) destekler
--  pgcrypto : gen_random_uuid() ile UUID üretimi ve şifre hash'leme
--  pg_trgm  : GIN indeksiyle fuzzy / ILIKE metin araması
-- ──────────────────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;      -- pgvector: embedding & similarity search
CREATE EXTENSION IF NOT EXISTS pgcrypto;    -- UUID üretimi ve kriptografik hash
CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- Trigram tabanlı fuzzy metin arama


-- ══════════════════════════════════════════════════════════════════════════════
--  BÖLÜM 1: KULLANICI VE KİMLİK YÖNETİMİ
-- ══════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────────
--  USERS — Tüm varlıkların kök sahibi; soft-delete için is_active kullanılır.
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    -- Birincil anahtar: çarpışma riski sıfır, dağıtık sistemlerde sıra bağımsız
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,       -- Giriş kimliği; unique index otomatik oluşur
    username        VARCHAR(100) UNIQUE NOT NULL,       -- Görünen ad; URL slug'larında kullanılabilir
    hashed_password TEXT NOT NULL,                     -- bcrypt / argon2 hash; asla düz metin saklanmaz
    full_name       VARCHAR(255),                      -- Opsiyonel tam isim
    -- Abonelik katmanı: ücretsiz → profesyonel → kurumsal
    tier            VARCHAR(20)  DEFAULT 'free'
                        CHECK (tier IN ('free','pro','enterprise')),
    is_active       BOOLEAN      DEFAULT TRUE,         -- FALSE = soft-delete; kayıt silinmez
    is_verified     BOOLEAN      DEFAULT FALSE,        -- E-posta doğrulama durumu
    created_at      TIMESTAMPTZ  DEFAULT NOW(),        -- Kayıt oluşturma zamanı (UTC+offset)
    updated_at      TIMESTAMPTZ  DEFAULT NOW(),        -- Trigger ile her UPDATE'de güncellenir
    metadata        JSONB        DEFAULT '{}'          -- Genişletilebilir ek alan (avatar_url, locale vb.)
);

-- Giriş sorguları e-posta veya kullanıcı adı üzerinden yapılacağı için her ikisi de indexlendi
CREATE INDEX IF NOT EXISTS idx_users_email    ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);


-- ──────────────────────────────────────────────────────────────────────────────
--  REFRESH TOKENS — JWT yenileme tokenlarını saklar; rotation'da eskisi silinir.
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    -- Ham token istemcide; DB'de sadece SHA-256 hash tutulur (güvenlik)
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,    -- Token geçerlilik sonu; süresi dolanlara cron ile temizlenir
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);


-- ══════════════════════════════════════════════════════════════════════════════
--  BÖLÜM 2: DEVELOPLUS ÇEKIRDEK TABLOLARI
--  Bu bölümdeki tablolar sol bardaki proje listesini ve sağdaki
--  Chat / Stack görünümünü doğrudan besler.
-- ══════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────────
--  PROJECTS — Sol çubukta listelenen proje kartlarının kaynağı.
--  Her kullanıcı birden fazla projeye sahip olabilir (1-to-many).
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Kullanıcı silindiğinde projeler de kaskad ile temizlenir
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_name VARCHAR(255) NOT NULL,                -- Kullanıcının verdiği proje adı
    description  TEXT,                                -- Opsiyonel kısa açıklama metni
    -- Durum: active = aktif geliştirme, archived = salt okunur arşiv
    status       VARCHAR(20)  DEFAULT 'active'
                     CHECK (status IN ('active','archived')),
    created_at   TIMESTAMPTZ  DEFAULT NOW(),           -- Proje oluşturma zamanı
    updated_at   TIMESTAMPTZ  DEFAULT NOW()            -- Trigger ile otomatik güncellenir
);

-- Sol bar proje listesi user_id'ye göre filtrelenir; created_at DESC sıralanır
CREATE INDEX IF NOT EXISTS idx_projects_user_id    ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at DESC);
-- Duruma göre filtreleme (active/archived sekmesi) için ayrı index
CREATE INDEX IF NOT EXISTS idx_projects_status     ON projects(status);


-- ──────────────────────────────────────────────────────────────────────────────
--  PROJECT_SURVEY_DATA — Proje oluşturma sihirbazından gelen teknik kısıt verileri.
--
--  JSONB SEÇİMİNİN GEREKÇESİ:
--    Anket soruları zamanla değişebilir (yeni alan eklenir, eskisi kaldırılır).
--    Her soruyu ayrı sütun olarak tutmak her değişiklikte ALTER TABLE gerektirir.
--    JSONB; schema-less esneklik + B-tree ve GIN indeks desteği + PostgreSQL
--    operatörleri (->, ->>, @>) ile güçlü sorgulama imkânı sunar.
--
--  ÖRNEK responses değeri:
--    {
--      "expected_traffic": "high",          -- Düşük/Orta/Yüksek
--      "monthly_budget_usd": 500,           -- Aylık altyapı bütçesi
--      "team_size": 3,                      -- Geliştirici sayısı
--      "team_skills": ["Python","React"],   -- Mevcut yetkinlikler
--      "deployment_preference": "cloud",    -- Cloud/On-premise/Hybrid
--      "has_mobile": true,                  -- Mobil uygulama gereksinimi var mı
--      "compliance_needs": ["GDPR"]         -- Uyumluluk gereksinimleri
--    }
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_survey_data (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Bir projeye ait yalnızca bir anket seti olabilir (1-to-1)
    project_id  UUID NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
    -- Tüm anket yanıtları esnek JSONB yapısında tutulur
    responses   JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),   -- İlk anket doldurulma zamanı
    updated_at  TIMESTAMPTZ DEFAULT NOW()    -- Sonraki güncellemelerde trigger devreye girer
);

-- GIN indeksi: @> (contains) ve jsonb_path_query gibi JSONB operatörlerini hızlandırır
-- Örnek: WHERE responses @> '{"team_skills": ["Python"]}'
CREATE INDEX IF NOT EXISTS idx_survey_responses_gin
    ON project_survey_data USING GIN (responses);


-- ──────────────────────────────────────────────────────────────────────────────
--  CHAT_HISTORY — Sağdaki "Chat" sekmesine ait proje bazlı mesaj geçmişi.
--
--  NOT: Bu tablo proje odaklı stack danışmanı chatını tutar.
--  Genel amaçlı chatbot akışı için aşağıdaki chat_sessions / messages tabloları
--  kullanılmaya devam eder; ikisi birbirinden bağımsız ve paralel çalışır.
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Proje silindiğinde ilgili tüm mesajlar kaskad ile temizlenir
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    -- Konuşmadaki aktörü belirtir: 'user' = kullanıcı, 'assistant' = LLM yanıtı
    role            VARCHAR(20) NOT NULL
                        CHECK (role IN ('user', 'assistant', 'system')),
    message_content TEXT NOT NULL,          -- Ham mesaj içeriği (markdown destekli)
    -- Token sayaçları: maliyet takibi ve rate-limit hesaplamaları için
    prompt_tokens   INTEGER,
    completion_tokens INTEGER,
    total_tokens    INTEGER,
    -- Yanıt gecikme süresi: performans izleme dashboard'u için
    latency_ms      INTEGER,
    -- Hangi model kullandığını saklarız; A/B test veya model geçişlerinde önemli
    model_used      VARCHAR(100),
    created_at      TIMESTAMPTZ DEFAULT NOW()   -- Mesaj gönderim zamanı
);

-- Chat geçmişi her zaman project_id + created_at çiftine göre çekilir
CREATE INDEX IF NOT EXISTS idx_chat_history_project_id  ON chat_history(project_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at  ON chat_history(created_at);
-- Composite index: tek sorguda hem filtrele hem sırala (covering index avantajı)
CREATE INDEX IF NOT EXISTS idx_chat_history_project_time
    ON chat_history(project_id, created_at DESC);


-- ──────────────────────────────────────────────────────────────────────────────
--  STACK_RECOMMENDATIONS — Sağdaki "Stack" sekmesindeki 4 kutunun veri kaynağı.
--
--  VERSİYONLAMA MANTIĞI:
--    Her yeni LLM önerisi mevcut satırı güncellemez; yeni bir satır ekler.
--    Bu sayede "öneri geçmişi" korunur ve kullanıcı önceki versiyonlara
--    geri dönebilir. En güncel öneri MAX(version) ile bulunur.
--
--  4 KUTU YAPISI:
--    frontend_content  → "Frontend" kutusu (React, Vue, Next.js vb.)
--    backend_content   → "Backend" kutusu (FastAPI, Node, Spring vb.)
--    database_content  → "Database" kutusu (PostgreSQL, MongoDB, Redis vb.)
--    devops_content    → "DevOps" kutusu (Docker, K8s, CI/CD, Cloud vb.)
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stack_recommendations (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Proje silindiğinde tüm öneri versiyonları kaskad ile temizlenir
    project_id        UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    -- Versiyon numarası: 1, 2, 3 ... her yeni öneri +1 artar
    version           INTEGER NOT NULL DEFAULT 1,
    -- Frontend kutusu: framework, kütüphane ve rationale içeren metin
    frontend_content  TEXT,
    -- Backend kutusu: API framework, dil ve mimari açıklaması
    backend_content   TEXT,
    -- Database kutusu: primary ve secondary DB seçimleri + gerekçe
    database_content  TEXT,
    -- DevOps kutusu: CI/CD araçları, container, cloud provider önerisi
    devops_content    TEXT,
    -- Hangi anket yanıtlarının tetiklediğini izleme için snapshot
    generated_from    JSONB DEFAULT '{}',   -- Öneriyi üreten survey_responses snapshotu
    created_at        TIMESTAMPTZ DEFAULT NOW(),  -- Öneri üretim zamanı
    -- Aynı projede aynı versiyon numarası olamaz (bütünlük kuralı)
    CONSTRAINT uq_stack_project_version UNIQUE (project_id, version)
);

-- Stack paneli her zaman son versiyonu gösterir: WHERE project_id = ? ORDER BY version DESC LIMIT 1
CREATE INDEX IF NOT EXISTS idx_stack_project_id ON stack_recommendations(project_id);
-- Versiyon geçmişi listesi için bileşik index
CREATE INDEX IF NOT EXISTS idx_stack_project_version
    ON stack_recommendations(project_id, version DESC);


-- ══════════════════════════════════════════════════════════════════════════════
--  BÖLÜM 3: GENEL AMAÇLI CHATBOT ALTYAPISI (mevcut)
--  Aşağıdaki tablolar Developlus'un genel LLM chat özelliğini destekler.
--  Proje bazlı chat_history ile paralel çalışır; birbirini etkilemez.
-- ══════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────────
--  CHAT_SESSIONS — Genel chatbot oturumu; bir kullanıcının birden fazla
--  paralel konuşması olabilir (GPT/Claude tarzı oturum yönetimi).
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           TEXT DEFAULT 'Yeni Sohbet',        -- Oturum başlığı (ilk mesajdan türetilebilir)
    model_used      VARCHAR(100) DEFAULT 'qwen2.5-72b-instruct',  -- Varsayılan model
    system_prompt   TEXT,                              -- Oturuma özel sistem talimatı
    temperature     FLOAT DEFAULT 0.7,                 -- LLM yaratıcılık parametresi [0-2]
    max_tokens      INTEGER DEFAULT 4096,              -- Tek yanıt için token üst sınırı
    use_rag         BOOLEAN DEFAULT FALSE,             -- RAG (belge tabanlı) modu aktif mi
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),         -- Trigger ile güncellenir
    metadata        JSONB DEFAULT '{}'                 -- Ek oturum ayarları (pinned, tags vb.)
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id    ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON chat_sessions(created_at DESC);


-- ──────────────────────────────────────────────────────────────────────────────
--  MESSAGES — Genel chatbot mesajları; oturuma bağlı.
--  'tool' rolü: function calling / tool use yanıtları için ayrılmıştır.
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id        UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role              VARCHAR(20) NOT NULL
                          CHECK (role IN ('user','assistant','system','tool')),
    content           TEXT NOT NULL,
    prompt_tokens     INTEGER,
    completion_tokens INTEGER,
    total_tokens      INTEGER,
    latency_ms        INTEGER,
    model             VARCHAR(100),                    -- Override: oturum modelinden farklı kullanıldıysa
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    metadata          JSONB DEFAULT '{}'               -- Tool call detayları, citations vb.
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);


-- ══════════════════════════════════════════════════════════════════════════════
--  BÖLÜM 4: RAG (RETRIEVAL AUGMENTED GENERATION) ALTYAPISI
-- ══════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────────
--  DOCUMENTS — Kullanıcının yüklediği belgeler; chunklara bölünmeden önce
--  işlem durumu (pending → processing → ready / failed) burada izlenir.
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename    VARCHAR(500) NOT NULL,
    file_type   VARCHAR(50),                           -- 'pdf', 'txt', 'md' vb.
    file_size   INTEGER,                               -- Bayt cinsinden boyut
    chunk_count INTEGER DEFAULT 0,                     -- Oluşturulan chunk sayısı
    -- İşlem pipeline durumu: Celery task'ı bu sütunu günceller
    status      VARCHAR(20) DEFAULT 'pending'
                    CHECK (status IN ('pending','processing','ready','failed')),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    metadata    JSONB DEFAULT '{}'                     -- Yazar, sayfa sayısı, kaynak URL vb.
);

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status  ON documents(status);


-- ──────────────────────────────────────────────────────────────────────────────
--  DOCUMENT_CHUNKS — Belge parçaları + pgvector embedding.
--
--  HNSW INDEX SEÇİMİ:
--    IVFFlat'a kıyasla daha yüksek recall, daha hızlı sorgu.
--    m=16 / ef_construction=64 → bellek ↔ hız dengesi için standart değerler.
--    vector_cosine_ops: normalize edilmiş embedding'ler için en uygun metrik.
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS document_chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,                      -- Belge içindeki sıra numarası (0-based)
    chunk_text  TEXT NOT NULL,                         -- Ham metin parçası
    embedding   vector(1536),                          -- text-embedding-v3 / ada-002 uyumlu boyut
    token_count INTEGER,                               -- Chunk token sayısı (context penceresi yönetimi)
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    metadata    JSONB DEFAULT '{}'                     -- Sayfa no, başlık, kaynak bölüm vb.
);

-- HNSW indeksi: cosine similarity ile Approximate Nearest Neighbor araması
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON document_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_chunks_user_id     ON document_chunks(user_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);


-- ══════════════════════════════════════════════════════════════════════════════
--  BÖLÜM 5: İZLEME VE ANALİTİK
-- ══════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────────
--  API_USAGE — Her LLM çağrısının token tüketimi ve maliyeti.
--  user_id NULL olabilir: anonim istekler veya kullanıcı silindikten sonra da
--  kayıtlar korunur (ON DELETE SET NULL).
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS api_usage (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID REFERENCES users(id) ON DELETE SET NULL,  -- Anonim istek desteği
    model               VARCHAR(100),                  -- Çağrılan model adı
    endpoint            VARCHAR(200),                  -- API endpoint (örn: /api/chat)
    prompt_tokens       INTEGER DEFAULT 0,
    completion_tokens   INTEGER DEFAULT 0,
    total_tokens        INTEGER DEFAULT 0,
    cost_usd            NUMERIC(10,6) DEFAULT 0,       -- Hesaplanan tahmini maliyet
    latency_ms          INTEGER,                       -- Uçtan uca yanıt süresi
    status_code         INTEGER,                       -- HTTP durum kodu (200, 429, 500 vb.)
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_user_id    ON api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_created_at ON api_usage(created_at DESC);


-- ══════════════════════════════════════════════════════════════════════════════
--  BÖLÜM 6: OTOMATİK GÜNCELLEME TRİGGER'LARI
--  updated_at sütunu olan her tablo için tek bir fonksiyon paylaşılır.
--  Bu yaklaşım DRY prensibine uyar ve bakım maliyetini düşürür.
-- ══════════════════════════════════════════════════════════════════════════════

-- Paylaşımlı trigger fonksiyonu: NEW.updated_at'ı her UPDATE'de NOW() yapar
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

-- users tablosu: profil güncellemelerinde otomatik zaman damgası
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- projects tablosu: proje adı, durum vb. değiştiğinde güncellenir
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- project_survey_data tablosu: anket yanıtları revize edildiğinde güncellenir
CREATE TRIGGER update_survey_data_updated_at
    BEFORE UPDATE ON project_survey_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- chat_sessions tablosu: başlık veya model ayarı değiştiğinde güncellenir
CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
