import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { ApiResponse, ApiError } from '../types/api';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('eterna-home-auth');
        if (token) {
          try {
            const authData = JSON.parse(token);
            if (authData.state?.token) {
              config.headers.Authorization = `Bearer ${authData.state.token}`;
            }
          } catch (error) {
            console.error('Error parsing auth token:', error);
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
      (response: AxiosResponse) => response,
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

  // Generic GET request
  async get<T>(url: string, params?: any): Promise<ApiResponse<T>> {
    const response = await this.api.get<ApiResponse<T>>(url, { params });
    return response.data;
  }

  // Generic POST request
  async post<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.api.post<ApiResponse<T>>(url, data);
    return response.data;
  }

  // Generic PUT request
  async put<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.api.put<ApiResponse<T>>(url, data);
    return response.data;
  }

  // Generic DELETE request
  async delete<T>(url: string): Promise<ApiResponse<T>> {
    const response = await this.api.delete<ApiResponse<T>>(url);
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.api.get('/health');
      return true;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  // Get current user info
  async getCurrentUser() {
    return this.get('/auth/me');
  }

  // Get tenant info
  async getTenantInfo(tenantId: string) {
    return this.get(`/tenants/${tenantId}`);
  }
}

export const apiService = new ApiService(); 