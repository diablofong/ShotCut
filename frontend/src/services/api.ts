import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // 允許攜帶 Cookie（refresh_token）
});

// Token 儲存在內存中，由 AuthContext 管理
let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

// 請求攔截器：附加 JWT access token
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 防止 refresh 無限迴圈的標記
let isRefreshing = false;
let pendingRequests: Array<(token: string) => void> = [];

function onRefreshSuccess(newToken: string) {
  pendingRequests.forEach((cb) => cb(newToken));
  pendingRequests = [];
}

function onRefreshFailed() {
  pendingRequests = [];
  setAccessToken(null);
  window.location.href = '/login';
}

// 回應攔截器：401 時自動用 refresh token 換取新 access token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 非 401，或是 refresh / login 本身失敗，直接拒絕
    if (
      error.response?.status !== 401 ||
      originalRequest.url?.includes('/auth/refresh') ||
      originalRequest.url?.includes('/auth/login') ||
      originalRequest._retry
    ) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // 等待 refresh 完成後重試
      return new Promise((resolve) => {
        pendingRequests.push((token: string) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          resolve(api(originalRequest));
        });
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const { data } = await axios.post('/api/auth/refresh', {}, { withCredentials: true });
      const newToken: string = data.access_token;
      setAccessToken(newToken);
      api.defaults.headers.common.Authorization = `Bearer ${newToken}`;
      onRefreshSuccess(newToken);
      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return api(originalRequest);
    } catch {
      onRefreshFailed();
      return Promise.reject(error);
    } finally {
      isRefreshing = false;
    }
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
  logout: () => api.post('/auth/logout'),
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
  upload: (file: File, onProgress?: (percent: number) => void) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/videos/upload', form, {
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
  },
  // R2 Presigned PUT 上傳流程
  getUploadUrl: (filename: string, contentType: string) =>
    api.get('/videos/upload-url', { params: { filename, content_type: contentType } }),
  uploadToR2: async (
    presignedUrl: string,
    file: File,
    onProgress?: (percent: number) => void,
  ): Promise<void> => {
    await new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('PUT', presignedUrl);
      xhr.setRequestHeader('Content-Type', file.type || 'video/mp4');
      if (onProgress) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            onProgress(Math.round((e.loaded * 100) / e.total));
          }
        };
      }
      xhr.onload = () => (xhr.status >= 200 && xhr.status < 300 ? resolve() : reject(new Error(`R2 upload failed: ${xhr.status}`)));
      xhr.onerror = () => reject(new Error('R2 upload network error'));
      xhr.send(file);
    });
  },
  confirmUpload: (id: number) => api.post(`/videos/${id}/confirm`),
  streamUrl: (id: number) => api.get<{ url: string }>(`/videos/${id}/stream-url`),
  update: (id: number, data: { title: string }) => api.put(`/videos/${id}`, data),
  delete: (id: number) => api.delete(`/videos/${id}`),
  batchDelete: (ids: number[]) => api.post('/videos/batch/delete', { ids }),
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
  batchDelete: (ids: number[]) => api.post('/clips/batch/delete', { ids }),
};

// 精華剪輯
export const highlightApi = {
  list: () => api.get('/highlights'),
  generate: (data: Record<string, unknown>) => api.post('/highlights/generate', data),
  delete: (id: number) => api.delete(`/highlights/${id}`),
  batchDelete: (ids: number[]) => api.post('/highlights/batch/delete', { ids }),
};

// 分享
export const shareApi = {
  create: (highlightId: number, expiration: string = '7d') =>
    api.post('/shares', { highlight_id: highlightId, expiration }),
  get: (token: string) => api.get(`/shares/${token}`),
  delete: (id: number) => api.delete(`/shares/${id}`),
};

/**
 * 建立影片下載進度的 WebSocket 連線。
 * 連線失敗時回傳 null，由呼叫端降級至 polling。
 */
export function createProgressWebSocket(
  videoId: number,
  onMessage: (data: Record<string, unknown>) => void,
  onClose?: () => void,
): WebSocket | null {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const token = getAccessToken();
  const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
  const wsUrl = `${protocol}//${window.location.host}/api/videos/${videoId}/ws/progress${tokenParam}`;
  try {
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as Record<string, unknown>;
        onMessage(data);
      } catch {
        // ignore parse errors
      }
    };
    ws.onclose = () => onClose?.();
    ws.onerror = () => {
      ws.close();
      onClose?.();
    };
    return ws;
  } catch {
    return null;
  }
}

export default api;
