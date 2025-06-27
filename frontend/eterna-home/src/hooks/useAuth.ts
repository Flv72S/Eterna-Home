import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { LoginCredentials } from '../types/auth';

export const useAuth = () => {
  const navigate = useNavigate();
  const authStore = useAuthStore();

  // Initialize auth on mount
  useEffect(() => {
    authStore.initializeAuth();
  }, [authStore]);

  const login = async (credentials: LoginCredentials) => {
    try {
      await authStore.login(credentials);
      
      // Check if user has multiple tenants
      if (authStore.availableTenants.length > 1) {
        navigate('/select-tenant');
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = () => {
    authStore.logout();
    navigate('/login');
  };

  const isAuthenticated = authStore.isAuthenticated;
  const currentUser = authStore.user;
  const currentTenantId = authStore.currentTenantId;
  const isLoading = authStore.isLoading;
  const error = authStore.error;

  return {
    login,
    logout,
    isAuthenticated,
    currentUser,
    currentTenantId,
    isLoading,
    error,
    clearError: authStore.clearError,
  };
}; 