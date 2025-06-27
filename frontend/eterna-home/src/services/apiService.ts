import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { ApiResponse } from '../types/api';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: '/api/v1',
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

        const activeHouseId = localStorage.getItem('eterna_home_active_house_id');
        if (activeHouseId) {
          config.headers['X-House-ID'] = activeHouseId;
          
          if (config.method === 'get' && config.params) {
            config.params.house_id = activeHouseId;
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
          if (error.response?.data?.detail?.includes('casa')) {
            console.warn('Accesso negato alla casa selezionata:', error.response.data.detail);
            
            localStorage.removeItem('eterna_home_active_house_id');
            
            this.showHouseAccessError(error.response.data.detail);
          } else {
            localStorage.removeItem('eterna-home-auth');
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  private showHouseAccessError(message: string) {
    const notification = document.createElement('div');
    notification.className = `
      fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50
      flex items-center space-x-2
    `;
    notification.innerHTML = `
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
      </svg>
      <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 5000);
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

  // Upload file con house_id automatico
  async uploadFile<T>(url: string, file: File, additionalData?: any): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);
    
    const activeHouseId = localStorage.getItem('eterna_home_active_house_id');
    if (activeHouseId) {
      formData.append('house_id', activeHouseId);
    }
    
    if (additionalData) {
      Object.keys(additionalData).forEach(key => {
        formData.append(key, additionalData[key]);
      });
    }

    const response = await this.api.post<ApiResponse<T>>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
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

  // Get user houses summary
  async getUserHouses() {
    return this.get('/user-house/my-houses/summary');
  }

  // Get documents for current house
  async getDocuments(params?: any) {
    return this.get('/documents', params);
  }

  // Get BIM models for current house
  async getBimModels(params?: any) {
    return this.get('/bim', params);
  }

  // Get nodes for current house
  async getNodes(params?: any) {
    return this.get('/nodes', params);
  }
}

export const apiService = new ApiService(); 