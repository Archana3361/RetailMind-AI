import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

const MainLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className={`app-layout ${collapsed ? 'sidebar-is-collapsed' : ''}`}>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="sidebar-overlay d-lg-none" onClick={() => setMobileOpen(false)} />
      )}

      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(c => !c)}
      />

      <div className="main-area">
        <Topbar
          sidebarCollapsed={collapsed}
          onToggleSidebar={() => setMobileOpen(o => !o)}
        />
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
