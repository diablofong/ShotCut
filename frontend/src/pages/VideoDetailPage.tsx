import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { videoApi, analysisApi, markApi, clipApi } from '../services/api';
import VideoPlayer, { type VideoPlayerHandle, type Mark } from '../components/VideoPlayer';

/** 類別選項 */
const CATEGORIES = [
  { value: 'offense', label: '進攻', color: 'bg-blue-500' },
  { value: 'defense', label: '防守', color: 'bg-emerald-500' },
  { value: 'highlight', label: '精彩', color: 'bg-amber-500' },
  { value: 'turnover', label: '失誤', color: 'bg-red-500' },
] as const;

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

interface MarkData {
  id: number;
  video_id: number;
  time: number;
  category: string;
  label: string;
  player_numbers: number[];
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

  // 資料狀態
  const [video, setVideo] = useState<Video | null>(null);
  const [marks, setMarks] = useState<MarkData[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // 新增標記表單
  const [markCategory, setMarkCategory] = useState<string>('highlight');
  const [markLabel, setMarkLabel] = useState('');
  const [playerNumbersInput, setPlayerNumbersInput] = useState('');
  const [startOffset, setStartOffset] = useState(3);
  const [endOffset, setEndOffset] = useState(3);

  // 操作狀態
  const [analyzing, setAnalyzing] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [creatingMark, setCreatingMark] = useState(false);

  // 側面板顯示
  const [sidePanel, setSidePanel] = useState<'candidates' | 'marks'>('marks');

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

  /** 建立標記 */
  const handleCreateMark = async () => {
    const time = playerRef.current?.getCurrentTime() ?? currentTime;
    const playerNumbers = playerNumbersInput
      .split(/[,，\s]+/)
      .map((s) => parseInt(s.trim(), 10))
      .filter((n) => !isNaN(n));

    setCreatingMark(true);
    setError('');
    try {
      await markApi.create(videoId, {
        time,
        category: markCategory,
        label: markLabel || CATEGORIES.find((c) => c.value === markCategory)?.label || '',
        player_numbers: playerNumbers,
        start_offset: startOffset,
        end_offset: endOffset,
      });
      await fetchMarks();
      setMarkLabel('');
      setPlayerNumbersInput('');
    } catch {
      setError('建立標記失敗');
    } finally {
      setCreatingMark(false);
    }
  };

  /** 刪除標記 */
  const handleDeleteMark = async (markId: number) => {
    try {
      await markApi.delete(markId);
      setMarks((prev) => prev.filter((m) => m.id !== markId));
    } catch {
      setError('刪除標記失敗');
    }
  };

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
    playerRef.current?.seekTo(time);
  };

  /** 從候選時間點建立標記 */
  const createMarkFromCandidate = (candidate: Candidate) => {
    seekTo(candidate.time);
    setMarkCategory('highlight');
    setMarkLabel(candidate.type === 'whistle' ? '哨音' : '歡呼');
  };

  // 轉換為 VideoPlayer 元件所需的 marks 格式
  const playerMarks: Mark[] = marks.map((m) => ({
    id: m.id,
    time: m.time,
    label: m.label,
    category: m.category,
  }));

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

  const videoSrc = `/api/videos/${videoId}/stream`;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 頂部導航 */}
      <header className="bg-white shadow">
        <div className="mx-auto max-w-screen-2xl px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-xl font-bold text-gray-900 hover:text-blue-600">
              ShotCut
            </Link>
            <span className="text-gray-400">/</span>
            <Link to="/videos" className="text-gray-600 hover:text-blue-600">影片管理</Link>
            <span className="text-gray-400">/</span>
            <h1 className="text-lg font-semibold text-gray-800 truncate max-w-xs">
              {video.title}
            </h1>
          </div>
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
      </header>

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

      <main className="mx-auto max-w-screen-2xl px-4 py-6">
        <div className="flex gap-6">
          {/* 左側：播放器 + 快速標記 */}
          <div className="flex-1 min-w-0">
            {/* 播放器 */}
            <div className="rounded-lg bg-black overflow-hidden">
              <VideoPlayer
                ref={playerRef}
                src={videoSrc}
                marks={playerMarks}
                onTimeUpdate={setCurrentTime}
              />
            </div>

            {/* 目前時間顯示 */}
            <div className="mt-2 text-sm text-gray-500">
              目前時間：{formatTime(currentTime)}
            </div>

            {/* 快速標記面板 */}
            <div className="mt-4 rounded-lg bg-white p-5 shadow">
              <h3 className="text-base font-semibold mb-3">快速標記</h3>

              {/* 分類按鈕 */}
              <div className="flex gap-2 mb-3">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat.value}
                    onClick={() => setMarkCategory(cat.value)}
                    className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                      markCategory === cat.value
                        ? `${cat.color} text-white shadow-sm`
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>

              {/* 標籤 */}
              <div className="mb-3">
                <label className="block text-sm text-gray-600 mb-1">標籤（選填）</label>
                <input
                  type="text"
                  value={markLabel}
                  onChange={(e) => setMarkLabel(e.target.value)}
                  placeholder="例：三分球、快攻..."
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              {/* 球員編號 */}
              <div className="mb-3">
                <label className="block text-sm text-gray-600 mb-1">球員編號（多個以逗號分隔）</label>
                <input
                  type="text"
                  value={playerNumbersInput}
                  onChange={(e) => setPlayerNumbersInput(e.target.value)}
                  placeholder="例：7, 11, 23"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              {/* 時間範圍 */}
              <div className="flex gap-4 mb-4">
                <div className="flex-1">
                  <label className="block text-sm text-gray-600 mb-1">前 N 秒</label>
                  <input
                    type="number"
                    min={0}
                    max={30}
                    value={startOffset}
                    onChange={(e) => setStartOffset(Number(e.target.value))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-sm text-gray-600 mb-1">後 N 秒</label>
                  <input
                    type="number"
                    min={0}
                    max={30}
                    value={endOffset}
                    onChange={(e) => setEndOffset(Number(e.target.value))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* 建立標記按鈕 */}
              <button
                onClick={handleCreateMark}
                disabled={creatingMark}
                className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {creatingMark ? '建立中...' : `在 ${formatTime(currentTime)} 建立標記`}
              </button>
            </div>
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
              <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto">
                {marks.length === 0 ? (
                  <div className="text-center py-8 text-sm text-gray-400">
                    尚無標記，在播放時點擊「建立標記」
                  </div>
                ) : (
                  [...marks]
                    .sort((a, b) => a.time - b.time)
                    .map((mark) => {
                      const cat = CATEGORIES.find((c) => c.value === mark.category);
                      return (
                        <div
                          key={mark.id}
                          className="rounded-lg bg-white p-3 shadow-sm hover:shadow transition-shadow cursor-pointer"
                          onClick={() => seekTo(mark.time)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span
                                className={`inline-block w-2.5 h-2.5 rounded-full ${cat?.color || 'bg-gray-400'}`}
                              />
                              <span className="text-sm font-medium">{mark.label}</span>
                            </div>
                            <span className="text-xs text-gray-400 font-mono">
                              {formatTime(mark.time)}
                            </span>
                          </div>
                          {mark.player_numbers.length > 0 && (
                            <div className="mt-1 text-xs text-gray-500">
                              球員：{mark.player_numbers.join(', ')} 號
                            </div>
                          )}
                          <div className="mt-1 flex items-center justify-between">
                            <span className="text-xs text-gray-400">
                              範圍：前 {mark.start_offset}s / 後 {mark.end_offset}s
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
                          建立標記
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
