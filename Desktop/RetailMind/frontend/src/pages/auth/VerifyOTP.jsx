import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { authApi } from '../../services/api';
import AlertMessage from '../../components/AlertMessage';

const VerifyOTP = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const email = state?.email || '';
  const purpose = state?.purpose || 'registration';

  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [cooldown, setCooldown] = useState(0);
  const inputs = useRef([]);

  useEffect(() => {
    if (!email) navigate('/register');
  }, [email]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown(c => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  const handleChange = (i, val) => {
    if (!/^\d*$/.test(val)) return;
    const next = [...otp];
    next[i] = val.slice(-1);
    setOtp(next);
    if (val && i < 5) inputs.current[i + 1]?.focus();
  };

  const handleKeyDown = (i, e) => {
    if (e.key === 'Backspace' && !otp[i] && i > 0) inputs.current[i - 1]?.focus();
  };

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length === 6) {
      setOtp(pasted.split(''));
      inputs.current[5]?.focus();
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    const code = otp.join('');
    if (code.length < 6) { setError('Please enter all 6 digits.'); return; }
    setError(''); setLoading(true);
    try {
      if (purpose === 'registration') {
        await authApi.verifyOtp({ email, otp: code });
        navigate('/login', { state: { message: 'Account verified! You can now sign in.' } });
      } else {
        const res = await authApi.verifyResetOtp({ email, otp: code });
        navigate('/reset-password', { state: { email, reset_token: res.data.reset_token } });
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Invalid OTP.');
      setOtp(['', '', '', '', '', '']);
      inputs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    setError(''); setSuccess(''); setResending(true);
    try {
      await authApi.resendOtp({ email, purpose });
      setSuccess('A new OTP has been sent to your email.');
      setCooldown(60);
      setOtp(['', '', '', '', '', '']);
      inputs.current[0]?.focus();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to resend OTP.');
      if (err.response?.status === 429) {
        const match = detail?.match(/(\d+)/);
        if (match) setCooldown(parseInt(match[1]));
      }
    } finally {
      setResending(false);
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
          <i className="bi bi-shield-lock"></i>
        </div>

        <h2 className="auth-title">Verify your {purpose === 'registration' ? 'account' : 'identity'}</h2>
        <p className="auth-subtitle">
          Enter the 6-digit code sent to<br />
          <strong>{email}</strong>
        </p>

        <AlertMessage type="danger" message={error} onClose={() => setError('')} />
        <AlertMessage type="success" message={success} onClose={() => setSuccess('')} />

        <form onSubmit={submit}>
          <div className="otp-inputs" onPaste={handlePaste}>
            {otp.map((digit, i) => (
              <input
                key={i}
                ref={el => inputs.current[i] = el}
                type="text"
                inputMode="numeric"
                maxLength={1}
                className={`otp-box ${digit ? 'otp-filled' : ''}`}
                value={digit}
                onChange={e => handleChange(i, e.target.value)}
                onKeyDown={e => handleKeyDown(i, e)}
                autoFocus={i === 0}
              />
            ))}
          </div>

          <button type="submit" className="btn btn-primary w-100 btn-auth mt-3" disabled={loading}>
            {loading
              ? <><span className="spinner-border spinner-border-sm me-2" />Verifying...</>
              : <><i className="bi bi-check2-circle me-2"></i>Verify OTP</>
            }
          </button>
        </form>

        <div className="otp-resend-row">
          <span className="text-muted small">Didn't receive it?</span>
          {cooldown > 0
            ? <span className="otp-cooldown">Resend in {cooldown}s</span>
            : (
              <button className="btn-link-plain" onClick={resend} disabled={resending}>
                {resending ? 'Sending...' : 'Resend OTP'}
              </button>
            )
          }
        </div>

        <p className="auth-footer-text mt-3">
          <Link to="/login" className="auth-link">← Back to Sign In</Link>
        </p>
      </div>
    </div>
  );
};

export default VerifyOTP;
