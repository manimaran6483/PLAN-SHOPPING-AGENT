"""
Token Usage Monitor for Ultra-Optimized Insurance Plan Processing

This script monitors and reports token usage across the entire pipeline
to help track optimization effectiveness and costs.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List
import os

logger = logging.getLogger(__name__)

class TokenUsageMonitor:
    """
    Monitor and track token usage across the pipeline to ensure 
    ultra-optimization is working effectively.
    """
    
    def __init__(self, log_file: str = "token_usage.json"):
        self.log_file = log_file
        self.session_stats = {
            "session_start": datetime.now().isoformat(),
            "total_documents_processed": 0,
            "total_extraction_tokens": 0,
            "total_chunking_tokens": 0,
            "total_embedding_tokens": 0,
            "total_query_tokens": 0,
            "optimization_level": "ultra_zero_token",
            "document_stats": []
        }
        
        # Load existing stats if available
        self.load_existing_stats()
    
    def load_existing_stats(self):
        """Load existing usage statistics."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    existing_data = json.load(f)
                    if "total_documents_processed" in existing_data:
                        # Preserve historical data
                        self.session_stats["historical_total_documents"] = existing_data.get("total_documents_processed", 0)
                        self.session_stats["historical_total_tokens"] = (
                            existing_data.get("total_extraction_tokens", 0) +
                            existing_data.get("total_chunking_tokens", 0) +
                            existing_data.get("total_embedding_tokens", 0) +
                            existing_data.get("total_query_tokens", 0)
                        )
            except Exception as e:
                logger.warning(f"Could not load existing stats: {e}")
    
    def log_document_processing(self, plan_id: str, optimization_stats: Dict[str, Any]):
        """Log token usage for document processing."""
        doc_stats = {
            "plan_id": plan_id,
            "timestamp": datetime.now().isoformat(),
            "extraction_tokens": optimization_stats.get("extraction_tokens", 0),
            "chunking_tokens": optimization_stats.get("chunking_tokens", 0),
            "embedding_tokens": optimization_stats.get("embedding_tokens_estimate", 0),
            "chunks_created": optimization_stats.get("chunks_created", 0),
            "features_extracted": optimization_stats.get("features_extracted", 0),
            "optimization_level": optimization_stats.get("optimization_level", "unknown")
        }
        
        # Update session totals
        self.session_stats["total_documents_processed"] += 1
        self.session_stats["total_extraction_tokens"] += doc_stats["extraction_tokens"]
        self.session_stats["total_chunking_tokens"] += doc_stats["chunking_tokens"]
        self.session_stats["total_embedding_tokens"] += doc_stats["embedding_tokens"]
        self.session_stats["document_stats"].append(doc_stats)
        
        # Log the achievement
        logger.info(f"TOKEN USAGE for {plan_id}:")
        logger.info(f"  Extraction: {doc_stats['extraction_tokens']} tokens")
        logger.info(f"  Chunking: {doc_stats['chunking_tokens']} tokens")
        logger.info(f"  Embeddings: ~{doc_stats['embedding_tokens']} tokens")
        logger.info(f"  Total: ~{doc_stats['extraction_tokens'] + doc_stats['chunking_tokens'] + doc_stats['embedding_tokens']} tokens")
        
        # Save updated stats
        self.save_stats()
    
    def log_query_processing(self, query: str, query_stats: Dict[str, Any]):
        """Log token usage for query processing."""
        query_tokens = query_stats.get("estimated_tokens", 0)
        self.session_stats["total_query_tokens"] += query_tokens
        
        logger.info(f"QUERY TOKEN USAGE: ~{query_tokens} tokens for query: '{query[:50]}...'")
        
        # Save updated stats
        self.save_stats()
    
    def save_stats(self):
        """Save current statistics to file."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.session_stats, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save token usage stats: {e}")
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        total_tokens = (
            self.session_stats["total_extraction_tokens"] +
            self.session_stats["total_chunking_tokens"] +
            self.session_stats["total_embedding_tokens"] +
            self.session_stats["total_query_tokens"]
        )
        
        docs_processed = self.session_stats["total_documents_processed"]
        avg_tokens_per_doc = total_tokens / docs_processed if docs_processed > 0 else 0
        
        # Calculate cost estimates (rough OpenAI pricing)
        embedding_cost = (self.session_stats["total_embedding_tokens"] / 1000) * 0.0001  # $0.0001 per 1K tokens
        gpt4_mini_cost = ((total_tokens - self.session_stats["total_embedding_tokens"]) / 1000) * 0.0015  # $0.0015 per 1K tokens
        total_cost = embedding_cost + gpt4_mini_cost
        
        report = {
            "optimization_summary": {
                "optimization_level": "ultra_zero_token",
                "session_start": self.session_stats["session_start"],
                "documents_processed": docs_processed,
                "total_tokens_used": total_tokens,
                "average_tokens_per_document": round(avg_tokens_per_doc, 2),
                "estimated_cost_usd": round(total_cost, 4)
            },
            "token_breakdown": {
                "extraction_tokens": self.session_stats["total_extraction_tokens"],
                "chunking_tokens": self.session_stats["total_chunking_tokens"],
                "embedding_tokens": self.session_stats["total_embedding_tokens"],
                "query_tokens": self.session_stats["total_query_tokens"]
            },
            "cost_breakdown": {
                "embedding_cost_usd": round(embedding_cost, 4),
                "processing_cost_usd": round(gpt4_mini_cost, 4),
                "total_cost_usd": round(total_cost, 4)
            },
            "optimization_achievements": [
                f"Extraction tokens: {self.session_stats['total_extraction_tokens']} (Target: 0 SUCCESS)" if self.session_stats['total_extraction_tokens'] == 0 else f"Extraction tokens: {self.session_stats['total_extraction_tokens']} (Target: 0 FAIL)",
                f"Chunking tokens: {self.session_stats['total_chunking_tokens']} (Target: 0 SUCCESS)" if self.session_stats['total_chunking_tokens'] == 0 else f"Chunking tokens: {self.session_stats['total_chunking_tokens']} (Target: 0 FAIL)",
                f"Only embedding tokens used for processing: {self.session_stats['total_embedding_tokens']}",
                f"Average tokens per document: {round(avg_tokens_per_doc, 2)}"
            ],
            "historical_data": {
                "historical_documents": self.session_stats.get("historical_total_documents", 0),
                "historical_tokens": self.session_stats.get("historical_total_tokens", 0)
            }
        }
        
        return report
    
    def print_optimization_report(self):
        """Print a formatted optimization report."""
        report = self.get_optimization_report()
        
        print("\n" + "="*60)
        print("ULTRA-OPTIMIZATION TOKEN USAGE REPORT")
        print("="*60)
        
        print(f"\nDocuments Processed: {report['optimization_summary']['documents_processed']}")
        print(f"Total Tokens Used: {report['optimization_summary']['total_tokens_used']:,}")
        print(f"Average Tokens/Doc: {report['optimization_summary']['average_tokens_per_document']}")
        print(f"Estimated Cost: ${report['optimization_summary']['estimated_cost_usd']}")
        
        print(f"\nToken Breakdown:")
        print(f"  Extraction: {report['token_breakdown']['extraction_tokens']:,} tokens")
        print(f"  Chunking: {report['token_breakdown']['chunking_tokens']:,} tokens")
        print(f"  Embeddings: {report['token_breakdown']['embedding_tokens']:,} tokens")
        print(f"  Queries: {report['token_breakdown']['query_tokens']:,} tokens")
        
        print(f"\nOptimization Status:")
        for achievement in report['optimization_achievements']:
            print(f"  • {achievement}")
        
        print("\n" + "="*60)

# Global monitor instance
token_monitor = TokenUsageMonitor()

def get_token_monitor() -> TokenUsageMonitor:
    """Get the global token usage monitor."""
    return token_monitor
