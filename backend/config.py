from functools import lru_cache

from pydantic import field_validator, model_validator
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

    # 生產環境標誌
    is_production: bool = False

    # 儲存後端（"local" 或 "r2"）
    storage_backend: str = "local"

    # Cloudflare R2 設定（storage_backend=r2 時必填）
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = ""
    r2_endpoint_url: str = ""

    # 功能開關（Feature Flags）
    enable_clips: bool = True
    enable_highlights: bool = True
    enable_sharing: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_r2_settings(self) -> "Settings":
        if self.storage_backend == "r2":
            missing = [
                name for name, val in [
                    ("R2_ACCESS_KEY_ID", self.r2_access_key_id),
                    ("R2_SECRET_ACCESS_KEY", self.r2_secret_access_key),
                    ("R2_BUCKET_NAME", self.r2_bucket_name),
                    ("R2_ENDPOINT_URL", self.r2_endpoint_url),
                ]
                if not val
            ]
            if missing:
                raise ValueError(f"STORAGE_BACKEND=r2 時以下設定不可為空：{', '.join(missing)}")
        return self

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """驗證 Secret Key 強度"""
        if len(v) < 32:
            raise ValueError('SECRET_KEY 長度必須至少 32 字符')
        # 檢查是否為常見預設值
        weak_keys = ['change-me', 'test', 'secret', 'password', 'default']
        if v.lower() in weak_keys:
            raise ValueError(f'SECRET_KEY 不可使用常見預設值: {", ".join(weak_keys)}')
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
