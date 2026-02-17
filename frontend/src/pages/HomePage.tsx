import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function HomePage() {
  const { user, isAdmin, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">ShotCut</h1>
            <p className="mt-1 text-gray-500">籃球比賽影片標記與片段擷取工具</p>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-600">{user?.display_name}</span>
            {isAdmin && <Link to="/users" className="text-blue-600 font-medium hover:text-blue-800">使用者管理</Link>}
            <button onClick={logout} className="text-red-600 hover:text-red-800">登出</button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Link to="/videos" className="rounded-lg bg-white p-6 shadow hover:shadow-md transition-shadow">
            <h2 className="text-xl font-semibold">影片管理</h2>
            <p className="mt-2 text-gray-600">上傳或下載比賽影片</p>
          </Link>
          <Link to="/clips" className="rounded-lg bg-white p-6 shadow hover:shadow-md transition-shadow">
            <h2 className="text-xl font-semibold">片段管理</h2>
            <p className="mt-2 text-gray-600">瀏覽與管理影片片段</p>
          </Link>
          <Link to="/highlights" className="rounded-lg bg-white p-6 shadow hover:shadow-md transition-shadow">
            <h2 className="text-xl font-semibold">精華剪輯</h2>
            <p className="mt-2 text-gray-600">產出與分享個人精華</p>
          </Link>
        </div>
      </main>
    </div>
  );
}
