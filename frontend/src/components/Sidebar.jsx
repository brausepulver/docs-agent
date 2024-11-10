import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    FileText,
    Settings,
    User,
    LogOut
} from 'lucide-react';

import { useAuth } from '../context/AuthContext';

import '../styles/Sidebar.css';

const Sidebar = () => {
    const location = useLocation();

    const { logout } = useAuth();

    const menuItems = [
        { path: '/dashboard', name: 'Dashboard', icon: LayoutDashboard },
        { path: '/documents', name: 'Documents', icon: FileText },
        { path: '/integrations', name: 'Integrations', icon: Settings }
    ];

    const isActive = (path) => location.pathname === path;

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
                        <div className="user-avatar">
                            <User size={20} />
                        </div>
                        <div className="user-info">
                            <span className="user-name">John Doe</span>
                            <span className="user-email">john@example.com</span>
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
