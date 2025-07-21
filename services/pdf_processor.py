import os
import uuid
from typing import List, Dict, Any
import PyPDF2
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging

logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    async def extract_text_pypdf2(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text with PyPDF2: {str(e)}")
            raise

    async def extract_text_pdfplumber(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber (better for complex layouts)."""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text with pdfplumber: {str(e)}")
            raise

    async def extract_text(self, file_path: str, method: str = "pdfplumber") -> str:
        """Extract text from PDF using specified method."""
        if method == "pypdf2":
            return await self.extract_text_pypdf2(file_path)
        elif method == "pdfplumber":
            return await self.extract_text_pdfplumber(file_path)
        else:
            raise ValueError(f"Unsupported extraction method: {method}")

    def create_chunks(self, text: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """Split text into chunks using LangChain text splitter."""
        if not text.strip():
            raise ValueError("Empty text provided for chunking")

        if metadata is None:
            metadata = {}

        try:
            chunks = self.text_splitter.split_text(text)
            documents = []
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    doc_metadata = {
                        **metadata,
                        "chunk_id": i,
                        "chunk_size": len(chunk),
                        "total_chunks": len(chunks)
                    }
                    documents.append(Document(
                        page_content=chunk.strip(),
                        metadata=doc_metadata
                    ))
            
            return documents
        except Exception as e:
            logger.error(f"Error creating chunks: {str(e)}")
            raise

    async def process_pdf(self, file_path: str, document_id: str, filename: str) -> List[Document]:
        """Complete PDF processing pipeline."""
        try:
            # Extract text
            logger.info(f"Extracting text from {filename}")
            text = await self.extract_text(file_path)
            
            if not text.strip():
                raise ValueError("No text could be extracted from PDF")

            # Get file stats
            file_size = os.path.getsize(file_path)
            
            # Create metadata
            metadata = {
                "document_id": document_id,
                "filename": filename,
                "file_path": file_path,
                "file_size": file_size,
                "text_length": len(text)
            }

            # Create chunks
            logger.info(f"Creating chunks for {filename}")
            documents = self.create_chunks(text, metadata)
            
            logger.info(f"Successfully processed {filename}: {len(documents)} chunks created")
            return documents

        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {str(e)}")
            raise

    def validate_pdf(self, file_path: str) -> bool:
        """Validate if file is a proper PDF."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages) > 0
        except Exception:
            return False

    def get_pdf_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic information about the PDF."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                info = {
                    "page_count": len(pdf_reader.pages),
                    "file_size": os.path.getsize(file_path),
                    "metadata": pdf_reader.metadata if hasattr(pdf_reader, 'metadata') else {}
                }
                return info
        except Exception as e:
            logger.error(f"Error getting PDF info: {str(e)}")
            return {"page_count": 0, "file_size": 0, "metadata": {}}