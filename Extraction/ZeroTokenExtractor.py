import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ZeroTokenExtractor:
    """
    Ultra-efficient extractor that uses ZERO OpenAI tokens.
    Pure regex-based pattern matching for insurance plan data.
    Designed for maximum speed and minimum cost.
    """
    
    def __init__(self):
        # Compiled regex patterns for efficiency
        self.patterns = {
            'deductible': re.compile(r'deductible[:\s]*\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
            'copay': re.compile(r'copay[:\s]*\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
            'coinsurance': re.compile(r'coinsurance[:\s]*(\d+)%?', re.IGNORECASE),
            'premium': re.compile(r'premium[:\s]*\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
            'out_of_pocket_max': re.compile(r'out.of.pocket[:\s]*maximum[:\s]*\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
            'plan_name': re.compile(r'(?:plan\s+name|product\s+name)[:\s]*([^\n\r]{10,100})', re.IGNORECASE),
            'carrier': re.compile(r'(?:carrier|insurance\s+company|insurer)[:\s]*([^\n\r]{5,50})', re.IGNORECASE),
            'network_type': re.compile(r'(?:network\s+type|plan\s+type)[:\s]*([^\n\r]{3,30})', re.IGNORECASE)
        }
        
        # Money pattern for general cost extraction
        self.money_pattern = re.compile(r'\$[\d,]+(?:\.\d{2})?')
        self.percentage_pattern = re.compile(r'\d+(?:\.\d+)?%')
        
        # Insurance-specific keywords for categorization
        self.category_keywords = {
            'medical': ['medical', 'physician', 'hospital', 'surgery', 'diagnostic'],
            'prescription': ['prescription', 'drug', 'pharmacy', 'medication', 'formulary'],
            'preventive': ['preventive', 'wellness', 'screening', 'vaccination', 'physical'],
            'emergency': ['emergency', 'urgent', 'ambulance', 'er'],
            'specialist': ['specialist', 'referral', 'consultation'],
            'mental_health': ['mental health', 'behavioral', 'therapy', 'counseling'],
            'maternity': ['maternity', 'pregnancy', 'delivery', 'prenatal']
        }
    
    def extract_costs(self, text: str) -> Dict[str, Any]:
        """Extract cost information using regex patterns only."""
        costs = {}
        
        # Extract specific cost types
        for cost_type, pattern in self.patterns.items():
            if cost_type in ['deductible', 'copay', 'premium', 'out_of_pocket_max']:
                matches = pattern.findall(text)
                if matches:
                    # Take the first match and clean it
                    cost_value = matches[0].replace(',', '')
                    try:
                        costs[cost_type] = float(cost_value)
                    except ValueError:
                        costs[cost_type] = cost_value
        
        # Extract coinsurance percentage
        coinsurance_matches = self.patterns['coinsurance'].findall(text)
        if coinsurance_matches:
            try:
                costs['coinsurance_percent'] = int(coinsurance_matches[0])
            except ValueError:
                costs['coinsurance_percent'] = coinsurance_matches[0]
        
        return costs
    
    def extract_plan_basics(self, text: str) -> Dict[str, str]:
        """Extract basic plan information using regex."""
        basics = {}
        
        # Extract plan name
        plan_matches = self.patterns['plan_name'].findall(text)
        if plan_matches:
            basics['plan_name'] = plan_matches[0].strip()
        
        # Extract carrier
        carrier_matches = self.patterns['carrier'].findall(text)
        if carrier_matches:
            basics['carrier'] = carrier_matches[0].strip()
        
        # Extract network type
        network_matches = self.patterns['network_type'].findall(text)
        if network_matches:
            basics['network_type'] = network_matches[0].strip()
        
        return basics
    
    def extract_coverage_by_category(self, text: str) -> Dict[str, List[str]]:
        """Categorize coverage information by service type."""
        coverage = {}
        
        # Convert text to lowercase for matching
        text_lower = text.lower()
        
        for category, keywords in self.category_keywords.items():
            category_coverage = []
            
            for keyword in keywords:
                # Find sentences containing the keyword
                keyword_pattern = rf'[^.!?]*{re.escape(keyword)}[^.!?]*[.!?]'
                matches = re.findall(keyword_pattern, text, re.IGNORECASE)
                
                for match in matches:
                    # Clean up the sentence
                    sentence = match.strip()
                    if len(sentence) > 20:  # Filter out very short matches
                        category_coverage.append(sentence)
            
            if category_coverage:
                coverage[category] = category_coverage[:3]  # Limit to top 3 per category
        
        return coverage
    
    def extract_network_info(self, text: str) -> Dict[str, Any]:
        """Extract network and provider information."""
        network_info = {}
        
        # Look for in-network vs out-of-network mentions
        in_network_pattern = r'in.network[^.!?]*[.!?]'
        out_network_pattern = r'out.of.network[^.!?]*[.!?]'
        
        in_network_mentions = re.findall(in_network_pattern, text, re.IGNORECASE)
        out_network_mentions = re.findall(out_network_pattern, text, re.IGNORECASE)
        
        if in_network_mentions:
            network_info['in_network_coverage'] = in_network_mentions[:2]
        
        if out_network_mentions:
            network_info['out_network_coverage'] = out_network_mentions[:2]
        
        return network_info
    
    def extract_key_numbers(self, text: str) -> Dict[str, List[str]]:
        """Extract all important numbers from the document."""
        numbers = {
            'dollar_amounts': [],
            'percentages': []
        }
        
        # Extract dollar amounts
        money_matches = self.money_pattern.findall(text)
        numbers['dollar_amounts'] = list(set(money_matches))[:10]  # Unique values, limit 10
        
        # Extract percentages
        percent_matches = self.percentage_pattern.findall(text)
        numbers['percentages'] = list(set(percent_matches))[:10]  # Unique values, limit 10
        
        return numbers
    
    def extract_plan_details(self, text: str, plan_id: str) -> Dict[str, Any]:
        """
        Main extraction method using ZERO API tokens.
        Pure regex-based extraction for maximum efficiency.
        """
        logger.info(f"Extracting plan details for {plan_id} using zero-token approach")
        
        if not text or len(text.strip()) < 100:
            logger.warning(f"Insufficient text for extraction: {plan_id}")
            return {
                "plan_id": plan_id,
                "error": "Insufficient text for extraction"
            }
        
        # Extract all information using regex patterns
        plan_details = {
            "plan_id": plan_id,
            "extraction_method": "zero_token_regex",
            "text_length": len(text)
        }
        
        # Extract basic plan information
        plan_basics = self.extract_plan_basics(text)
        plan_details.update(plan_basics)
        
        # Extract cost structure
        costs = self.extract_costs(text)
        if costs:
            plan_details["cost_structure"] = costs
        
        # Extract coverage by category
        coverage = self.extract_coverage_by_category(text)
        if coverage:
            plan_details["coverage_by_category"] = coverage
        
        # Extract network information
        network_info = self.extract_network_info(text)
        if network_info:
            plan_details["network_information"] = network_info
        
        # Extract key numbers
        key_numbers = self.extract_key_numbers(text)
        if key_numbers:
            plan_details["key_financial_data"] = key_numbers
        
        # Create a summary of extracted features
        features_found = []
        if plan_basics:
            features_found.extend(plan_basics.keys())
        if costs:
            features_found.extend(costs.keys())
        if coverage:
            features_found.append(f"coverage_categories: {len(coverage)}")
        
        plan_details["extraction_summary"] = {
            "features_extracted": len(features_found),
            "feature_list": features_found,
            "api_calls_used": 0,  # Zero API calls!
            "tokens_used": 0      # Zero tokens!
        }
        
        logger.info(f"Extracted {len(features_found)} features for {plan_id} with ZERO tokens")
        
        return plan_details
    
    def quick_plan_summary(self, plan_details: Dict[str, Any]) -> str:
        """Generate a quick text summary of the plan without API calls."""
        plan_id = plan_details.get("plan_id", "Unknown Plan")
        summary_parts = [f"Plan: {plan_id}"]
        
        # Add plan name if available
        if "plan_name" in plan_details:
            summary_parts.append(f"Name: {plan_details['plan_name']}")
        
        # Add cost information
        costs = plan_details.get("cost_structure", {})
        if costs:
            cost_summary = []
            if "deductible" in costs:
                cost_summary.append(f"Deductible: ${costs['deductible']}")
            if "copay" in costs:
                cost_summary.append(f"Copay: ${costs['copay']}")
            if "coinsurance_percent" in costs:
                cost_summary.append(f"Coinsurance: {costs['coinsurance_percent']}%")
            
            if cost_summary:
                summary_parts.append("Costs: " + ", ".join(cost_summary))
        
        # Add coverage information
        coverage = plan_details.get("coverage_by_category", {})
        if coverage:
            coverage_types = list(coverage.keys())
            summary_parts.append(f"Coverage: {', '.join(coverage_types)}")
        
        return " | ".join(summary_parts)
