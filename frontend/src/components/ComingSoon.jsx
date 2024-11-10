// frontend/src/components/ComingSoon.jsx

import React from 'react';
import { Loader2, AlertCircle, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

import '../styles/ComingSoon.css';

const ComingSoon = () => {
    return (
        <div className="coming-soon-page">
            <div className="coming-soon-container">
                <div className="coming-soon-content">
                    <div className="coming-soon-header">
                        <div className="status-badge">
                            <Loader2 className="animate-spin" size={16} />
                            <span>In Development</span>
                        </div>
                        <h1 className="coming-soon-title">Dashboard Coming Soon</h1>
                        <p className="coming-soon-subtitle">
                            We're working hard to bring you a powerful dashboard experience.
                            In the meantime, check out our existing features.
                        </p>
                    </div>

                    <div className="feature-preview">
                        <div className="feature-grid">
                            <div className="feature-card">
                                <div className="card-content">
                                    <h3>Documents</h3>
                                    <p>Manage your connected Google Docs and view your document history.</p>
                                    <Link to="/documents" className="feature-link">
                                        <span>View Documents</span>
                                        <ExternalLink size={16} />
                                    </Link>
                                </div>
                            </div>

                            <div className="feature-card">
                                <div className="card-content">
                                    <h3>Integrations</h3>
                                    <p>Connect your favorite tools and enhance your workflow.</p>
                                    <Link to="/integrations" className="feature-link">
                                        <span>Manage Integrations</span>
                                        <ExternalLink size={16} />
                                    </Link>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ComingSoon;
