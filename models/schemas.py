from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentCreate(BaseModel):
    filename: str = Field(..., description="Name of the PDF file")


class DocumentResponse(BaseModel):
    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Name of the PDF file")
    status: DocumentStatus = Field(..., description="Processing status")
    upload_date: datetime = Field(..., description="Upload timestamp")
    chunk_count: Optional[int] = Field(None, description="Number of text chunks")
    file_size: Optional[int] = Field(None, description="File size in bytes")


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="Question about the PDF content")
    document_id: Optional[str] = Field(None, description="Specific document ID to search in")
    max_chunks: int = Field(default=5, ge=1, le=10, description="Maximum number of relevant chunks to retrieve")


class AnswerResponse(BaseModel):
    answer: str = Field(..., description="Generated answer")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    sources: List[dict] = Field(..., description="Source chunks with metadata")
    document_id: Optional[str] = Field(None, description="Source document ID")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    uptime: float = Field(..., description="Uptime in seconds")