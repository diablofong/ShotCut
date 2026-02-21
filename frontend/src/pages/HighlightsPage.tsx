import { useState, useEffect, useCallback, useRef } from 'react';
import { highlightApi, shareApi, clipApi } from '../services/api';
import VideoPlayer, { type VideoPlayerHandle } from '../components/VideoPlayer';
import Navbar from '../components/Navbar';
import DataTable, { type Column } from '../components/DataTable';
import SearchInput from '../components/SearchInput';
import { useSearch } from '../hooks/useSearch';

interface Highlight {
  id: number;
  title: string;
  file_path: string;
  player_numbers: number[];
  categories: string[];
  created_at: string;
}

interface Share {
  id: number;
  highlight_id: number;
  token: string;
  expires_at: string | null;
}

interface Clip {
  id: number;
  category: string;
  label: string;
  player_numbers: number[];
}

const CATEGORY_OPTIONS = [
  { value: 'offense', label: '進攻' },
  { value: 'defense', label: '防守' },
  { value: 'turnover', label: '失誤' },
];

const CATEGORY_LABELS: Record<string, string> = {
  offense: '進攻',
  defense: '防守',
  turnover: '失誤',
};

const EXPIRATION_OPTIONS = [
  { value: '1d', label: '24 小時' },
  { value: '7d', label: '7 天' },
  { value: '30d', label: '30 天' },
  { value: 'never', label: '永久' },
];

function formatRemainingTime(expiresAt: string | null): string {
  if (!expiresAt) return '永久有效';
  const diff = new Date(expiresAt).getTime() - Date.now();
  if (diff <= 0) return '已過期';
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  if (days > 0) return `剩餘 ${days} 天 ${hours} 小時`;
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  if (hours > 0) return `剩餘 ${hours} 小時 ${minutes} 分`;
  return `剩餘 ${minutes} 分鐘`;
}

export default function HighlightsPage() {
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [playingHighlight, setPlayingHighlight] = useState<Highlight | null>(null);
  const playerRef = useRef<VideoPlayerHandle>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  const [showForm, setShowForm] = useState(false);
  const [selectedPlayers, setSelectedPlayers] = useState<number[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [generating, setGenerating] = useState(false);

  const [shares, setShares] = useState<Record<number, Share>>({});
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [shareExpiration, setShareExpiration] = useState<string>('7d');
  const [sharingId, setSharingId] = useState<number | null>(null);

  const [allPlayers, setAllPlayers] = useState<number[]>([]);

  const { searchQuery, setSearchQuery, filteredItems: filteredHighlights } = useSearch(
    highlights,
    useCallback(
      (hl: Highlight) => [
        hl.title,
        ...hl.player_numbers.map(String),
        ...hl.categories.map((c) => CATEGORY_LABELS[c] || c),
      ],
      [],
    ),
  );

  const fetchHighlights = useCallback(async () => {
    setLoading(true);
    try {
      const res = await highlightApi.list();
      setHighlights(res.data);
    } catch {
      setError('無法載入精華剪輯列表');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAllPlayers = useCallback(async () => {
    try {
      const res = await clipApi.list();
      const clips: Clip[] = res.data;
      const players = Array.from(
        new Set(clips.flatMap((c) => c.player_numbers)),
      ).sort((a, b) => a - b);
      setAllPlayers(players);
    } catch {
      setError('無法載入球員資料');
    }
  }, []);

  useEffect(() => {
    fetchHighlights();
    fetchAllPlayers();
  }, [fetchHighlights, fetchAllPlayers]);

  const handleGenerate = async () => {
    if (selectedPlayers.length === 0 && selectedCategories.length === 0) {
      setError('請至少選擇一位球員或一個標籤分類');
      return;
    }
    setGenerating(true);
    setError('');
    try {
      await highlightApi.generate({
        player_numbers: selectedPlayers,
        categories: selectedCategories,
      });
      await fetchHighlights();
      setShowForm(false);
      setSelectedPlayers([]);
      setSelectedCategories([]);
    } catch {
      setError('產出精華剪輯失敗');
    } finally {
      setGenerating(false);
    }
  };

  const handleCreateShare = async (highlightId: number) => {
    setSharingId(highlightId);
  };

  const handleConfirmShare = async (highlightId: number) => {
    try {
      const res = await shareApi.create(highlightId, shareExpiration);
      const share: Share = res.data;
      setShares((prev) => ({ ...prev, [highlightId]: share }));
      setSharingId(null);
    } catch {
      setError('建立分享連結失敗');
    }
  };

  const handleDelete = async (highlightId: number) => {
    if (!confirm('確定要刪除此精華剪輯嗎？此操作無法復原。')) return;
    try {
      await highlightApi.delete(highlightId);
      setHighlights((prev) => prev.filter((hl) => hl.id !== highlightId));
      if (playingHighlight?.id === highlightId) setPlayingHighlight(null);
    } catch {
      setError('刪除精華剪輯失敗');
    }
  };

  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return;
    if (!confirm(`確定要刪除所選的 ${selectedIds.size} 部精華剪輯嗎？此操作無法復原。`)) return;
    try {
      await highlightApi.batchDelete(Array.from(selectedIds));
      setHighlights((prev) => prev.filter((hl) => !selectedIds.has(hl.id)));
      if (playingHighlight && selectedIds.has(playingHighlight.id)) setPlayingHighlight(null);
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
    if (selectedIds.size === filteredHighlights.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredHighlights.map((hl) => hl.id)));
    }
  };

  const handleCopyLink = (highlightId: number) => {
    const share = shares[highlightId];
    if (!share) return;
    const url = `${window.location.origin}/share/${share.token}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopiedId(highlightId);
      setTimeout(() => setCopiedId(null), 2000);
    });
  };

  const togglePlayer = (num: number) => {
    setSelectedPlayers((prev) =>
      prev.includes(num) ? prev.filter((n) => n !== num) : [...prev, num],
    );
  };

  const toggleCategory = (value: string) => {
    setSelectedCategories((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value],
    );
  };

  const columns: Column<Highlight>[] = [
    {
      key: 'select',
      header: '',
      width: 'w-12',
      render: (hl) => (
        <div onClick={(e) => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={selectedIds.has(hl.id)}
            onChange={() => toggleSelect(hl.id)}
            className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
        </div>
      ),
    },
    {
      key: 'thumbnail',
      header: '縮圖',
      width: 'w-20',
      render: (hl) => (
        <img
          src={`/api/highlights/${hl.id}/thumbnail`}
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
      key: 'title',
      header: '標題',
      sortable: true,
      sortFn: (a, b) => a.title.localeCompare(b.title),
      render: (hl) => <span className="font-medium text-gray-900">{hl.title}</span>,
    },
    {
      key: 'players',
      header: '球員',
      width: 'w-32',
      render: (hl) =>
        hl.player_numbers.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {hl.player_numbers.map((num) => (
              <span key={num} className="inline-block rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
                {num} 號
              </span>
            ))}
          </div>
        ) : (
          <span className="text-gray-400 text-xs">—</span>
        ),
    },
    {
      key: 'categories',
      header: '分類',
      width: 'w-32',
      render: (hl) =>
        hl.categories.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {hl.categories.map((cat) => (
              <span key={cat} className="inline-block rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                {CATEGORY_LABELS[cat] || cat}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-gray-400 text-xs">—</span>
        ),
    },
    {
      key: 'created_at',
      header: '建立時間',
      sortable: true,
      width: 'w-40',
      sortFn: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      render: (hl) => (
        <span className="text-gray-600 text-xs">
          {new Date(hl.created_at).toLocaleString('zh-TW')}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '操作',
      width: 'w-52',
      render: (hl) => (
        <div className="flex flex-col gap-1" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPlayingHighlight(hl)}
              className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded hover:bg-blue-50"
            >
              播放
            </button>
            <a
              href={`/api/highlights/${hl.id}/download`}
              className="text-xs text-gray-600 hover:text-gray-800 px-2 py-1 rounded hover:bg-gray-100"
            >
              下載
            </a>
            {shares[hl.id] ? (
              <button
                onClick={() => handleCopyLink(hl.id)}
                className="text-xs text-green-600 hover:text-green-800 px-2 py-1 rounded hover:bg-green-50"
              >
                {copiedId === hl.id ? '已複製!' : '複製連結'}
              </button>
            ) : sharingId === hl.id ? null : (
              <button
                onClick={() => handleCreateShare(hl.id)}
                className="text-xs text-purple-600 hover:text-purple-800 px-2 py-1 rounded hover:bg-purple-50"
              >
                分享
              </button>
            )}
            <button
              onClick={() => handleDelete(hl.id)}
              className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded hover:bg-red-50"
            >
              刪除
            </button>
          </div>
          {/* 分享到期選擇器 */}
          {sharingId === hl.id && (
            <div className="flex items-center gap-2 mt-1">
              <select
                value={shareExpiration}
                onChange={(e) => setShareExpiration(e.target.value)}
                className="rounded border border-gray-300 px-2 py-1 text-xs focus:border-blue-500 focus:outline-none"
              >
                {EXPIRATION_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <button
                onClick={() => handleConfirmShare(hl.id)}
                className="text-xs text-white bg-purple-600 hover:bg-purple-700 px-2 py-1 rounded"
              >
                確認分享
              </button>
              <button
                onClick={() => setSharingId(null)}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                取消
              </button>
            </div>
          )}
          {/* 顯示分享剩餘時間 */}
          {shares[hl.id] && (
            <span className="text-xs text-gray-400">
              {formatRemainingTime(shares[hl.id].expires_at)}
            </span>
          )}
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

        {/* 新增精華按鈕 */}
        <div className="mb-6 flex items-center justify-between">
          <span className="text-sm text-gray-500">共 {filteredHighlights.length} 部精華剪輯</span>
          <button
            onClick={() => setShowForm(!showForm)}
            className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {showForm ? '取消' : '產出新精華'}
          </button>
        </div>

        {/* 產出表單 */}
        {showForm && (
          <div className="mb-6 rounded-lg bg-white p-6 shadow">
            <h3 className="text-base font-semibold mb-4">產出個人精華剪輯</h3>

            <div className="mb-4">
              <label className="block text-sm text-gray-600 font-medium mb-2">選擇球員</label>
              {allPlayers.length === 0 ? (
                <p className="text-sm text-gray-400">尚無片段中的球員資料</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {allPlayers.map((num) => (
                    <button
                      key={num}
                      onClick={() => togglePlayer(num)}
                      className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                        selectedPlayers.includes(num)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {num} 號
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="mb-4">
              <label className="block text-sm text-gray-600 font-medium mb-2">選擇標籤分類</label>
              <div className="flex flex-wrap gap-2">
                {CATEGORY_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => toggleCategory(opt.value)}
                    className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                      selectedCategories.includes(opt.value)
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={generating}
              className="rounded-lg bg-green-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              {generating ? '產出中...' : '開始產出'}
            </button>
          </div>
        )}

        {/* 播放器 */}
        {playingHighlight && (
          <div className="mb-6 rounded-lg bg-white p-4 shadow">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-800">
                播放：{playingHighlight.title}
              </h3>
              <button
                onClick={() => setPlayingHighlight(null)}
                className="text-sm text-gray-400 hover:text-gray-600"
              >
                關閉播放
              </button>
            </div>
            <div className="max-w-3xl mx-auto">
              <VideoPlayer
                ref={playerRef}
                src={`/api/highlights/${playingHighlight.id}/stream`}
              />
            </div>
          </div>
        )}

        {/* 搜尋列 */}
        <div className="mb-4 flex items-center gap-4">
          <div className="w-72">
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="搜尋標題、球員、分類..."
            />
          </div>
        </div>

        {/* 批量操作列 */}
        {filteredHighlights.length > 0 && (
          <div className="mb-4 flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer hover:text-gray-800">
              <input
                type="checkbox"
                checked={selectedIds.size === filteredHighlights.length && filteredHighlights.length > 0}
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

        {/* 精華表格 */}
        <DataTable
          columns={columns}
          data={filteredHighlights}
          keyExtractor={(hl) => hl.id}
          onRowClick={(hl) => setPlayingHighlight(hl)}
          emptyMessage="尚無精華剪輯，請先產出"
          loading={loading}
        />
      </main>
    </div>
  );
}
