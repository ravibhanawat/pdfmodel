# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required. In production, consider implementing API keys or OAuth.

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running and healthy.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 1234.56
}
```

### 2. Upload PDF

**POST** `/upload-pdf`

Upload and process a PDF file.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field containing PDF

**Response:**
```json
{
  "id": "ddc93492-cc1b-453c-84b7-6918c7660c6a",
  "filename": "resume.pdf",
  "status": "processing",
  "upload_date": "2025-07-21T10:30:00.123456",
  "chunk_count": null,
  "file_size": null
}
```

**Error Responses:**
- `400`: Invalid file type or file too large
- `500`: Processing error

### 3. Ask Question

**POST** `/ask-question`

Ask a question about uploaded PDF content.

**Request Body:**
```json
{
  "question": "What is the person's name?",
  "document_id": "optional-document-id",
  "max_chunks": 5
}
```

**Response:**
```json
{
  "answer": "The person's name is John Doe.",
  "confidence": 0.95,
  "sources": [
    {
      "chunk_id": "chunk-123",
      "content": "JOHN DOE\nSoftware Engineer...",
      "similarity": 0.92,
      "filename": "resume.pdf",
      "document_id": "doc-456"
    }
  ],
  "document_id": "doc-456"
}
```

**Question Types Supported:**
- **Names**: "What is the name?", "Who is this person?"
- **Skills**: "What are the skills?", "What technologies does he know?"
- **Experience**: "What is the work experience?", "Where has he worked?"
- **Education**: "What is the educational background?"
- **Contact**: "What is the email address?", "What is the phone number?"
- **General**: Any question about document content

### 4. List Documents

**GET** `/documents`

Get a list of all uploaded documents.

**Response:**
```json
{
  "documents": [
    {
      "id": "doc-123",
      "filename": "resume.pdf",
      "status": "completed",
      "upload_date": "2025-07-21T10:30:00.123456",
      "chunk_count": 5,
      "file_size": 65891
    }
  ],
  "total": 1
}
```

**Document Status Values:**
- `processing`: PDF is being processed
- `completed`: Ready for questions
- `failed`: Processing failed

### 5. Get Document Details

**GET** `/documents/{document_id}`

Get details about a specific document.

**Parameters:**
- `document_id`: Unique document identifier

**Response:**
```json
{
  "id": "doc-123",
  "filename": "resume.pdf",
  "status": "completed",
  "upload_date": "2025-07-21T10:30:00.123456",
  "chunk_count": 5,
  "file_size": 65891
}
```

### 6. Delete Document

**DELETE** `/documents/{document_id}`

Delete a document and all its associated data.

**Parameters:**
- `document_id`: Unique document identifier

**Response:**
```json
{
  "message": "Document doc-123 deleted successfully"
}
```

### 7. System Statistics

**GET** `/stats`

Get system statistics and information.

**Response:**
```json
{
  "total_documents": 5,
  "total_chunks": 25,
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "vector_store_path": "./chroma_db",
  "uptime": 1234.56,
  "upload_directory": "./uploads"
}
```

## Debug Endpoints

### Get Document Chunks

**GET** `/debug/chunks/{document_id}`

Get all chunks for a specific document (for debugging).

**Response:**
```json
{
  "document_id": "doc-123",
  "chunks": [
    {
      "id": "chunk-456",
      "content": "Document text content...",
      "metadata": {
        "filename": "resume.pdf",
        "chunk_id": "chunk-456",
        "document_id": "doc-123"
      }
    }
  ]
}
```

### Debug Search

**POST** `/debug/search`

Test similarity search directly (for debugging).

**Request Body:**
```json
{
  "question": "test query",
  "document_id": "optional-doc-id"
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid input)
- `404`: Resource not found
- `500`: Internal server error

Error responses include details:
```json
{
  "detail": "Error message description",
  "error_code": "ERROR_TYPE"
}
```

## File Upload Limits

- **Maximum file size**: 50MB
- **Supported formats**: PDF only
- **Processing timeout**: 30 seconds
- **Concurrent uploads**: Unlimited (processed in background)

## Rate Limiting

Currently no rate limiting is implemented. Consider adding rate limiting for production use.

## CORS

CORS is enabled for all origins (`*`). In production, configure specific allowed origins.

## Example Usage

### Python
```python
import requests

# Upload PDF
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload-pdf',
        files={'file': f}
    )
    doc_info = response.json()

# Ask question
response = requests.post(
    'http://localhost:8000/ask-question',
    json={'question': 'What is this document about?'}
)
answer = response.json()
print(answer['answer'])
```

### JavaScript
```javascript
// Upload PDF
const formData = new FormData();
formData.append('file', pdfFile);

const uploadResponse = await fetch('/upload-pdf', {
    method: 'POST',
    body: formData
});

// Ask question
const questionResponse = await fetch('/ask-question', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        question: 'What is this document about?'
    })
});
```

### cURL
```bash
# Upload PDF
curl -X POST -F "file=@document.pdf" http://localhost:8000/upload-pdf

# Ask question
curl -X POST -H "Content-Type: application/json" \
     -d '{"question": "What is this document about?"}' \
     http://localhost:8000/ask-question
```