import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="nav-bar">
      <Link to="/dashboard" className="nav-logo">
        <div className="nav-logo-accent"></div>
        <span style={{ fontFamily: 'Syne', fontWeight: 800 }}>
          <span style={{ color: 'var(--text-primary)' }}>ATS</span>
          <span style={{ color: 'var(--accent)' }}>Pro</span>
        </span>
      </Link>
      <div className="nav-links">
        <Link 
          to="/history" 
          className={`nav-link ${location.pathname === '/history' ? 'active' : ''}`}
        >
          History
        </Link>
        <Link 
          to="/dashboard" 
          className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
        >
          Dashboard
        </Link>
        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      </div>
    </div>
  );
}

export default Navbar;
