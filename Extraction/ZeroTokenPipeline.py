from typing import Any, Dict
from Extraction.PlanDocumentProcessor import PlanDocumentProcessor
from Extraction.ZeroTokenExtractor import ZeroTokenExtractor
import logging

logger = logging.getLogger(__name__)

class ZeroTokenPipeline:
    """
    Ultra-optimized pipeline that uses ZERO OpenAI tokens for processing.
    Only uses embeddings API for final vector storage.
    Maximum efficiency, minimum cost.
    """
    
    def __init__(self):
        self.processor = PlanDocumentProcessor()
        self.extractor = ZeroTokenExtractor()  # Zero tokens for extraction
        
    def process_plan_document(self, pdf_path: str, plan_id: str) -> Dict[str, Any]:
        """
        Process plan document with ZERO token usage for extraction/chunking.
        Only embeddings will use tokens (unavoidable for vector storage).
        """
        logger.info(f"Processing {pdf_path} for {plan_id} with zero-token pipeline")
        
        try:
            # Extract text from PDF (no API calls)
            document_text = self.processor.extract_text_from_pdf(pdf_path)
            
            if not document_text or len(document_text.strip()) < 100:
                logger.warning(f"Minimal text extracted from {pdf_path}")
                return {
                    "plan_id": plan_id,
                    "error": "Insufficient text extracted from PDF"
                }
            
            # Extract tables (no API calls)
            tables = self.processor.extract_tables_from_pdf(pdf_path)
            tables_text = ""
            if tables:
                try:
                    tables_text = "\n\n".join([
                        t.to_string() if hasattr(t, 'to_string') else str(t) 
                        for t in tables if not (hasattr(t, 'empty') and t.empty)
                    ])
                except Exception as e:
                    logger.warning(f"Error processing tables for {plan_id}: {e}")
                    tables_text = ""
            
            # Combine all text
            full_text = f"{document_text}\n\n{tables_text}".strip()
            
            # Extract structured information using ZERO tokens
            plan_details = self.extractor.extract_plan_details(full_text, plan_id)
            
            if "error" in plan_details:
                return plan_details
            
            # Add raw text for chunking
            plan_details["raw_document_text"] = document_text
            plan_details["tables_text"] = tables_text
            plan_details["full_text"] = full_text
            
            # Add processing metadata
            plan_details["processing_stats"] = {
                "document_length": len(document_text),
                "tables_found": len(tables) if tables else 0,
                "total_text_length": len(full_text),
                "extraction_tokens_used": 0,  # Zero!
                "chunking_tokens_used": 0,    # Will be zero!
                "pipeline_version": "zero_token_v1"
            }
            
            logger.info(f"Successfully processed {plan_id} with ZERO extraction tokens")
            
            return plan_details
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path} for {plan_id}: {str(e)}")
            return {
                "plan_id": plan_id,
                "error": f"Processing failed: {str(e)}"
            }
    
    def get_processing_summary(self, plan_details: Dict[str, Any]) -> str:
        """Generate a processing summary without using any tokens."""
        stats = plan_details.get("processing_stats", {})
        extraction_summary = plan_details.get("extraction_summary", {})
        
        summary_parts = [
            f"Plan ID: {plan_details.get('plan_id', 'Unknown')}",
            f"Text Length: {stats.get('document_length', 0):,} chars",
            f"Features Extracted: {extraction_summary.get('features_extracted', 0)}",
            f"Tokens Used: {extraction_summary.get('tokens_used', 0)}",  # Should be 0
            f"API Calls: {extraction_summary.get('api_calls_used', 0)}"   # Should be 0
        ]
        
        return " | ".join(summary_parts)
