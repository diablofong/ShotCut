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

    # 目錄設定（暫存用，上傳最終存 S3）
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

    # S3-compatible 物件儲存設定（必填）
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_bucket_name: str = ""
    s3_endpoint_url: str = ""
    # 公開存取 URL（選填）：presigned URL 的 hostname 會替換為此值
    # 自建版填 http://localhost:9000，雲端版（R2/S3 直接可達）留空
    s3_public_url: str = ""

    # 向後相容：舊 R2_* 環境變數（自動映射到 s3_*）
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
    def validate_s3_settings(self) -> "Settings":
        # 向後相容：R2_* → S3_*（若 S3_* 未設定但 R2_* 有值）
        if not self.s3_access_key_id and self.r2_access_key_id:
            self.s3_access_key_id = self.r2_access_key_id
        if not self.s3_secret_access_key and self.r2_secret_access_key:
            self.s3_secret_access_key = self.r2_secret_access_key
        if not self.s3_bucket_name and self.r2_bucket_name:
            self.s3_bucket_name = self.r2_bucket_name
        if not self.s3_endpoint_url and self.r2_endpoint_url:
            self.s3_endpoint_url = self.r2_endpoint_url

        # 驗證 S3 設定完整性（測試環境跳過：SQLite + 無 S3 設定）
        is_test = self.database_url.startswith("sqlite")
        if not is_test:
            missing = [
                name for name, val in [
                    ("S3_ACCESS_KEY_ID", self.s3_access_key_id),
                    ("S3_SECRET_ACCESS_KEY", self.s3_secret_access_key),
                    ("S3_BUCKET_NAME", self.s3_bucket_name),
                    ("S3_ENDPOINT_URL", self.s3_endpoint_url),
                ]
                if not val
            ]
            if missing:
                raise ValueError(f"以下 S3 設定不可為空：{', '.join(missing)}")
        return self

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError('SECRET_KEY 長度必須至少 32 字符')
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
