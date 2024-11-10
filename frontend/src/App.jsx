import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Auth0Provider } from '@auth0/auth0-react';
import { AuthProvider } from './context/AuthContext';
import LandingPage from './components/LandingPage';
import UserIntegrations from './components/UserIntegrations';
import DashboardLayout from './components/DashboardLayout';
import DocumentList from './components/DocumentList';
import AuthPage from './components/AuthPage';
import ComingSoon from './components/ComingSoon';
import ProtectedRoute from './components/ProtectedRoute';

const auth0Config = {
    domain: import.meta.env.VITE_AUTH0_DOMAIN,
    clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
    authorizationParams: {
        redirect_uri: window.location.origin,
        audience: import.meta.env.VITE_AUTH0_AUDIENCE,
        scope: "openid profile email"
    },
    // For better dev experience
    cacheLocation: "localstorage",
    useRefreshTokens: true
};

function App() {
    return (
        <Auth0Provider {...auth0Config}>
            <AuthProvider>
                <Router>
                    <Routes>
                        <Route path="/" element={<LandingPage />} />
                        <Route path="/register" element={<AuthPage />} />
                        <Route path="/login" element={<AuthPage />} />
                        <Route element={
                            <ProtectedRoute>
                                <DashboardLayout />
                            </ProtectedRoute>
                        }>
                            <Route path="/dashboard" element={<ComingSoon />} />
                            <Route path="/integrations" element={<UserIntegrations />} />
                            <Route path="/documents" element={<DocumentList />} />
                        </Route>
                    </Routes>
                </Router>
            </AuthProvider>
        </Auth0Provider>
    );
}

export default App;
