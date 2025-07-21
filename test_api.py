#!/usr/bin/env python3
"""
Test script for the PDF Question-Answering API.
This script demonstrates how to use the API endpoints.
"""

import requests
import json
import time
import sys
from pathlib import Path


class PDFQAClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def health_check(self):
        """Check if the API is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Health check failed: {e}")
            return None

    def upload_pdf(self, file_path: str):
        """Upload a PDF file."""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, 'application/pdf')}
                response = self.session.post(f"{self.base_url}/upload-pdf", files=files)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Upload failed: {e}")
            return None

    def ask_question(self, question: str, document_id: str = None, max_chunks: int = 5):
        """Ask a question about the PDF content."""
        try:
            data = {
                "question": question,
                "max_chunks": max_chunks
            }
            if document_id:
                data["document_id"] = document_id

            response = self.session.post(f"{self.base_url}/ask-question", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Question failed: {e}")
            return None

    def list_documents(self):
        """List all uploaded documents."""
        try:
            response = self.session.get(f"{self.base_url}/documents")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"List documents failed: {e}")
            return None

    def get_document(self, document_id: str):
        """Get details about a specific document."""
        try:
            response = self.session.get(f"{self.base_url}/documents/{document_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Get document failed: {e}")
            return None

    def delete_document(self, document_id: str):
        """Delete a document."""
        try:
            response = self.session.delete(f"{self.base_url}/documents/{document_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Delete document failed: {e}")
            return None

    def get_stats(self):
        """Get system statistics."""
        try:
            response = self.session.get(f"{self.base_url}/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Get stats failed: {e}")
            return None


def test_api():
    """Test the PDF QA API with example operations."""
    client = PDFQAClient()
    
    print("=== PDF Question-Answering API Test ===\n")
    
    # 1. Health check
    print("1. Health Check:")
    health = client.health_check()
    if health:
        print(f"✅ API is healthy - Status: {health.get('status')}")
        print(f"   Version: {health.get('version')}")
        print(f"   Uptime: {health.get('uptime', 0):.2f}s\n")
    else:
        print("❌ API health check failed\n")
        return

    # 2. List documents (initially empty)
    print("2. List Documents (initially):")
    docs = client.list_documents()
    if docs:
        print(f"✅ Found {docs.get('total', 0)} documents")
        for doc in docs.get('documents', []):
            print(f"   - {doc['filename']} (ID: {doc['id']}) - Status: {doc['status']}")
    print()

    # 3. Upload a PDF (you'll need to provide a test PDF file)
    print("3. Upload PDF:")
    test_pdf = "test.pdf"  # Change this to your test PDF file path
    if Path(test_pdf).exists():
        upload_result = client.upload_pdf(test_pdf)
        if upload_result:
            document_id = upload_result['id']
            print(f"✅ PDF uploaded successfully")
            print(f"   Document ID: {document_id}")
            print(f"   Filename: {upload_result['filename']}")
            print(f"   Status: {upload_result['status']}")
            
            # Wait for processing to complete
            print("   Waiting for processing to complete...")
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(2)
                doc_info = client.get_document(document_id)
                if doc_info and doc_info['status'] == 'completed':
                    print(f"✅ Processing completed - {doc_info['chunk_count']} chunks created")
                    break
                elif doc_info and doc_info['status'] == 'failed':
                    print("❌ Processing failed")
                    return
                else:
                    print(f"   Still processing... ({i*2}s)")
            
        else:
            print("❌ PDF upload failed")
            return
    else:
        print(f"❌ Test PDF file not found: {test_pdf}")
        print("   Please create a test PDF file or update the path")
        document_id = None
    print()

    # 4. Ask questions (if document was uploaded)
    if document_id:
        print("4. Ask Questions:")
        questions = [
            "What is this document about?",
            "Can you summarize the main points?",
            "What are the key topics covered?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"   Question {i}: {question}")
            answer = client.ask_question(question, document_id)
            if answer:
                print(f"   Answer: {answer['answer'][:200]}...")
                print(f"   Confidence: {answer['confidence']:.2f}")
                print(f"   Sources: {len(answer['sources'])} chunks")
            else:
                print("   ❌ Failed to get answer")
            print()

    # 5. List documents again
    print("5. List Documents (after upload):")
    docs = client.list_documents()
    if docs:
        print(f"✅ Found {docs.get('total', 0)} documents")
        for doc in docs.get('documents', []):
            print(f"   - {doc['filename']} (ID: {doc['id']}) - Status: {doc['status']}")
            if doc.get('chunk_count'):
                print(f"     Chunks: {doc['chunk_count']}, Size: {doc.get('file_size', 0)} bytes")
    print()

    # 6. Get system stats
    print("6. System Statistics:")
    stats = client.get_stats()
    if stats:
        print(f"✅ Total documents: {stats.get('total_documents', 0)}")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   Embedding model: {stats.get('embedding_model', 'unknown')}")
        print(f"   Embedding dimension: {stats.get('embedding_dimension', 'unknown')}")
    print()

    print("=== Test completed ===")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        client = PDFQAClient(base_url)
    else:
        client = PDFQAClient()
    
    test_api()