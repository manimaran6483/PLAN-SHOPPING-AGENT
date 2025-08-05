import tiktoken
import uuid
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class UltraOptimizedChunker:
    """
    Ultra-optimized chunker that uses ZERO LLM calls for chunking.
    Only uses rule-based text processing and semantic boundaries.
    Designed to minimize token usage to absolute minimum.
    """
    
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Insurance-specific section markers (no LLM needed)
        self.insurance_keywords = {
            'cost': ['deductible', 'copay', 'coinsurance', 'premium', 'cost', 'fee', 'payment'],
            'coverage': ['coverage', 'benefit', 'covered', 'included', 'service'],
            'network': ['in-network', 'out-of-network', 'provider', 'hospital', 'facility'],
            'prescription': ['prescription', 'drug', 'medication', 'pharmacy', 'formulary'],
            'care': ['emergency', 'urgent care', 'specialist', 'primary care', 'doctor'],
            'special': ['mental health', 'maternity', 'preventive', 'wellness', 'dental', 'vision']
        }
        
    def count_tokens(self, text: str) -> int:
        """Count tokens efficiently."""
        return len(self.tokenizer.encode(text))
    
    def split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences using regex (no LLM)."""
        # Handle common sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def find_semantic_boundary(self, text: str, target_position: int) -> int:
        """
        Find the best semantic boundary near target position using rules.
        No LLM calls - pure rule-based logic.
        """
        # Look for paragraph breaks first
        paragraph_breaks = [m.start() for m in re.finditer(r'\n\s*\n', text)]
        
        # Find closest paragraph break to target
        best_pos = target_position
        min_distance = float('inf')
        
        for break_pos in paragraph_breaks:
            distance = abs(break_pos - target_position)
            if distance < min_distance and distance < 200:  # Within reasonable range
                min_distance = distance
                best_pos = break_pos
        
        # If no good paragraph break, look for sentence endings
        if min_distance > 100:
            sentence_endings = [m.end() for m in re.finditer(r'[.!?]\s+', text)]
            for end_pos in sentence_endings:
                distance = abs(end_pos - target_position)
                if distance < min_distance and distance < 100:
                    min_distance = distance
                    best_pos = end_pos
        
        return best_pos
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key insurance phrases using regex patterns."""
        phrases = []
        
        # Pattern for dollar amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?'
        money_matches = re.findall(money_pattern, text)
        phrases.extend(money_matches)
        
        # Pattern for percentages
        percent_pattern = r'\d+%'
        percent_matches = re.findall(percent_pattern, text)
        phrases.extend(percent_matches)
        
        # Insurance-specific phrases
        for category, keywords in self.insurance_keywords.items():
            for keyword in keywords:
                pattern = rf'\b{re.escape(keyword)}[^.!?]*[.!?]'
                matches = re.findall(pattern, text, re.IGNORECASE)
                phrases.extend(matches)
        
        return phrases[:10]  # Limit to top 10 most relevant
    
    def create_smart_chunks(self, text: str, plan_id: str) -> List[Dict[str, Any]]:
        """
        Create semantically meaningful chunks without any LLM calls.
        Pure rule-based approach for maximum efficiency.
        """
        chunks = []
        
        if not text or len(text.strip()) < 50:
            return chunks
        
        # Clean and normalize text
        text = re.sub(r'\s+', ' ', text.strip())
        total_tokens = self.count_tokens(text)
        
        logger.info(f"Processing {total_tokens} tokens for {plan_id}")
        
        # If text is small enough, create single chunk
        if total_tokens <= self.chunk_size:
            chunk = {
                "id": str(uuid.uuid4()),
                "content": text,
                "metadata": {
                    "plan_id": plan_id,
                    "chunk_type": "single_document",
                    "token_count": total_tokens,
                    "key_phrases": self.extract_key_phrases(text)
                }
            }
            chunks.append(chunk)
            return chunks
        
        # Split into chunks using semantic boundaries
        start_pos = 0
        chunk_num = 1
        
        while start_pos < len(text):
            # Calculate target end position
            target_end = start_pos + (self.chunk_size * 4)  # Rough character estimate
            
            if target_end >= len(text):
                # Last chunk
                chunk_text = text[start_pos:]
            else:
                # Find semantic boundary
                actual_end = self.find_semantic_boundary(text, target_end)
                chunk_text = text[start_pos:actual_end]
            
            # Ensure minimum chunk size
            if len(chunk_text.strip()) < 100 and chunks:
                # Add to previous chunk if too small
                chunks[-1]["content"] += " " + chunk_text
                chunks[-1]["metadata"]["token_count"] = self.count_tokens(chunks[-1]["content"])
                break
            
            # Create chunk
            chunk_tokens = self.count_tokens(chunk_text)
            chunk = {
                "id": str(uuid.uuid4()),
                "content": chunk_text.strip(),
                "metadata": {
                    "plan_id": plan_id,
                    "chunk_number": chunk_num,
                    "chunk_type": "semantic_section",
                    "token_count": chunk_tokens,
                    "key_phrases": self.extract_key_phrases(chunk_text)
                }
            }
            chunks.append(chunk)
            
            # Move to next position with overlap
            overlap_chars = min(self.chunk_overlap * 4, len(chunk_text) // 4)
            start_pos = actual_end - overlap_chars if target_end < len(text) else len(text)
            chunk_num += 1
        
        logger.info(f"Created {len(chunks)} chunks for {plan_id} - Total tokens processed: {total_tokens}")
        return chunks
    
    def chunk_structured_data(self, structured_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create chunks from structured plan data without LLM calls.
        Each data section becomes a focused chunk.
        """
        chunks = []
        plan_id = structured_data.get("plan_id", "unknown")
        
        # Create chunks from key structured sections
        sections_to_chunk = [
            ("plan_overview", "Plan Overview"),
            ("cost_structure", "Cost Structure"),
            ("coverage_details", "Coverage Details"),
            ("network_info", "Network Information"),
            ("prescription_coverage", "Prescription Coverage"),
            ("special_benefits", "Special Benefits")
        ]
        
        for section_key, section_name in sections_to_chunk:
            section_data = structured_data.get(section_key)
            if section_data and isinstance(section_data, dict):
                # Convert dict to readable text
                section_text = self._dict_to_text(section_data, section_name)
                
                if section_text and len(section_text.strip()) > 50:
                    chunk = {
                        "id": str(uuid.uuid4()),
                        "content": section_text,
                        "metadata": {
                            "plan_id": plan_id,
                            "chunk_type": f"structured_{section_key}",
                            "section_name": section_name,
                            "token_count": self.count_tokens(section_text),
                            "source": "structured_extraction"
                        }
                    }
                    chunks.append(chunk)
        
        return chunks
    
    def _dict_to_text(self, data: Dict[str, Any], section_name: str) -> str:
        """Convert dictionary data to readable text format."""
        text_parts = [f"{section_name}:"]
        
        for key, value in data.items():
            if value:
                key_formatted = key.replace('_', ' ').title()
                if isinstance(value, dict):
                    text_parts.append(f"\n{key_formatted}:")
                    for sub_key, sub_value in value.items():
                        if sub_value:
                            sub_key_formatted = sub_key.replace('_', ' ').title()
                            text_parts.append(f"  - {sub_key_formatted}: {sub_value}")
                elif isinstance(value, list):
                    text_parts.append(f"\n{key_formatted}: {', '.join(str(v) for v in value)}")
                else:
                    text_parts.append(f"\n{key_formatted}: {value}")
        
        return '\n'.join(text_parts)
    
    def process_document(self, document_text: str, structured_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Main method to process document with zero LLM calls.
        Combines structured chunks and semantic text chunks.
        """
        plan_id = structured_data.get("plan_id", "unknown")
        all_chunks = []
        
        # Create chunks from structured data (most important)
        structured_chunks = self.chunk_structured_data(structured_data)
        all_chunks.extend(structured_chunks)
        
        # Create semantic chunks from raw text
        text_chunks = self.create_smart_chunks(document_text, plan_id)
        all_chunks.extend(text_chunks)
        
        total_tokens = sum(chunk["metadata"]["token_count"] for chunk in all_chunks)
        logger.info(f"Generated {len(all_chunks)} chunks with total {total_tokens} tokens for {plan_id}")
        
        return all_chunks
