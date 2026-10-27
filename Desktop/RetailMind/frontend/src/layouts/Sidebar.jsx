import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const navGroups = [
  {
    items: [{ to: '/dashboard', icon: 'grid-1x2', label: 'Dashboard' }],
  },
  {
    label: 'MANAGE',
    items: [
      { to: '/products', icon: 'box-seam', label: 'Products' },
      { to: '/sales', icon: 'receipt', label: 'Sales' },
      { to: '/purchases', icon: 'truck', label: 'Purchases' },
      { to: '/inventory', icon: 'archive', label: 'Inventory' },
    ],
  },
  {
    label: 'BUSINESS',
    items: [
      { to: '/customers', icon: 'people', label: 'Customers' },
      { to: '/suppliers', icon: 'building', label: 'Suppliers' },
      { to: '/analytics', icon: 'bar-chart-line', label: 'Analytics' },
    ],
  },
  {
    label: 'AI INTELLIGENCE',
    items: [
      { to: '/demand-prediction', icon: 'cpu', label: 'Demand Prediction' },
      { to: '/stock-intelligence', icon: 'graph-up-arrow', label: 'Stock Intelligence' },
    ],
  },
  {
    items: [
      { to: '/reports', icon: 'file-earmark-text', label: 'Reports' },
      { to: '/settings', icon: 'gear', label: 'Settings' },
    ],
  },
];

const Sidebar = ({ collapsed, onToggle }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <div className="sidebar-brand">
        <div className="brand-logo">
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="7" fill="#3b82f6" fillOpacity="0.15" />
            <path d="M7 22 L13 12 L17 18 L21 10 L25 16" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
            <circle cx="25" cy="16" r="2" fill="#10b981" />
          </svg>
        </div>
        {!collapsed && (
          <div className="brand-text">
            <span className="brand-name">RetailMind</span>
            <span className="brand-tag">AI</span>
          </div>
        )}
        <button className="sidebar-toggle" onClick={onToggle}>
          <i className={`bi bi-${collapsed ? 'chevron-right' : 'chevron-left'}`}></i>
        </button>
      </div>

      <nav className="sidebar-nav">
        {navGroups.map((group, gi) => (
          <div key={gi} className="nav-group">
            {group.label && !collapsed && (
              <p className="nav-group-label">{group.label}</p>
            )}
            {group.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `nav-item ${isActive ? 'nav-item-active' : ''}`
                }
                title={collapsed ? item.label : ''}
              >
                <i className={`bi bi-${item.icon} nav-icon`}></i>
                {!collapsed && <span className="nav-label">{item.label}</span>}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        {!collapsed && user && (
          <div className="user-info">
            <div className="user-avatar">
              {user.full_name?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="user-details">
              <p className="user-name">{user.full_name}</p>
              <p className="user-shop">{user.shop_name}</p>
            </div>
          </div>
        )}
        <button className="logout-btn" onClick={handleLogout} title="Logout">
          <i className="bi bi-box-arrow-right"></i>
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
