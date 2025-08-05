from typing import Any, Dict
import re
import logging

logger = logging.getLogger(__name__)

class OptimizedPlanInformationExtractor:
    """
    Optimized extractor that uses rule-based patterns instead of LLM calls
    to minimize token usage while extracting key insurance information.
    """
    
    def __init__(self):
        # Define patterns for key insurance terms
        self.extraction_patterns = {
            "deductible": [
                r'(?i)deductible[:\s]+\$?(\d+(?:,\d+)?(?:\.\d{2})?)',
                r'(?i)\$(\d+(?:,\d+)?(?:\.\d{2})?)[\s]+deductible',
                r'(?i)individual.*deductible[:\s]+\$?(\d+(?:,\d+)?(?:\.\d{2})?)',
                r'(?i)family.*deductible[:\s]+\$?(\d+(?:,\d+)?(?:\.\d{2})?)'
            ],
            "copayments": [
                r'(?i)copay[:\s]+\$?(\d+(?:\.\d{2})?)',
                r'(?i)co-pay[:\s]+\$?(\d+(?:\.\d{2})?)',
                r'(?i)primary.*care[:\s]+\$?(\d+(?:\.\d{2})?)',
                r'(?i)specialist[:\s]+\$?(\d+(?:\.\d{2})?)'
            ],
            "coinsurance": [
                r'(?i)coinsurance[:\s]+(\d+)%',
                r'(?i)(\d+)%.*coinsurance',
                r'(?i)you.*pay[:\s]+(\d+)%'
            ],
            "out_of_pocket_maximum": [
                r'(?i)out.of.pocket.*maximum[:\s]+\$?(\d+(?:,\d+)?(?:\.\d{2})?)',
                r'(?i)maximum.*out.of.pocket[:\s]+\$?(\d+(?:,\d+)?(?:\.\d{2})?)',
                r'(?i)annual.*limit[:\s]+\$?(\d+(?:,\d+)?(?:\.\d{2})?)'
            ],
            "premium": [
                r'(?i)premium[:\s]+\$?(\d+(?:,\d+)?(?:\.\d{2})?)',
                r'(?i)monthly.*cost[:\s]+\$?(\d+(?:,\d+)?(?:\.\d{2})?)',
                r'(?i)\$(\d+(?:,\d+)?(?:\.\d{2})?).*per.*month'
            ]
        }
    
    def extract_plan_details(self, document_text: str, plan_id: str) -> Dict[str, Any]:
        """
        Extract plan details using efficient rule-based patterns.
        No LLM calls = No token usage for extraction.
        """
        logger.info(f"Extracting plan details for {plan_id} using rule-based approach")
        
        extracted_info = {"plan_id": plan_id}
        
        # Extract each type of information using patterns
        for info_type, patterns in self.extraction_patterns.items():
            values = []
            
            for pattern in patterns:
                matches = re.finditer(pattern, document_text)
                for match in matches:
                    value = match.group(1)
                    if value not in values:  # Avoid duplicates
                        values.append(value)
            
            if values:
                # Take the first value or combine multiple values
                if len(values) == 1:
                    extracted_info[info_type] = f"${values[0]}" if info_type != "coinsurance" else f"{values[0]}%"
                else:
                    # For multiple values, create a structured response
                    extracted_info[info_type] = {
                        "values": values,
                        "primary": f"${values[0]}" if info_type != "coinsurance" else f"{values[0]}%"
                    }
            else:
                extracted_info[info_type] = "Not specified in document"
        
        # Extract additional insurance-specific information
        extracted_info.update(self._extract_coverage_details(document_text))
        extracted_info.update(self._extract_network_info(document_text))
        
        logger.info(f"Extracted {len(extracted_info)} fields for {plan_id}")
        return extracted_info
    
    def _extract_coverage_details(self, text: str) -> Dict[str, str]:
        """Extract coverage-specific details."""
        coverage_patterns = {
            "emergency_services": [
                r'(?i)emergency.*room[:\s]+\$?(\d+(?:\.\d{2})?)',
                r'(?i)er.*visit[:\s]+\$?(\d+(?:\.\d{2})?)'
            ],
            "specialist_coverage": [
                r'(?i)specialist.*visit[:\s]+\$?(\d+(?:\.\d{2})?)',
                r'(?i)specialist.*copay[:\s]+\$?(\d+(?:\.\d{2})?)'
            ],
            "prescription_coverage": [
                r'(?i)generic.*drug[:\s]+\$?(\d+(?:\.\d{2})?)',
                r'(?i)brand.*drug[:\s]+\$?(\d+(?:\.\d{2})?)',
                r'(?i)prescription[:\s]+\$?(\d+(?:\.\d{2})?)'
            ]
        }
        
        coverage_info = {}
        for coverage_type, patterns in coverage_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    coverage_info[coverage_type] = f"${match.group(1)}"
                    break
            
            if coverage_type not in coverage_info:
                coverage_info[coverage_type] = "Not specified"
        
        return coverage_info
    
    def _extract_network_info(self, text: str) -> Dict[str, str]:
        """Extract network information."""
        network_patterns = {
            "network_type": [
                r'(?i)(HMO|PPO|EPO|POS)',
                r'(?i)(Health Maintenance Organization|Preferred Provider Organization)'
            ],
            "network_name": [
                r'(?i)network[:\s]+([A-Z][A-Za-z\s]+(?:Network|Health|Medical))',
                r'(?i)provider.*network[:\s]+([A-Z][A-Za-z\s]+)'
            ]
        }
        
        network_info = {}
        for net_type, patterns in network_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    network_info[net_type] = match.group(1).strip()
                    break
            
            if net_type not in network_info:
                network_info[net_type] = "Not specified"
        
        return network_info
