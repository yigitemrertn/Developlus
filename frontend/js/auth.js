/* ═════════════════════════════════════════════════════════════
   Developlus — Auth JS
   Hem chat sayfası hem de landing page için auth durumu.
   ═════════════════════════════════════════════════════════════ */

// Landing page'de oturum açıksa CTA butonlarını güncelle
(function updateLandingAuth() {
  if (!document.getElementById('nav-login')) return; // Chat sayfasında çalışma
  if (Token && Token.isLoggedIn()) {
    const loginBtn    = document.getElementById('nav-login');
    const registerBtn = document.getElementById('nav-register');
    const heroBtn     = document.getElementById('hero-start');
    if (loginBtn)    loginBtn.textContent    = 'Dashboard';
    if (registerBtn) { registerBtn.textContent = 'Chate Git'; registerBtn.href = 'chat.html'; }
    if (heroBtn)     heroBtn.href = 'chat.html';
  }
})();

// ─── Chat sayfası auth ─────────────────────────────────────────

function switchTab(tab) {
  const loginForm    = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  if (!loginForm) return;
  if (tab === 'login') {
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');
  } else {
    loginForm.classList.add('hidden');
    registerForm.classList.remove('hidden');
  }
}

function togglePassword(inputId) {
  const input = document.getElementById(inputId);
  input.type = input.type === 'password' ? 'text' : 'password';
}

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  const span    = btn.querySelector('span');
  const spinner = btn.querySelector('.btn-spinner');
  btn.disabled  = loading;
  if (span)    span.classList.toggle('hidden', loading);
  if (spinner) spinner.classList.toggle('hidden', !loading);
}

function showError(containerId, msg) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.textContent = msg;
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 5000);
}

async function handleLogin() {
  const email    = document.getElementById('login-email')?.value?.trim();
  const password = document.getElementById('login-password')?.value;
  if (!email || !password) return showError('login-error', 'Email ve şifre zorunludur');

  setLoading('login-btn', true);
  try {
    const data = await AuthAPI.login({ email, password });
    Token.set(data.access_token, data.refresh_token);
    await loadCurrentUser();
    showApp();
  } catch (err) {
    showError('login-error', err.message);
  } finally {
    setLoading('login-btn', false);
  }
}

async function handleRegister() {
  const fullName = document.getElementById('reg-fullname')?.value?.trim();
  const username = document.getElementById('reg-username')?.value?.trim();
  const email    = document.getElementById('reg-email')?.value?.trim();
  const password = document.getElementById('reg-password')?.value;

  if (!username || !email || !password) return showError('register-error', 'Tüm alanları doldurun');

  setLoading('register-btn', true);
  try {
    await AuthAPI.register({ email, username, password, full_name: fullName });
    // Otomatik giriş
    const loginData = await AuthAPI.login({ email, password });
    Token.set(loginData.access_token, loginData.refresh_token);
    await loadCurrentUser();
    showApp();
  } catch (err) {
    showError('register-error', err.message);
  } finally {
    setLoading('register-btn', false);
  }
}

async function handleLogout() {
  try { await AuthAPI.logout(); } catch {}
  Token.clear();
  location.reload();
}

async function loadCurrentUser() {
  try {
    const user = await AuthAPI.me();
    localStorage.setItem('dv_user', JSON.stringify(user));
    updateUserUI(user);
  } catch {}
}

function updateUserUI(user) {
  const nameEl  = document.getElementById('user-display-name');
  const tierEl  = document.getElementById('user-tier');
  const avatarEl = document.getElementById('user-avatar');
  if (nameEl)  nameEl.textContent  = user.full_name || user.username;
  if (tierEl)  tierEl.textContent  = user.tier;
  if (avatarEl) avatarEl.textContent = (user.full_name || user.username || 'U')[0].toUpperCase();
}

function showApp() {
  const modal = document.getElementById('auth-modal');
  const app   = document.getElementById('app');
  if (modal) modal.classList.remove('active');
  if (app)   app.classList.remove('hidden');
}

// Sayfa yüklendiğinde auth kontrolü
document.addEventListener('DOMContentLoaded', async () => {
  // Sadece chat.html'de çalış
  if (!document.getElementById('auth-modal')) return;

  if (Token.isLoggedIn()) {
    await loadCurrentUser();
    showApp();
    // Cached user varsa hemen göster
    const cached = localStorage.getItem('dv_user');
    if (cached) updateUserUI(JSON.parse(cached));
  }

  // Enter tuşu
  document.getElementById('login-password')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') handleLogin();
  });
  document.getElementById('reg-password')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') handleRegister();
  });
});
