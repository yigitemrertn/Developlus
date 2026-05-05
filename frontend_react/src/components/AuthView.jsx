import React, { useState } from 'react';
import { Mail, Lock, LogIn, UserPlus } from 'lucide-react';

export default function AuthView({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({ email: '', username: '', password: '', api: '' });
  const [isLoading, setIsLoading] = useState(false);

  const validate = () => {
    let isValid = true;
    const newErrors = { email: '', username: '', password: '', api: '' };

    if (!email || !/^\S+@\S+\.\S+$/.test(email)) {
      newErrors.email = 'Geçerli bir e-posta adresi giriniz.';
      isValid = false;
    }

    if (!isLogin && (!username || username.length < 3)) {
      newErrors.username = 'Kullanıcı adı en az 3 karakter olmalıdır.';
      isValid = false;
    }

    if (!password || password.length < 8) {
      newErrors.password = 'Şifre en az 8 karakter olmalıdır.';
      isValid = false;
    } else if (!isLogin) {
        if (!/[A-Z]/.test(password)) {
            newErrors.password = 'Şifre en az bir büyük harf içermelidir.';
            isValid = false;
        }
        if (!/\d/.test(password)) {
            newErrors.password = 'Şifre en az bir rakam içermelidir.';
            isValid = false;
        }
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (validate()) {
      setIsLoading(true);
      try {
        const endpoint = isLogin ? '/auth/login' : '/auth/register';
        const payload = isLogin 
            ? { email, password }
            : { email, username, password };
            
        const response = await fetch(`http://localhost:8000${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (isLogin) {
                localStorage.setItem('access_token', data.access_token);
                onLogin();
            } else {
                // Kayıt başarılı, login ekranına geç
                setIsLogin(true);
                setErrors({ email: '', username: '', password: '', api: 'Kayıt başarılı! Lütfen giriş yapın.' });
            }
        } else {
            setErrors(prev => ({ ...prev, api: data.detail || 'Bir hata oluştu.' }));
        }
      } catch (err) {
          setErrors(prev => ({ ...prev, api: 'Sunucuya bağlanılamadı.' }));
      } finally {
          setIsLoading(false);
      }
    }
  };

  return (
    <div className="auth-container app-layout">
      <div className="noise-overlay" />
      <div className="glow-orb glow-1" />
      <div className="glow-orb glow-2" />
      
      <div className="auth-card glass">
        <div className="auth-header">
          <div className="logo-text">Developlus</div>
          <h2>{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
          <p className="subtitle">
            {isLogin 
              ? 'Enter your credentials to access your projects.' 
              : 'Sign up to start building your tech stack.'}
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {errors.api && <div className="error-text" style={{ textAlign: 'center', marginBottom: '1rem', padding: '0.5rem', background: 'rgba(255,0,0,0.1)', borderRadius: '4px' }}>{errors.api}</div>}
          
          <div className="input-group">
            <label>Email Address</label>
            <div className="input-wrapper">
              <Mail size={18} className="input-icon" />
              <input 
                type="email" 
                placeholder="you@example.com" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            {errors.email && <span className="error-text">{errors.email}</span>}
          </div>

          {!isLogin && (
            <div className="input-group">
              <label>Username</label>
              <div className="input-wrapper">
                <UserPlus size={18} className="input-icon" />
                <input 
                  type="text" 
                  placeholder="johndoe" 
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
              {errors.username && <span className="error-text">{errors.username}</span>}
            </div>
          )}

          <div className="input-group">
            <label>Password</label>
            <div className="input-wrapper">
              <Lock size={18} className="input-icon" />
              <input 
                type="password" 
                placeholder="••••••••" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {errors.password && <span className="error-text">{errors.password}</span>}
          </div>

          <button type="submit" className="auth-submit-btn primary" disabled={isLoading}>
            {isLoading ? 'Lütfen bekleyin...' : (isLogin ? <><LogIn size={18} /> Login</> : <><UserPlus size={18} /> Sign Up</>)}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button 
              className="toggle-auth-btn"
              onClick={() => {
                setIsLogin(!isLogin);
                setErrors({ email: '', username: '', password: '', api: '' });
              }}
            >
              {isLogin ? 'Sign up' : 'Log in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
