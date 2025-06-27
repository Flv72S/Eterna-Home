export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
  message?: string;
}

export interface ApiConfig {
  baseURL: string;
  timeout: number;
  headers: Record<string, string>;
} 