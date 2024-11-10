import React, { useState } from 'react';
import { Github, Check, ChevronLeft, ExternalLink, Star } from 'lucide-react';
import { Link } from 'react-router-dom';
import '../styles/ManageGithub.css';

const ManageGithub = () => {
    const [repositories, setRepositories] = useState([
        {
            id: 1,
            name: 'awesome-project',
            description: 'A really awesome project with lots of documentation',
            isPrivate: false,
            enabled: true,
            stars: 128,
            url: 'https://github.com/username/awesome-project'
        },
        {
            id: 2,
            name: 'documentation-repo',
            description: 'Technical documentation and guides for the team',
            isPrivate: true,
            enabled: false,
            stars: 45,
            url: 'https://github.com/username/documentation-repo'
        },
        {
            id: 3,
            name: 'blog-posts',
            description: 'Collection of technical blog posts and articles',
            isPrivate: false,
            enabled: true,
            stars: 89,
            url: 'https://github.com/username/blog-posts'
        }
    ]);

    const [loading, setLoading] = useState(false);

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
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        setLoading(false);
    };

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
                                    {repo.isPrivate && (
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
                                        href={repo.url}
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
