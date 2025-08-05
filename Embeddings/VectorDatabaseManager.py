from typing import Any, Dict, List
from openai import OpenAI
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import uuid

class VectorDatabaseManager:
    def __init__(self, openai_api_key: str, db_directory: str = "chroma_db"):
        print(openai_api_key)
        self.client = OpenAI(api_key=openai_api_key)    
        self.chroma_client = chromadb.PersistentClient(path=db_directory)
        
        # Use OpenAI's embedding function "text-embedding-ada-002"
        self.embedding_function = OpenAIEmbeddingFunction(
            api_key=openai_api_key,
            model_name = "text-embedding-ada-002"
        )
        
        # Create collection if it doesn't exist
        self.collection = self.chroma_client.get_or_create_collection(
            name="insurance_plans", 
            embedding_function=self.embedding_function
        )
        
    def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for text using OpenAI API."""
        response = self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=text,
            dimensions=1536
        )
        return response.data[0].embedding
    
    def add_chunks_to_vector_db(self, chunks: List[Dict[str, Any]]) -> bool:
        """Add document chunks to the vector database."""
        if not chunks:
            print("No chunks to add to vector database")
            return False
        
        try:
            # Prepare data for batch insertion - handle both old and new chunk formats
            ids = []
            texts = []
            metadatas = []
            
            for chunk in chunks:
                # Handle different chunk formats
                if "content" in chunk:
                    # New ultra-optimized format
                    chunk_id = chunk.get("id", str(chunk.get("metadata", {}).get("chunk_id", "unknown")))
                    text_content = chunk["content"]
                    metadata = chunk.get("metadata", {})
                elif "text" in chunk:
                    # Old format
                    chunk_id = chunk["metadata"].get("chunk_id", str(uuid.uuid4()))
                    text_content = chunk["text"]
                    metadata = chunk["metadata"]
                else:
                    print(f"Warning: Skipping chunk with unknown format: {chunk.keys()}")
                    continue
                
                # Ensure chunk_id is in metadata
                if "chunk_id" not in metadata:
                    metadata["chunk_id"] = chunk_id
                
                ids.append(chunk_id)
                texts.append(text_content)
                metadatas.append(metadata)
            
            if not ids:
                print("No valid chunks found to add")
                return False
            
            print(f"Adding {len(ids)} chunks to ChromaDB...")
            
            # Add to collection - ChromaDB will handle embedding generation
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            
            print(f"Successfully added {len(ids)} chunks to vector database")
            return True
            
        except Exception as e:
            print(f"Error adding chunks to vector database: {str(e)}")
            return False
        
    def search(self, query: str, plan_id: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant information based on query."""
        try:
            # Optionally filter by plan ID
            filter_condition = {"plan_id": plan_id} if plan_id else None
            
            print(f"Searching ChromaDB for query: '{query[:50]}...' with filter: {filter_condition}")
            
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=filter_condition
            )
            
            print(f"ChromaDB returned {len(results['documents'][0])} results")
            
            # Format results
            formatted_results = []
            if results['documents'][0]:  # Check if we have results
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "text": results['documents'][0][i],
                        "page_content": results['documents'][0][i],  # Add for compatibility
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            else:
                print("No results found in ChromaDB")
                
            return formatted_results
            
        except Exception as e:
            print(f"Error searching vector database: {str(e)}")
            return []
        
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection."""
        try:
            count = self.collection.count()
            return {
                "collection_name": "insurance_plans",
                "document_count": count,
                "has_documents": count > 0
            }
        except Exception as e:
            print(f"Error getting collection info: {str(e)}")
            return {
                "collection_name": "insurance_plans",
                "document_count": 0,
                "has_documents": False,
                "error": str(e)
            }