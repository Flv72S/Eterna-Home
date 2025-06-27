import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { jwtDecode } from 'jwt-decode';
import { AuthState, User, JWTToken, LoginCredentials } from '../types/auth';
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
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      currentTenantId: null,
      availableTenants: [],
      isLoading: false,
      error: null,

      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await authService.login(credentials);
          const token = response.access_token;
          const decodedToken = jwtDecode<JWTToken>(token);
          
          set({
            token,
            user: response.user,
            isAuthenticated: true,
            currentTenantId: decodedToken.tenant_id,
            availableTenants: [decodedToken.tenant_id],
            isLoading: false,
            error: null,
          });
          
          authService.setAuthToken(token);
          
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.response?.data?.detail || 'Errore durante il login',
            isAuthenticated: false,
          });
          throw error;
        }
      },

      logout: () => {
        authService.clearAuthToken();
        set({
          token: null,
          user: null,
          isAuthenticated: false,
          currentTenantId: null,
          availableTenants: [],
          isLoading: false,
          error: null,
        });
      },

      setCurrentTenant: (tenantId: string) => {
        set({ currentTenantId: tenantId });
      },

      clearError: () => {
        set({ error: null });
      },

      initializeAuth: () => {
        const { token } = get();
        
        if (token) {
          try {
            const decodedToken = jwtDecode<JWTToken>(token);
            const currentTime = Date.now() / 1000;
            
            if (decodedToken.exp < currentTime) {
              get().logout();
              return;
            }
            
            authService.setAuthToken(token);
            
            set({
              isAuthenticated: true,
              currentTenantId: decodedToken.tenant_id,
              availableTenants: [decodedToken.tenant_id],
            });
            
          } catch (error) {
            console.error('Error decoding token:', error);
            get().logout();
          }
        }
      },
    }),
    {
      name: 'eterna-home-auth',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        currentTenantId: state.currentTenantId,
        availableTenants: state.availableTenants,
      }),
    }
  )
); 