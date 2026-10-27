import { useAuth } from '../context/AuthContext';

const Topbar = ({ sidebarCollapsed, onToggleSidebar }) => {
  const { user } = useAuth();
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button className="topbar-menu-btn d-lg-none" onClick={onToggleSidebar}>
          <i className="bi bi-list"></i>
        </button>
        <p className="topbar-date">{dateStr}</p>
      </div>
      <div className="topbar-right">
        <div className="topbar-user">
          <div className="topbar-avatar">
            {user?.full_name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="topbar-user-info d-none d-md-block">
            <p className="topbar-user-name">{user?.full_name}</p>
            <p className="topbar-user-shop">{user?.shop_name}</p>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
