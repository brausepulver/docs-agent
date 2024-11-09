import React, { useState } from 'react';
import { Github, FileCheck, FileX } from 'lucide-react';
import '../styles/UserIntegrations.css';

const UserIntegrations = () => {
    const [integrations, setIntegrations] = useState([
        {
            id: 'google-docs',
            name: 'Google Docs',
            description: 'Connect your Google Docs account to enable smart document collaboration.',
            icon: '/google-docs-logo.png',
            connected: false
        },
        {
            id: 'github',
            name: 'GitHub',
            description: 'Sync your GitHub repositories to manage documentation effortlessly.',
            icon: '/github-logo.png',
            connected: true
        },
        {
            id: 'notion',
            name: 'Notion',
            description: 'Link your Notion workspace for seamless knowledge integration.',
            icon: '/notion-logo.png',
            connected: false
        }
    ]);

    const toggleConnection = (id) => {
        setIntegrations(integrations.map(integration => 
            integration.id === id 
                ? { ...integration, connected: !integration.connected }
                : integration
        ));
    };

    return (
        <div className="user-page">
            <div className="user-container">
                <div className="user-header">
                    <h1 className="user-title">Integrations</h1>
                    <p className="user-subtitle">
                        Connect your favorite tools to enhance your documentation workflow
                    </p>
                </div>

                <div className="integrations-grid">
                    {integrations.map((integration) => (
                        <div key={integration.id} className="integration-tile">
                            <div className="integration-header">
                                <div className="integration-info">
                                    <div className="integration-icon">
                                        <img
                                            src={integration.icon}
                                            alt={integration.name}
                                            style={{ width: '24px', height: '24px' }}
                                            onError={(e) => {
                                                e.target.style.display = 'none';
                                                e.target.parentElement.innerHTML = integration.id === 'github' 
                                                    ? '<Github size={24} />' 
                                                    : '<div style="width: 24px; height: 24px; background-color: #f5f5f5;"></div>';
                                            }}
                                        />
                                    </div>
                                    <span className="integration-name">{integration.name}</span>
                                </div>
                                <div className={`integration-status ${integration.connected ? 'status-connected' : 'status-disconnected'}`}>
                                    {integration.connected ? (
                                        <>
                                            <FileCheck size={16} />
                                            <span>Connected</span>
                                        </>
                                    ) : (
                                        <>
                                            <FileX size={16} />
                                            <span>Not connected</span>
                                        </>
                                    )}
                                </div>
                            </div>
                            <p className="integration-description">{integration.description}</p>
                            <div className="integration-actions">
                                <button
                                    className={integration.connected ? 'btn-disconnect' : 'btn-connect'}
                                    onClick={() => toggleConnection(integration.id)}
                                >
                                    {integration.connected ? 'Disconnect' : 'Connect'}
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default UserIntegrations;
