import { useState, useEffect, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { userApi } from '../services/api';

interface UserItem {
  id: number;
  username: string;
  display_name: string;
  role: string;
  is_active: boolean;
}

export default function UsersPage() {
  const { user: currentUser, logout } = useAuth();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [role, setRole] = useState('user');
  const [error, setError] = useState('');

  const loadUsers = async () => {
    const res = await userApi.list();
    setUsers(res.data);
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await userApi.create({ username, password, display_name: displayName, role });
      setUsername('');
      setPassword('');
      setDisplayName('');
      setRole('user');
      setShowForm(false);
      loadUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || '建立失敗');
    }
  };

  const toggleActive = async (u: UserItem) => {
    await userApi.update(u.id, { is_active: !u.is_active });
    loadUsers();
  };

  const handleDelete = async (u: UserItem) => {
    if (!confirm(`確定要刪除使用者 "${u.display_name}" 嗎？`)) return;
    try {
      await userApi.delete(u.id);
      loadUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || '刪除失敗');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 flex items-center justify-between">
          <div>
            <Link to="/" className="text-3xl font-bold text-gray-900 hover:text-blue-600">ShotCut</Link>
            <p className="mt-1 text-gray-500">使用者管理</p>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-600">{currentUser?.display_name}（{currentUser?.role}）</span>
            <Link to="/users" className="text-blue-600 font-medium">使用者管理</Link>
            <button onClick={logout} className="text-red-600 hover:text-red-800">登出</button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">使用者列表</h2>
          <button
            onClick={() => setShowForm(!showForm)}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            {showForm ? '取消' : '新增使用者'}
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleCreate} className="bg-white rounded-lg shadow p-6 mb-6 space-y-4">
            {error && <div className="rounded bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">帳號</label>
                <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">密碼</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">顯示名稱</label>
                <input type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)} required
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
                <select value={role} onChange={(e) => setRole(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm">
                  <option value="user">一般使用者</option>
                  <option value="admin">管理員</option>
                </select>
              </div>
            </div>
            <button type="submit" className="rounded-md bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700">
              建立
            </button>
          </form>
        )}

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">帳號</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">顯示名稱</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">角色</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">狀態</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="px-6 py-4 text-sm text-gray-900">{u.username}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{u.display_name}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${u.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'}`}>
                      {u.role === 'admin' ? '管理員' : '一般使用者'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {u.is_active ? '啟用' : '停用'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-right space-x-2">
                    {u.id !== currentUser?.id && (
                      <>
                        <button onClick={() => toggleActive(u)} className="text-blue-600 hover:text-blue-800">
                          {u.is_active ? '停用' : '啟用'}
                        </button>
                        <button onClick={() => handleDelete(u)} className="text-red-600 hover:text-red-800">
                          刪除
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
