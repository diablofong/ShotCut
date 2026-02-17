import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { videoApi, analysisApi, markApi, clipApi } from '../services/api';
import VideoPlayer, { type VideoPlayerHandle, type Mark } from '../components/VideoPlayer';
import Navbar from '../components/Navbar';

/** 類別選項（3 類） */
const CATEGORIES = [
  { value: 'offense', label: '進攻', color: 'bg-blue-500', toastBg: 'bg-blue-600', lightBg: 'bg-blue-50', borderColor: 'border-blue-400' },
  { value: 'defense', label: '防守', color: 'bg-emerald-500', toastBg: 'bg-emerald-600', lightBg: 'bg-emerald-50', borderColor: 'border-emerald-400' },
  { value: 'turnover', label: '失誤', color: 'bg-red-500', toastBg: 'bg-red-600', lightBg: 'bg-red-50', borderColor: 'border-red-400' },
] as const;

const CATEGORY_BORDER: Record<string, string> = {
  offense: 'border-l-blue-500',
  defense: 'border-l-emerald-500',
  turnover: 'border-l-red-500',
};

interface Video {
  id: number;
  title: string;
  source: string;
  status: string;
  duration: number | null;
  file_path: string;
}

interface Candidate {
  id: number;
  time: number;
  type: string;
  confidence: number;
}

interface PlayerInfo {
  number: number;
  name: string;
}

interface MarkData {
  id: number;
  video_id: number;
  time: number;
  start_time: number;
  end_time: number;
  category: string;
  label: string;
  player_numbers: number[];
  players: PlayerInfo[];
  start_offset: number;
  end_offset: number;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function VideoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const videoId = Number(id);
  const playerRef = useRef<VideoPlayerHandle>(null);
  const markListRef = useRef<HTMLDivElement>(null);

  // 資料狀態
  const [video, setVideo] = useState<Video | null>(null);
  const [marks, setMarks] = useState<MarkData[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // 錄製模式狀態
  const [recording, setRecording] = useState<{
    category: string;
    label: string;
    startTime: number;
  } | null>(null);

  // 操作狀態
  const [analyzing, setAnalyzing] = useState(false);
  const [extracting, setExtracting] = useState(false);

  // 標記編輯狀態
  const [editingMarkId, setEditingMarkId] = useState<number | null>(null);
  const [editStartTime, setEditStartTime] = useState(0);
  const [editEndTime, setEditEndTime] = useState(0);
  const [editCategory, setEditCategory] = useState('offense');
  const [editLabel, setEditLabel] = useState('');
  const [editPlayers, setEditPlayers] = useState('');
  const [savingMark, setSavingMark] = useState(false);

  // 側面板顯示
  const [sidePanel, setSidePanel] = useState<'candidates' | 'marks'>('marks');

  // Toast 提示（帶類別顏色）
  const [toast, setToast] = useState<{ message: string; category?: string } | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  /** 載入影片資料 */
  const fetchVideo = useCallback(async () => {
    try {
      const res = await videoApi.get(videoId);
      setVideo(res.data);
    } catch {
      setError('無法載入影片資料');
    } finally {
      setLoading(false);
    }
  }, [videoId]);

  /** 載入標記 */
  const fetchMarks = useCallback(async () => {
    try {
      const res = await markApi.list(videoId);
      setMarks(res.data);
    } catch {
      /* 靜默處理 */
    }
  }, [videoId]);

  /** 載入候選時間點 */
  const fetchCandidates = useCallback(async () => {
    try {
      const res = await analysisApi.candidates(videoId);
      setCandidates(res.data);
    } catch {
      /* 靜默處理 */
    }
  }, [videoId]);

  useEffect(() => {
    fetchVideo();
    fetchMarks();
    fetchCandidates();
  }, [fetchVideo, fetchMarks, fetchCandidates]);

  /** 顯示 toast 提示 */
  const showToast = useCallback((msg: string, category?: string) => {
    setToast({ message: msg, category });
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 2500);
  }, []);

  /** 鍵盤快捷鍵：1=進攻 2=防守 3=失誤，Esc=結束錄製 */
  const SHORTCUT_MAP: Record<string, (typeof CATEGORIES)[number]> = {
    '1': CATEGORIES[0],
    '2': CATEGORIES[1],
    '3': CATEGORIES[2],
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

      // Esc：結束錄製
      if (e.key === 'Escape' && recording) {
        e.preventDefault();
        finishRecording();
        return;
      }

      // 1-3：開始錄製
      const cat = SHORTCUT_MAP[e.key];
      if (!cat) return;
      e.preventDefault();

      if (recording) return; // 已在錄製中，忽略

      const time = playerRef.current?.getCurrentTime() ?? currentTime;
      playerRef.current?.pause();
      setRecording({ category: cat.value, label: cat.label, startTime: time });
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recording, currentTime]);

  /** 結束錄製並建立標記 */
  const finishRecording = useCallback(async () => {
    if (!recording) return;
    const endTime = playerRef.current?.getCurrentTime() ?? currentTime;
    playerRef.current?.pause();

    const startTime = recording.startTime;
    const cat = CATEGORIES.find((c) => c.value === recording.category);
    const label = recording.label;

    // 確保 endTime > startTime
    const actualStart = Math.min(startTime, endTime);
    const actualEnd = Math.max(startTime, endTime);

    if (actualEnd - actualStart < 0.5) {
      showToast('標記時間太短（至少 0.5 秒）', 'error');
      setRecording(null);
      return;
    }

    try {
      await markApi.create(videoId, {
        start_time: actualStart,
        end_time: actualEnd,
        category: recording.category,
        label,
        player_numbers: [],
      });
      await fetchMarks();
      showToast(
        `${cat?.label || label} 標記完成 (${formatTime(actualStart)} ~ ${formatTime(actualEnd)})`,
        recording.category,
      );
    } catch {
      showToast('標記建立失敗', 'error');
    }
    setRecording(null);
  }, [recording, currentTime, videoId, fetchMarks, showToast]);

  /** 取消錄製 */
  const cancelRecording = useCallback(() => {
    setRecording(null);
  }, []);

  /** 觸發音訊分析 */
  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError('');
    try {
      await analysisApi.analyze(videoId);
      await fetchCandidates();
      setSidePanel('candidates');
    } catch {
      setError('音訊分析失敗');
    } finally {
      setAnalyzing(false);
    }
  };

  /** 開始編輯標記 */
  const startEditMark = (mark: MarkData) => {
    setEditingMarkId(mark.id);
    setEditStartTime(mark.start_time);
    setEditEndTime(mark.end_time);
    setEditCategory(mark.category);
    setEditLabel(mark.label);
    const playersStr = (mark.players ?? []).map((p) =>
      p.name ? `${p.number} ${p.name}` : `${p.number}`
    ).join(', ');
    setEditPlayers(playersStr || mark.player_numbers.join(', '));
  };

  /** 取消編輯 */
  const cancelEditMark = () => {
    setEditingMarkId(null);
  };

  /** 解析球員輸入字串（如 "7 林書豪, 11 王大明" 或 "7, 11"） */
  const parsePlayers = (input: string): PlayerInfo[] => {
    if (!input.trim()) return [];
    return input.split(/[,，]/).map((part) => {
      const trimmed = part.trim();
      const match = trimmed.match(/^(\d+)\s*(.*)/);
      if (match) {
        return { number: parseInt(match[1], 10), name: match[2].trim() };
      }
      return null;
    }).filter((p): p is PlayerInfo => p !== null && !isNaN(p.number));
  };

  /** 儲存標記修改 */
  const handleUpdateMark = async () => {
    if (editingMarkId === null) return;
    const players = parsePlayers(editPlayers);

    setSavingMark(true);
    try {
      await markApi.update(editingMarkId, {
        start_time: editStartTime,
        end_time: editEndTime,
        category: editCategory,
        label: editLabel,
        players,
      });
      await fetchMarks();
      setEditingMarkId(null);
      showToast('標記已更新');
    } catch {
      setError('更新標記失敗');
    } finally {
      setSavingMark(false);
    }
  };

  /** 刪除標記 */
  const handleDeleteMark = async (markId: number) => {
    try {
      await markApi.delete(markId);
      setMarks((prev) => prev.filter((m) => m.id !== markId));
      if (editingMarkId === markId) setEditingMarkId(null);
    } catch {
      setError('刪除標記失敗');
    }
  };

  /** 色塊拖曳微調回呼 */
  const handleMarkUpdate = useCallback(async (markId: number, startTime: number, endTime: number) => {
    try {
      await markApi.update(markId, { start_time: startTime, end_time: endTime });
      await fetchMarks();
    } catch {
      setError('更新標記失敗');
    }
  }, [fetchMarks]);

  /** 批次擷取片段 */
  const handleExtractClips = async () => {
    setExtracting(true);
    setError('');
    try {
      await clipApi.extract(videoId);
      alert('片段擷取已開始，請前往「片段管理」查看結果');
    } catch {
      setError('擷取片段失敗');
    } finally {
      setExtracting(false);
    }
  };

  /** 跳轉到指定時間 */
  const seekTo = (time: number) => {
    playerRef.current?.seekTo(Math.max(0, time));
  };

  /** 從候選時間點建立標記 */
  const createMarkFromCandidate = (candidate: Candidate) => {
    seekTo(candidate.time);
  };

  // 轉換為 VideoPlayer 元件所需的 marks 格式
  const playerMarks: Mark[] = marks.map((m) => ({
    id: m.id,
    time: m.time,
    start_time: m.start_time,
    end_time: m.end_time,
    label: m.label,
    category: m.category,
  }));

  // 計算目前播放中的 Active 標記
  const activeMarkId = useMemo(() => {
    return marks.find((m) => {
      return currentTime >= m.start_time && currentTime <= m.end_time;
    })?.id ?? null;
  }, [marks, currentTime]);

  // Active 標記自動捲動到視野
  useEffect(() => {
    if (activeMarkId === null || !markListRef.current) return;
    const el = markListRef.current.querySelector(`[data-mark-id="${activeMarkId}"]`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [activeMarkId]);

  // 錄製中的分類資訊
  const recordingCat = recording ? CATEGORIES.find((c) => c.value === recording.category) : null;

  // Toast 背景色
  const toastBg = toast?.category
    ? CATEGORIES.find((c) => c.value === toast.category)?.toastBg || (toast.category === 'error' ? 'bg-red-800' : 'bg-gray-900')
    : 'bg-gray-900';

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <span className="text-gray-500">載入中...</span>
      </div>
    );
  }

  if (!video) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <span className="text-red-500">找不到影片</span>
      </div>
    );
  }

  const token = localStorage.getItem('token') || '';
  const videoSrc = `/api/videos/${videoId}/stream?token=${encodeURIComponent(token)}`;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      {/* 影片操作列 */}
      <div className="bg-white border-b">
        <div className="mx-auto max-w-screen-2xl px-4 py-2 flex items-center justify-between">
          <h1 className="text-base font-semibold text-gray-800 truncate max-w-md">
            {video.title}
          </h1>
          <div className="flex gap-2">
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
            >
              {analyzing ? '分析中...' : '音訊分析'}
            </button>
            <button
              onClick={handleExtractClips}
              disabled={extracting || marks.length === 0}
              className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              {extracting ? '擷取中...' : '批次擷取片段'}
            </button>
          </div>
        </div>
      </div>

      {/* 錯誤提示 */}
      {error && (
        <div className="mx-auto max-w-screen-2xl px-4 mt-4">
          <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
            <button className="ml-2 font-medium underline" onClick={() => setError('')}>
              關閉
            </button>
          </div>
        </div>
      )}

      {/* Toast 提示（帶類別顏色） */}
      {toast && (
        <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50 animate-fade-in">
          <div className={`rounded-lg px-5 py-3 text-sm text-white shadow-lg flex items-center gap-2 ${toastBg}`}>
            {toast.message}
          </div>
        </div>
      )}

      <main className="mx-auto max-w-screen-2xl px-4 py-6">
        <div className="flex gap-6">
          {/* 左側：播放器 + 快捷列 */}
          <div className="flex-1 min-w-0">
            {/* 播放器 */}
            <div className="rounded-lg bg-black overflow-hidden">
              <VideoPlayer
                ref={playerRef}
                src={videoSrc}
                marks={playerMarks}
                currentTime={currentTime}
                onTimeUpdate={setCurrentTime}
                onMarkUpdate={handleMarkUpdate}
                recording={recording ? { startTime: recording.startTime, category: recording.category } : null}
              />
            </div>

            {/* 快捷列 */}
            {recording ? (
              /* 錄製中 */
              <div className={`mt-3 rounded-lg px-4 py-3 shadow flex items-center gap-3 flex-wrap ${recordingCat?.lightBg || 'bg-white'} border ${recordingCat?.borderColor || 'border-gray-200'}`}>
                <span className="flex items-center gap-2">
                  <span className="relative flex h-3 w-3">
                    <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${recordingCat?.color || 'bg-gray-500'}`}></span>
                    <span className={`relative inline-flex rounded-full h-3 w-3 ${recordingCat?.color || 'bg-gray-500'}`}></span>
                  </span>
                  <span className="text-sm font-semibold">{recordingCat?.label} 標記中</span>
                </span>

                <span className="text-sm text-gray-600">
                  起點 <span className="font-mono font-medium">{formatTime(recording.startTime)}</span>
                </span>
                <span className="text-gray-400">→</span>
                <span className="text-sm text-gray-600">
                  目前 <span className="font-mono font-medium">{formatTime(currentTime)}</span>
                </span>

                <span className="text-xs text-gray-400 ml-1">
                  ({Math.max(0, Math.round(currentTime - recording.startTime))} 秒)
                </span>

                <div className="ml-auto flex gap-2">
                  <button
                    onClick={finishRecording}
                    className="rounded-lg bg-gray-800 px-3 py-2 text-sm font-medium text-white hover:bg-gray-900"
                  >
                    <kbd className="inline-block bg-white/20 rounded px-1.5 py-0.5 text-xs font-bold mr-1.5">Esc</kbd>
                    結束標記
                  </button>
                  <button
                    onClick={cancelRecording}
                    className="rounded-lg bg-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-300"
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              /* 未錄製 */
              <div className="mt-3 rounded-lg bg-white px-4 py-3 shadow flex items-center gap-3 flex-wrap">
                <span className="text-sm font-mono text-gray-700 bg-gray-100 rounded px-2 py-1 min-w-[3.5rem] text-center">
                  {formatTime(currentTime)}
                </span>

                {CATEGORIES.map((cat, index) => (
                  <button
                    key={cat.value}
                    onClick={() => {
                      const time = playerRef.current?.getCurrentTime() ?? currentTime;
                      playerRef.current?.pause();
                      setRecording({ category: cat.value, label: cat.label, startTime: time });
                    }}
                    className={`rounded-lg px-3 py-2 text-sm font-medium transition-all ${cat.color} text-white hover:opacity-90 active:scale-95`}
                    title={`按 ${index + 1} 開始標記${cat.label}`}
                  >
                    <kbd className="inline-block bg-white/30 rounded px-1.5 py-0.5 text-xs font-bold mr-1.5">
                      {index + 1}
                    </kbd>
                    {cat.label}
                  </button>
                ))}

                <span className="ml-auto text-xs text-gray-400">
                  按數字鍵開始標記，Esc 結束
                </span>
              </div>
            )}
          </div>

          {/* 右側面板 */}
          <div className="w-80 shrink-0">
            {/* 面板切換 */}
            <div className="flex rounded-lg bg-gray-200 p-1 mb-4">
              <button
                onClick={() => setSidePanel('marks')}
                className={`flex-1 rounded-md py-2 text-sm font-medium transition-all ${
                  sidePanel === 'marks'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                標記 ({marks.length})
              </button>
              <button
                onClick={() => setSidePanel('candidates')}
                className={`flex-1 rounded-md py-2 text-sm font-medium transition-all ${
                  sidePanel === 'candidates'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                候選點 ({candidates.length})
              </button>
            </div>

            {/* 標記列表 */}
            {sidePanel === 'marks' && (
              <div ref={markListRef} className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto">
                {marks.length === 0 ? (
                  <div className="text-center py-8 text-sm text-gray-400">
                    尚無標記<br />
                    <span className="text-xs">播放影片時按 <kbd className="bg-gray-200 rounded px-1.5 py-0.5 mx-0.5">1</kbd>~<kbd className="bg-gray-200 rounded px-1.5 py-0.5 mx-0.5">3</kbd> 開始標記</span>
                  </div>
                ) : (
                  [...marks]
                    .sort((a, b) => a.start_time - b.start_time)
                    .map((mark) => {
                      const cat = CATEGORIES.find((c) => c.value === mark.category);
                      const isEditing = editingMarkId === mark.id;
                      const isActive = activeMarkId === mark.id;
                      const duration = Math.round(mark.end_time - mark.start_time);
                      return (
                        <div
                          key={mark.id}
                          data-mark-id={mark.id}
                          className={`rounded-lg bg-white shadow-sm transition-all group ${
                            isEditing
                              ? 'ring-2 ring-blue-400'
                              : isActive
                                ? `border-l-4 ${CATEGORY_BORDER[mark.category] || 'border-l-gray-400'} bg-gray-50 shadow`
                                : 'hover:shadow hover:bg-gray-50 cursor-pointer'
                          }`}
                        >
                          {/* 卡片摘要 */}
                          <div
                            className="p-3 relative"
                            onClick={() => isEditing ? undefined : seekTo(mark.start_time)}
                          >
                            {/* Hover 播放圖示 */}
                            {!isEditing && (
                              <div className="absolute right-3 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M6.3 2.841A1.5 1.5 0 004 4.11v11.78a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                                </svg>
                              </div>
                            )}
                            <div className="flex items-center justify-between pr-6">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`inline-block w-2.5 h-2.5 rounded-sm ${cat?.color || 'bg-gray-400'}`}
                                />
                                <span className="text-sm font-medium">{mark.label}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-400 font-mono">
                                  {formatTime(mark.start_time)} ~ {formatTime(mark.end_time)}
                                </span>
                                <span className="text-xs text-gray-300">
                                  ({duration}秒)
                                </span>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    isEditing ? cancelEditMark() : startEditMark(mark);
                                  }}
                                  className={`text-xs font-medium ${isEditing ? 'text-gray-500 hover:text-gray-700' : 'text-blue-500 hover:text-blue-700'}`}
                                >
                                  {isEditing ? '收合' : '編輯'}
                                </button>
                              </div>
                            </div>
                            {((mark.players ?? []).length > 0 || mark.player_numbers.length > 0) && (
                              <div className="mt-1 text-xs text-gray-500">
                                球員：{(mark.players ?? []).length > 0
                                  ? mark.players.map((p) => p.name ? `${p.number} ${p.name}` : `${p.number} 號`).join(', ')
                                  : mark.player_numbers.map((n) => `${n} 號`).join(', ')}
                              </div>
                            )}
                            {!isEditing && (
                              <div className="mt-1 flex items-center justify-between">
                                <span className="text-xs text-gray-400">
                                  {isActive && <span className="text-emerald-500 font-medium mr-1">播放中</span>}
                                </span>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeleteMark(mark.id);
                                  }}
                                  className="text-xs text-red-500 hover:text-red-700"
                                >
                                  刪除
                                </button>
                              </div>
                            )}
                          </div>

                          {/* 展開編輯表單 */}
                          {isEditing && (
                            <div className="border-t border-gray-100 p-3 space-y-3">
                              {/* 分類 */}
                              <div className="flex gap-1.5">
                                {CATEGORIES.map((c) => (
                                  <button
                                    key={c.value}
                                    onClick={() => setEditCategory(c.value)}
                                    className={`rounded px-2.5 py-1 text-xs font-medium transition-all ${
                                      editCategory === c.value
                                        ? `${c.color} text-white`
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                    }`}
                                  >
                                    {c.label}
                                  </button>
                                ))}
                              </div>

                              {/* 標籤 */}
                              <div>
                                <label className="block text-xs text-gray-500 mb-1">標籤</label>
                                <input
                                  type="text"
                                  value={editLabel}
                                  onChange={(e) => setEditLabel(e.target.value)}
                                  className="w-full rounded border border-gray-300 px-2.5 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                />
                              </div>

                              {/* 起點 / 終點 */}
                              <div className="flex gap-3">
                                <div className="flex-1">
                                  <label className="block text-xs text-gray-500 mb-1">起點（秒）</label>
                                  <input
                                    type="number"
                                    step="0.1"
                                    min={0}
                                    value={editStartTime}
                                    onChange={(e) => setEditStartTime(Number(e.target.value))}
                                    className="w-full rounded border border-gray-300 px-2.5 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                  />
                                </div>
                                <div className="flex-1">
                                  <label className="block text-xs text-gray-500 mb-1">終點（秒）</label>
                                  <input
                                    type="number"
                                    step="0.1"
                                    min={0}
                                    value={editEndTime}
                                    onChange={(e) => setEditEndTime(Number(e.target.value))}
                                    className="w-full rounded border border-gray-300 px-2.5 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                  />
                                </div>
                              </div>

                              {/* 球員 */}
                              <div>
                                <label className="block text-xs text-gray-500 mb-1">球員（號碼 名字，逗號分隔）</label>
                                <input
                                  type="text"
                                  value={editPlayers}
                                  onChange={(e) => setEditPlayers(e.target.value)}
                                  placeholder="例：7 林書豪, 11 王大明"
                                  className="w-full rounded border border-gray-300 px-2.5 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                />
                              </div>

                              {/* 操作按鈕 */}
                              <div className="flex gap-2">
                                <button
                                  onClick={handleUpdateMark}
                                  disabled={savingMark}
                                  className="flex-1 rounded bg-blue-600 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                                >
                                  {savingMark ? '儲存中...' : '儲存'}
                                </button>
                                <button
                                  onClick={() => handleDeleteMark(mark.id)}
                                  className="rounded bg-red-50 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-100"
                                >
                                  刪除
                                </button>
                                <button
                                  onClick={cancelEditMark}
                                  className="rounded bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-200"
                                >
                                  取消
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })
                )}
              </div>
            )}

            {/* 候選時間點列表 */}
            {sidePanel === 'candidates' && (
              <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto">
                {candidates.length === 0 ? (
                  <div className="text-center py-8 text-sm text-gray-400">
                    尚無候選時間點，請先執行音訊分析
                  </div>
                ) : (
                  candidates.map((c) => (
                    <div
                      key={c.id}
                      className="rounded-lg bg-white p-3 shadow-sm hover:shadow transition-shadow cursor-pointer"
                      onClick={() => seekTo(c.time)}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">
                          {c.type === 'whistle' ? '哨音' : c.type === 'cheer' ? '歡呼' : c.type}
                        </span>
                        <span className="text-xs text-gray-400 font-mono">
                          {formatTime(c.time)}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center justify-between">
                        <span className="text-xs text-gray-500">
                          信心度：{(c.confidence * 100).toFixed(0)}%
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            createMarkFromCandidate(c);
                          }}
                          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                        >
                          跳轉
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
