import React from 'react';
import { Link } from 'react-router-dom';
import { Github, Twitter } from 'lucide-react';

import '../styles/Footer.css';

const Footer = () => {
    return (
        <footer className="footer">
            <div className="footer-container">
                <div className="footer-main">
                    <div className="footer-brand">
                        <Link to="/" className="footer-logo">
                            DocsAgent
                        </Link>
                        <p className="footer-tagline">
                            Your AI-powered document companion
                        </p>
                    </div>
                </div>

                <div className="footer-bottom">
                    <div className="footer-legal">
                        <span>© 2024 DocsAgent. All rights reserved.</span>
                        <Link to="/privacy">Privacy Policy</Link>
                        <Link to="/terms">Terms of Service</Link>
                    </div>
                    <div className="footer-social">
                        <a href="https://github.com/docsagent" target="_blank" rel="noopener noreferrer" aria-label="GitHub">
                            <Github size={20} />
                        </a>
                        <a href="https://twitter.com/docsagent" target="_blank" rel="noopener noreferrer" aria-label="Twitter">
                            <Twitter size={20} />
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
