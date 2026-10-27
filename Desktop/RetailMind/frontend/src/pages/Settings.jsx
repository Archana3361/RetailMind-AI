import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../services/api';
import PageHeader from '../components/PageHeader';
import AlertMessage from '../components/AlertMessage';

const Settings = () => {
  const { user } = useAuth();
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [pwLoading, setPwLoading] = useState(false);
  const [pwError, setPwError] = useState('');
  const [pwSuccess, setPwSuccess] = useState('');
  const [showPw, setShowPw] = useState(false);

  const handlePw = e => setPwForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const changePw = async (e) => {
    e.preventDefault();
    if (pwForm.new_password !== pwForm.confirm_password) {
      setPwError('New passwords do not match.'); return;
    }
    if (pwForm.new_password.length < 8) {
      setPwError('New password must be at least 8 characters.'); return;
    }
    setPwLoading(true); setPwError(''); setPwSuccess('');
    try {
      // Use the reset-password endpoint (email + new password)
      await authApi.resetPassword({ email: user.email, new_password: pwForm.new_password, confirm_password: pwForm.confirm_password });
      setPwSuccess('Password changed successfully.');
      setPwForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      setPwError(err.response?.data?.detail || 'Failed to change password.');
    } finally { setPwLoading(false); }
  };

  return (
    <div className="page-container">
      <PageHeader title="Settings" subtitle="Manage your account and preferences" />

      <div className="settings-layout">
        {/* Account Info */}
        <div className="settings-card">
          <h4 className="settings-section-title">
            <i className="bi bi-person-circle me-2"></i>Account Information
          </h4>
          <div className="settings-info-grid">
            <div className="settings-info-item">
              <p className="si-label">Full Name</p>
              <p className="si-value">{user?.full_name}</p>
            </div>
            <div className="settings-info-item">
              <p className="si-label">Email</p>
              <p className="si-value">{user?.email}</p>
            </div>
            <div className="settings-info-item">
              <p className="si-label">Mobile</p>
              <p className="si-value">{user?.mobile}</p>
            </div>
            <div className="settings-info-item">
              <p className="si-label">Shop Name</p>
              <p className="si-value">{user?.shop_name}</p>
            </div>
            <div className="settings-info-item">
              <p className="si-label">Account Status</p>
              <p className="si-value">
                <span className="badge bg-success">Verified & Active</span>
              </p>
            </div>
          </div>
        </div>

        {/* Change Password */}
        <div className="settings-card">
          <h4 className="settings-section-title">
            <i className="bi bi-shield-lock me-2"></i>Change Password
          </h4>
          <AlertMessage type="success" message={pwSuccess} onClose={() => setPwSuccess('')} />
          <AlertMessage type="danger" message={pwError} onClose={() => setPwError('')} />
          <form onSubmit={changePw} style={{ maxWidth: 420 }}>
            <div className="mb-3">
              <label className="form-label">New Password</label>
              <div className="input-group">
                <input type={showPw ? 'text' : 'password'} name="new_password" className="form-control"
                  placeholder="Min 8 characters" value={pwForm.new_password} onChange={handlePw} required />
                <button type="button" className="input-group-text btn-show-pass" onClick={() => setShowPw(s => !s)}>
                  <i className={`bi bi-eye${showPw ? '-slash' : ''}`}></i>
                </button>
              </div>
            </div>
            <div className="mb-4">
              <label className="form-label">Confirm New Password</label>
              <input type={showPw ? 'text' : 'password'} name="confirm_password" className="form-control"
                placeholder="Repeat new password" value={pwForm.confirm_password} onChange={handlePw} required />
            </div>
            <button type="submit" className="btn btn-primary" disabled={pwLoading}>
              {pwLoading ? <span className="spinner-border spinner-border-sm me-2" /> : null}
              Update Password
            </button>
          </form>
        </div>

        {/* App Info */}
        <div className="settings-card">
          <h4 className="settings-section-title">
            <i className="bi bi-info-circle me-2"></i>Application
          </h4>
          <div className="settings-info-grid">
            <div className="settings-info-item">
              <p className="si-label">Application</p>
              <p className="si-value">RetailMind AI</p>
            </div>
            <div className="settings-info-item">
              <p className="si-label">Version</p>
              <p className="si-value">1.0.0</p>
            </div>
            <div className="settings-info-item">
              <p className="si-label">ML Model</p>
              <p className="si-value">HistGradientBoosting (R² = 0.7927)</p>
            </div>
            <div className="settings-info-item">
              <p className="si-label">Backend</p>
              <p className="si-value">FastAPI + MongoDB</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
