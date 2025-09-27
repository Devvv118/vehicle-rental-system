import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();

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
          <div className="user-info">
            <span>Admin User</span>
            <div className="user-avatar">👤</div>
          </div>
        </div>
      </header>

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