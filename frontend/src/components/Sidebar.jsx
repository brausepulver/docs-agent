import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    FileText,
    Settings,
    LogOut
} from 'lucide-react';

import { useAuth } from '../context/AuthContext';

import '../styles/Sidebar.css';

const Sidebar = () => {
    const location = useLocation();
    const { logout, user } = useAuth();

    const menuItems = [
        { path: '/dashboard', name: 'Dashboard', icon: LayoutDashboard },
        { path: '/documents', name: 'Documents', icon: FileText },
        { path: '/integrations', name: 'Integrations', icon: Settings }
    ];

    const isActive = (path) => location.pathname === path;

    const getUserInitial = (name) => {
        return name ? name.charAt(0).toUpperCase() : '?';
    };

    return (
        <aside className="sidebar">
            <div className="sidebar-content">
                <div className="sidebar-header">
                    <Link to="/" className="sidebar-logo">
                        DocsAgent
                    </Link>
                </div>

                <nav className="sidebar-nav">
                    {menuItems.map((item) => (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={`sidebar-link ${isActive(item.path) ? 'active' : ''}`}
                        >
                            <item.icon size={20} />
                            <span>{item.name}</span>
                        </Link>
                    ))}
                </nav>

                <div className="sidebar-footer">
                    <div className="sidebar-user">
                        {user?.picture ? (
                            <img
                                src={user.picture}
                                alt={user.name}
                                className="user-avatar"
                            />
                        ) : (
                            <div className="user-avatar user-initial">
                                {getUserInitial(user?.name)}
                            </div>
                        )}
                        <div className="user-info">
                            <span className="user-name">{user?.name || 'Loading...'}</span>
                            <span className="user-email">{user?.email || ''}</span>
                        </div>
                    </div>
                    <button className="sidebar-logout" onClick={logout}>
                        <LogOut size={20} />
                        <span>Log out</span>
                    </button>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
