import { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { videoApi } from '../services/api';

interface Video {
  id: number;
  title: string;
  source: string;
  status: string;
  duration: number | null;
  created_at: string;
}

/** 狀態標籤樣式 */
function statusBadge(status: string) {
  switch (status) {
    case 'ready':
      return 'bg-green-100 text-green-800';
    case 'downloading':
      return 'bg-yellow-100 text-yellow-800';
    case 'error':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

function statusLabel(status: string) {
  switch (status) {
    case 'ready':
      return '就緒';
    case 'downloading':
      return '下載中';
    case 'error':
      return '錯誤';
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

  /** 載入影片列表 */
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

  /** 初始載入 */
  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  /** 輪詢下載中的影片狀態 */
  useEffect(() => {
    const hasDownloading = videos.some((v) => v.status === 'downloading');
    if (hasDownloading) {
      pollingRef.current = setInterval(async () => {
        const res = await videoApi.list();
        setVideos(res.data);
        const stillDownloading = (res.data as Video[]).some(
          (v) => v.status === 'downloading'
        );
        if (!stillDownloading && pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
      }, 3000);
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [videos]);

  /** YouTube 下載 */
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

  /** 檔案上傳 */
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

  /** 刪除影片 */
  const handleDelete = async (id: number) => {
    if (!confirm('確定要刪除此影片嗎？')) return;
    try {
      await videoApi.delete(id);
      setVideos((prev) => prev.filter((v) => v.id !== id));
    } catch {
      setError('刪除失敗');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 頂部導航 */}
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-xl font-bold text-gray-900 hover:text-blue-600">
              ShotCut
            </Link>
            <span className="text-gray-400">/</span>
            <h1 className="text-xl font-semibold text-gray-800">影片管理</h1>
          </div>
          <nav className="flex gap-4 text-sm">
            <Link to="/clips" className="text-gray-600 hover:text-blue-600">片段管理</Link>
            <Link to="/highlights" className="text-gray-600 hover:text-blue-600">精華剪輯</Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        {/* 錯誤提示 */}
        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
            <button
              className="ml-2 font-medium underline"
              onClick={() => setError('')}
            >
              關閉
            </button>
          </div>
        )}

        {/* 上傳/下載區 */}
        <div className="mb-8 rounded-lg bg-white p-6 shadow">
          <h2 className="text-lg font-semibold mb-4">新增影片</h2>

          {/* YouTube 下載 */}
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

          {/* 檔案上傳 */}
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

        {/* 影片列表 */}
        {loading ? (
          <div className="text-center py-12 text-gray-500">載入中...</div>
        ) : videos.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            尚無影片，請先上傳或下載影片
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {videos.map((video) => (
              <div
                key={video.id}
                className="rounded-lg bg-white shadow hover:shadow-md transition-shadow overflow-hidden"
              >
                {/* 卡片主體（可點擊） */}
                <div
                  className="p-5 cursor-pointer"
                  onClick={() => navigate(`/videos/${video.id}`)}
                >
                  <h3 className="font-semibold text-gray-900 truncate">
                    {video.title}
                  </h3>
                  <div className="mt-2 flex items-center gap-3 text-sm text-gray-500">
                    <span className="capitalize">{video.source === 'youtube' ? 'YouTube' : '本機上傳'}</span>
                    <span>{formatDuration(video.duration)}</span>
                  </div>
                  <div className="mt-2">
                    <span
                      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${statusBadge(video.status)}`}
                    >
                      {statusLabel(video.status)}
                    </span>
                  </div>
                </div>

                {/* 操作列 */}
                <div className="border-t border-gray-100 px-5 py-3 flex justify-end">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(video.id);
                    }}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    刪除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
