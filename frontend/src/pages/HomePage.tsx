import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">籃球比賽影片標記與片段擷取工具</h2>
        </div>
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
