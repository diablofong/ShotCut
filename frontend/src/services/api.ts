import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

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
  delete: (id: number) => api.delete(`/videos/${id}`),
  status: (id: number) => api.get(`/videos/${id}/status`),
};

// 音訊分析
export const analysisApi = {
  analyze: (videoId: number, params?: { sensitivity?: number; min_interval?: number }) =>
    api.post(`/videos/${videoId}/analyze`, params),
  candidates: (videoId: number) => api.get(`/videos/${videoId}/candidates`),
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
};

// 分享
export const shareApi = {
  create: (highlightId: number) => api.post('/shares', { highlight_id: highlightId }),
  get: (token: string) => api.get(`/shares/${token}`),
  delete: (id: number) => api.delete(`/shares/${id}`),
};

export default api;
