import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { shareApi } from '../services/api';
import VideoPlayer, { type VideoPlayerHandle } from '../components/VideoPlayer';

interface ShareData {
  id: number;
  highlight_id: number;
  token: string;
  highlight: {
    id: number;
    title: string;
    file_path: string;
  };
}

export default function SharePage() {
  const { token } = useParams<{ token: string }>();
  const [shareData, setShareData] = useState<ShareData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const playerRef = useRef<VideoPlayerHandle>(null);

  useEffect(() => {
    if (!token) {
      setError('無效的分享連結');
      setLoading(false);
      return;
    }

    const fetchShare = async () => {
      try {
        const res = await shareApi.get(token);
        setShareData(res.data);
      } catch {
        setError('此分享連結無效或已過期');
      } finally {
        setLoading(false);
      }
    };

    fetchShare();
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <span className="text-gray-400">載入中...</span>
      </div>
    );
  }

  if (error || !shareData) {
    return (
      <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-2">ShotCut</h1>
          <p className="text-red-400 text-sm">{error || '無法載入分享內容'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      {/* 簡潔頂部 */}
      <header className="px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-white">ShotCut</h1>
        </div>
        <div className="text-sm text-gray-400">分享播放</div>
      </header>

      {/* 影片標題 */}
      <div className="px-6 pb-4">
        <h2 className="text-xl font-semibold text-white">
          {shareData.highlight.title}
        </h2>
      </div>

      {/* 播放器 */}
      <div className="flex-1 flex items-start justify-center px-6 pb-8">
        <div className="w-full max-w-4xl">
          <VideoPlayer
            ref={playerRef}
            src={`/api/highlights/${shareData.highlight_id}/stream`}
          />
        </div>
      </div>

      {/* 底部 */}
      <footer className="px-6 py-4 text-center">
        <p className="text-xs text-gray-500">
          由 ShotCut 籃球影片標記工具產出
        </p>
      </footer>
    </div>
  );
}
