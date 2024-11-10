import React, { useEffect, useState } from 'react';
import { FileText, ExternalLink, X, Loader2 } from 'lucide-react';
import '../styles/DocumentList.css';
import { useAuth } from '../context/AuthContext';

const DocumentList = () => {
    const { createAuthenticatedAxios, user } = useAuth();
    const [documents, setDocuments] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const [removing, setRemoving] = useState(new Set()); // Track which docs are being removed

    useEffect(() => {
        fetchDocuments();
    }, [createAuthenticatedAxios]);

    const fetchDocuments = async () => {
        try {
            setLoading(true);
            const authAxios = await createAuthenticatedAxios();
            const response = await authAxios.get('/api/documents');
            setDocuments(response.data);
        } catch (err) {
            setError("Failed to load documents.");
            console.error('Error fetching documents:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleRemove = async (docId) => {
        try {
            setRemoving(prev => new Set([...prev, docId]));
            const authAxios = await createAuthenticatedAxios();
            await authAxios.delete(`/api/documents/${docId}`);
            setDocuments(docs => docs.filter(doc => doc.id !== docId));
        } catch (err) {
            console.error('Error removing document:', err);
            // Show error in UI
            const errorMessage = err.response?.data?.detail || "Failed to remove document.";
            setError(errorMessage);
        } finally {
            setRemoving(prev => {
                const next = new Set(prev);
                next.delete(docId);
                return next;
            });
        }
    };

    if (error) return (
        <div className="document-page">
            <div className="document-container">
                <div className="document-header">
                    <h1 className="document-title">Your Documents</h1>
                    <p className="document-subtitle">
                        Manage your connected Google Docs. Remove documents you no longer want the agent to access.
                    </p>
                </div>
                <div className="error-container">
                    <p className="error-message">{error}</p>
                    <button
                        onClick={fetchDocuments}
                        className="retry-button"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        </div>
    );

    return (
        <div className="document-page">
            <div className="document-container">
                <div className="document-header">
                    <h1 className="document-title">Your Documents</h1>
                    <p className="document-subtitle">
                        Manage your connected Google Docs. Remove documents you no longer want the agent to access.
                    </p>
                </div>

                <div className="document-grid">
                    {loading ? (
                        <div className="loading-container">
                            <Loader2 className="loading-spinner" size={48} />
                            <p>Loading your documents...</p>
                        </div>
                    ) : documents.length > 0 ? (
                        documents.map((doc) => (
                            <div key={doc.id} className="document-card">
                                <button
                                    className="remove-button"
                                    onClick={() => handleRemove(doc.id)}
                                    disabled={removing.has(doc.id)}
                                >
                                    {removing.has(doc.id) ? (
                                        <Loader2 className="loading-spinner" size={16} />
                                    ) : (
                                        <X size={16} />
                                    )}
                                </button>

                                <div className="document-card-header">
                                    <div className="document-icon">
                                        <FileText size={24} />
                                    </div>
                                    <h3 className="document-name">{doc.name}</h3>
                                </div>

                                <div className="document-card-footer">
                                    <a
                                        href={`https://docs.google.com/document/d/${doc.id}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="document-link"
                                    >
                                        <span>Open Document</span>
                                        <ExternalLink size={16} />
                                    </a>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="no-documents">
                            <FileText size={48} className="empty-icon" />
                            <h3>No Documents Found</h3>
                            <p>Share a Google Doc with the agent to get started, use the same Google email ({user.email}) to share the document.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DocumentList;
