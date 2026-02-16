import { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import type Player from 'video.js/dist/types/player';

/** 標記資料型別 */
export interface Mark {
  id: number;
  time: number;
  label: string;
  category: string;
}

/** 類別對應顏色 */
const CATEGORY_COLORS: Record<string, string> = {
  offense: '#3b82f6',   // 藍
  defense: '#10b981',   // 綠
  highlight: '#f59e0b', // 黃
  turnover: '#ef4444',  // 紅
};

export interface VideoPlayerProps {
  src: string;
  marks?: Mark[];
  onTimeUpdate?: (currentTime: number) => void;
}

export interface VideoPlayerHandle {
  getCurrentTime: () => number;
  seekTo: (time: number) => void;
}

const VideoPlayer = forwardRef<VideoPlayerHandle, VideoPlayerProps>(
  ({ src, marks = [], onTimeUpdate }, ref) => {
    const videoRef = useRef<HTMLDivElement>(null);
    const playerRef = useRef<Player | null>(null);
    const markersRef = useRef<HTMLDivElement>(null);

    useImperativeHandle(ref, () => ({
      getCurrentTime: () => {
        return playerRef.current?.currentTime() ?? 0;
      },
      seekTo: (time: number) => {
        playerRef.current?.currentTime(time);
      },
    }));

    // 初始化 Video.js
    useEffect(() => {
      if (!videoRef.current) return;

      const videoElement = document.createElement('video-js');
      videoElement.classList.add('vjs-big-play-centered', 'vjs-fluid');
      videoRef.current.appendChild(videoElement);

      const player = videojs(videoElement, {
        controls: true,
        autoplay: false,
        preload: 'auto',
        responsive: true,
        fluid: true,
        sources: [{ src, type: 'video/mp4' }],
      });

      player.on('timeupdate', () => {
        const t = player.currentTime() ?? 0;
        onTimeUpdate?.(t);
      });

      playerRef.current = player;

      return () => {
        if (playerRef.current) {
          playerRef.current.dispose();
          playerRef.current = null;
        }
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [src]);

    // 更新 onTimeUpdate 回呼參考
    useEffect(() => {
      const player = playerRef.current;
      if (!player) return;

      const handler = () => {
        const t = player.currentTime() ?? 0;
        onTimeUpdate?.(t);
      };

      player.off('timeupdate');
      player.on('timeupdate', handler);
    }, [onTimeUpdate]);

    // 渲染標記點
    useEffect(() => {
      if (!markersRef.current || !playerRef.current) return;
      const duration = playerRef.current.duration() || 1;

      markersRef.current.innerHTML = '';
      marks.forEach((mark) => {
        const pct = (mark.time / duration) * 100;
        const dot = document.createElement('div');
        dot.title = `${mark.label} (${formatTime(mark.time)})`;
        dot.style.position = 'absolute';
        dot.style.left = `${pct}%`;
        dot.style.top = '0';
        dot.style.width = '8px';
        dot.style.height = '8px';
        dot.style.borderRadius = '50%';
        dot.style.backgroundColor = CATEGORY_COLORS[mark.category] || '#6b7280';
        dot.style.transform = 'translateX(-50%)';
        dot.style.cursor = 'pointer';
        dot.style.zIndex = '10';
        dot.addEventListener('click', () => {
          playerRef.current?.currentTime(mark.time);
        });
        markersRef.current!.appendChild(dot);
      });
    }, [marks]);

    return (
      <div className="relative">
        <div ref={videoRef} />
        {/* 時間軸標記層 */}
        <div
          ref={markersRef}
          className="relative w-full h-3 bg-gray-200 rounded mt-1"
          style={{ position: 'relative' }}
        />
        {/* 圖例 */}
        {marks.length > 0 && (
          <div className="flex gap-4 mt-2 text-xs text-gray-600">
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-blue-500" /> 進攻
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500" /> 防守
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-amber-500" /> 精彩
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-red-500" /> 失誤
            </span>
          </div>
        )}
      </div>
    );
  }
);

VideoPlayer.displayName = 'VideoPlayer';

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default VideoPlayer;
