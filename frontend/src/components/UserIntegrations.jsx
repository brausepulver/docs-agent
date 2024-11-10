import { FileCheck, FileX, Loader2 } from 'lucide-react';
import '../styles/UserIntegrations.css';
import { useAuth0 } from '@auth0/auth0-react';
import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

const UserIntegrations = () => {
    const { createAuthenticatedAxios } = useAuth();
    const { getAccessTokenSilently } = useAuth0();
    const [accessToken, setAccessToken] = useState('');
    const [isLoading, setIsLoading] = useState(true);

    const checkStatus = useCallback(async (name) => {
        try {
            const axios = await createAuthenticatedAxios();
            const response = await axios.get(`/auth/${name}/status`);
            const { connected } = response.data;
            return connected;
        } catch (error) {
            console.error(`Failed to check ${name} status:`, error);
            return false;
        }
    }, [getAccessTokenSilently]);

    const [integrations, setIntegrations] = useState([
        {
            id: 'google-docs',
            name: 'Google Docs',
            description: 'Connect your Google Docs account to enable smart document collaboration.',
            icon: '/google-docs-logo.png',
            connected: true,
            disabled: true
        },
        {
            id: 'github',
            name: 'GitHub',
            description: 'Sync your GitHub repositories to manage code and documents effortlessly.',
            icon: '/github-logo.png',
            connected: false,
            href: `${import.meta.env.VITE_API_URL}/auth/github`
        },
        {
            id: 'notion',
            name: 'Notion',
            description: 'Link your Notion workspace for seamless knowledge integration.',
            icon: '/notion-logo.png',
            connected: false,
            disabled: true,
            comingSoon: true
        }
    ]);

    useEffect(() => {
        const integrationsToCheck = integrations.filter(integration => ['github'].includes(integration.id));

        Promise.all(
            integrationsToCheck.map(async integration => {
                const connected = await checkStatus(integration.id);
                return { id: integration.id, connected };
            })
        ).then(statuses => {
            setIntegrations(prev => prev.map(integration => ({
                ...integration,
                connected: statuses.find(s => s.id === integration.id)?.connected || integration.connected
            })));
            setIsLoading(false);
        });
    }, [checkStatus]);

    useEffect(() => {
        const fetchAccessToken = async () => {
            const token = await getAccessTokenSilently();
            setAccessToken(token);
        };
        fetchAccessToken();
    }, [getAccessTokenSilently]);

    return (
        <div className="user-page">
            <div className="user-container">
                <div className="user-header">
                    <h1 className="user-title">Integrations</h1>
                    <p className="user-subtitle">
                        Connect your favorite tools to enhance your writing workflow
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
                            <div className="integration-bottom">
                                {integration.comingSoon && (
                                    <span className="coming-soon-pill">Coming Soon</span>
                                )}
                                <div className="integration-actions">
                                    {integration.disabled ? (
                                        <button
                                            className={`btn-disabled ${integration.connected ? 'btn-connected' : ''}`}
                                            disabled
                                        >
                                            {integration.connected ? 'Connected' : 'Connect'}
                                        </button>
                                    ) : (
                                        <a
                                            href={!integration.connected ? `${integration.href}?state=${accessToken}` : '#'}
                                            className={`${integration.connected ? 'btn-disconnect' : 'btn-connect'} inline-block text-center no-underline`}
                                        >
                                            {isLoading && integration.id === 'github' ? (
                                                <div className="loading-container-integration">
                                                    <span>Loading...</span>
                                                </div>
                                            ) : (
                                                integration.connected ? 'Disconnect' : 'Connect'
                                            )}
                                        </a>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default UserIntegrations;
