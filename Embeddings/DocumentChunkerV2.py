import tiktoken
import numpy as np
import uuid
import re
from typing import List, Dict, Any, Tuple
from openai import OpenAI

class DocumentChunkerV2:
    """
    Advanced document chunker using proposition-based chunking.
    
    This approach breaks documents into atomic facts/propositions rather than 
    fixed-size chunks, which improves retrieval accuracy for insurance documents.
    """
    
    def __init__(self, openai_api_key: str, max_tokens: int = 1000, min_tokens: int = 50):
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.client = OpenAI(api_key=openai_api_key)
        
    def extract_propositions(self, text: str) -> List[str]:
        """
        Extract atomic propositions from text using LLM.
        Each proposition should be a standalone fact that can be understood independently.
        """
        prompt = f"""
        Extract atomic facts/propositions from the following insurance document text. 
        Each proposition should be:
        1. A standalone fact that can be understood independently
        2. Complete and self-contained
        3. Focused on a single concept or rule
        4. Include relevant context (plan name, coverage type, etc.)
        
        Format: Return each proposition on a new line, starting with "- "
        
        Text:
        {text}
        
        Propositions:
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing insurance documents and extracting atomic facts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=2000
            )
            
            propositions_text = response.choices[0].message.content
            
            # Parse propositions from response
            propositions = []
            for line in propositions_text.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    proposition = line[2:].strip()
                    if len(proposition) > 10:  # Filter out very short propositions
                        propositions.append(proposition)
            
            return propositions
            
        except Exception as e:
            print(f"Error extracting propositions: {e}")
            # Fallback to sentence-based splitting
            return self._fallback_sentence_split(text)
    
    def _fallback_sentence_split(self, text: str) -> List[str]:
        """
        Fallback method: Split text into sentences as propositions.
        Used when LLM extraction fails.
        """
        # Simple sentence splitting with insurance-specific patterns
        sentences = re.split(r'[.!?]+\s+', text)
        
        propositions = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Filter out very short sentences
                propositions.append(sentence)
        
        return propositions
    
    def group_related_propositions(self, propositions: List[str], plan_id: str) -> List[Dict[str, Any]]:
        """
        Group related propositions into coherent chunks while maintaining semantic meaning.
        """
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for i, proposition in enumerate(propositions):
            prop_tokens = len(self.tokenizer.encode(proposition))
            
            # Check if adding this proposition would exceed max tokens
            if current_tokens + prop_tokens > self.max_tokens and current_chunk:
                # Create chunk from current propositions
                chunk_text = '. '.join(current_chunk) + '.'
                chunks.append(self._create_chunk(chunk_text, plan_id, len(chunks)))
                
                # Start new chunk
                current_chunk = [proposition]
                current_tokens = prop_tokens
            else:
                current_chunk.append(proposition)
                current_tokens += prop_tokens
        
        # Add remaining propositions as final chunk
        if current_chunk:
            chunk_text = '. '.join(current_chunk) + '.'
            chunks.append(self._create_chunk(chunk_text, plan_id, len(chunks)))
        
        return chunks
    
    def semantic_grouping(self, propositions: List[str], plan_id: str) -> List[Dict[str, Any]]:
        """
        Advanced semantic grouping using embeddings to group similar propositions.
        """
        if len(propositions) <= 3:
            # For small sets, group all together
            chunk_text = '. '.join(propositions) + '.'
            return [self._create_chunk(chunk_text, plan_id, 0)]
        
        # For now, use simple grouping (can be enhanced with embeddings)
        return self.group_related_propositions(propositions, plan_id)
    
    def _create_chunk(self, text: str, plan_id: str, chunk_index: int) -> Dict[str, Any]:
        """Create a standardized chunk dictionary."""
        tokens = self.tokenizer.encode(text)
        
        return {
            "text": text,
            "metadata": {
                "chunk_id": f"{plan_id}-prop-{chunk_index}-{uuid.uuid4().hex[:8]}",
                "plan_id": plan_id,
                "token_count": len(tokens),
                "chunk_type": "proposition_based",
                "chunk_index": chunk_index
            }
        }
    
    def chunk_insurance_document(self, text: str, plan_id: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Main method to chunk insurance documents using proposition-based approach.
        """
        if not text or not text.strip():
            return []
        
        # Step 1: Extract atomic propositions
        propositions = self.extract_propositions(text)
        
        if not propositions:
            # Fallback to basic chunking if no propositions extracted
            return self._fallback_basic_chunking(text, plan_id, metadata)
        
        # Step 2: Group related propositions into chunks
        chunks = self.semantic_grouping(propositions, plan_id)
        
        # Step 3: Add additional metadata if provided
        if metadata:
            for chunk in chunks:
                chunk["metadata"].update(metadata)
        
        return chunks
    
    def _fallback_basic_chunking(self, text: str, plan_id: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Fallback to basic sentence-aware chunking if proposition extraction fails.
        """
        sentences = re.split(r'[.!?]+\s+', text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_tokens = len(self.tokenizer.encode(sentence))
            
            if current_tokens + sentence_tokens > self.max_tokens and current_chunk:
                # Create chunk
                chunk_text = '. '.join(current_chunk) + '.'
                chunk = self._create_chunk(chunk_text, plan_id, len(chunks))
                if metadata:
                    chunk["metadata"].update(metadata)
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = '. '.join(current_chunk) + '.'
            chunk = self._create_chunk(chunk_text, plan_id, len(chunks))
            if metadata:
                chunk["metadata"].update(metadata)
            chunks.append(chunk)
        
        return chunks
    
    def chunk_structured_plan_data(self, plan_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create proposition-based chunks from structured plan data.
        Each chunk represents a specific insurance concept or rule.
        """
        chunks = []
        plan_id = plan_details.get("plan_id", "unknown")
        
        # Define insurance-specific sections and their importance
        section_priorities = {
            "costs": ["premium", "deductible", "out_of_pocket_maximum", "coinsurance"],
            "coverage": ["preventive_care", "primary_care_visits", "specialist_visits", 
                        "emergency_care", "hospital_stay", "prescription_drugs"],
            "network": ["network_name", "hospital_count", "physician_count"],
            "additional_benefits": ["telehealth", "wellness_program"]
        }
        
        for main_section, subsections in section_priorities.items():
            if main_section in plan_details:
                section_data = plan_details[main_section]
                
                if isinstance(section_data, dict):
                    # Process each subsection as a separate proposition
                    for subsection in subsections:
                        if subsection in section_data:
                            proposition = self._format_insurance_proposition(
                                plan_id, main_section, subsection, section_data[subsection]
                            )
                            
                            chunk = self._create_chunk(proposition, plan_id, len(chunks))
                            chunk["metadata"]["section"] = main_section
                            chunk["metadata"]["subsection"] = subsection
                            chunks.append(chunk)
        
        return chunks
    
    def _format_insurance_proposition(self, plan_id: str, section: str, subsection: str, data: Any) -> str:
        """
        Format insurance data into readable propositions.
        """
        plan_name = plan_id.replace('-', ' ').title()
        section_name = section.replace('_', ' ').title()
        subsection_name = subsection.replace('_', ' ').title()
        
        if isinstance(data, dict):
            # Handle nested data structures
            if 'in_network' in data and 'out_of_network' in data:
                in_net = data['in_network']
                out_net = data['out_of_network']
                
                if isinstance(in_net, dict) and 'amount' in in_net:
                    return f"For {plan_name}, {subsection_name} costs ${in_net['amount']} in-network and ${out_net.get('amount', 'varies')} out-of-network."
                else:
                    return f"For {plan_name}, {subsection_name} in-network: ${in_net}, out-of-network: ${out_net}."
            else:
                # General dict handling
                formatted_items = []
                for key, value in data.items():
                    formatted_items.append(f"{key.replace('_', ' ')}: {value}")
                return f"For {plan_name} {subsection_name}: {', '.join(formatted_items)}."
        else:
            # Simple value
            return f"For {plan_name}, {subsection_name} is {data}."
