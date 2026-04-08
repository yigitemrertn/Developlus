/* ═════════════════════════════════════════════════════════════
   Developlus — Chat JS
   SSE streaming, session yönetimi, RAG, Markdown rendering
   ═════════════════════════════════════════════════════════════ */

// ─── State ────────────────────────────────────────────────────
let currentSessionId = null;
let isStreaming = false;
let allSessions  = [];
let allDocs = [];

// Marked.js yapılandırması (Markdown → HTML)
if (typeof marked !== 'undefined') {
  marked.setOptions({
    breaks: true,
    gfm: true,
    sanitize: false,
  });
}

// ─── Uygulama Başlatma ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  if (!document.getElementById('app')) return;

  // Giriş yapmış kullanıcı için sessionsları yükle
  if (Token.isLoggedIn()) {
    await loadSessions();
    await loadDocuments();
  }
});

// ─── Sessions ─────────────────────────────────────────────────
async function loadSessions() {
  try {
    allSessions = await ChatAPI.getSessions();
    renderSessions(allSessions);
  } catch (err) {
    console.error('Oturumlar yüklenemedi:', err);
  }
}

function renderSessions(sessions) {
  const list  = document.getElementById('sessions-list');
  const empty = document.getElementById('sessions-empty');
  if (!list) return;

  if (sessions.length === 0) {
    empty.style.display = 'flex';
    list.innerHTML = '';
    list.appendChild(empty);
    return;
  }

  empty.style.display = 'none';
  list.innerHTML = '';

  sessions.forEach(session => {
    const item = document.createElement('div');
    item.className = `session-item${session.id === currentSessionId ? ' active' : ''}`;
    item.dataset.id = session.id;
    item.innerHTML = `
      <div class="session-icon">💬</div>
      <div class="session-info">
        <div class="session-name" title="${escapeHtml(session.title)}">${escapeHtml(session.title)}</div>
        <div class="session-meta">${session.message_count} mesaj · ${formatDate(session.updated_at)}</div>
      </div>
      <button class="session-delete" onclick="deleteSession(event, '${session.id}')" title="Sil">✕</button>
    `;
    item.addEventListener('click', () => openSession(session));
    list.appendChild(item);
  });
}

function filterSessions(query) {
  const filtered = allSessions.filter(s =>
    s.title.toLowerCase().includes(query.toLowerCase())
  );
  renderSessions(filtered);
}

async function createNewSession() {
  if (isStreaming) return;
  try {
    const session = await ChatAPI.createSession({
      title: 'Yeni Sohbet',
      model_used: document.getElementById('model-select')?.value || 'qwen-turbo',
    });
    allSessions.unshift(session);
    renderSessions(allSessions);
    openSession(session);
  } catch (err) {
    alert('Oturum oluşturulamadı: ' + err.message);
  }
}

async function openSession(session) {
  currentSessionId = session.id;

  // UI güncelle
  document.querySelectorAll('.session-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === session.id);
  });

  // Welcome → Messages
  document.getElementById('welcome-screen').classList.add('hidden');
  document.getElementById('messages-area').classList.remove('hidden');
  document.getElementById('current-session-title').textContent = session.title;

  // RAG badge
  const ragBadge = document.getElementById('rag-badge');
  if (ragBadge) ragBadge.classList.toggle('hidden', !session.use_rag);

  // Mesajları yükle
  await loadMessages(session.id);

  // Fokus
  document.getElementById('message-input')?.focus();
}

async function deleteSession(event, sessionId) {
  event.stopPropagation();
  if (!confirm('Bu sohbeti silmek istediğinizden emin misiniz?')) return;
  try {
    await ChatAPI.deleteSession(sessionId);
    allSessions = allSessions.filter(s => s.id !== sessionId);
    renderSessions(allSessions);
    if (currentSessionId === sessionId) {
      currentSessionId = null;
      document.getElementById('welcome-screen').classList.remove('hidden');
      document.getElementById('messages-area').classList.add('hidden');
    }
  } catch (err) {
    alert('Silinemedi: ' + err.message);
  }
}

// ─── Messages ─────────────────────────────────────────────────
async function loadMessages(sessionId) {
  const list = document.getElementById('messages-list');
  list.innerHTML = '';
  try {
    const messages = await ChatAPI.getMessages(sessionId);
    messages.forEach(msg => appendMessage(msg.role, msg.content, msg.created_at, false));
    scrollToBottom();
  } catch (err) {
    console.error('Mesajlar yüklenemedi:', err);
  }
}

function appendMessage(role, content, time = null, animate = true) {
  const list = document.getElementById('messages-list');
  const user = JSON.parse(localStorage.getItem('dv_user') || '{}');

  const div = document.createElement('div');
  div.className = `message ${role}${animate ? '' : ''}`;

  const avatar = role === 'user'
    ? `<div class="message-avatar">${(user.full_name || user.username || 'U')[0].toUpperCase()}</div>`
    : `<div class="message-avatar">🤖</div>`;

  const name = role === 'user' ? (user.full_name || user.username || 'Siz') : 'Developlus AI';
  const timeStr = time ? formatTime(time) : formatTime(new Date().toISOString());

  // Markdown render
  const rendered = role === 'assistant' && typeof marked !== 'undefined'
    ? marked.parse(content)
    : escapeHtml(content).replace(/\n/g, '<br>');

  div.innerHTML = `
    ${avatar}
    <div class="message-content">
      <div class="message-header">
        <span class="message-role">${name}</span>
        <span class="message-time">${timeStr}</span>
      </div>
      <div class="message-body">${rendered}</div>
    </div>
  `;

  list.appendChild(div);
  if (animate) scrollToBottom();
  return div;
}

function appendTypingIndicator() {
  const list = document.getElementById('messages-list');
  const div = document.createElement('div');
  div.id = 'typing-indicator';
  div.className = 'message assistant';
  div.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  list.appendChild(div);
  scrollToBottom();
  return div;
}

// ─── Send Message ─────────────────────────────────────────────
async function sendMessage() {
  if (isStreaming || !currentSessionId) return;
  const input = document.getElementById('message-input');
  const message = input.value.trim();
  if (!message) return;

  // Oturum yoksa önce oluştur
  if (!currentSessionId) {
    await createNewSession();
  }

  // UI sıfırla
  input.value = '';
  autoResize(input);
  updateCharCount('');
  document.getElementById('send-btn').disabled = true;
  isStreaming = true;

  // Kullanıcı mesajını ekle
  appendMessage('user', message);

  // Typing indicator
  const typingEl = appendTypingIndicator();

  // Streaming yanıt kutusu hazırla
  let assistantDiv = null;
  let accumulatedText = '';

  await ChatAPI.streamChat(
    currentSessionId,
    message,
    // onToken
    (token) => {
      if (typingEl.parentNode) typingEl.remove();
      if (!assistantDiv) {
        assistantDiv = appendMessage('assistant', '', null, false);
      }
      accumulatedText += token;
      const bodyEl = assistantDiv.querySelector('.message-body');
      if (bodyEl) {
        bodyEl.innerHTML = typeof marked !== 'undefined'
          ? marked.parse(accumulatedText)
          : escapeHtml(accumulatedText).replace(/\n/g, '<br>');
      }
      scrollToBottom();
    },
    // onDone
    async () => {
      if (typingEl.parentNode) typingEl.remove();
      isStreaming = false;
      document.getElementById('send-btn').disabled = !input.value.trim();
      // Session başlığını güncelle
      await loadSessions();
    },
    // onError
    (errMsg) => {
      if (typingEl.parentNode) typingEl.remove();
      appendMessage('assistant', `❌ Hata: ${errMsg}`);
      isStreaming = false;
      document.getElementById('send-btn').disabled = !input.value.trim();
    }
  );
}

async function startWithPrompt(prompt) {
  await createNewSession();
  const input = document.getElementById('message-input');
  input.value = prompt;
  autoResize(input);
  updateCharCount(prompt);
  document.getElementById('send-btn').disabled = false;
  await sendMessage();
}

// ─── Input Handlers ───────────────────────────────────────────
function handleKeyDown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
  const val = textarea.value;
  updateCharCount(val);
  document.getElementById('send-btn').disabled = !val.trim() || isStreaming;
}

function updateCharCount(val) {
  const el = document.getElementById('char-count');
  if (!el) return;
  const len = val.length;
  el.textContent = `${len} / 32000`;
  el.className = 'char-count' + (len > 28000 ? ' warn' : '') + (len > 32000 ? ' over' : '');
}

// ─── RAG Mode ─────────────────────────────────────────────────
async function toggleRagMode() {
  if (!currentSessionId) return;
  const session = allSessions.find(s => s.id === currentSessionId);
  if (!session) return;

  const newRag = !session.use_rag;
  try {
    await ChatAPI.updateSession(currentSessionId, { use_rag: newRag });
    session.use_rag = newRag;
    const badge = document.getElementById('rag-badge');
    const btn   = document.getElementById('rag-toggle-btn');
    if (badge) badge.classList.toggle('hidden', !newRag);
    if (btn)   btn.classList.toggle('active', newRag);
  } catch {}
}

async function updateCurrentModel(model) {
  if (!currentSessionId) return;
  try {
    await ChatAPI.updateSession(currentSessionId, { model_used: model });
    const session = allSessions.find(s => s.id === currentSessionId);
    if (session) session.model_used = model;
  } catch {}
}

// ─── Documents (RAG) ──────────────────────────────────────────
async function loadDocuments() {
  try {
    allDocs = await RAGAPI.getDocuments();
    renderDocuments();
    updateDocsCount();
  } catch {}
}

function renderDocuments() {
  const list = document.getElementById('docs-list');
  if (!list) return;
  if (allDocs.length === 0) {
    list.innerHTML = '<p style="font-size:13px;color:var(--text-muted);text-align:center;padding:20px">Henüz belge yok</p>';
    return;
  }
  list.innerHTML = allDocs.map(doc => `
    <div class="doc-item" id="doc-${doc.id}">
      <div class="doc-icon">${doc.file_type === 'application/pdf' ? '📄' : '📝'}</div>
      <div class="doc-info">
        <div class="doc-name" title="${escapeHtml(doc.filename)}">${escapeHtml(doc.filename)}</div>
        <div class="doc-status ${doc.status}">${statusLabel(doc.status)} · ${doc.chunk_count} bölüm</div>
      </div>
      <button class="doc-delete" onclick="deleteDoc('${doc.id}')">✕</button>
    </div>
  `).join('');
}

function updateDocsCount() {
  const el = document.getElementById('docs-count');
  if (!el) return;
  if (allDocs.length > 0) {
    el.textContent = allDocs.length;
    el.classList.remove('hidden');
  } else {
    el.classList.add('hidden');
  }
}

async function handleFileUpload(input) {
  const file = input.files[0];
  if (!file) return;
  input.value = '';

  const progress = document.getElementById('upload-progress');
  const fill     = document.getElementById('progress-fill');
  const status   = document.getElementById('upload-status');

  progress.classList.remove('hidden');
  fill.style.width = '0%';
  status.textContent = 'Yükleniyor...';

  try {
    const doc = await RAGAPI.uploadDocument(file, (pct) => {
      fill.style.width = pct + '%';
      status.textContent = `Yükleniyor... ${pct}%`;
    });
    status.textContent = 'İndeksleniyor...';
    allDocs.unshift(doc);
    renderDocuments();
    updateDocsCount();
    setTimeout(() => progress.classList.add('hidden'), 2000);
  } catch (err) {
    status.textContent = '❌ ' + err.message;
    setTimeout(() => progress.classList.add('hidden'), 3000);
  }
}

async function deleteDoc(docId) {
  if (!confirm('Bu belgeyi silmek istediğinizden emin misiniz?')) return;
  try {
    await RAGAPI.deleteDocument(docId);
    allDocs = allDocs.filter(d => d.id !== docId);
    renderDocuments();
    updateDocsCount();
  } catch (err) {
    alert('Silinemedi: ' + err.message);
  }
}

function toggleDocsPanel() {
  const panel = document.getElementById('docs-panel');
  panel.classList.toggle('hidden');
}

// ─── Sidebar ──────────────────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('collapsed');
}

// ─── Utilities ────────────────────────────────────────────────
function scrollToBottom() {
  const list = document.getElementById('messages-list');
  if (list) list.scrollTop = list.scrollHeight;
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  const now = new Date();
  const diff = now - d;
  if (diff < 60 * 60 * 1000) return 'az önce';
  if (diff < 24 * 60 * 60 * 1000) return 'bugün';
  return d.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
}

function formatTime(isoStr) {
  if (!isoStr) return '';
  return new Date(isoStr).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
}

function statusLabel(status) {
  const labels = { ready: 'Hazır ✓', pending: 'Bekliyor', processing: 'İndeksleniyor...', failed: 'Başarısız ✗' };
  return labels[status] || status;
}
