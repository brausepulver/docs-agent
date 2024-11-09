import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Loading = () => (
    <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
    }}>
    Loading...
    </div>
);

const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, isLoading } = useAuth();
    const location = useLocation();

    if (isLoading) {
        return <Loading />;
    }

    if (!isAuthenticated) {
        // Redirect to login but remember where they were trying to go
        return <Navigate to="/login" state={{ from: location.pathname }} replace />;
    }

    return children;
};

export default ProtectedRoute;
