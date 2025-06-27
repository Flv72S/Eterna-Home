export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface JWTToken {
  sub: string; // user_id
  tenant_id: string;
  role: string;
  exp: number;
  iat: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  currentTenantId: string | null;
  availableTenants: string[];
  isLoading: boolean;
  error: string | null;
}

export interface Tenant {
  id: string;
  name: string;
  description?: string;
}

export interface Role {
  id: string;
  name: string;
  description?: string;
  permissions: string[];
} 