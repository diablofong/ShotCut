from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 必填設定（缺少則啟動失敗）
    database_url: str
    secret_key: str

    # JWT 設定
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7

    # CORS（逗號分隔）
    cors_origins: str = ""

    # 目錄設定
    upload_dir: str = "./uploads"
    clip_dir: str = "./clips"
    highlight_dir: str = "./highlights"
    thumbnail_dir: str = "./thumbnails"

    # 上傳限制
    max_upload_size_mb: int = 2048

    # FFmpeg 設定
    ffmpeg_timeout: int = 300

    # 管理員初始帳號（seed 用）
    admin_username: str = ""
    admin_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
