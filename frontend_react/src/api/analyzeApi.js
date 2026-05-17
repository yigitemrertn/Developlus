import { generateMockResults } from '../data/categories';

const API_URL = import.meta.env.VITE_API_URL;

/**
 * Proje açıklamasını analiz eder.
 * Backend hazır olunca mock kaldırılır, sadece fetch çağrısı kalır.
 *
 * @param {string} prompt - Kullanıcının proje açıklaması
 * @returns {Promise<Array>} - Teknoloji önerileri dizisi
 */
export async function analyzeProject(prompt) {
  // Backend bağlantısı varsa gerçek API'ye git
  if (API_URL) {
    try {
      const res = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      if (!res.ok) throw new Error('API hatası');
      const data = await res.json();
      return data.results;
    } catch (err) {
      console.warn('Backend bağlantısı başarısız, mock data kullanılıyor:', err);
    }
  }

  // Mock: backend hazır olmadan çalışmak için
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(generateMockResults(prompt));
    }, 1800);
  });
}

const chatResponsesPool = [
  'Proje fikrin ilginç görünüyor! Hangi ölçekte bir kullanıcı kitlesini hedefliyorsun?',
  'Bu tür projeler için genellikle React + FastAPI kombinasyonu çok iyi çalışır.',
  'Veritabanı seçiminde proje gereksinimlerini iyi analiz etmek önemli. İlişkisel mi yoksa NoSQL mu daha uygun?',
  'Microservices mimarisi ölçeklenebilirlik için harika ama MVP aşamasında monolith ile başlamak daha pratik olabilir.',
  'CI/CD pipeline kurmayı unutma! GitHub Actions başlangıç için ideal.',
  'Authentication için NextAuth.js veya Clerk gibi modern çözümler geliştirme sürecini çok hızlandırır.',
  'Docker ile deployment yapman taşınabilirlik açısından büyük avantaj sağlar.',
  'API tasarımında REST ve GraphQL arasında projenin ihtiyaçlarına göre seçim yapmalısın.',
];

/**
 * Chat mesajına yanıt üretir.
 * Backend LLM hazır olunca buraya fetch eklenecek.
 */
export async function sendChatMessage(message) {
  if (API_URL) {
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });
      if (!res.ok) throw new Error('Chat API hatası');
      const data = await res.json();
      return data.reply;
    } catch (err) {
      console.warn('Chat backend bağlantısı başarısız, mock yanıt kullanılıyor:', err);
    }
  }

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(chatResponsesPool[Math.floor(Math.random() * chatResponsesPool.length)]);
    }, 800);
  });
}

export async function getLatestStack(projectId) {
  if (API_URL) {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API_URL}/projects/${projectId}/stack`, {
        headers: { 
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error('Stack API hatası');
      return await res.json();
    } catch (err) {
      console.error('Stack fetching failed:', err);
      return null;
    }
  }
  return null;
}
