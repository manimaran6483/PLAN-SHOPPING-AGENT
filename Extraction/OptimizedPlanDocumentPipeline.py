from typing import Any, Dict
from Extraction.PlanDocumentProcessor import PlanDocumentProcessor
from Extraction.OptimizedPlanInformationExtractor import OptimizedPlanInformationExtractor
import logging

logger = logging.getLogger(__name__)

class OptimizedPlanDocumentPipeline:
    """
    Optimized pipeline that minimizes API calls while processing plan documents.
    Uses rule-based extraction instead of LLM calls for most operations.
    """
    
    def __init__(self, openai_api_key: str = None):
        self.processor = PlanDocumentProcessor()
        self.extractor = OptimizedPlanInformationExtractor()  # No API key needed
        self.openai_api_key = openai_api_key  # Keep for future LLM fallback if needed
        
    def process_plan_document(self, pdf_path: str, plan_id: str) -> Dict[str, Any]:
        """
        Process a plan document using optimized, rule-based approach.
        Minimal API calls = Minimal token usage.
        """
        logger.info(f"Processing plan document {pdf_path} for {plan_id}")
        
        try:
            # Extract text from PDF (no API calls)
            document_text = self.processor.extract_text_from_pdf(pdf_path)
            
            if not document_text or len(document_text.strip()) < 100:
                logger.warning(f"Minimal text extracted from {pdf_path}")
                return {"plan_id": plan_id, "error": "Insufficient text extracted"}
            
            # Extract tables (no API calls)
            tables = self.processor.extract_tables_from_pdf(pdf_path)
            tables_text = ""
            if tables:
                tables_text = "\n\n".join([
                    t.to_string() if hasattr(t, 'to_string') else str(t) 
                    for t in tables if not (hasattr(t, 'empty') and t.empty)
                ])
            
            # Combine text for processing
            combined_text = f"{document_text}\n\n{tables_text}"
            
            # Extract structured information using rule-based approach (no API calls)
            plan_details = self.extractor.extract_plan_details(combined_text, plan_id)
            
            # Add raw text for chunking
            plan_details["raw_document_text"] = document_text
            plan_details["tables_text"] = tables_text
            plan_details["processing_method"] = "optimized_rule_based"
            
            logger.info(f"Successfully processed {plan_id} with {len(plan_details)} fields extracted")
            return plan_details
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {str(e)}")
            return {
                "plan_id": plan_id,
                "error": str(e),
                "processing_method": "failed"
            }
