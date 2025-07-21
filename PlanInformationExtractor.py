from typing import Any, Dict
from openai import OpenAI
import re
import json

class PlanInformationExtractor:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        
    def extract_plan_details(self, document_text: str, plan_id: str) -> Dict[str, Any]:
        """Extract structured details from plan document text using LLM."""
        
        # Define sections we want to extract
        sections = [
            "deductible", 
            "copayments", 
            "coinsurance", 
            "out_of_pocket_maximum",
            "prescription_coverage",
            "specialist_coverage",
            "emergency_services",
            "hospitalization",
            "preventive_care",
            "mental_health_services",
            "maternity_care"
        ]
        
        # Use regex to locate sections (can be enhanced with more sophisticated patterns)
        section_data = {}
        for section in sections:
            # Convert underscores to spaces for searching
            search_term = section.replace("_", " ")
            
            # Simple pattern matching - would need refinement for real documents
            pattern = re.compile(f"({search_term}|{search_term.title()})[\s\:]+(.*?)(?=\n\n|\Z)", 
                               re.IGNORECASE | re.DOTALL)
            matches = pattern.findall(document_text)
            if matches:
                section_data[section] = matches[0][1].strip()
        
        # For complex extraction, use LLM approach
        if not section_data or len(section_data) < 5:  # Fallback if regex fails
            return self._extract_with_llm(document_text, plan_id)
            
        # Add plan identifier
        section_data["plan_id"] = plan_id
        return section_data
        
    def _extract_with_llm(self, document_text: str, plan_id: str) -> Dict[str, Any]:
        """Use LLM to extract structured information from document text."""
        
        # For long documents, we might need to chunk and process separately
        # This is a simplified version
        
        prompt = f"""
        You are an expert in health insurance plans. Extract the following information from 
        the plan document text below. Return ONLY a JSON object with these keys:
        
        - deductible: Individual and family deductible amounts
        - copayments: Copay amounts for different services
        - coinsurance: Coinsurance percentages for different services
        - out_of_pocket_maximum: Maximum out-of-pocket expenses
        - prescription_coverage: Details about prescription drug coverage
        - specialist_coverage: Coverage for specialist visits
        - emergency_services: Coverage for emergency services
        - hospitalization: Coverage for hospital stays
        - preventive_care: Coverage for preventive services
        - mental_health_services: Coverage for mental health services
        - maternity_care: Coverage for maternity services
        
        If information for any field is not found, use "Not specified" as the value.
        
        DOCUMENT TEXT:
        {document_text[:4000]}  # Truncated for API limits
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        extracted_info = json.loads(response.choices[0].message.content)
        extracted_info["plan_id"] = plan_id
        return extracted_info