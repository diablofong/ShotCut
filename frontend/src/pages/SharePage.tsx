import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import VideoPlayer, { type VideoPlayerHandle } from '../components/VideoPlayer';
import axios from 'axios';

interface ShareData {
  id: number;
  highlight_id: number;
  token: string;
  expires_at: string | null;
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
  const [expired, setExpired] = useState(false);
  const playerRef = useRef<VideoPlayerHandle>(null);

  useEffect(() => {
    if (!token) {
      setError('無效的分享連結');
      setLoading(false);
      return;
    }

    const fetchShare = async () => {
      try {
        const res = await axios.get(`/api/shares/${token}`);
        setShareData(res.data);
      } catch (err) {
        if (axios.isAxiosError(err) && err.response?.status === 410) {
          setExpired(true);
        } else {
          setError('此分享連結無效');
        }
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

  if (expired) {
    return (
      <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">ShotCut</h1>
          <div className="rounded-lg bg-gray-800 p-8 max-w-md">
            <svg className="mx-auto h-12 w-12 text-yellow-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-lg font-semibold text-white mb-2">連結已過期</h2>
            <p className="text-gray-400 text-sm">此分享連結已超過有效期限，無法繼續觀看。</p>
          </div>
        </div>
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
      <header className="px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-white">ShotCut</h1>
        </div>
        <div className="text-sm text-gray-400">分享播放</div>
      </header>

      <div className="px-6 pb-4">
        <h2 className="text-xl font-semibold text-white">
          {shareData.highlight.title}
        </h2>
        {shareData.expires_at && (
          <p className="text-xs text-gray-500 mt-1">
            有效期至：{new Date(shareData.expires_at).toLocaleString('zh-TW')}
          </p>
        )}
      </div>

      <div className="flex-1 flex items-start justify-center px-6 pb-8">
        <div className="w-full max-w-4xl">
          <VideoPlayer
            ref={playerRef}
            src={`/api/shares/${token}/stream`}
          />
        </div>
      </div>

      <footer className="px-6 py-4 text-center">
        <p className="text-xs text-gray-500">
          由 ShotCut 籃球影片標記工具產出
        </p>
      </footer>
    </div>
  );
}
