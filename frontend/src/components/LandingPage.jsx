import { Link } from 'react-router-dom';
import { ChevronRight, Github, LogIn, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import IntegrationSection from './IntegrationSection';
import Footer from './Footer';

import '../styles/LandingPage.css';

const LandingPage = () => {
    const { isAuthenticated, logout, user } = useAuth();

    const scrollToSection = (e, id) => {
        e.preventDefault();
        const element = document.querySelector(id);
        if (element) {
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'start',
            });
        }
    };

    const renderAuthButtons = () => {
        if (isAuthenticated) {
            return (
                <div className="nav-buttons">
                    <Link to="/dashboard" className="btn-secondary">
                        Dashboard
                    </Link>
                    <button onClick={logout} className="btn-primary">
                        <LogOut size={18} />
                        <span>Sign out</span>
                    </button>
                </div>
            );
        }

        return (
            <div className="nav-buttons">
                <Link to="/login" className="btn-secondary">
                    <LogIn size={18} />
                    <span>Sign in</span>
                </Link>
                <Link to="/register" className="btn-primary">Start for free</Link>
            </div>
        );
    };

    const renderHeroCTA = () => {
        if (isAuthenticated) {
            return (
                <div className="hero-cta">
                    <Link to="/dashboard" className="btn-primary btn-large">Go to Dashboard</Link>
                </div>
            );
        }

        return (
            <div className="hero-cta">
                <Link to="/register" className="btn-primary btn-large">Start for free</Link>
                <p className="hero-note">No credit card required. Cancel anytime.</p>
            </div>
        );
    };

    return (
        <div className="app">
            <nav className="navbar">
                <Link to="/" className="nav-logo">DocsAgent</Link>
                <div className="nav-center">
                    <div className="nav-links">
                        <a href="#features" onClick={(e) => scrollToSection(e, '#features')}>
                            Features
                        </a>
                        <a href="#integrations" onClick={(e) => scrollToSection(e, '#integrations')}>
                            Integrations
                        </a>
                    </div>
                </div>
                {renderAuthButtons()}
            </nav>

            <main className="hero">
                <Link to="#github-integration" className="new-feature-tag">
                    <span className="tag-new">New</span>
                    <span className="tag-feature">
                        <Github size={18} />
                        GitHub Integration
                    </span>
                    <ChevronRight size={18} className="tag-arrow" />
                </Link>

                <h1 className="hero-title">
                    Like having a brilliant<br />assistant in every doc
                </h1>

                <p className="hero-subtitle">
                    DocsAgent is your AI-powered document companion that integrates with Google Docs and GitHub.
                    Get smart suggestions, cross-reference your entire document repository, and collaborate smarter.
                </p>

                {renderHeroCTA()}

                <div className="hero-image">
                    <img
                        src="/hero-demo.png"
                        alt="DocsAgent Interface Demo"
                        onError={(e) => {
                            e.target.style.backgroundColor = '#f5f5f5';
                            e.target.style.height = '500px';
                        }}
                    />
                </div>

                <section id="integrations">
                    <IntegrationSection />
                </section>
            </main>
            <Footer />
        </div>
    );
};

export default LandingPage;
