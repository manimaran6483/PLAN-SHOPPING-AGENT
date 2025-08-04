import tiktoken
import numpy as np
import uuid
from typing import List, Dict, Any, Tuple

class DocumentChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # OpenAI's tokenizer
        
    def split_text_into_chunks(self, text: str, plan_id: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks with metadata."""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        # Create default metadata if not provided
        if metadata is None:
            metadata = {}
            
        # Add plan ID to metadata
        metadata["plan_id"] = plan_id
        
        # Create chunks with token counts
        i = 0
        while i < len(tokens):
            # Get chunk tokens
            chunk_tokens = tokens[i:i + self.chunk_size]
            # Convert back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # Create chunk with metadata
            chunk = {
                "text": chunk_text,
                "metadata": {
                    **metadata,
                    "chunk_id": f"{plan_id}-{len(chunks)}-{uuid.uuid4().hex}",
                    "token_count": len(chunk_tokens)
                }
            }
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            i += self.chunk_size - self.chunk_overlap
            
        return chunks
    
    def chunk_plan_document(self, plan_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks from structured plan details."""
        chunks = []
        plan_id = plan_details.get("plan_id", "unknown")
        
        # Create a chunk for each major section
        for section, content in plan_details.items():
            if section == "plan_id":
                continue
                
            # Format section as readable text
            section_text = f"{section.replace('_', ' ').title()}: {content}"
            
            # Create chunk with appropriate metadata
            section_chunks = self.split_text_into_chunks(
                section_text, 
                plan_id,
                {"section": section}
            )
            chunks.extend(section_chunks)
            
        return chunks