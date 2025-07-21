# Development Guide

## 🏗️ Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   AI Services   │
│   (HTML/CSS/JS) │◄──►│   Backend       │◄──►│   (Embeddings)  │
│                 │    │                 │    │                 │
│ • Upload UI     │    │ • PDF Upload    │    │ • Sentence      │
│ • Chat Interface│    │ • Text Extract  │    │   Transformers  │
│ • Doc Management│    │ • API Endpoints │    │ • Vector Search │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Data Layer    │
                       │                 │
                       │ • ChromaDB      │
                       │ • File Storage  │
                       │ • JSON Metadata │
                       └─────────────────┘
```

### Data Flow
1. **Upload**: PDF → FastAPI → Text Extraction → Chunking → Embeddings → ChromaDB
2. **Query**: Question → Embedding → Vector Search → Context Retrieval → Answer Generation
3. **Management**: CRUD operations on documents and metadata

## 📁 Project Structure

```
pdfmodel/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── logger_config.py       # Logging setup
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── documents_metadata.json # Persistent document metadata
│
├── models/               # Data models
│   ├── __init__.py
│   └── schemas.py       # Pydantic models
│
├── services/            # Business logic
│   ├── __init__.py
│   ├── pdf_processor.py  # PDF text extraction
│   ├── embedding_service.py # Text embeddings
│   └── rag_service.py   # RAG pipeline
│
├── database/            # Data access layer
│   ├── __init__.py
│   └── vector_store.py  # ChromaDB operations
│
├── static/              # Frontend assets
│   ├── index.html       # Main UI
│   ├── css/
│   │   └── style.css    # Styling
│   └── js/
│       └── app.js       # Frontend logic
│
├── uploads/             # PDF file storage
├── chroma_db/           # Vector database
├── logs/                # Application logs
└── docs/                # Documentation
    ├── API_DOCUMENTATION.md
    ├── DEVELOPMENT_GUIDE.md
    └── DEPLOYMENT_GUIDE.md
```

## 🔧 Core Components

### 1. PDF Processing (`services/pdf_processor.py`)
- **Text Extraction**: Dual engine support (PyPDF2 + pdfplumber)
- **Chunking**: LangChain RecursiveCharacterTextSplitter
- **Validation**: File type and size checks
- **Metadata**: File info extraction

**Key Methods:**
```python
async def extract_text(file_path: str) -> str
def create_chunks(text: str) -> List[Document]
async def process_pdf(file_path: str, doc_id: str, filename: str) -> List[Document]
```

### 2. Embedding Service (`services/embedding_service.py`)
- **Model**: Sentence-transformers (all-MiniLM-L6-v2)
- **Batch Processing**: Memory-efficient embedding generation
- **Caching**: Optional embedding cache
- **Similarity**: Cosine similarity calculations

**Key Methods:**
```python
def encode_texts(texts: List[str]) -> List[List[float]]
def encode_query(query: str) -> List[float]
def encode_documents(documents: List[Document]) -> List[List[float]]
```

### 3. Vector Store (`database/vector_store.py`)
- **ChromaDB**: Persistent vector database
- **Operations**: Add, search, delete, list
- **Metadata**: Document and chunk metadata
- **Filtering**: Document-specific searches

**Key Methods:**
```python
def add_documents(documents: List[Document], embeddings: List[List[float]]) -> bool
def similarity_search(query_embedding: List[float], k: int) -> List[Dict]
def delete_document(document_id: str) -> bool
```

### 4. RAG Service (`services/rag_service.py`)
- **Pipeline**: End-to-end RAG implementation
- **Answer Generation**: Specialized extraction logic
- **Metadata Management**: Persistent document metadata
- **Question Types**: Names, skills, experience, contact, education

**Key Methods:**
```python
async def process_and_store_pdf(file_path: str, filename: str, doc_id: str) -> Dict
async def answer_question(question: str, doc_id: str, max_chunks: int) -> Dict
def list_documents() -> List[Dict]
```

### 5. Frontend (`static/`)
- **Upload Interface**: Drag & drop with progress tracking
- **Chat UI**: Real-time conversation interface
- **Document Management**: Visual cards with actions
- **API Integration**: RESTful communication with backend

**Key Classes:**
```javascript
class PDFQAApp {
    async uploadFile(file)
    async sendQuestion()
    async loadDocuments()
    addChatMessage(sender, content, metadata)
}
```

## 🧪 Testing

### Manual Testing
```bash
# Start the server
python main.py

# Test endpoints
curl http://localhost:8000/health
curl -X POST -F "file=@test.pdf" http://localhost:8000/upload-pdf
curl -X POST -H "Content-Type: application/json" \
     -d '{"question": "test"}' http://localhost:8000/ask-question
```

### Unit Testing (Future Enhancement)
```python
# Example test structure
def test_pdf_extraction():
    processor = PDFProcessor()
    text = await processor.extract_text("test.pdf")
    assert len(text) > 0

def test_embedding_generation():
    service = EmbeddingService()
    embeddings = service.encode_texts(["test text"])
    assert len(embeddings[0]) == 384  # Model dimension
```

## 🔧 Configuration

### Environment Variables
```bash
# Application
APP_NAME="PDF Question-Answering API"
DEBUG=false
HOST="0.0.0.0"
PORT=8000

# File Processing
MAX_FILE_SIZE=52428800  # 50MB
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# AI/ML
EMBEDDING_MODEL="all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD=0.1

# Paths
UPLOAD_DIR="./uploads"
VECTOR_STORE_PATH="./chroma_db"
LOG_FILE="./logs/app.log"
```

### Configuration Class (`config.py`)
```python
class Settings(BaseSettings):
    app_name: str = "PDF Question-Answering API"
    debug: bool = False
    embedding_model: str = "all-MiniLM-L6-v2"
    # ... other settings
```

## 📊 Performance Considerations

### Memory Usage
- **Embeddings**: ~1.5MB model in memory
- **PDFs**: Processed in chunks, not loaded entirely
- **Vector Store**: ChromaDB handles memory management
- **Frontend**: Minimal JavaScript, no heavy frameworks

### Processing Speed
- **PDF Upload**: ~1-5 seconds depending on size
- **Embedding Generation**: ~100ms per chunk
- **Vector Search**: ~10-50ms
- **Answer Generation**: ~10-100ms

### Scaling
- **Horizontal**: Multiple FastAPI instances behind load balancer
- **Vertical**: Increase CPU/RAM for faster processing
- **Database**: ChromaDB can handle millions of vectors
- **Storage**: File system for PDFs, consider cloud storage for production

## 🐛 Debugging

### Logging
```python
# Enable debug logging
LOG_LEVEL="DEBUG"

# Check logs
tail -f logs/app.log
```

### Debug Endpoints
```bash
# Check document chunks
curl http://localhost:8000/debug/chunks/{document_id}

# Test similarity search
curl -X POST -H "Content-Type: application/json" \
     -d '{"question": "test"}' http://localhost:8000/debug/search
```

### Common Issues
1. **"No documents found"**: Check if upload was successful
2. **"Not relevant enough"**: Lower similarity threshold
3. **Empty responses**: Verify text extraction worked
4. **Memory errors**: Reduce chunk size or batch size

## 🔄 Development Workflow

### 1. Setup
```bash
# Clone/create project
git clone <repo> && cd pdfmodel

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
```

### 2. Development
```bash
# Run in development mode
python main.py

# Frontend development
# Edit files in static/ directory
# No build process needed
```

### 3. Code Style
- **Python**: Follow PEP 8
- **JavaScript**: Use modern ES6+ features
- **CSS**: BEM methodology preferred
- **Comments**: Docstrings for all public methods

### 4. Version Control
```bash
# Ignore these files
echo "chroma_db/" >> .gitignore
echo "uploads/" >> .gitignore
echo "logs/" >> .gitignore
echo "documents_metadata.json" >> .gitignore
echo ".env" >> .gitignore
```

## 🚀 Future Enhancements

### Short Term
- [ ] Add user authentication
- [ ] Implement rate limiting
- [ ] Add more file formats (Word, TXT)
- [ ] Improve error handling

### Medium Term
- [ ] Multi-language support
- [ ] Advanced question types
- [ ] Document comparison
- [ ] Export functionality

### Long Term
- [ ] Real LLM integration (GPT, Claude)
- [ ] Advanced analytics
- [ ] Multi-user support
- [ ] Cloud deployment templates

## 🧩 Extension Points

### Adding New Question Types
```python
# In rag_service.py
def _extract_custom_info(self, content: str, question: str) -> str:
    # Custom extraction logic
    return "Custom answer"

# In _simple_answer_generation method
elif "custom_keyword" in question_lower:
    answer = self._extract_custom_info(combined_content, question)
```

### Custom Embedding Models
```python
# In embedding_service.py
def __init__(self, model_name: str = "custom-model"):
    self.model = SentenceTransformer(model_name)
```

### Additional File Types
```python
# In pdf_processor.py
class DocumentProcessor:  # Rename from PDFProcessor
    def extract_text_from_docx(self, file_path: str) -> str:
        # Word document processing
        pass
```