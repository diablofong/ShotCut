import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { videoApi } from '../services/api';
import Navbar from '../components/Navbar';
import DataTable, { type Column } from '../components/DataTable';
import SearchInput from '../components/SearchInput';
import { useSearch } from '../hooks/useSearch';

interface Video {
  id: number;
  title: string;
  source_type: string;
  status: string;
  duration: number | null;
  error_message: string | null;
  download_progress: number | null;
  download_speed: number | null;
  download_eta: number | null;
  created_at: string;
}

function statusBadge(status: string) {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'pending':
    case 'downloading':
      return 'bg-yellow-100 text-yellow-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

function statusLabel(status: string) {
  switch (status) {
    case 'completed':
      return '就緒';
    case 'pending':
      return '等待中';
    case 'downloading':
      return '下載中';
    case 'failed':
      return '失敗';
    default:
      return status;
  }
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return '--:--';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function formatSpeed(bytesPerSec: number | null): string {
  if (bytesPerSec == null || bytesPerSec <= 0) return '';
  if (bytesPerSec >= 1024 * 1024) return `${(bytesPerSec / 1024 / 1024).toFixed(1)} MB/s`;
  return `${(bytesPerSec / 1024).toFixed(0)} KB/s`;
}

function formatEta(seconds: number | null): string {
  if (seconds == null || seconds <= 0) return '';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m > 0) return `剩餘 ${m}分${s}秒`;
  return `剩餘 ${s}秒`;
}

export default function VideosPage() {
  const navigate = useNavigate();
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [downloading, setDownloading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [renamingId, setRenamingId] = useState<number | null>(null);
  const [renameTitle, setRenameTitle] = useState('');

  const { searchQuery, setSearchQuery, filteredItems: filteredVideos } = useSearch(
    videos,
    useCallback((v: Video) => [v.title], []),
  );

  const fetchVideos = useCallback(async () => {
    try {
      const res = await videoApi.list();
      setVideos(res.data);
    } catch {
      setError('無法載入影片列表');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  const hasInProgress = videos.some((v) => v.status === 'pending' || v.status === 'downloading');

  useEffect(() => {
    if (!hasInProgress) return;

    pollingRef.current = setInterval(async () => {
      try {
        const res = await videoApi.list();
        setVideos(res.data);
      } catch { /* polling 失敗時靜默忽略 */ }
    }, 2000);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [hasInProgress]);

  const handleDownload = async () => {
    if (!youtubeUrl.trim()) return;
    setDownloading(true);
    setError('');
    try {
      await videoApi.download(youtubeUrl.trim());
      setYoutubeUrl('');
      await fetchVideos();
    } catch {
      setError('下載失敗，請檢查網址');
    } finally {
      setDownloading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      await videoApi.upload(file);
      await fetchVideos();
    } catch {
      setError('上傳失敗');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const startRename = (video: Video) => {
    setRenamingId(video.id);
    setRenameTitle(video.title);
  };

  const handleRename = async (id: number) => {
    if (!renameTitle.trim()) return;
    try {
      await videoApi.update(id, { title: renameTitle.trim() });
      setVideos((prev) =>
        prev.map((v) => (v.id === id ? { ...v, title: renameTitle.trim() } : v)),
      );
      setRenamingId(null);
    } catch {
      setError('重新命名失敗');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('確定要刪除此影片嗎？')) return;
    try {
      await videoApi.delete(id);
      setVideos((prev) => prev.filter((v) => v.id !== id));
    } catch {
      setError('刪除失敗');
    }
  };

  const columns: Column<Video>[] = [
    {
      key: 'thumbnail',
      header: '縮圖',
      width: 'w-20',
      render: (v) => (
        <img
          src={`/api/videos/${v.id}/thumbnail?token=${encodeURIComponent(localStorage.getItem('token') || '')}`}
          alt=""
          className="w-16 h-9 object-cover rounded bg-gray-200"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = 'none';
            (e.target as HTMLImageElement).parentElement!.classList.add('flex', 'items-center', 'justify-center');
            const placeholder = document.createElement('div');
            placeholder.className = 'w-16 h-9 rounded bg-gray-200 flex items-center justify-center text-gray-400 text-xs';
            placeholder.textContent = '無圖';
            (e.target as HTMLImageElement).parentElement!.appendChild(placeholder);
          }}
        />
      ),
    },
    {
      key: 'title',
      header: '影片名稱',
      sortable: true,
      sortFn: (a, b) => a.title.localeCompare(b.title),
      render: (v) =>
        renamingId === v.id ? (
          <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
            <input
              type="text"
              value={renameTitle}
              onChange={(e) => setRenameTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleRename(v.id);
                if (e.key === 'Escape') setRenamingId(null);
              }}
              autoFocus
              className="flex-1 rounded border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button
              onClick={() => handleRename(v.id)}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              儲存
            </button>
            <button
              onClick={() => setRenamingId(null)}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              取消
            </button>
          </div>
        ) : (
          <span className="font-medium text-gray-900 truncate block max-w-xs">{v.title}</span>
        ),
    },
    {
      key: 'source_type',
      header: '來源',
      sortable: true,
      width: 'w-28',
      sortFn: (a, b) => a.source_type.localeCompare(b.source_type),
      render: (v) => (
        <span className="text-gray-600">
          {v.source_type === 'youtube' ? 'YouTube' : '本機上傳'}
        </span>
      ),
    },
    {
      key: 'duration',
      header: '時長',
      sortable: true,
      width: 'w-24',
      sortFn: (a, b) => (a.duration ?? 0) - (b.duration ?? 0),
      render: (v) => <span className="text-gray-600 tabular-nums">{formatDuration(v.duration)}</span>,
    },
    {
      key: 'status',
      header: '狀態',
      sortable: true,
      width: 'w-44',
      sortFn: (a, b) => a.status.localeCompare(b.status),
      render: (v) => (
        <div>
          <span
            className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${statusBadge(v.status)}`}
          >
            {statusLabel(v.status)}
          </span>
          {(v.status === 'downloading' || v.status === 'pending') && (
            <div className="mt-1">
              <div className="flex items-center justify-between text-xs text-gray-500 mb-0.5">
                <span>
                  {v.download_progress != null ? `${v.download_progress.toFixed(1)}%` : '準備中...'}
                </span>
                <span className="ml-2">
                  {formatSpeed(v.download_speed)}
                  {v.download_speed && v.download_eta ? ' · ' : ''}
                  {formatEta(v.download_eta)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-blue-500 h-1.5 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${Math.min(v.download_progress ?? 0, 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'actions',
      header: '操作',
      width: 'w-28',
      render: (v) => (
        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => startRename(v)}
            className="text-xs text-gray-600 hover:text-gray-800 px-2 py-1 rounded hover:bg-gray-100"
            title="重新命名"
          >
            重新命名
          </button>
          <button
            onClick={() => handleDelete(v.id)}
            className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded hover:bg-red-50"
            title="刪除"
          >
            刪除
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="mx-auto max-w-7xl px-4 py-8">
        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
            <button className="ml-2 font-medium underline" onClick={() => setError('')}>
              關閉
            </button>
          </div>
        )}

        {/* 上傳/下載區 */}
        <div className="mb-6 rounded-lg bg-white p-6 shadow">
          <h2 className="text-lg font-semibold mb-4">新增影片</h2>

          <div className="flex gap-2 mb-4">
            <input
              type="text"
              placeholder="貼上 YouTube 網址..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleDownload()}
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button
              onClick={handleDownload}
              disabled={downloading || !youtubeUrl.trim()}
              className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {downloading ? '下載中...' : '下載'}
            </button>
          </div>

          <div className="flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="rounded-lg border border-gray-300 bg-white px-5 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              {uploading ? '上傳中...' : '選擇檔案上傳'}
            </button>
            <span className="text-xs text-gray-400">支援 MP4、MOV 等影片格式</span>
          </div>
        </div>

        {/* 搜尋列 + 統計 */}
        <div className="mb-4 flex items-center gap-4">
          <div className="w-72">
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="搜尋影片名稱..."
            />
          </div>
          <span className="text-sm text-gray-500">
            共 {filteredVideos.length} 部影片
          </span>
        </div>

        {/* 影片表格 */}
        <DataTable
          columns={columns}
          data={filteredVideos}
          keyExtractor={(v) => v.id}
          onRowClick={(v) => renamingId !== v.id && navigate(`/videos/${v.id}`)}
          emptyMessage="尚無影片，請先上傳或下載影片"
          loading={loading}
        />
      </main>
    </div>
  );
}
