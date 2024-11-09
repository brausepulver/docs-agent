// frontend/src/components/IntegrationSection.jsx
import React from 'react';
import '../styles/IntegrationSection.css';

const IntegrationSection = () => {
    const integrations = [
        {
            name: 'Google Docs',
            description: 'Write and collaborate smarter',
            logo: '/google-docs-logo.png'
        },
        {
            name: 'GitHub',
            description: 'Manage documentation effortlessly',
            logo: '/github-logo.png'
        },
        {
            name: 'Notion',
            description: 'Connect your workspace',
            logo: '/notion-logo.png'
        }
    ];

    return (
        <section className="integration-section">
            <div className="integration-container">
                <div className="integration-header">
                    <h3 className="integration-title">
                        Seamless integration with tools you love
                    </h3>
                    <p className="integration-subtitle">
                        Connect your favorite tools and streamline your documentation process
                    </p>
                </div>

                <div className="integration-grid">
                    {integrations.map((integration) => (
                        <div
                            key={integration.name}
                            className="integration-card"
                        >
                            <div className="integration-icon">
                                <img
                                    src={integration.logo}
                                    alt={integration.name}
                                    className="integration-logo"
                                    onError={(e) => {
                                        e.target.style.backgroundColor = '#f5f5f5';
                                        e.target.style.height = '32px';
                                    }}
                                />
                            </div>
                            <h4 className="integration-card-title">{integration.name}</h4>
                            <p className="integration-card-description">{integration.description}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default IntegrationSection;