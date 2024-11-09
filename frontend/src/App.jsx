import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import UserIntegrations from './components/UserIntegrations.jsx';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/integrations" element={<UserIntegrations />} />
      </Routes>
    </Router>
  );
}

export default App;
