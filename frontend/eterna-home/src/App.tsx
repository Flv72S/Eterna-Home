import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { HouseProvider } from './context/HouseContext';
import { AuthGuard } from './components/AuthGuard';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';

function App() {
  const { isAuthenticated } = useAuthStore();

  return (
    <Router>
      <HouseProvider>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            {/* Route pubbliche */}
            <Route 
              path="/login" 
              element={
                isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
              } 
            />
            
            {/* Route protette */}
            <Route 
              path="/dashboard" 
              element={
                <AuthGuard>
                  <DashboardPage />
                </AuthGuard>
              } 
            />
            
            {/* Redirect di default */}
            <Route 
              path="/" 
              element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} 
            />
            
            {/* Catch all - redirect a dashboard se autenticato, altrimenti a login */}
            <Route 
              path="*" 
              element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} 
            />
          </Routes>
        </div>
      </HouseProvider>
    </Router>
  );
}

export default App; 