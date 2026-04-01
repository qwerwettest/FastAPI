from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Project metadata
    PROJECT_NAME: str = "IPChain MVP"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "IPChain - платформа токенизации объектов интеллектуальной собственности"
    
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # Security
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Debug
    DEBUG: bool = False
    
    # USPTO API integration
    USPTO_API_URL: str = "https://developer.uspto.gov/ptab-api"
    USPTO_API_TIMEOUT: int = 30
    USPTO_API_KEY: str = ""
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 10
    
    # File upload
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_DOCUMENT_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
    ]
    
    # Object storage (S3-compatible)
    STORAGE_PROVIDER: str = "local"  # local, s3
    STORAGE_BUCKET: str = ""
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""
    STORAGE_ENDPOINT: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
