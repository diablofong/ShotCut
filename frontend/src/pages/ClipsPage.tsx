import { useState, useEffect, useCallback, useRef } from 'react';
import { clipApi } from '../services/api';
import VideoPlayer, { type VideoPlayerHandle } from '../components/VideoPlayer';
import Navbar from '../components/Navbar';
import DataTable, { type Column } from '../components/DataTable';
import SearchInput from '../components/SearchInput';
import { useSearch } from '../hooks/useSearch';

interface Clip {
  id: number;
  video_id: number;
  mark_id: number;
  file_path: string;
  category: string;
  label: string;
  video_title: string;
  player_numbers: number[];
  start_time: number;
  end_time: number;
  created_at: string;
}

const CATEGORY_OPTIONS = [
  { value: '', label: '全部分類' },
  { value: 'offense', label: '進攻' },
  { value: 'defense', label: '防守' },
  { value: 'turnover', label: '失誤' },
];

const CATEGORY_LABELS: Record<string, string> = {
  offense: '進攻',
  defense: '防守',
  turnover: '失誤',
};

function categoryLabel(category: string) {
  return CATEGORY_LABELS[category] || category;
}

function categoryBadge(category: string) {
  switch (category) {
    case 'offense':
      return 'bg-blue-100 text-blue-800';
    case 'defense':
      return 'bg-emerald-100 text-emerald-800';
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

  const [filterCategory, setFilterCategory] = useState('');
  const [filterPlayer, setFilterPlayer] = useState('');

  const [previewClip, setPreviewClip] = useState<Clip | null>(null);
  const previewPlayerRef = useRef<VideoPlayerHandle>(null);
  const previewContainerRef = useRef<HTMLDivElement>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

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

  const { searchQuery, setSearchQuery, filteredItems: filteredClips } = useSearch(
    clips,
    useCallback(
      (c: Clip) => [
        c.label,
        c.video_title,
        categoryLabel(c.category),
        ...c.player_numbers.map(String),
      ],
      [],
    ),
  );

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

  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return;
    if (!confirm(`確定要刪除所選的 ${selectedIds.size} 個片段嗎？`)) return;
    try {
      await clipApi.batchDelete(Array.from(selectedIds));
      setClips((prev) => prev.filter((c) => !selectedIds.has(c.id)));
      if (previewClip && selectedIds.has(previewClip.id)) setPreviewClip(null);
      setSelectedIds(new Set());
    } catch {
      setError('批量刪除失敗');
    }
  };

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === filteredClips.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredClips.map((c) => c.id)));
    }
  };

  const handleSelectClip = useCallback((clip: Clip) => {
    setPreviewClip(clip);
    setTimeout(() => {
      previewContainerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);
  }, []);

  const allPlayers = Array.from(
    new Set(clips.flatMap((c) => c.player_numbers)),
  ).sort((a, b) => a - b);

  const columns: Column<Clip>[] = [
    {
      key: 'select',
      header: '',
      width: 'w-12',
      render: (c) => (
        <div onClick={(e) => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={selectedIds.has(c.id)}
            onChange={() => toggleSelect(c.id)}
            className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
        </div>
      ),
    },
    {
      key: 'thumbnail',
      header: '縮圖',
      width: 'w-20',
      render: (c) => (
        <img
          src={`/api/clips/${c.id}/thumbnail`}
          alt=""
          className="w-16 h-9 object-cover rounded bg-gray-200"
          onError={(e) => {
            const img = e.target as HTMLImageElement;
            img.style.display = 'none';
            const parent = img.parentElement!;
            if (!parent.querySelector('.placeholder')) {
              const placeholder = document.createElement('div');
              placeholder.className = 'placeholder w-16 h-9 rounded bg-gray-200 flex items-center justify-center text-gray-400 text-xs';
              placeholder.textContent = '無圖';
              parent.appendChild(placeholder);
            }
          }}
        />
      ),
    },
    {
      key: 'video_title',
      header: '影片',
      sortable: true,
      sortFn: (a, b) => a.video_title.localeCompare(b.video_title),
      render: (c) => (
        <span className="text-gray-700 truncate block max-w-[200px]" title={c.video_title}>
          {c.video_title}
        </span>
      ),
    },
    {
      key: 'label',
      header: '標記',
      sortable: true,
      sortFn: (a, b) => a.label.localeCompare(b.label),
      render: (c) => (
        <div className="flex items-center gap-2">
          <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${categoryBadge(c.category)}`}>
            {categoryLabel(c.category)}
          </span>
          <span className="font-medium text-gray-900 text-sm">{c.label}</span>
        </div>
      ),
    },
    {
      key: 'time_range',
      header: '時間區段',
      sortable: true,
      width: 'w-32',
      sortFn: (a, b) => a.start_time - b.start_time,
      render: (c) => (
        <span className="text-gray-600 tabular-nums">
          {formatTime(c.start_time)} ~ {formatTime(c.end_time)}
        </span>
      ),
    },
    {
      key: 'player_numbers',
      header: '球員',
      width: 'w-32',
      render: (c) =>
        c.player_numbers.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {c.player_numbers.map((num) => (
              <span key={num} className="inline-block rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                {num} 號
              </span>
            ))}
          </div>
        ) : (
          <span className="text-gray-400 text-xs">—</span>
        ),
    },
    {
      key: 'actions',
      header: '操作',
      width: 'w-36',
      render: (c) => (
        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => handleSelectClip(c)}
            className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded hover:bg-blue-50"
          >
            播放
          </button>
          <a
            href={`/api/clips/${c.id}/download`}
            className="text-xs text-gray-600 hover:text-gray-800 px-2 py-1 rounded hover:bg-gray-100"
          >
            下載
          </a>
          <button
            onClick={() => handleDelete(c.id)}
            className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded hover:bg-red-50"
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
                src={`/api/clips/${previewClip.id}/stream`}
                autoplay
              />
            </div>
          </div>
        )}

        {/* 搜尋 + 篩選列 */}
        <div className="mb-4 flex flex-wrap gap-3 items-center">
          <div className="w-72">
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="搜尋影片、標記、分類、球員..."
            />
          </div>

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

          <span className="text-sm text-gray-500 ml-auto">
            共 {filteredClips.length} 個片段
          </span>
        </div>

        {/* 批量操作列 */}
        {filteredClips.length > 0 && (
          <div className="mb-4 flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer hover:text-gray-800">
              <input
                type="checkbox"
                checked={selectedIds.size === filteredClips.length && filteredClips.length > 0}
                onChange={toggleSelectAll}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              全選
            </label>
            {selectedIds.size > 0 && (
              <>
                <span className="text-sm text-gray-500">
                  已選 {selectedIds.size} 筆
                </span>
                <button
                  onClick={handleBatchDelete}
                  className="text-sm text-red-600 hover:text-red-800 font-medium px-3 py-1.5 rounded hover:bg-red-50"
                >
                  刪除所選
                </button>
              </>
            )}
          </div>
        )}

        {/* 片段表格 */}
        <DataTable
          columns={columns}
          data={filteredClips}
          keyExtractor={(c) => c.id}
          onRowClick={handleSelectClip}
          emptyMessage="尚無片段，請先在影片中建立標記並擷取片段"
          loading={loading}
        />
      </main>
    </div>
  );
}
