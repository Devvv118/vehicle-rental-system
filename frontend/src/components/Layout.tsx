import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { pingServer, resetDemoData } from '../services/api';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [serverWaking, setServerWaking] = useState(false);
  const location = useLocation();

  // Render's free tier sleeps when idle: if the server does not answer quickly, ask the user to wait,
  // keep retrying, and reload once it is up so every page fetches fresh data.
  useEffect(() => {
    let cancelled = false;
    let wasSlow = false;
    const slowTimer = window.setTimeout(() => {
      wasSlow = true;
      if (!cancelled) setServerWaking(true);
    }, 2500);

    const check = async () => {
      while (!cancelled) {
        if (await pingServer()) break;
        wasSlow = true;
        if (!cancelled) setServerWaking(true);
        await new Promise((r) => setTimeout(r, 3000));
      }
      window.clearTimeout(slowTimer);
      if (cancelled) return;
      if (wasSlow) window.location.reload();
      else setServerWaking(false);
    };
    check();

    return () => {
      cancelled = true;
      window.clearTimeout(slowTimer);
    };
  }, []);

  const handleReset = async () => {
    if (!window.confirm('Reset the demo? This deletes ALL current data and restores the original example data.')) return;
    setResetting(true);
    try {
      await resetDemoData();
      window.location.assign('/dashboard'); // full reload so no stale data stays on screen
    } catch (e) {
      setResetting(false);
      window.alert('Could not reset the demo: ' + (e instanceof Error ? e.message : String(e)));
    }
  };

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const menuItems = [
    {
      path: '/dashboard',
      name: 'Dashboard',
      icon: '📊'
    },
    {
      path: '/customers',
      name: 'Customers',
      icon: '👥'
    },
    {
      path: '/vehicles',
      name: 'Vehicles',
      icon: '🚗'
    },
    {
      path: '/rentals',
      name: 'Rentals',
      icon: '📋'
    },
    {
      path: '/reservations',
      name: 'Reservations',
      icon: '📅'
    },
    {
      path: '/employees',
      name: 'Employees',
      icon: '👷'
    },
    {
      path: '/locations',
      name: 'Locations',
      icon: '📍'
    },
    {
      path: '/maintenance',
      name: 'Maintenance',
      icon: '🔧'
    },
    {
      path: '/incidents',
      name: 'Incidents',
      icon: '⚠️'
    },
    {
      path: '/reports',
      name: 'Reports',
      icon: '📈'
    }
  ];

  return (
    <div className="layout">
      <header className="header">
        <div className="header-left">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            ☰
          </button>
          <h1 className="app-title">Car Rental Management</h1>
        </div>
        <div className="header-right">
          <button className="reset-demo-btn" onClick={handleReset} disabled={resetting}>
            {resetting ? 'Resetting…' : '↺ Reset demo data'}
          </button>
          <div className="user-info">
            <span>Admin User</span>
            <div className="user-avatar">👤</div>
          </div>
        </div>
      </header>

      {serverWaking && (
        <div className="server-waking-banner" role="status">
          The server is starting up (free hosting). Please wait, this can take up to a minute. The page will refresh
          automatically.
        </div>
      )}

      <div className="main-container">
        <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
          <nav className="nav">
            <ul className="nav-list">
              {menuItems.map((item) => (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`nav-link ${isActive(item.path) ? 'active' : ''}`}
                  >
                    <span className="nav-icon">{item.icon}</span>
                    {sidebarOpen && <span className="nav-text">{item.name}</span>}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </aside>

        <main className="content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;