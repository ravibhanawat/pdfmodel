import os
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from langchain.schema import Document
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.collection_name = "pdf_documents"
        self._initialize_client()

    def _initialize_client(self):
        """Initialize ChromaDB client."""
        try:
            # Ensure directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "PDF document chunks with embeddings"}
            )
            
            logger.info(f"ChromaDB initialized with collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            raise

    def add_documents(self, documents: List[Document], embeddings: List[List[float]]) -> bool:
        """Add documents with embeddings to the vector store."""
        try:
            if len(documents) != len(embeddings):
                raise ValueError("Number of documents must match number of embeddings")

            # Prepare data for ChromaDB
            ids = []
            metadatas = []
            texts = []

            for i, doc in enumerate(documents):
                # Generate unique ID for each chunk
                chunk_id = str(uuid.uuid4())
                ids.append(chunk_id)
                
                # Prepare metadata (ChromaDB requires serializable values)
                metadata = doc.metadata.copy()
                metadata["chunk_id"] = chunk_id
                
                # Ensure all metadata values are serializable
                for key, value in metadata.items():
                    if not isinstance(value, (str, int, float, bool)):
                        metadata[key] = str(value)
                
                metadatas.append(metadata)
                texts.append(doc.page_content)

            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

            logger.info(f"Added {len(documents)} documents to vector store")
            return True

        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise

    def similarity_search(
        self, 
        query_embedding: List[float], 
        k: int = 5,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using embedding similarity."""
        try:
            # Prepare where clause for filtering by document_id if provided
            where_clause = None
            if document_id:
                where_clause = {"document_id": document_id}

            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_clause
            )

            # Format results
            search_results = []
            if results and results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    }
                    search_results.append(result)

            logger.info(f"Found {len(search_results)} similar documents")
            return search_results

        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise

    def get_documents_by_id(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document."""
        try:
            results = self.collection.get(
                where={"document_id": document_id}
            )

            documents = []
            if results and results['documents']:
                for i in range(len(results['documents'])):
                    doc = {
                        "id": results['ids'][i],
                        "content": results['documents'][i],
                        "metadata": results['metadatas'][i]
                    }
                    documents.append(doc)

            logger.info(f"Retrieved {len(documents)} chunks for document {document_id}")
            return documents

        except Exception as e:
            logger.error(f"Error getting documents by ID: {str(e)}")
            raise

    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a specific document."""
        try:
            # Get all chunk IDs for the document
            results = self.collection.get(
                where={"document_id": document_id}
            )

            if results and results['ids']:
                # Delete all chunks
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            else:
                logger.warning(f"No chunks found for document {document_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all unique documents in the vector store."""
        try:
            # Get all documents
            results = self.collection.get()
            
            # Group by document_id
            documents = {}
            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    doc_id = metadata.get('document_id')
                    if doc_id and doc_id not in documents:
                        documents[doc_id] = {
                            "document_id": doc_id,
                            "filename": metadata.get('filename', 'Unknown'),
                            "chunk_count": 0,
                            "file_size": metadata.get('file_size', 0),
                            "text_length": metadata.get('text_length', 0)
                        }
                    if doc_id:
                        documents[doc_id]["chunk_count"] += 1

            return list(documents.values())

        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        try:
            count = self.collection.count()
            
            # Get unique documents count
            documents = self.list_documents()
            
            stats = {
                "total_chunks": count,
                "total_documents": len(documents),
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            raise

    def reset_collection(self) -> bool:
        """Reset (clear) the entire collection."""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "PDF document chunks with embeddings"}
            )
            logger.info("Vector store collection reset successfully")
            return True

        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            raise