import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

interface AuthGuardProps {
  children: React.ReactNode;
  requireTenant?: boolean;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ 
  children, 
  requireTenant = true 
}) => {
  const { isAuthenticated, currentTenantId, initializeAuth } = useAuthStore();
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

  return <>{children}</>;
}; 