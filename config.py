import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = Field(default="PDF Question-Answering API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # File upload settings
    upload_dir: str = Field(default="./uploads", description="Upload directory")
    max_file_size: int = Field(default=50 * 1024 * 1024, description="Maximum file size in bytes")
    allowed_extensions: list = Field(default=[".pdf"], description="Allowed file extensions")
    
    # Embedding settings
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model")
    chunk_size: int = Field(default=1000, description="Text chunk size")
    chunk_overlap: int = Field(default=200, description="Chunk overlap")
    
    # Vector store settings
    vector_store_path: str = Field(default="./chroma_db", description="Vector database path")
    
    # RAG settings
    default_max_chunks: int = Field(default=5, description="Default maximum chunks to retrieve")
    similarity_threshold: float = Field(default=0.3, description="Similarity threshold for relevance")
    
    # CORS settings
    allowed_origins: list = Field(default=["*"], description="Allowed CORS origins")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()