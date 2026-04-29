import axios from 'axios';
import { message } from 'antd';

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — add auth token if available
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — unified error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    const response = error.response;

    // 统一错误处理：非200-299状态码显示错误提示
    if (response) {
      // 提取错误信息，优先使用message，否则使用"接口报错"
      const errorMessage = response.data?.message || 'HTTP Error';
      message.error(errorMessage);
    }

    // 开发环境下输出详细错误信息
    if (import.meta.env.DEV) {
      console.error('[API]', error.response?.status, error.config?.url, error.message);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
