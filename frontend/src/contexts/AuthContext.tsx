import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import api, { setAccessToken } from '../services/api';

interface AuthUser {
  id: number;
  username: string;
  display_name: string;
  role: 'admin' | 'user';
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // 初始化時嘗試使用 refresh token 取得 access token
  useEffect(() => {
    api.post('/auth/refresh', {})
      .then((res) => {
        const newToken = res.data.access_token;
        setToken(newToken);
        setAccessToken(newToken);
        // 取得使用者資訊
        return api.get('/auth/me');
      })
      .then((res) => setUser(res.data))
      .catch(() => {
        // refresh 失敗或無 cookie，視為未登入
        setToken(null);
        setAccessToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    const res = await api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    const { access_token, user: userData } = res.data;
    setToken(access_token);
    setAccessToken(access_token);
    setUser(userData);
  };

  const logout = () => {
    setToken(null);
    setAccessToken(null);
    setUser(null);
    // 呼叫後端登出以清除 refresh token cookie
    api.post('/auth/logout').catch(() => {
      // 忽略錯誤
    });
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, isAdmin: user?.role === 'admin' }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
