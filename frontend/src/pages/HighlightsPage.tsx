import { useState, useEffect, useCallback, useRef } from 'react';
import { highlightApi, shareApi, clipApi } from '../services/api';
import VideoPlayer, { type VideoPlayerHandle } from '../components/VideoPlayer';
import Navbar from '../components/Navbar';

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
  { value: 'highlight', label: '精彩' },
  { value: 'turnover', label: '失誤' },
];

export default function HighlightsPage() {
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // 播放
  const [playingHighlight, setPlayingHighlight] = useState<Highlight | null>(null);
  const playerRef = useRef<VideoPlayerHandle>(null);

  // 產出新精華表單
  const [showForm, setShowForm] = useState(false);
  const [selectedPlayers, setSelectedPlayers] = useState<number[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [generating, setGenerating] = useState(false);

  // 分享
  const [shares, setShares] = useState<Record<number, Share>>({});
  const [copiedId, setCopiedId] = useState<number | null>(null);

  // 所有片段的球員編號（用於選擇器）
  const [allPlayers, setAllPlayers] = useState<number[]>([]);

  /** 載入精華剪輯 */
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

  /** 載入所有片段以提取球員編號 */
  const fetchAllPlayers = useCallback(async () => {
    try {
      const res = await clipApi.list();
      const clips: Clip[] = res.data;
      const players = Array.from(
        new Set(clips.flatMap((c) => c.player_numbers))
      ).sort((a, b) => a - b);
      setAllPlayers(players);
    } catch {
      /* 靜默處理 */
    }
  }, []);

  useEffect(() => {
    fetchHighlights();
    fetchAllPlayers();
  }, [fetchHighlights, fetchAllPlayers]);

  /** 產出精華剪輯 */
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

  /** 建立分享連結 */
  const handleCreateShare = async (highlightId: number) => {
    try {
      const res = await shareApi.create(highlightId);
      const share: Share = res.data;
      setShares((prev) => ({ ...prev, [highlightId]: share }));
    } catch {
      setError('建立分享連結失敗');
    }
  };

  /** 刪除精華剪輯 */
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

  /** 複製分享連結 */
  const handleCopyLink = (highlightId: number) => {
    const share = shares[highlightId];
    if (!share) return;
    const url = `${window.location.origin}/share/${share.token}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopiedId(highlightId);
      setTimeout(() => setCopiedId(null), 2000);
    });
  };

  /** 切換球員選擇 */
  const togglePlayer = (num: number) => {
    setSelectedPlayers((prev) =>
      prev.includes(num) ? prev.filter((n) => n !== num) : [...prev, num]
    );
  };

  /** 切換分類選擇 */
  const toggleCategory = (value: string) => {
    setSelectedCategories((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    );
  };

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

        {/* 新增精華按鈕 */}
        <div className="mb-6 flex items-center justify-between">
          <span className="text-sm text-gray-500">共 {highlights.length} 部精華剪輯</span>
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

            {/* 球員選擇 */}
            <div className="mb-4">
              <label className="block text-sm text-gray-600 font-medium mb-2">
                選擇球員
              </label>
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

            {/* 標籤分類選擇 */}
            <div className="mb-4">
              <label className="block text-sm text-gray-600 font-medium mb-2">
                選擇標籤分類
              </label>
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
                src={`/api/highlights/${playingHighlight.id}/stream?token=${encodeURIComponent(localStorage.getItem('token') || '')}`}
              />
            </div>
          </div>
        )}

        {/* 精華剪輯列表 */}
        {loading ? (
          <div className="text-center py-12 text-gray-500">載入中...</div>
        ) : highlights.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            尚無精華剪輯，請先產出
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {highlights.map((hl) => (
              <div
                key={hl.id}
                className="rounded-lg bg-white shadow hover:shadow-md transition-shadow overflow-hidden"
              >
                <div className="p-5">
                  <h3 className="font-semibold text-gray-900 truncate mb-2">
                    {hl.title}
                  </h3>

                  {/* 球員 */}
                  {hl.player_numbers.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {hl.player_numbers.map((num) => (
                        <span
                          key={num}
                          className="inline-block rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700"
                        >
                          {num} 號
                        </span>
                      ))}
                    </div>
                  )}

                  {/* 分類標籤 */}
                  {hl.categories.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {hl.categories.map((cat) => (
                        <span
                          key={cat}
                          className="inline-block rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                        >
                          {CATEGORY_OPTIONS.find((o) => o.value === cat)?.label || cat}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="text-xs text-gray-400">
                    {new Date(hl.created_at).toLocaleString('zh-TW')}
                  </div>
                </div>

                {/* 操作列 */}
                <div className="border-t border-gray-100 px-5 py-3 flex items-center justify-between">
                  <button
                    onClick={() => setPlayingHighlight(hl)}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    播放
                  </button>
                  <div className="flex items-center gap-3">
                    <a
                      href={`/api/highlights/${hl.id}/download?token=${encodeURIComponent(localStorage.getItem('token') || '')}`}
                      className="text-sm text-gray-600 hover:text-gray-800 font-medium"
                    >
                      下載
                    </a>
                    {shares[hl.id] ? (
                      <button
                        onClick={() => handleCopyLink(hl.id)}
                        className="text-sm text-green-600 hover:text-green-800 font-medium"
                      >
                        {copiedId === hl.id ? '已複製!' : '複製連結'}
                      </button>
                    ) : (
                      <button
                        onClick={() => handleCreateShare(hl.id)}
                        className="text-sm text-purple-600 hover:text-purple-800 font-medium"
                      >
                        建立分享
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(hl.id)}
                      className="text-sm text-red-500 hover:text-red-700 font-medium"
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
