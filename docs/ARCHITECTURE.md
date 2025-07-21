# Technical Architecture

## 🏗️ System Overview

The PDF Question-Answering application is built using a modern, scalable architecture that combines web technologies, artificial intelligence, and vector databases to provide intelligent document analysis capabilities.

## 🎯 Core Principles

- **Modularity**: Separation of concerns with distinct layers
- **Scalability**: Horizontal and vertical scaling capabilities
- **Performance**: Optimized for speed and resource efficiency
- **Maintainability**: Clean code with comprehensive documentation
- **Extensibility**: Easy to add new features and integrations

## 📐 Architecture Layers

### 1. Presentation Layer (Frontend)
```
┌─────────────────────────────────────────────┐
│              Frontend Layer                 │
├─────────────────────────────────────────────┤
│ • HTML5 Semantic Structure                  │
│ • CSS3 Modern Styling & Animations          │
│ • Vanilla JavaScript (ES6+)                 │
│ • Responsive Design (Mobile-First)          │
│ • Progressive Enhancement                    │
└─────────────────────────────────────────────┘
```

**Components:**
- **Upload Interface**: Drag & drop with progress tracking
- **Chat Interface**: Real-time messaging with typing indicators
- **Document Management**: Visual cards with CRUD operations
- **Status Management**: Loading states and error handling

**Technologies:**
- HTML5 with semantic markup
- CSS3 with Flexbox/Grid layouts
- Vanilla JavaScript (no frameworks)
- FontAwesome icons
- RESTful API integration

### 2. Application Layer (FastAPI Backend)
```
┌─────────────────────────────────────────────┐
│            Application Layer                │
├─────────────────────────────────────────────┤
│ • FastAPI Framework                         │
│ • RESTful API Endpoints                     │
│ • Async Request Handling                    │
│ • Input Validation (Pydantic)              │
│ • Error Handling & Logging                  │
│ • CORS & Security Middleware               │
└─────────────────────────────────────────────┘
```

**Core Endpoints:**
- `POST /upload-pdf`: File upload and processing
- `POST /ask-question`: Question answering
- `GET /documents`: Document listing
- `DELETE /documents/{id}`: Document deletion
- `GET /health`: Health checks

**Key Features:**
- Async/await for non-blocking operations
- Background tasks for PDF processing
- Comprehensive error handling
- Request/response validation
- OpenAPI documentation

### 3. Business Logic Layer (Services)
```
┌─────────────────────────────────────────────┐
│           Business Logic Layer              │
├─────────────────────────────────────────────┤
│ • PDF Processing Service                    │
│ • Embedding Service                         │
│ • RAG (Retrieval Augmented Generation)     │
│ • Vector Store Management                   │
│ • Metadata Management                       │
└─────────────────────────────────────────────┘
```

#### PDF Processing Service
- **Text Extraction**: Dual-engine approach (PyPDF2 + pdfplumber)
- **Content Chunking**: LangChain RecursiveCharacterTextSplitter
- **Validation**: File type and size verification
- **Metadata Extraction**: Document properties and statistics

#### Embedding Service
- **Model**: Sentence-transformers (all-MiniLM-L6-v2)
- **Batch Processing**: Memory-efficient embedding generation
- **Caching**: Optional embedding cache for performance
- **Similarity**: Cosine similarity calculations

#### RAG Service
- **Pipeline Orchestration**: End-to-end question answering
- **Context Retrieval**: Vector similarity search
- **Answer Generation**: Specialized extraction algorithms
- **Metadata Management**: Persistent document information

### 4. Data Layer
```
┌─────────────────────────────────────────────┐
│                Data Layer                   │
├─────────────────────────────────────────────┤
│ • ChromaDB (Vector Database)                │
│ • File System (PDF Storage)                 │
│ • JSON Files (Metadata Persistence)        │
│ • In-Memory Caching                         │
└─────────────────────────────────────────────┘
```

## 🔄 Data Flow Architecture

### 1. Document Upload Flow
```
User Upload → FastAPI → PDF Processor → Text Extraction → Chunking → 
Embedding Generation → Vector Storage → Metadata Persistence → Response
```

**Detailed Steps:**
1. **Frontend**: User selects/drops PDF file
2. **Validation**: File type, size, and format checks
3. **Storage**: Temporary file storage with unique ID
4. **Text Extraction**: PyPDF2/pdfplumber extraction
5. **Chunking**: LangChain text splitting (1000 chars, 200 overlap)
6. **Embedding**: Sentence-transformer vector generation
7. **Vector Storage**: ChromaDB persistence with metadata
8. **Metadata**: JSON file persistence for document info
9. **Response**: Status and document ID return

### 2. Question Answering Flow
```
User Question → Embedding → Vector Search → Context Retrieval → 
Answer Generation → Response Formatting → Frontend Display
```

**Detailed Steps:**
1. **Frontend**: User submits question
2. **Embedding**: Question vector generation
3. **Search**: ChromaDB similarity search (top-k results)
4. **Filtering**: Relevance threshold application
5. **Context Assembly**: Top chunks combination
6. **Answer Generation**: Specialized extraction algorithms
7. **Response**: Answer with confidence and sources
8. **Display**: Frontend chat message rendering

## 🧠 AI/ML Architecture

### Embedding Pipeline
```
Text Input → Tokenization → Model Processing → Vector Output
     ↓              ↓              ↓              ↓
Raw Text → [Token IDs] → Neural Network → [384-dim Vector]
```

**Model Specifications:**
- **Architecture**: Transformer-based (BERT-like)
- **Dimensions**: 384 (all-MiniLM-L6-v2)
- **Context Length**: 512 tokens
- **Language**: English (primary)
- **Performance**: ~100ms per query

### Similarity Search
```
Query Vector → ChromaDB Index → Cosine Similarity → Top-K Results
     ↓              ↓                ↓                  ↓
[384 floats] → HNSW Index → Distance Calc → Ranked Results
```

**Search Parameters:**
- **Algorithm**: HNSW (Hierarchical Navigable Small World)
- **Metric**: Cosine similarity
- **Index Size**: Dynamic (grows with documents)
- **Query Time**: O(log n) average case

### Answer Generation
```
Retrieved Context → Pattern Matching → Information Extraction → Answer Formatting
        ↓                 ↓                    ↓                    ↓
    Text Chunks → Regex/Rules → Structured Data → Natural Language
```

**Extraction Types:**
- **Names**: Pattern recognition for personal names
- **Skills**: Technology keyword matching
- **Experience**: Date and role extraction
- **Contact**: Email and phone pattern matching
- **Education**: Institution and degree identification

## 🗄️ Database Architecture

### ChromaDB Structure
```
Collection: pdf_documents
├── Documents (Text Chunks)
├── Embeddings (Vector Representations)
├── Metadata (Document Information)
└── IDs (Unique Identifiers)
```

**Schema:**
```json
{
  "id": "uuid4-string",
  "document": "text-content",
  "embedding": [0.1, 0.2, ...],
  "metadata": {
    "document_id": "doc-uuid",
    "filename": "document.pdf",
    "chunk_id": "chunk-uuid",
    "chunk_size": 1000,
    "total_chunks": 10
  }
}
```

### Metadata Persistence
```json
{
  "document_id": {
    "document_id": "uuid",
    "filename": "name.pdf",
    "file_path": "uploads/path",
    "upload_date": "2025-07-21T10:30:00",
    "chunk_count": 10,
    "file_size": 65891,
    "status": "completed"
  }
}
```

## 🔧 Component Interactions

### Service Dependencies
```
FastAPI App
├── RAG Service
│   ├── PDF Processor
│   ├── Embedding Service
│   └── Vector Store
├── Configuration
└── Logging
```

### Data Dependencies
```
PDF Files → Text Extraction → Text Chunks → Embeddings → Vector DB
                                ↓
                          Metadata → JSON File
```

## 📊 Performance Characteristics

### Throughput
- **PDF Upload**: 1-10 files/minute (depending on size)
- **Question Processing**: 10-100 questions/minute
- **Concurrent Users**: 10-50 (single instance)
- **Vector Search**: <100ms per query

### Resource Usage
- **Memory**: 2-4GB (base + model + data)
- **CPU**: 2-4 cores (optimal performance)
- **Storage**: Variable (PDFs + vectors + metadata)
- **Network**: Minimal (REST API only)

### Scalability Limits
- **Documents**: 10,000+ (single instance)
- **Chunks**: 100,000+ (ChromaDB limit much higher)
- **File Size**: 50MB max (configurable)
- **Concurrent Uploads**: 10 (background processing)

## 🔒 Security Architecture

### Input Validation
```
User Input → FastAPI Validation → Pydantic Models → Business Logic
     ↓              ↓                    ↓              ↓
Raw Data → Type Check → Schema Validation → Safe Processing
```

### File Security
- **Type Validation**: PDF-only uploads
- **Size Limits**: 50MB maximum
- **Content Scanning**: Text-only extraction
- **Storage Isolation**: Dedicated upload directory

### API Security
- **CORS**: Configurable origin restrictions
- **Input Sanitization**: Pydantic validation
- **Error Handling**: No sensitive data leakage
- **Rate Limiting**: (Optional, not implemented)

## 🚀 Deployment Architecture

### Single Instance
```
Load Balancer (Nginx) → FastAPI App → ChromaDB → File System
                            ↓
                        Static Files
```

### Multi-Instance (Scaled)
```
Load Balancer → [FastAPI App 1] → Shared ChromaDB → Shared Storage
              → [FastAPI App 2] ↗                ↗
              → [FastAPI App N] ↗                ↗
```

### Cloud Architecture
```
CDN → ALB → ECS/K8s → RDS/DocumentDB → S3/Cloud Storage
       ↓         ↓            ↓              ↓
   SSL Term   Auto Scale   Vector DB     File Storage
```

## 🔄 Extension Points

### New File Types
```python
class DocumentProcessor:  # Extend PDF processor
    def extract_text_docx(self, file_path: str) -> str: ...
    def extract_text_txt(self, file_path: str) -> str: ...
```

### Custom Embeddings
```python
class CustomEmbeddingService:
    def __init__(self, model_name: str): ...
    def encode_with_openai(self, texts: List[str]) -> List[List[float]]: ...
```

### Advanced Q&A
```python
class LLMAnswerGenerator:
    def generate_with_gpt(self, context: str, question: str) -> str: ...
    def generate_with_claude(self, context: str, question: str) -> str: ...
```

## 📈 Future Architecture Considerations

### Microservices Evolution
```
API Gateway → Auth Service → PDF Service → Embedding Service → Vector Service
                ↓               ↓              ↓               ↓
            User Mgmt     File Processing  ML Models      Database
```

### Event-Driven Architecture
```
Upload Event → PDF Queue → Processing → Embedding Queue → Storage → Notification
```

### Streaming Processing
```
Real-time Upload → Stream Processing → Live Indexing → Instant Search
```

This architecture provides a solid foundation for the current application while allowing for future growth and enhancement.