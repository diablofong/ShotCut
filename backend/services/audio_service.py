import os
import subprocess

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.candidate import Candidate
from backend.models.video import Video

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def _extract_audio(video_path: str, output_path: str):
    """使用 FFmpeg 從影片提取音訊為 WAV"""
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-ac", "1", "-ar", "22050", "-vn", output_path],
        capture_output=True,
        check=True,
    )


def _detect_whistles(
    y: np.ndarray, sr: int, sensitivity: float = 0.5, min_interval: float = 2.0
) -> list[dict]:
    """哨音偵測：帶通濾波 (2kHz-4kHz) + 短時能量峰值偵測"""
    from scipy.signal import butter, filtfilt

    # 帶通濾波 2kHz-4kHz
    nyquist = sr / 2
    low = 2000 / nyquist
    high = min(4000 / nyquist, 0.99)
    b, a = butter(4, [low, high], btype="band")
    filtered = filtfilt(b, a, y)

    # 短時能量
    frame_length = int(0.05 * sr)  # 50ms 窗口
    hop_length = int(0.025 * sr)   # 25ms 步進
    energy = []
    for i in range(0, len(filtered) - frame_length, hop_length):
        energy.append(np.sum(filtered[i : i + frame_length] ** 2))
    energy = np.array(energy)

    if len(energy) == 0:
        return []

    # 閾值 = 平均值 + sensitivity 倍標準差
    threshold = np.mean(energy) + (3.0 - sensitivity * 2.0) * np.std(energy)

    # 峰值偵測
    candidates = []
    last_time = -min_interval
    for i, e in enumerate(energy):
        t = i * hop_length / sr
        if e > threshold and (t - last_time) >= min_interval:
            confidence = min(float(e / threshold), 3.0) / 3.0
            candidates.append({"timestamp": round(t, 2), "type": "whistle", "confidence": round(confidence, 2)})
            last_time = t

    return candidates


def _detect_cheers(
    y: np.ndarray, sr: int, sensitivity: float = 0.5, min_interval: float = 3.0
) -> list[dict]:
    """歡呼聲偵測：寬頻能量突增 + 持續時間閾值"""
    # 短時能量（較大窗口）
    frame_length = int(0.2 * sr)   # 200ms 窗口
    hop_length = int(0.1 * sr)     # 100ms 步進
    energy = []
    for i in range(0, len(y) - frame_length, hop_length):
        energy.append(np.sum(y[i : i + frame_length] ** 2))
    energy = np.array(energy)

    if len(energy) < 10:
        return []

    # 計算能量變化率
    from scipy.ndimage import uniform_filter1d
    smoothed = uniform_filter1d(energy, size=5)
    baseline = uniform_filter1d(energy, size=50)

    # 能量突增偵測
    ratio = np.where(baseline > 0, smoothed / baseline, 0)
    threshold = 1.5 + (1.0 - sensitivity) * 2.0

    candidates = []
    last_time = -min_interval
    for i, r in enumerate(ratio):
        t = i * hop_length / sr
        if r > threshold and (t - last_time) >= min_interval:
            confidence = min(float(r / threshold), 3.0) / 3.0
            candidates.append({"timestamp": round(t, 2), "type": "cheer", "confidence": round(confidence, 2)})
            last_time = t

    return candidates


async def analyze_video(
    db: AsyncSession,
    video_id: int,
    sensitivity: float = 0.5,
    min_interval: float = 2.0,
):
    """對影片執行音訊分析，產出候選時間點"""
    video = await db.get(Video, video_id)
    if not video or video.status != "completed" or not video.file_path:
        raise ValueError("影片不存在或尚未完成下載")

    # 提取音訊
    audio_dir = os.path.join(UPLOAD_DIR, str(video_id))
    os.makedirs(audio_dir, exist_ok=True)
    audio_path = os.path.join(audio_dir, "audio.wav")

    if not os.path.exists(audio_path):
        _extract_audio(video.file_path, audio_path)

    # 載入音訊
    import librosa
    y, sr = librosa.load(audio_path, sr=22050, mono=True)

    # 偵測
    whistles = _detect_whistles(y, sr, sensitivity, min_interval)
    cheers = _detect_cheers(y, sr, sensitivity, min_interval)

    # 儲存候選時間點
    all_candidates = sorted(whistles + cheers, key=lambda c: c["timestamp"])
    for c in all_candidates:
        db.add(Candidate(
            video_id=video_id,
            timestamp=c["timestamp"],
            type=c["type"],
            confidence=c["confidence"],
        ))
    await db.commit()

    return all_candidates
