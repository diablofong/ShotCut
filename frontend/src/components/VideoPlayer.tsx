import { useEffect, useRef, useImperativeHandle, forwardRef, useCallback } from 'react';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import type Player from 'video.js/dist/types/player';

/** 標記資料型別 */
export interface Mark {
  id: number;
  time: number;
  start_time: number;
  end_time: number;
  label: string;
  category: string;
}

/** 類別對應顏色 */
const CATEGORY_COLORS: Record<string, string> = {
  offense: '#3b82f6',   // 藍
  defense: '#10b981',   // 綠
  turnover: '#ef4444',  // 紅
};

export interface VideoPlayerProps {
  src: string;
  marks?: Mark[];
  currentTime?: number;
  autoplay?: boolean;
  onTimeUpdate?: (currentTime: number) => void;
  onMarkUpdate?: (markId: number, startTime: number, endTime: number) => void;
  recording?: { startTime: number; category: string } | null;
}

export interface VideoPlayerHandle {
  getCurrentTime: () => number;
  seekTo: (time: number) => void;
  pause: () => void;
  play: () => void;
}

const VideoPlayer = forwardRef<VideoPlayerHandle, VideoPlayerProps>(
  ({ src, marks = [], currentTime = 0, autoplay = false, onTimeUpdate, onMarkUpdate, recording }, ref) => {
    const videoRef = useRef<HTMLDivElement>(null);
    const playerRef = useRef<Player | null>(null);
    const markersRef = useRef<HTMLDivElement>(null);
    const playheadRef = useRef<HTMLDivElement>(null);
    const tooltipRef = useRef<HTMLDivElement>(null);
    const recordingBlockRef = useRef<HTMLDivElement>(null);
    const dragRef = useRef<{
      markId: number;
      edge: 'left' | 'right';
      startTime: number;
      endTime: number;
    } | null>(null);

    useImperativeHandle(ref, () => ({
      getCurrentTime: () => {
        return playerRef.current?.currentTime() ?? 0;
      },
      seekTo: (time: number) => {
        playerRef.current?.currentTime(time);
      },
      pause: () => {
        playerRef.current?.pause();
      },
      play: () => {
        playerRef.current?.play();
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
        autoplay,
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

    // 渲染標記色塊
    useEffect(() => {
      if (!markersRef.current || !playerRef.current) return;
      const duration = playerRef.current.duration() || 1;

      // 清除舊色塊
      const children = markersRef.current.querySelectorAll('.mark-block');
      children.forEach((c) => c.remove());

      marks.forEach((mark) => {
        const startPct = (mark.start_time / duration) * 100;
        const endPct = (mark.end_time / duration) * 100;
        const width = Math.max(endPct - startPct, 0.5);
        const color = CATEGORY_COLORS[mark.category] || '#6b7280';

        // 主色塊
        const block = document.createElement('div');
        block.className = 'mark-block';
        block.title = `${mark.label} (${formatTime(mark.start_time)} ~ ${formatTime(mark.end_time)})`;
        block.style.cssText = `
          position: absolute; left: ${startPct}%; width: ${width}%;
          height: 100%; background-color: ${color}80; border-radius: 2px;
          cursor: pointer; z-index: 5; transition: background-color 0.15s ease;
        `;

        block.addEventListener('mouseenter', () => {
          block.style.backgroundColor = `${color}cc`;
        });
        block.addEventListener('mouseleave', () => {
          block.style.backgroundColor = `${color}80`;
        });
        block.addEventListener('click', (e) => {
          e.stopPropagation();
          playerRef.current?.currentTime(mark.start_time);
        });

        // 左拖曳把手
        if (onMarkUpdate) {
          const leftHandle = document.createElement('div');
          leftHandle.style.cssText = `
            position: absolute; left: 0; top: 0; width: 6px; height: 100%;
            cursor: ew-resize; z-index: 15; border-radius: 2px 0 0 2px;
          `;
          leftHandle.addEventListener('mouseenter', () => {
            leftHandle.style.backgroundColor = `${color}`;
          });
          leftHandle.addEventListener('mouseleave', () => {
            if (!dragRef.current) leftHandle.style.backgroundColor = '';
          });
          leftHandle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            e.preventDefault();
            dragRef.current = { markId: mark.id, edge: 'left', startTime: mark.start_time, endTime: mark.end_time };
          });
          block.appendChild(leftHandle);

          // 右拖曳把手
          const rightHandle = document.createElement('div');
          rightHandle.style.cssText = `
            position: absolute; right: 0; top: 0; width: 6px; height: 100%;
            cursor: ew-resize; z-index: 15; border-radius: 0 2px 2px 0;
          `;
          rightHandle.addEventListener('mouseenter', () => {
            rightHandle.style.backgroundColor = `${color}`;
          });
          rightHandle.addEventListener('mouseleave', () => {
            if (!dragRef.current) rightHandle.style.backgroundColor = '';
          });
          rightHandle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            e.preventDefault();
            dragRef.current = { markId: mark.id, edge: 'right', startTime: mark.start_time, endTime: mark.end_time };
          });
          block.appendChild(rightHandle);
        }

        markersRef.current!.appendChild(block);
      });
    }, [marks, onMarkUpdate]);

    // 拖曳事件處理（全域 mousemove/mouseup）
    useEffect(() => {
      const handleMouseMove = (e: MouseEvent) => {
        if (!dragRef.current || !markersRef.current || !playerRef.current || !tooltipRef.current) return;
        const rect = markersRef.current.getBoundingClientRect();
        const pct = Math.max(0, Math.min((e.clientX - rect.left) / rect.width, 1));
        const duration = playerRef.current.duration() || 1;
        const time = pct * duration;

        tooltipRef.current.textContent = formatTime(time);
        tooltipRef.current.style.left = `${pct * 100}%`;
        tooltipRef.current.style.display = 'block';

        if (dragRef.current.edge === 'left') {
          dragRef.current.startTime = Math.min(time, dragRef.current.endTime - 0.5);
        } else {
          dragRef.current.endTime = Math.max(time, dragRef.current.startTime + 0.5);
        }
      };

      const handleMouseUp = () => {
        if (!dragRef.current) return;
        const { markId, startTime, endTime } = dragRef.current;
        dragRef.current = null;
        if (tooltipRef.current) tooltipRef.current.style.display = 'none';
        onMarkUpdate?.(markId, startTime, endTime);
      };

      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }, [onMarkUpdate]);

    // 更新播放位置指示器
    useEffect(() => {
      if (!playheadRef.current || !playerRef.current) return;
      const duration = playerRef.current.duration() || 1;
      const pct = Math.min((currentTime / duration) * 100, 100);
      playheadRef.current.style.left = `${pct}%`;
    }, [currentTime]);

    // 錄製中動態色塊
    useEffect(() => {
      if (!recordingBlockRef.current || !playerRef.current) return;
      if (!recording) {
        recordingBlockRef.current.style.display = 'none';
        return;
      }
      const duration = playerRef.current.duration() || 1;
      const startPct = (recording.startTime / duration) * 100;
      const currentPct = (currentTime / duration) * 100;
      const width = Math.max(currentPct - startPct, 0.3);
      const color = CATEGORY_COLORS[recording.category] || '#6b7280';

      recordingBlockRef.current.style.display = 'block';
      recordingBlockRef.current.style.left = `${startPct}%`;
      recordingBlockRef.current.style.width = `${width}%`;
      recordingBlockRef.current.style.backgroundColor = `${color}60`;
      recordingBlockRef.current.style.borderColor = color;
    }, [recording, currentTime]);

    // 時間軸點擊跳轉
    const handleTimelineClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
      if (!markersRef.current || !playerRef.current) return;
      const rect = markersRef.current.getBoundingClientRect();
      const pct = Math.max(0, Math.min((e.clientX - rect.left) / rect.width, 1));
      const duration = playerRef.current.duration() || 1;
      playerRef.current.currentTime(pct * duration);
    }, []);

    // 時間軸 hover tooltip
    const handleTimelineMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
      if (!markersRef.current || !playerRef.current || !tooltipRef.current) return;
      if (dragRef.current) return; // 拖曳中由拖曳邏輯控制 tooltip
      const rect = markersRef.current.getBoundingClientRect();
      const pct = Math.max(0, Math.min((e.clientX - rect.left) / rect.width, 1));
      const duration = playerRef.current.duration() || 1;
      const time = pct * duration;
      tooltipRef.current.textContent = formatTime(time);
      tooltipRef.current.style.left = `${pct * 100}%`;
      tooltipRef.current.style.display = 'block';
    }, []);

    const handleTimelineMouseLeave = useCallback(() => {
      if (tooltipRef.current && !dragRef.current) {
        tooltipRef.current.style.display = 'none';
      }
    }, []);

    return (
      <div className="relative">
        <div ref={videoRef} />
        {/* 時間軸標記層（可點擊） */}
        <div
          ref={markersRef}
          className="relative w-full h-5 bg-gray-200 rounded mt-1 cursor-pointer"
          onClick={handleTimelineClick}
          onMouseMove={handleTimelineMouseMove}
          onMouseLeave={handleTimelineMouseLeave}
        >
          {/* 錄製中動態色塊 */}
          <div
            ref={recordingBlockRef}
            className="absolute top-0 h-full rounded pointer-events-none z-8 border-2 border-dashed"
            style={{ display: 'none' }}
          />
          {/* 播放位置指示器 */}
          <div
            ref={playheadRef}
            className="absolute top-0 w-0.5 h-full bg-white z-30 pointer-events-none"
            style={{ left: '0%', boxShadow: '0 0 3px rgba(0,0,0,0.5)' }}
          />
          {/* Hover tooltip */}
          <div
            ref={tooltipRef}
            className="absolute -top-7 -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-0.5 rounded pointer-events-none z-40"
            style={{ display: 'none' }}
          />
        </div>
        {/* 圖例 */}
        {(marks.length > 0 || recording) && (
          <div className="flex gap-4 mt-2 text-xs text-gray-600">
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-sm bg-blue-500" /> 進攻
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-sm bg-emerald-500" /> 防守
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-sm bg-red-500" /> 失誤
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
