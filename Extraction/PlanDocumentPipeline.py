from typing import Any, Dict
from Extraction.PlanDocumentProcessor import PlanDocumentProcessor
from Extraction.PlanInformationExtractor import PlanInformationExtractor


class PlanDocumentPipeline:
    def __init__(self, openai_api_key: str):
        self.processor = PlanDocumentProcessor()
        self.extractor = PlanInformationExtractor(openai_api_key)
        
    def process_plan_document(self, pdf_path: str, plan_id: str) -> Dict[str, Any]:
        """Process a plan document and extract structured information."""
        # Extract text
        document_text = self.processor.extract_text_from_pdf(pdf_path)
        
        # Extract tables and convert to text for processing
        tables = self.processor.extract_tables_from_pdf(pdf_path)
        tables_text = "\n\n".join([t.to_string() for t in tables if not t.empty])
        
        # Combine text for processing
        combined_text = f"{document_text}\n\n{tables_text}"
        
        # Extract structured information
        plan_details = self.extractor.extract_plan_details(combined_text, plan_id)
        
        return plan_details