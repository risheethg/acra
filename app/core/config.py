"""
Application configuration management.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application settings using environment variables.
    """
    # Celery settings
    REDIS_URL: str = ""
    GOOGLE_API_KEY: str= ""
    GITHUB_ACCESS_TOKEN:str= ""

    # Pydantic settings configuration
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

# Create a singleton instance of the settings
settings = Settings()
