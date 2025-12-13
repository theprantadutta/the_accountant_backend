"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_CLIENT: str = "postgres"
    DATABASE_HOST: str
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "the_accountant_db"
    DATABASE_USERNAME: str
    DATABASE_PASSWORD: str
    DATABASE_SSL: bool = False

    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components"""
        return (
            f"postgresql://{self.DATABASE_USERNAME}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "The Accountant API"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "*"

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS origins from string"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # Firebase (Auth only)
    FIREBASE_PROJECT_ID: str = "the-accountant-8dadf"
    FIREBASE_AUTH_ENABLED: bool = True
    GOOGLE_WEB_CLIENT_ID: str = ""
    FCM_CREDENTIALS_PATH: str = "firebase-admin-sdk.json"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8002

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
