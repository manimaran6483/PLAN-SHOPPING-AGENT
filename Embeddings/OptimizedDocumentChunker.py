import tiktoken
import uuid
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class OptimizedDocumentChunker:
    """
    Optimized document chunker that uses rule-based semantic chunking 
    to minimize OpenAI API calls while maintaining quality.
    """
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Insurance-specific keywords for semantic boundaries
        self.section_markers = [
            r'(?i)(deductible|copay|coinsurance|premium|coverage|benefit)',
            r'(?i)(in-network|out-of-network|provider|hospital)',
            r'(?i)(prescription|drug|medication|pharmacy)',
            r'(?i)(emergency|urgent care|specialist|primary care)',
            r'(?i)(mental health|maternity|preventive|wellness)'
        ]
        
        # Sentence boundary patterns
        self.sentence_endings = r'[.!?]+\s+'
        
    def extract_insurance_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Extract insurance sections using rule-based patterns instead of LLM.
        Much more efficient for token usage.
        """
        sections = []
        
        # Split by common insurance document patterns
        section_patterns = [
            r'(?i)(?:^|\n\n+)([A-Z][^.!?]*(?:deductible|copay|premium|coverage)[^.!?]*[.!?])',
            r'(?i)(?:^|\n\n+)([A-Z][^.!?]*(?:in-network|out-of-network)[^.!?]*[.!?])',
            r'(?i)(?:^|\n\n+)([A-Z][^.!?]*(?:prescription|drug|medication)[^.!?]*[.!?])',
            r'(?i)(?:^|\n\n+)([A-Z][^.!?]*(?:emergency|urgent|specialist)[^.!?]*[.!?])',
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                section_text = match.group(1).strip()
                if len(section_text) > 20:  # Filter very short matches
                    sections.append({
                        'text': section_text,
                        'type': self._classify_section_type(section_text)
                    })
        
        # If no specific sections found, split by paragraphs
        if not sections:
            paragraphs = re.split(r'\n\n+', text)
            for para in paragraphs:
                para = para.strip()
                if len(para) > 50:  # Only meaningful paragraphs
                    sections.append({
                        'text': para,
                        'type': 'general'
                    })
        
        return sections
    
    def _classify_section_type(self, text: str) -> str:
        """Classify section type based on keywords."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['deductible', 'premium', 'cost']):
            return 'costs'
        elif any(word in text_lower for word in ['coverage', 'benefit', 'covered']):
            return 'coverage'
        elif any(word in text_lower for word in ['network', 'provider', 'hospital']):
            return 'network'
        elif any(word in text_lower for word in ['prescription', 'drug', 'medication']):
            return 'prescriptions'
        else:
            return 'general'
    
    def smart_sentence_split(self, text: str) -> List[str]:
        """
        Split text into sentences while preserving context for insurance terms.
        """
        # Split by sentence endings but keep insurance-related sentences together
        sentences = re.split(self.sentence_endings, text)
        
        smart_chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if adding this sentence exceeds our target chunk size
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            potential_tokens = len(self.tokenizer.encode(potential_chunk))
            
            if potential_tokens > self.chunk_size and current_chunk:
                # Save current chunk and start new one
                smart_chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = potential_chunk
        
        # Add remaining chunk
        if current_chunk.strip():
            smart_chunks.append(current_chunk.strip())
        
        return smart_chunks
    
    def chunk_insurance_document(self, text: str, plan_id: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Optimized chunking that minimizes API calls while maintaining semantic quality.
        """
        chunks = []
        
        if not text or not text.strip():
            return chunks
        
        # Step 1: Extract sections using rule-based approach (no API calls)
        sections = self.extract_insurance_sections(text)
        
        # Step 2: Process each section
        for section_idx, section in enumerate(sections):
            section_text = section['text']
            section_type = section['type']
            
            # Step 3: Smart sentence-based chunking within each section
            section_chunks = self.smart_sentence_split(section_text)
            
            # Step 4: Create chunks with metadata
            for chunk_idx, chunk_text in enumerate(section_chunks):
                if len(chunk_text.strip()) < 20:  # Skip very short chunks
                    continue
                    
                chunk_metadata = {
                    "chunk_id": f"{plan_id}-opt-{len(chunks)}-{uuid.uuid4().hex[:8]}",
                    "plan_id": plan_id,
                    "token_count": len(self.tokenizer.encode(chunk_text)),
                    "chunk_type": "optimized_semantic",
                    "section_type": section_type,
                    "section_index": section_idx,
                    "chunk_index": chunk_idx
                }
                
                # Add any additional metadata
                if metadata:
                    chunk_metadata.update(metadata)
                
                chunks.append({
                    "text": chunk_text.strip(),
                    "metadata": chunk_metadata
                })
        
        # If no sections were found, fall back to simple chunking
        if not chunks:
            chunks = self._fallback_chunking(text, plan_id, metadata)
        
        logger.info(f"Created {len(chunks)} optimized chunks for {plan_id}")
        return chunks
    
    def _fallback_chunking(self, text: str, plan_id: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fallback to simple sentence-aware chunking."""
        chunks = []
        sentences = re.split(self.sentence_endings, text)
        
        current_chunk = ""
        current_tokens = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_tokens = len(self.tokenizer.encode(sentence))
            
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Create chunk
                chunk_metadata = {
                    "chunk_id": f"{plan_id}-fallback-{len(chunks)}-{uuid.uuid4().hex[:8]}",
                    "plan_id": plan_id,
                    "token_count": current_tokens,
                    "chunk_type": "fallback_semantic",
                    "section_type": "general"
                }
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                chunks.append({
                    "text": current_chunk.strip(),
                    "metadata": chunk_metadata
                })
                
                # Start new chunk
                current_chunk = sentence
                current_tokens = sentence_tokens
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk.strip():
            chunk_metadata = {
                "chunk_id": f"{plan_id}-fallback-{len(chunks)}-{uuid.uuid4().hex[:8]}",
                "plan_id": plan_id,
                "token_count": current_tokens,
                "chunk_type": "fallback_semantic",
                "section_type": "general"
            }
            
            if metadata:
                chunk_metadata.update(metadata)
            
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": chunk_metadata
            })
        
        return chunks
    
    def chunk_structured_plan_data(self, plan_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create optimized chunks from structured plan data without API calls.
        """
        chunks = []
        plan_id = plan_details.get("plan_id", "unknown")
        
        # Define structure for efficient processing
        important_sections = {
            "costs": {
                "priority": 1,
                "subsections": ["premium", "deductible", "out_of_pocket_maximum", "coinsurance"]
            },
            "coverage": {
                "priority": 2,
                "subsections": ["preventive_care", "primary_care_visits", "specialist_visits", 
                              "emergency_care", "hospital_stay", "prescription_drugs"]
            },
            "network": {
                "priority": 3,
                "subsections": ["network_name", "hospital_count", "physician_count"]
            }
        }
        
        for section_name, section_info in important_sections.items():
            if section_name in plan_details:
                section_data = plan_details[section_name]
                
                if isinstance(section_data, dict):
                    # Create one comprehensive chunk per major section instead of multiple small ones
                    section_text = self._format_section_as_text(plan_id, section_name, section_data)
                    
                    if section_text and len(section_text.strip()) > 20:
                        chunk_metadata = {
                            "chunk_id": f"{plan_id}-struct-{section_name}-{uuid.uuid4().hex[:8]}",
                            "plan_id": plan_id,
                            "token_count": len(self.tokenizer.encode(section_text)),
                            "chunk_type": "structured_data",
                            "section_type": section_name,
                            "priority": section_info["priority"]
                        }
                        
                        chunks.append({
                            "text": section_text,
                            "metadata": chunk_metadata
                        })
        
        logger.info(f"Created {len(chunks)} structured chunks for {plan_id}")
        return chunks
    
    def _format_section_as_text(self, plan_id: str, section_name: str, section_data: Dict) -> str:
        """Format section data as readable text efficiently."""
        plan_name = plan_id.replace('_', ' ').replace('-', ' ').title()
        formatted_text = f"{plan_name} {section_name.replace('_', ' ').title()}:\n"
        
        text_parts = []
        
        for key, value in section_data.items():
            key_formatted = key.replace('_', ' ').title()
            
            if isinstance(value, dict):
                # Handle nested structures efficiently
                if 'in_network' in value and 'out_of_network' in value:
                    in_net = value['in_network']
                    out_net = value['out_of_network']
                    text_parts.append(f"{key_formatted}: ${in_net} in-network, ${out_net} out-of-network")
                else:
                    # Flatten nested dict
                    nested_parts = []
                    for nested_key, nested_value in value.items():
                        nested_parts.append(f"{nested_key.replace('_', ' ')}: {nested_value}")
                    text_parts.append(f"{key_formatted}: {', '.join(nested_parts)}")
            else:
                text_parts.append(f"{key_formatted}: {value}")
        
        formatted_text += ". ".join(text_parts) + "."
        return formatted_text
