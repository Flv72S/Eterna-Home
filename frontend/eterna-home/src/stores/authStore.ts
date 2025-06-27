import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthState, LoginCredentials } from '../types/auth';
import { authService } from '../services/authService';

interface AuthStore extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  setCurrentTenant: (tenantId: string) => void;
  clearError: () => void;
  initializeAuth: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // Initial state
      token: null,
      user: null,
      isAuthenticated: false,
      currentTenantId: null,
      availableTenants: [],
      error: null,
      isLoading: false,

      // Actions
      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authService.login(credentials);
          set({
            token: response.access_token,
            user: response.user,
            isAuthenticated: true,
            currentTenantId: response.user.tenant_id,
            availableTenants: [response.user.tenant_id],
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Errore durante il login',
          });
          throw error;
        }
      },

      logout: () => {
        authService.logout();
        set({
          token: null,
          user: null,
          isAuthenticated: false,
          currentTenantId: null,
          availableTenants: [],
          error: null,
          isLoading: false,
        });
      },

      setCurrentTenant: (tenantId: string) => {
        set({ currentTenantId: tenantId });
      },

      clearError: () => {
        set({ error: null });
      },

      initializeAuth: () => {
        const token = localStorage.getItem('eterna-home-auth');
        if (token) {
          try {
            const authData = JSON.parse(token);
            if (authData.state?.token && authData.state?.user) {
              set({
                token: authData.state.token,
                user: authData.state.user,
                isAuthenticated: true,
                currentTenantId: authData.state.user.tenant_id,
                availableTenants: [authData.state.user.tenant_id],
              });
            }
          } catch (error) {
            console.error('Error parsing auth data:', error);
            localStorage.removeItem('eterna-home-auth');
          }
        }
      },
    }),
    {
      name: 'eterna-home-auth',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        currentTenantId: state.currentTenantId,
        availableTenants: state.availableTenants,
      }),
    }
  )
); 