from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys
    GEN_ENG_API_KEY: str | None = None
    GROQ_API: str | None = None

    # Model settings
    MODEL_NAME: str = "llama-3.3-70b-versatile"
    TEMPERATURE: float = 0.3

    # Scoring weights
    SKILL_WEIGHT: float = 0.5
    EXPERIENCE_WEIGHT: float = 0.3
    EDUCATION_WEIGHT: float = 0.2

    # Paths
    DATA_DIR: str = "data"
    OUTPUT_DIR: str = "data/outputs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Add this line to ignore extra env vars


# Global settings instance
settings = Settings()
