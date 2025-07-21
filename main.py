import os
import uuid
import asyncio
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import time

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging

from models.schemas import (
    DocumentResponse, QuestionRequest, AnswerResponse, 
    DocumentListResponse, ErrorResponse, HealthResponse
)
from services.rag_service import RAGService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PDF Question-Answering API",
    description="A FastAPI application for uploading PDFs and asking questions about their content using RAG",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
rag_service: RAGService = None
app_start_time = time.time()

# Configuration
UPLOAD_DIR = Path("./uploads")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf"}

# Ensure upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global rag_service
    try:
        logger.info("Initializing RAG service...")
        rag_service = RAGService(
            embedding_model="all-MiniLM-L6-v2",
            chunk_size=1000,
            chunk_overlap=200,
            vector_store_path="./chroma_db"
        )
        logger.info("RAG service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down PDF QA application")


def get_rag_service() -> RAGService:
    """Dependency to get RAG service instance."""
    if rag_service is None:
        raise HTTPException(status_code=500, detail="RAG service not initialized")
    return rag_service


def validate_pdf_file(file: UploadFile) -> None:
    """Validate uploaded PDF file."""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only PDF files are allowed."
        )
    
    # Check file size (this is approximate from content-length header)
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )


async def save_uploaded_file(file: UploadFile, document_id: str) -> str:
    """Save uploaded file and return file path."""
    try:
        # Create filename with document ID to avoid conflicts
        file_ext = Path(file.filename).suffix.lower()
        safe_filename = f"{document_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            
            # Final file size check
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
                )
            
            buffer.write(content)
        
        logger.info(f"Saved file: {file_path}")
        return str(file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")


async def process_pdf_background(file_path: str, filename: str, document_id: str, rag_service: RAGService):
    """Background task to process PDF."""
    try:
        await rag_service.process_and_store_pdf(file_path, filename, document_id)
        logger.info(f"Background processing completed for document: {document_id}")
    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint - redirect to frontend."""
    return RedirectResponse(url="/static/index.html")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    uptime = time.time() - app_start_time
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=uptime
    )


@app.post("/upload-pdf", response_model=DocumentResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Upload and process a PDF file.
    
    The file will be processed in the background and its status can be checked
    using the document ID returned in the response.
    """
    try:
        # Validate file
        validate_pdf_file(file)
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Save uploaded file
        file_path = await save_uploaded_file(file, document_id)
        
        # Add background task for processing
        background_tasks.add_task(
            process_pdf_background,
            file_path,
            file.filename,
            document_id,
            rag_service
        )
        
        # Return immediate response
        return DocumentResponse(
            id=document_id,
            filename=file.filename,
            status="processing",
            upload_date=datetime.now(),
            chunk_count=None,
            file_size=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload PDF file")


@app.post("/ask-question", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Ask a question about uploaded PDF content.
    
    The question will be answered using relevant content from uploaded PDFs.
    Optionally specify a document_id to search within a specific document.
    """
    try:
        result = await rag_service.answer_question(
            question=request.question,
            document_id=request.document_id,
            max_chunks=request.max_chunks
        )
        
        return AnswerResponse(**result)
        
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process question")


@app.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    List all uploaded documents with their processing status.
    """
    try:
        documents_data = rag_service.list_documents()
        
        documents = []
        for doc_data in documents_data:
            doc = DocumentResponse(
                id=doc_data["document_id"],
                filename=doc_data["filename"],
                status=doc_data.get("status", "unknown"),
                upload_date=doc_data.get("upload_date", datetime.now()),
                chunk_count=doc_data.get("chunk_count"),
                file_size=doc_data.get("file_size")
            )
            documents.append(doc)
        
        return DocumentListResponse(
            documents=documents,
            total=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Get details about a specific document.
    """
    try:
        metadata = rag_service.get_document_metadata(document_id)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(
            id=document_id,
            filename=metadata["filename"],
            status=metadata.get("status", "unknown"),
            upload_date=metadata.get("upload_date", datetime.now()),
            chunk_count=metadata.get("chunk_count"),
            file_size=metadata.get("file_size")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get document")


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Delete a document and all its associated data.
    """
    try:
        success = rag_service.delete_document(document_id)
        
        if success:
            return {"message": f"Document {document_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@app.get("/stats")
async def get_stats(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Get system statistics.
    """
    try:
        stats = rag_service.get_service_stats()
        stats["uptime"] = time.time() - app_start_time
        stats["upload_directory"] = str(UPLOAD_DIR)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@app.get("/debug/chunks/{document_id}")
async def get_document_chunks(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Debug endpoint to see document chunks."""
    try:
        chunks = rag_service.vector_store.get_documents_by_id(document_id)
        return {"document_id": document_id, "chunks": chunks}
    except Exception as e:
        logger.error(f"Error getting chunks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chunks")

@app.post("/debug/search")
async def debug_search(
    request: dict,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Debug endpoint to test similarity search."""
    try:
        question = request.get("question", "")
        question_embedding = rag_service.embedding_service.encode_query(question)
        
        # Search with very low threshold
        search_results = rag_service.vector_store.similarity_search(
            query_embedding=question_embedding,
            k=5,
            document_id=request.get("document_id")
        )
        
        return {
            "question": question,
            "results_count": len(search_results),
            "results": search_results
        }
    except Exception as e:
        logger.error(f"Error in debug search: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to debug search")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": f"HTTP_{exc.status_code}"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )