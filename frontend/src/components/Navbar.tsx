import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const NAV_LINKS = [
  { to: '/videos', label: '影片管理' },
  { to: '/clips', label: '片段管理' },
  { to: '/highlights', label: '精華剪輯' },
];

export default function Navbar() {
  const { user, isAdmin, logout } = useAuth();
  const location = useLocation();

  return (
    <header className="bg-white shadow">
      <div className="mx-auto max-w-screen-2xl px-4 py-3 flex items-center justify-between">
        {/* 左側：Logo + 導航 */}
        <div className="flex items-center gap-6">
          <Link to="/" className="text-xl font-bold text-gray-900 hover:text-blue-600">
            ShotCut
          </Link>
          <nav className="hidden sm:flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const isActive = location.pathname.startsWith(link.to);
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
            {isAdmin && (
              <Link
                to="/users"
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  location.pathname === '/users'
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                使用者管理
              </Link>
            )}
          </nav>
        </div>

        {/* 右側：使用者 + 登出 */}
        <div className="flex items-center gap-3 text-sm">
          <span className="text-gray-600">{user?.display_name}</span>
          <button
            onClick={logout}
            className="rounded-md px-3 py-1.5 text-red-600 hover:bg-red-50 hover:text-red-800 font-medium transition-colors"
          >
            登出
          </button>
        </div>
      </div>
    </header>
  );
}
