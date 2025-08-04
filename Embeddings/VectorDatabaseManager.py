from typing import Any, Dict, List
import numpy as np
from openai import OpenAI
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

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
    
    def add_chunks_to_vector_db(self, chunks: List[Dict[str, Any]]):
        """Add document chunks to the vector database."""
        # Prepare data for batch insertion
        ids = [chunk["metadata"]["chunk_id"] for chunk in chunks]
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        
    def search(self, query: str, plan_id: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant information based on query."""
        # Optionally filter by plan ID
        filter_condition = {"plan_id": plan_id} if plan_id else None
        
        # Perform search
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=filter_condition
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                "text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })
            
        return formatted_results