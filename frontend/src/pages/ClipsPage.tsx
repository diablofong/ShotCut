import { useState, useEffect, useCallback, useRef } from 'react';
import { clipApi } from '../services/api';
import VideoPlayer, { type VideoPlayerHandle } from '../components/VideoPlayer';
import Navbar from '../components/Navbar';

interface Clip {
  id: number;
  video_id: number;
  mark_id: number;
  file_path: string;
  category: string;
  label: string;
  player_numbers: number[];
  start_time: number;
  end_time: number;
  created_at: string;
}

const CATEGORY_OPTIONS = [
  { value: '', label: '全部分類' },
  { value: 'offense', label: '進攻' },
  { value: 'defense', label: '防守' },
  { value: 'highlight', label: '精彩' },
  { value: 'turnover', label: '失誤' },
];

function categoryLabel(category: string) {
  const found = CATEGORY_OPTIONS.find((c) => c.value === category);
  return found ? found.label : category;
}

function categoryBadge(category: string) {
  switch (category) {
    case 'offense':
      return 'bg-blue-100 text-blue-800';
    case 'defense':
      return 'bg-emerald-100 text-emerald-800';
    case 'highlight':
      return 'bg-amber-100 text-amber-800';
    case 'turnover':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function ClipsPage() {
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // 篩選
  const [filterCategory, setFilterCategory] = useState('');
  const [filterPlayer, setFilterPlayer] = useState('');

  // 預覽
  const [previewClip, setPreviewClip] = useState<Clip | null>(null);
  const previewPlayerRef = useRef<VideoPlayerHandle>(null);
  const previewContainerRef = useRef<HTMLDivElement>(null);

  /** 載入片段 */
  const fetchClips = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {};
      if (filterCategory) params.category = filterCategory;
      if (filterPlayer.trim()) params.player_number = parseInt(filterPlayer.trim(), 10);
      const res = await clipApi.list(params);
      setClips(res.data);
    } catch {
      setError('無法載入片段列表');
    } finally {
      setLoading(false);
    }
  }, [filterCategory, filterPlayer]);

  useEffect(() => {
    fetchClips();
  }, [fetchClips]);

  /** 刪除片段 */
  const handleDelete = async (id: number) => {
    if (!confirm('確定要刪除此片段嗎？')) return;
    try {
      await clipApi.delete(id);
      setClips((prev) => prev.filter((c) => c.id !== id));
      if (previewClip?.id === id) setPreviewClip(null);
    } catch {
      setError('刪除失敗');
    }
  };

  /** 選擇片段預覽 */
  const handleSelectClip = useCallback((clip: Clip) => {
    setPreviewClip(clip);
    // 滾動到預覽區域
    setTimeout(() => {
      previewContainerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);
  }, []);

  // 收集所有球員編號（去重排序）
  const allPlayers = Array.from(
    new Set(clips.flatMap((c) => c.player_numbers))
  ).sort((a, b) => a - b);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="mx-auto max-w-7xl px-4 py-8">
        {/* 錯誤提示 */}
        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
            <button className="ml-2 font-medium underline" onClick={() => setError('')}>
              關閉
            </button>
          </div>
        )}

        {/* 篩選列 */}
        <div className="mb-6 flex flex-wrap gap-3 items-center">
          <label className="text-sm text-gray-600 font-medium">篩選：</label>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {CATEGORY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          <select
            value={filterPlayer}
            onChange={(e) => setFilterPlayer(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">全部球員</option>
            {allPlayers.map((num) => (
              <option key={num} value={String(num)}>
                {num} 號
              </option>
            ))}
          </select>

          <span className="text-sm text-gray-400">
            共 {clips.length} 個片段
          </span>
        </div>

        {/* 預覽播放器 */}
        {previewClip && (
          <div ref={previewContainerRef} className="mb-6 rounded-lg bg-white p-4 shadow">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-800">
                預覽：{previewClip.label}
              </h3>
              <button
                onClick={() => setPreviewClip(null)}
                className="text-sm text-gray-400 hover:text-gray-600"
              >
                關閉預覽
              </button>
            </div>
            <div className="max-w-2xl mx-auto">
              <VideoPlayer
                ref={previewPlayerRef}
                src={`/api/clips/${previewClip.id}/stream?token=${encodeURIComponent(localStorage.getItem('token') || '')}`}
                autoplay
              />
            </div>
          </div>
        )}

        {/* 片段列表 */}
        {loading ? (
          <div className="text-center py-12 text-gray-500">載入中...</div>
        ) : clips.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            尚無片段，請先在影片中建立標記並擷取片段
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {clips.map((clip) => (
              <div
                key={clip.id}
                className="rounded-lg bg-white shadow hover:shadow-md transition-shadow overflow-hidden"
              >
                {/* 卡片主體 */}
                <div
                  className="p-4 cursor-pointer"
                  onClick={() => handleSelectClip(clip)}
                >
                  {/* 頂部標題行 */}
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900 truncate">
                      {clip.label}
                    </span>
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${categoryBadge(clip.category)}`}
                    >
                      {categoryLabel(clip.category)}
                    </span>
                  </div>

                  {/* 時間範圍 */}
                  <div className="text-sm text-gray-500 mb-1">
                    {formatTime(clip.start_time)} - {formatTime(clip.end_time)}
                  </div>

                  {/* 球員 */}
                  {clip.player_numbers.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {clip.player_numbers.map((num) => (
                        <span
                          key={num}
                          className="inline-block rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                        >
                          {num} 號
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* 操作列 */}
                <div className="border-t border-gray-100 px-4 py-2.5 flex items-center justify-between">
                  <button
                    onClick={() => handleSelectClip(clip)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    播放
                  </button>
                  <div className="flex items-center gap-3">
                    <a
                      href={`/api/clips/${clip.id}/download?token=${encodeURIComponent(localStorage.getItem('token') || '')}`}
                      className="text-sm text-gray-600 hover:text-gray-800"
                    >
                      下載
                    </a>
                    <button
                      onClick={() => handleDelete(clip.id)}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      刪除
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
