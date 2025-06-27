import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useActiveHouse } from '../hooks/useActiveHouse';

interface AuthGuardProps {
  children: React.ReactNode;
  requireTenant?: boolean;
  requireHouse?: boolean;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ 
  children, 
  requireTenant = true,
  requireHouse = false
}) => {
  const { isAuthenticated, currentTenantId, initializeAuth } = useAuthStore();
  const { hasActiveHouse, availableHouses, isLoading } = useActiveHouse();
  const location = useLocation();

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  // If not authenticated, redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If tenant is required but not selected, redirect to tenant selection
  if (requireTenant && !currentTenantId) {
    return <Navigate to="/select-tenant" state={{ from: location }} replace />;
  }

  // If house is required but not selected, show house selection message
  if (requireHouse && !isLoading && !hasActiveHouse) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow p-6">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100 mb-4">
              <svg className="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Casa richiesta
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              {availableHouses.length === 0 
                ? 'Non hai case disponibili. Contatta l\'amministratore.'
                : 'Seleziona una casa per accedere a questa pagina.'
              }
            </p>
            <button
              onClick={() => window.history.back()}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Torna indietro
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}; 