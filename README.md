# PDFModel - PDF Question-Answering Application

A complete full-stack application for uploading PDF files and asking questions about their content using RAG (Retrieval Augmented Generation). Built with FastAPI backend, modern JavaScript frontend, and powered by AI embeddings.

## 🚀 Features

### 📄 **PDF Processing**
- **Smart Upload**: Drag & drop interface with file validation
- **Text Extraction**: Dual engine support (PyPDF2 + pdfplumber)
- **Intelligent Chunking**: Semantic text splitting with LangChain
- **Background Processing**: Non-blocking PDF processing

### 🤖 **AI-Powered Q&A**
- **Natural Language Questions**: Ask questions in plain English
- **Smart Answer Generation**: Context-aware responses with confidence scoring
- **Specialized Extraction**: Names, skills, experience, contact info, education
- **Multi-Document Search**: Query across all documents or specific ones

### 💻 **Frontend Interface**
- **Modern UI**: Beautiful, responsive design with animations
- **Real-time Chat**: Conversational interface with typing indicators
- **Document Management**: Visual cards with status tracking
- **Progress Feedback**: Upload progress and processing status

### 🔧 **Technical Features**
- **Vector Search**: Efficient similarity search using ChromaDB
- **Persistent Storage**: Document metadata survives server restarts
- **Error Handling**: Comprehensive error handling and user feedback
- **CORS Support**: Configurable cross-origin requests
- **API Documentation**: Auto-generated Swagger/OpenAPI docs

## 🛠️ Technical Stack

### **Backend**
- **FastAPI**: Modern Python web framework
- **LangChain**: PDF processing and text splitting
- **ChromaDB**: Vector database for embeddings
- **Sentence-Transformers**: AI embeddings (all-MiniLM-L6-v2)
- **PyPDF2 & pdfplumber**: PDF text extraction

### **Frontend**
- **Vanilla JavaScript**: No framework dependencies
- **CSS3**: Modern styling with animations
- **HTML5**: Semantic markup
- **FontAwesome**: Professional icons

### **AI/ML**
- **Sentence-Transformers**: Text embeddings
- **Vector Similarity**: Cosine similarity search
- **RAG Pipeline**: Retrieval Augmented Generation

## 📁 Project Structure

```
pdfmodel/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings
├── logger_config.py       # Logging configuration
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables example
├── test_api.py           # API testing script
├── models/
│   ├── __init__.py
│   └── schemas.py        # Pydantic models
├── services/
│   ├── __init__.py
│   ├── pdf_processor.py  # PDF text extraction and chunking
│   ├── embedding_service.py  # Text embedding generation
│   └── rag_service.py    # RAG question answering service
├── database/
│   ├── __init__.py
│   └── vector_store.py   # ChromaDB vector database management
└── uploads/              # PDF file storage directory
```

## ⚡ Quick Start

### 1. Installation

```bash
# Clone the project
git clone https://github.com/ravibhanawat/pdfmodel.git
cd pdfmodel

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the environment file and customize if needed:
```bash
cp .env.example .env
```

### 3. Run the Application

```bash
# Start the FastAPI server
python main.py

# Or use uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### 4. API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

## 📚 API Endpoints

### Health Check
```http
GET /health
```

### Upload PDF
```http
POST /upload-pdf
Content-Type: multipart/form-data

file: <PDF file>
```

### Ask Question
```http
POST /ask-question
Content-Type: application/json

{
  "question": "What is this document about?",
  "document_id": "optional-document-id",
  "max_chunks": 5
}
```

### List Documents
```http
GET /documents
```

### Get Document Details
```http
GET /documents/{document_id}
```

### Delete Document
```http
DELETE /documents/{document_id}
```

### System Statistics
```http
GET /stats
```

## 🧪 Testing

### Using the Test Script

```bash
# Basic test (requires a test.pdf file in the project directory)
python test_api.py

# Test with custom API URL
python test_api.py http://localhost:8000
```

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Upload PDF
curl -X POST -F "file=@example.pdf" http://localhost:8000/upload-pdf

# Ask question
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}' \
  http://localhost:8000/ask-question

# List documents
curl http://localhost:8000/documents
```

### Using Python requests

```python
import requests

# Upload PDF
with open('example.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload-pdf',
        files={'file': f}
    )
    result = response.json()
    document_id = result['id']

# Ask question
response = requests.post(
    'http://localhost:8000/ask-question',
    json={
        'question': 'What is this document about?',
        'document_id': document_id
    }
)
answer = response.json()
print(answer['answer'])
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | PDF Question-Answering API | Application name |
| `DEBUG` | false | Debug mode |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `MAX_FILE_SIZE` | 52428800 | Max file size (50MB) |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Sentence transformer model |
| `CHUNK_SIZE` | 1000 | Text chunk size |
| `CHUNK_OVERLAP` | 200 | Chunk overlap |
| `VECTOR_STORE_PATH` | ./chroma_db | Vector database path |
| `LOG_LEVEL` | INFO | Logging level |

### Embedding Models

You can use different sentence-transformer models:

- `all-MiniLM-L6-v2` (default) - Fast, good quality, 384 dimensions
- `all-mpnet-base-v2` - Slower, better quality, 768 dimensions  
- `multi-qa-MiniLM-L6-cos-v1` - Optimized for Q&A tasks

## 🔧 Advanced Usage

### Custom Embedding Model

```python
# In main.py, modify the RAGService initialization
rag_service = RAGService(
    embedding_model="all-mpnet-base-v2",  # Higher quality model
    chunk_size=800,
    chunk_overlap=100
)
```

### Production Deployment

1. **Use a production WSGI server**:
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. **Configure reverse proxy** (nginx example):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Set production environment variables**:
```bash
export DEBUG=false
export ALLOWED_ORIGINS=["https://yourdomain.com"]
export LOG_FILE="/var/log/pdf-qa/app.log"
```

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t pdfmodel .
docker run -p 8000:8000 -v $(pwd)/uploads:/app/uploads pdfmodel
```

## 🔒 Security Considerations

- File upload size limits are enforced
- Only PDF files are accepted
- Input validation on all endpoints
- CORS configuration for cross-origin requests
- Consider adding authentication for production use

## 🐛 Troubleshooting

### Common Issues

1. **"Model not found" error**: The sentence-transformer model is downloaded on first use. Ensure internet connection.

2. **Large memory usage**: Reduce `chunk_size` or use a smaller embedding model.

3. **Slow processing**: For large PDFs, processing happens in background. Check document status via API.

4. **ChromaDB errors**: Ensure write permissions to the `vector_store_path` directory.

### Performance Tuning

- Adjust `chunk_size` and `chunk_overlap` based on your documents
- Use GPU for faster embedding generation (requires PyTorch with CUDA)
- Consider using a more powerful embedding model for better accuracy

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [📖 API Documentation](docs/API_DOCUMENTATION.md) | Complete REST API reference with examples |
| [🏗️ Architecture Guide](docs/ARCHITECTURE.md) | Technical system architecture and design |
| [🔧 Development Guide](docs/DEVELOPMENT_GUIDE.md) | Setup, development workflow, and debugging |
| [🚀 Deployment Guide](docs/DEPLOYMENT_GUIDE.md) | Production deployment and scaling |
| [📋 Project Overview](docs/PROJECT_OVERVIEW.md) | Executive summary and project details |

## 🎯 Quick Navigation

- **Getting Started**: Follow the [Quick Start](#quick-start) section above
- **API Reference**: See [API Documentation](docs/API_DOCUMENTATION.md)
- **Production Setup**: Check [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- **Development**: Read [Development Guide](docs/DEVELOPMENT_GUIDE.md)
- **Architecture**: Understand the [Technical Architecture](docs/ARCHITECTURE.md)

## 📝 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🤝 Contributing

Contributions are welcome! Please read the [Development Guide](docs/DEVELOPMENT_GUIDE.md) for setup instructions and coding standards.

## 📧 Support

For questions and support:
- Check the [Documentation](docs/) first
- Review the [API Documentation](docs/API_DOCUMENTATION.md) for API issues
- See [Troubleshooting](docs/DEPLOYMENT_GUIDE.md#troubleshooting) for common problems