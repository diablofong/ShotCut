import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

// 請求攔截器：附加 JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 回應攔截器：401 自動導向登入
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config.url?.includes('/auth/login')) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);

// 認證
export const authApi = {
  login: (username: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    return api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  me: () => api.get('/auth/me'),
};

// 使用者管理
export const userApi = {
  list: () => api.get('/users'),
  create: (data: { username: string; password: string; display_name: string; role: string }) =>
    api.post('/users', data),
  update: (id: number, data: Record<string, unknown>) => api.put(`/users/${id}`, data),
  delete: (id: number) => api.delete(`/users/${id}`),
};

// 影片
export const videoApi = {
  list: () => api.get('/videos'),
  get: (id: number) => api.get(`/videos/${id}`),
  download: (url: string) => api.post('/videos/download', { url }),
  upload: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/videos/upload', form);
  },
  update: (id: number, data: { title: string }) => api.put(`/videos/${id}`, data),
  delete: (id: number) => api.delete(`/videos/${id}`),
  status: (id: number) => api.get(`/videos/${id}/status`),
};

// 標記
export const markApi = {
  list: (videoId: number) => api.get(`/videos/${videoId}/marks`),
  create: (videoId: number, data: Record<string, unknown>) =>
    api.post(`/videos/${videoId}/marks`, data),
  update: (id: number, data: Record<string, unknown>) => api.put(`/marks/${id}`, data),
  delete: (id: number) => api.delete(`/marks/${id}`),
};

// 片段
export const clipApi = {
  list: (params?: Record<string, unknown>) => api.get('/clips', { params }),
  extract: (videoId: number) => api.post(`/videos/${videoId}/clips`),
  delete: (id: number) => api.delete(`/clips/${id}`),
};

// 精華剪輯
export const highlightApi = {
  list: () => api.get('/highlights'),
  generate: (data: Record<string, unknown>) => api.post('/highlights/generate', data),
  delete: (id: number) => api.delete(`/highlights/${id}`),
};

// 分享
export const shareApi = {
  create: (highlightId: number, expiration: string = '7d') =>
    api.post('/shares', { highlight_id: highlightId, expiration }),
  get: (token: string) => api.get(`/shares/${token}`),
  delete: (id: number) => api.delete(`/shares/${id}`),
};

export default api;
