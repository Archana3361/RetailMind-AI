import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../../services/api';
import AlertMessage from '../../components/AlertMessage';

const ForgotPassword = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      await authApi.forgotPassword({ email });
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
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
          <div className="text-center py-3">
            <div className="otp-icon-wrap" style={{ color: 'var(--color-success)' }}>
              <i className="bi bi-envelope-check"></i>
            </div>
            <h2 className="auth-title">Check your email</h2>
            <p className="auth-subtitle">
              If <strong>{email}</strong> is registered, a password reset OTP has been sent.
              Check your inbox and spam folder.
            </p>
            <button
              className="btn btn-primary btn-auth w-100 mt-2"
              onClick={() => navigate('/verify-otp', { state: { email, purpose: 'password_reset' } })}
            >
              <i className="bi bi-arrow-right me-2"></i>Enter OTP
            </button>
          </div>
          <p className="auth-footer-text">
            <Link to="/login" className="auth-link">← Back to Sign In</Link>
          </p>
        </div>
      </div>
    );
  }

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

        <div className="otp-icon-wrap">
          <i className="bi bi-key"></i>
        </div>
        <h2 className="auth-title">Forgot password?</h2>
        <p className="auth-subtitle">Enter your email and we'll send you a reset code.</p>

        <AlertMessage type="danger" message={error} onClose={() => setError('')} />

        <form onSubmit={submit}>
          <div className="mb-4">
            <label className="form-label">Email address</label>
            <div className="input-group">
              <span className="input-group-text"><i className="bi bi-envelope"></i></span>
              <input
                type="email" className="form-control" placeholder="you@example.com"
                value={email} onChange={e => setEmail(e.target.value)} required autoFocus
              />
            </div>
          </div>
          <button type="submit" className="btn btn-primary w-100 btn-auth" disabled={loading}>
            {loading
              ? <><span className="spinner-border spinner-border-sm me-2" />Sending...</>
              : <><i className="bi bi-send me-2"></i>Send Reset Code</>
            }
          </button>
        </form>

        <p className="auth-footer-text mt-3">
          <Link to="/login" className="auth-link">← Back to Sign In</Link>
        </p>
      </div>
    </div>
  );
};

export default ForgotPassword;
