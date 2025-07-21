import os
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain.schema import Document
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service with sentence-transformers model.
        
        Args:
            model_name: Name of the sentence-transformers model to use
                       Options: 'all-MiniLM-L6-v2' (fast, good quality)
                               'all-mpnet-base-v2' (slower, better quality)
                               'multi-qa-MiniLM-L6-cos-v1' (optimized for QA)
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dimension = None
        self._load_model()

    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Get embedding dimension
            test_embedding = self.model.encode(["test"])
            self.embedding_dimension = len(test_embedding[0])
            
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dimension}")
            
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise

    def encode_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Encode a list of texts into embeddings.
        
        Args:
            texts: List of text strings to encode
            batch_size: Batch size for processing (helps with memory management)
            
        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        try:
            if not texts:
                return []

            logger.info(f"Encoding {len(texts)} texts with batch size {batch_size}")
            
            # Process in batches to manage memory
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    show_progress_bar=False
                )
                
                # Convert numpy arrays to lists for JSON serialization
                batch_embeddings_list = [embedding.tolist() for embedding in batch_embeddings]
                all_embeddings.extend(batch_embeddings_list)

            logger.info(f"Successfully encoded {len(all_embeddings)} embeddings")
            return all_embeddings

        except Exception as e:
            logger.error(f"Error encoding texts: {str(e)}")
            raise

    def encode_query(self, query: str) -> List[float]:
        """
        Encode a single query string into an embedding.
        
        Args:
            query: Query string to encode
            
        Returns:
            Embedding as a list of floats
        """
        try:
            if not query.strip():
                raise ValueError("Empty query provided")

            logger.debug(f"Encoding query: {query[:100]}...")
            
            embedding = self.model.encode([query], convert_to_numpy=True)[0]
            return embedding.tolist()

        except Exception as e:
            logger.error(f"Error encoding query: {str(e)}")
            raise

    def encode_documents(self, documents: List[Document]) -> List[List[float]]:
        """
        Encode a list of LangChain Document objects.
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            List of embeddings corresponding to the documents
        """
        try:
            if not documents:
                return []

            # Extract text content from documents
            texts = [doc.page_content for doc in documents]
            
            return self.encode_texts(texts)

        except Exception as e:
            logger.error(f"Error encoding documents: {str(e)}")
            raise

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            
            return float(similarity)

        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "max_sequence_length": getattr(self.model, 'max_seq_length', None)
        }

    def validate_embedding_dimension(self, embedding: List[float]) -> bool:
        """Validate that an embedding has the correct dimension."""
        return len(embedding) == self.embedding_dimension


class EmbeddingCache:
    """Simple in-memory cache for embeddings to avoid recomputation."""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []

    def get(self, text: str) -> List[float]:
        """Get embedding from cache."""
        if text in self.cache:
            # Update access order
            self.access_order.remove(text)
            self.access_order.append(text)
            return self.cache[text]
        return None

    def put(self, text: str, embedding: List[float]):
        """Store embedding in cache."""
        if len(self.cache) >= self.max_size:
            # Remove least recently used
            oldest = self.access_order.pop(0)
            del self.cache[oldest]

        self.cache[text] = embedding
        self.access_order.append(text)

    def clear(self):
        """Clear the cache."""
        self.cache.clear()
        self.access_order.clear()

    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)