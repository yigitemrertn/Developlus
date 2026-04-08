/* ═════════════════════════════════════════════════════════════
   Developlus — API Client
   Tüm backend iletişimi bu dosya üzerinden yönetilir.
   ═════════════════════════════════════════════════════════════ */

const API_BASE = '/api';

// Token yönetimi
const Token = {
  get access()  { return localStorage.getItem('dv_access_token'); },
  get refresh() { return localStorage.getItem('dv_refresh_token'); },
  set(access, refresh) {
    localStorage.setItem('dv_access_token', access);
    localStorage.setItem('dv_refresh_token', refresh);
  },
  clear() {
    localStorage.removeItem('dv_access_token');
    localStorage.removeItem('dv_refresh_token');
    localStorage.removeItem('dv_user');
  },
  isLoggedIn() { return !!this.access; },
};

// ─── HTTP Client ───────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (Token.access) {
    headers['Authorization'] = `Bearer ${Token.access}`;
  }

  let res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  // 401 → refresh token dene
  if (res.status === 401 && Token.refresh) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${Token.access}`;
      res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
      });
    } else {
      Token.clear();
      window.location.href = 'chat.html';
      return null;
    }
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(data?.detail || data?.error || `HTTP ${res.status}`);
  return data;
}

async function tryRefreshToken() {
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: Token.refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    Token.set(data.access_token, data.refresh_token);
    return true;
  } catch { return false; }
}

// ─── Auth API ─────────────────────────────────────────────────
const AuthAPI = {
  register: (data) => apiFetch('/auth/register',  { method: 'POST', body: data }),
  login:    (data) => apiFetch('/auth/login',    { method: 'POST', body: data }),
  logout:   ()     => apiFetch('/auth/logout',   { method: 'POST', body: { refresh_token: Token.refresh } }),
  me:       ()     => apiFetch('/auth/me'),
};

// ─── Chat API ─────────────────────────────────────────────────
const ChatAPI = {
  getSessions:  ()                     => apiFetch('/chat/sessions'),
  createSession: (data)                => apiFetch('/chat/sessions', { method: 'POST', body: data }),
  updateSession: (id, data)            => apiFetch(`/chat/sessions/${id}`, { method: 'PATCH', body: data }),
  deleteSession: (id)                  => apiFetch(`/chat/sessions/${id}`, { method: 'DELETE' }),
  getMessages:  (sessionId)            => apiFetch(`/chat/sessions/${sessionId}/messages`),

  // SSE Streaming — özel implementasyon
  streamChat: async function(sessionId, message, onToken, onDone, onError) {
    try {
      const res = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${Token.access}`,
        },
        body: JSON.stringify({ session_id: sessionId, message }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Son satır tamamlanmamış olabilir

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const json = JSON.parse(line.slice(6));
              if (json.error) { onError(json.error); return; }
              if (json.done)  { onDone(); return; }
              if (json.token) { onToken(json.token); }
            } catch { continue; }
          }
        }
      }
      onDone();
    } catch (err) {
      onError(err.message);
    }
  },
};

// ─── RAG API ──────────────────────────────────────────────────
const RAGAPI = {
  getDocuments: () => apiFetch('/rag/documents'),

  uploadDocument: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API_BASE}/rag/documents`);
      xhr.setRequestHeader('Authorization', `Bearer ${Token.access}`);

      if (onProgress) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          const err = JSON.parse(xhr.responseText || '{}');
          reject(new Error(err.detail || `HTTP ${xhr.status}`));
        }
      };
      xhr.onerror = () => reject(new Error('Ağ hatası'));
      xhr.send(formData);
    });
  },

  deleteDocument: (id) => apiFetch(`/rag/documents/${id}`, { method: 'DELETE' }),
};
