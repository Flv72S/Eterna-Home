import axios, { AxiosInstance } from 'axios';
import { LoginCredentials, LoginResponse, User } from '../types/auth';
import { ApiResponse } from '../types/api';

class AuthService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: '/api/v1',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('eterna-home-auth');
        if (token) {
          const authData = JSON.parse(token);
          if (authData.state?.token) {
            config.headers.Authorization = `Bearer ${authData.state.token}`;
          }
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401 || error.response?.status === 403) {
          // Clear auth data and redirect to login
          localStorage.removeItem('eterna-home-auth');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    const response = await this.api.post<LoginResponse>('/auth/token', formData);
    return response.data;
  }

  async refreshToken(): Promise<LoginResponse> {
    const response = await this.api.post<LoginResponse>('/auth/refresh');
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get<ApiResponse<User>>('/auth/me');
    return response.data.data;
  }

  async logout(): Promise<void> {
    try {
      await this.api.post('/auth/logout');
    } catch (error) {
      console.error('Error during logout:', error);
    }
  }

  setAuthToken(token: string): void {
    this.api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearAuthToken(): void {
    delete this.api.defaults.headers.common['Authorization'];
  }
}

export const authService = new AuthService(); 