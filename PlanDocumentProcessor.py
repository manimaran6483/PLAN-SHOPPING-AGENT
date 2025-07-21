import fitz  # PyMuPDF
import pandas as pd
from typing import Dict, Any, List

class PlanDocumentProcessor:
    def __init__(self):
        # Initialize document parsing tools
        pass
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract raw text from PDF documents."""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
            
    def extract_tables_from_pdf(self, pdf_path: str) -> List[pd.DataFrame]:
        """Extract tables from PDF documents."""
        tables = []
        try:
            # Use tabula-py or similar library for table extraction
            import tabula
            tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
            return tables
        except Exception as e:
            print(f"Error extracting tables: {e}")
            return []