import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import AlertMessage from '../../components/AlertMessage';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const from = location.state?.from?.pathname || '/dashboard';

  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPass, setShowPass] = useState(false);

  const handle = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await authApi.login(form);
      login(res.data.access_token, res.data.user);
      navigate(from, { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <svg width="36" height="36" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#3b82f6" fillOpacity="0.12"/>
            <path d="M7 22 L13 12 L17 18 L21 10 L25 16" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            <circle cx="25" cy="16" r="2" fill="#10b981"/>
          </svg>
          <span className="auth-brand-name">RetailMind <span className="auth-brand-ai">AI</span></span>
        </div>

        <h2 className="auth-title">Welcome back</h2>
        <p className="auth-subtitle">Sign in to your account to continue</p>

        <AlertMessage type="danger" message={error} onClose={() => setError('')} />

        <form onSubmit={submit} noValidate>
          <div className="mb-3">
            <label className="form-label">Email address</label>
            <div className="input-group">
              <span className="input-group-text"><i className="bi bi-envelope"></i></span>
              <input
                type="email" name="email" className="form-control"
                placeholder="you@example.com"
                value={form.email} onChange={handle} required autoFocus
              />
            </div>
          </div>

          <div className="mb-4">
            <div className="d-flex justify-content-between align-items-center mb-1">
              <label className="form-label mb-0">Password</label>
              <Link to="/forgot-password" className="auth-link-small">Forgot password?</Link>
            </div>
            <div className="input-group">
              <span className="input-group-text"><i className="bi bi-lock"></i></span>
              <input
                type={showPass ? 'text' : 'password'} name="password" className="form-control"
                placeholder="Enter your password"
                value={form.password} onChange={handle} required
              />
              <button type="button" className="input-group-text btn-show-pass" onClick={() => setShowPass(s => !s)}>
                <i className={`bi bi-eye${showPass ? '-slash' : ''}`}></i>
              </button>
            </div>
          </div>

          <button type="submit" className="btn btn-primary w-100 btn-auth" disabled={loading}>
            {loading
              ? <><span className="spinner-border spinner-border-sm me-2" />Signing in...</>
              : <><i className="bi bi-box-arrow-in-right me-2"></i>Sign In</>
            }
          </button>
        </form>

        <p className="auth-footer-text">
          Don't have an account? <Link to="/register" className="auth-link">Create account</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
