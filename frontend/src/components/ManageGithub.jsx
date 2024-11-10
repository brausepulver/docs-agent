import React, { useState, useEffect } from 'react';
import { Github, Check, ChevronLeft, ExternalLink, Star } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/ManageGithub.css';
import { useAuth } from '../context/AuthContext';

const ManageGithub = () => {
    const [repositories, setRepositories] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadingRepos, setLoadingRepos] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();
    const { createAuthenticatedAxios } = useAuth();

    useEffect(() => {
        const fetchRepositories = async () => {
            setLoadingRepos(true);
            try {
                const axiosInstance = await createAuthenticatedAxios();
                const response = await axiosInstance.get('/api/github/repositories');
                const repos = response.data;
                const formattedRepos = repos.map(repo => ({
                    id: repo.id,
                    name: repo.name,
                    description: repo.description || '',
                    private: repo.private,
                    enabled: repo.enabled,
                    stars: repo.stars,
                    html_url: repo.html_url
                }));
                setRepositories(formattedRepos);
            } catch (err) {
                console.error(err);
                if (err.response && err.response.status === 400 && err.response.data.detail === "GitHub not connected") {
                    navigate('/integrations');
                } else {
                    setError('Failed to load repositories.');
                }
            } finally {
                setLoadingRepos(false);
            }
        };

        fetchRepositories();
    }, [createAuthenticatedAxios, navigate]);

    const toggleRepository = (repoId) => {
        setRepositories(repos =>
            repos.map(repo =>
                repo.id === repoId
                    ? { ...repo, enabled: !repo.enabled }
                    : repo
            )
        );
    };

    const saveChanges = async () => {
        setLoading(true);
        try {
            const selectedRepos = repositories.filter(repo => repo.enabled);
            const axiosInstance = await createAuthenticatedAxios();
            await axiosInstance.post('/api/github/save-repositories', { repositories: selectedRepos });
            // You can show a success message or navigate away
        } catch (error) {
            console.error(error);
            // Handle error (e.g., show an error message)
        } finally {
            setLoading(false);
        }
    };

    if (loadingRepos) {
        return <div>Loading repositories...</div>;
    }

    if (error) {
        return <div>Error: {error}</div>;
    }

    return (
        <div className="user-page">
            <div className="user-container">
                <div className="user-header">
                    <Link to="/integrations" className="back-button">
                        <ChevronLeft size={20} />
                        <span>Back to Integrations</span>
                    </Link>
                    <div className="github-header">
                        <div className="github-icon">
                            <Github size={24} />
                        </div>
                        <h1 className="user-title">GitHub Repositories</h1>
                    </div>
                    <p className="user-subtitle">
                        Select which repositories you want to index for documentation and knowledge retrieval.
                    </p>
                </div>

                <div className="repository-grid">
                    {repositories.map((repo) => (
                        <div key={repo.id} className="repository-card">
                            <div className="repository-header">
                                <div className="repository-header-content">
                                    <h3 className="repository-name">{repo.name}</h3>
                                    {repo.private && (
                                        <span className="private-badge">
                                            Private
                                        </span>
                                    )}
                                </div>
                                <button
                                    onClick={() => toggleRepository(repo.id)}
                                    className={`toggle-button ${repo.enabled ? 'enabled' : 'disabled'}`}
                                >
                                    <Check
                                        size={20}
                                        className={`check-icon ${repo.enabled ? 'visible' : ''}`}
                                    />
                                </button>
                            </div>

                            <div className="repository-content">
                                <p className="repository-description">{repo.description}</p>
                                <div className="repository-footer">
                                    <a
                                        href={repo.html_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="repository-link"
                                    >
                                        <span>View Repository</span>
                                        <ExternalLink size={16} />
                                    </a>
                                    <span className="repository-stars">
                                        <Star size={20}/> {repo.stars}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="save-container">
                    <button
                        onClick={saveChanges}
                        disabled={loading}
                        className="save-button"
                    >
                        {loading ? 'Saving changes...' : 'Save changes'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ManageGithub;
