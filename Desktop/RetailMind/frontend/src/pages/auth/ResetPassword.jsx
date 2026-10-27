import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { authApi } from '../../services/api';
import AlertMessage from '../../components/AlertMessage';

const ResetPassword = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const email = state?.email || '';
  const reset_token = state?.reset_token || '';

  const [form, setForm] = useState({ new_password: '', confirm_password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPass, setShowPass] = useState(false);

  useEffect(() => {
    if (!email || !reset_token) navigate('/forgot-password');
  }, [email, reset_token]);

  const submit = async (e) => {
    e.preventDefault();
    if (form.new_password !== form.confirm_password) {
      setError('Passwords do not match.'); return;
    }
    if (form.new_password.length < 8) {
      setError('Password must be at least 8 characters.'); return;
    }
    setError(''); setLoading(true);
    try {
      await authApi.resetPassword({ email, reset_token, ...form });
      navigate('/login', { state: { message: 'Password reset successfully. You can now sign in.' } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset password.');
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

        <div className="otp-icon-wrap">
          <i className="bi bi-shield-check"></i>
        </div>
        <h2 className="auth-title">Set new password</h2>
        <p className="auth-subtitle">Choose a strong password for <strong>{email}</strong></p>

        <AlertMessage type="danger" message={error} onClose={() => setError('')} />

        <form onSubmit={submit}>
          <div className="mb-3">
            <label className="form-label">New Password</label>
            <div className="input-group">
              <span className="input-group-text"><i className="bi bi-lock"></i></span>
              <input
                type={showPass ? 'text' : 'password'} className="form-control"
                placeholder="Min 8 characters"
                value={form.new_password}
                onChange={e => setForm(f => ({ ...f, new_password: e.target.value }))}
                required
              />
              <button type="button" className="input-group-text btn-show-pass" onClick={() => setShowPass(s => !s)}>
                <i className={`bi bi-eye${showPass ? '-slash' : ''}`}></i>
              </button>
            </div>
          </div>
          <div className="mb-4">
            <label className="form-label">Confirm New Password</label>
            <div className="input-group">
              <span className="input-group-text"><i className="bi bi-lock-fill"></i></span>
              <input
                type={showPass ? 'text' : 'password'} className="form-control"
                placeholder="Repeat password"
                value={form.confirm_password}
                onChange={e => setForm(f => ({ ...f, confirm_password: e.target.value }))}
                required
              />
            </div>
          </div>
          <button type="submit" className="btn btn-primary w-100 btn-auth" disabled={loading}>
            {loading
              ? <><span className="spinner-border spinner-border-sm me-2" />Resetting...</>
              : <><i className="bi bi-check2 me-2"></i>Reset Password</>
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

export default ResetPassword;
