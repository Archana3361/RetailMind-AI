import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../../services/api';
import AlertMessage from '../../components/AlertMessage';

// Field component at module scope to prevent remounting on parent re-renders
const Field = ({ name, label, type = 'text', placeholder, icon, value, onChange, error }) => (
  <div className="mb-3">
    <label className="form-label">{label}</label>
    <div className="input-group">
      <span className="input-group-text"><i className={`bi bi-${icon}`}></i></span>
      <input
        type={type} name={name} className={`form-control ${error ? 'is-invalid' : ''}`}
        placeholder={placeholder} value={value} onChange={onChange}
      />
    </div>
    {error && <div className="invalid-feedback d-block">{error}</div>}
  </div>
);

const Register = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: '', email: '', mobile: '', shop_name: '', password: '', confirm_password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});

  const handle = (e) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
    setFieldErrors(fe => ({ ...fe, [e.target.name]: '' }));
  };

  const validate = () => {
    const errs = {};
    if (!form.full_name.trim()) errs.full_name = 'Full name is required';
    if (!form.email.trim()) errs.email = 'Email is required';
    if (!form.mobile.trim()) errs.mobile = 'Mobile number is required';
    if (!form.shop_name.trim()) errs.shop_name = 'Shop name is required';
    if (form.password.length < 8) errs.password = 'Password must be at least 8 characters';
    if (form.password !== form.confirm_password) errs.confirm_password = 'Passwords do not match';
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (!validate()) return;
    setLoading(true);
    try {
      await authApi.register(form);
      navigate('/verify-otp', { state: { email: form.email, purpose: 'registration' } });
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map(d => d.msg).join(', '));
      } else {
        setError(typeof detail === 'string' ? detail : 'Registration failed.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card auth-card-wide">
        <div className="auth-brand">
          <svg width="36" height="36" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#3b82f6" fillOpacity="0.12"/>
            <path d="M7 22 L13 12 L17 18 L21 10 L25 16" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            <circle cx="25" cy="16" r="2" fill="#10b981"/>
          </svg>
          <span className="auth-brand-name">RetailMind <span className="auth-brand-ai">AI</span></span>
        </div>

        <h2 className="auth-title">Create your account</h2>
        <p className="auth-subtitle">Start managing your retail business smarter</p>

        <AlertMessage type="danger" message={error} onClose={() => setError('')} />

        <form onSubmit={submit} noValidate>
          <div className="row g-3">
            <div className="col-md-6">
              <Field name="full_name" label="Full Name" placeholder="John Smith" icon="person" value={form.full_name} onChange={handle} error={fieldErrors.full_name} />
            </div>
            <div className="col-md-6">
              <Field name="shop_name" label="Shop Name" placeholder="My Retail Store" icon="shop" value={form.shop_name} onChange={handle} error={fieldErrors.shop_name} />
            </div>
            <div className="col-md-6">
              <Field name="email" label="Email Address" type="email" placeholder="you@example.com" icon="envelope" value={form.email} onChange={handle} error={fieldErrors.email} />
            </div>
            <div className="col-md-6">
              <Field name="mobile" label="Mobile Number" type="tel" placeholder="+91 98765 43210" icon="phone" value={form.mobile} onChange={handle} error={fieldErrors.mobile} />
            </div>
            <div className="col-md-6">
              <div className="mb-0">
                <label className="form-label">Password</label>
                <div className="input-group">
                  <span className="input-group-text"><i className="bi bi-lock"></i></span>
                  <input
                    type={showPass ? 'text' : 'password'} name="password"
                    className={`form-control ${fieldErrors.password ? 'is-invalid' : ''}`}
                    placeholder="Min 8 characters" value={form.password} onChange={handle}
                  />
                  <button type="button" className="input-group-text btn-show-pass" onClick={() => setShowPass(s => !s)}>
                    <i className={`bi bi-eye${showPass ? '-slash' : ''}`}></i>
                  </button>
                </div>
                {fieldErrors.password && <div className="invalid-feedback d-block">{fieldErrors.password}</div>}
              </div>
            </div>
            <div className="col-md-6">
              <div className="mb-0">
                <label className="form-label">Confirm Password</label>
                <div className="input-group">
                  <span className="input-group-text"><i className="bi bi-lock-fill"></i></span>
                  <input
                    type={showPass ? 'text' : 'password'} name="confirm_password"
                    className={`form-control ${fieldErrors.confirm_password ? 'is-invalid' : ''}`}
                    placeholder="Repeat password" value={form.confirm_password} onChange={handle}
                  />
                </div>
                {fieldErrors.confirm_password && <div className="invalid-feedback d-block">{fieldErrors.confirm_password}</div>}
              </div>
            </div>
          </div>

          <button type="submit" className="btn btn-primary w-100 btn-auth mt-4" disabled={loading}>
            {loading
              ? <><span className="spinner-border spinner-border-sm me-2" />Creating account...</>
              : <><i className="bi bi-person-plus me-2"></i>Create Account</>
            }
          </button>
        </form>

        <p className="auth-footer-text">
          Already have an account? <Link to="/login" className="auth-link">Sign in</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
