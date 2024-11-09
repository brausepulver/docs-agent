import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import UserIntegrations from './components/UserIntegrations';
import DashboardLayout from './components/DashboardLayout';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route element={<DashboardLayout />}>
                    <Route path="/integrations" element={<UserIntegrations />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
