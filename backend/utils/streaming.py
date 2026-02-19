import os

from fastapi import HTTPException
from fastapi.responses import FileResponse, StreamingResponse


def validate_file_path(file_path: str, allowed_dir: str) -> None:
    """驗證 file_path 在允許的目錄內，否則拋出 404。"""
    real_path = os.path.realpath(file_path)
    real_dir = os.path.realpath(allowed_dir)
    if not real_path.startswith(real_dir + os.sep):
        raise HTTPException(status_code=404, detail="檔案不存在")


def parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    """解析並驗證 HTTP Range header，回傳 (start, end)。無效時拋出 416。"""
    try:
        if not range_header.startswith("bytes="):
            raise ValueError("格式錯誤")
        range_spec = range_header[6:]
        parts = range_spec.split("-", 1)
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=416,
            detail="無效的 Range header",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    if start < 0 or end < 0 or start > end or start >= file_size:
        raise HTTPException(
            status_code=416,
            detail="Range 超出範圍",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    end = min(end, file_size - 1)
    return start, end


def stream_file_response(file_path: str, file_size: int, range_header: str | None):
    """回傳檔案串流 Response，支援 Range 請求。"""
    if range_header:
        start, end = parse_range_header(range_header, file_size)
        content_length = end - start + 1

        def iter_file():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk = f.read(min(8192, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(
            iter_file(),
            status_code=206,
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
            },
        )

    return FileResponse(
        file_path,
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"},
    )
