from .VectorDatabaseManager import VectorDatabaseManager
from .UltraOptimizedChunker import UltraOptimizedChunker
from Extraction.ZeroTokenPipeline import ZeroTokenPipeline
from openai import OpenAI
import logging


logger = logging.getLogger(__name__)  # Logger for tracking ultra-optimization


class IFPPlanKnowledgeBase:
    """
    Ultra-optimized knowledge base that uses ZERO tokens for extraction and chunking.
    Only uses embeddings API for final vector storage, minimizing costs dramatically.
    """
    
    def __init__(self, openai_api_key: str, db_directory: str = "chroma_db"):
        self.openai_api_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key)
        self.document_pipeline = ZeroTokenPipeline()        # ZERO tokens for extraction
        self.chunker = UltraOptimizedChunker()              # ZERO tokens for chunking
        self.vector_db = VectorDatabaseManager(openai_api_key, db_directory)
        logger.info("Initialized ULTRA-OPTIMIZED knowledge base with ZERO-token processing")
        
    def process_and_store_plan(self, pdf_path: str, plan_id: str):
        """Process plan document and store in vector database with ZERO API calls for extraction/chunking."""
        logger.info(f"Starting ULTRA-OPTIMIZED processing for {plan_id}")
        
        # Extract structured information using ZERO tokens
        plan_details = self.document_pipeline.process_plan_document(pdf_path, plan_id)
        
        if "error" in plan_details:
            logger.error(f"Extraction failed for {plan_id}: {plan_details['error']}")
            return {
                "plan_id": plan_id,
                "chunks_stored": 0,
                "error": plan_details["error"],
                "tokens_used": 0
            }
        
        # Get processing summary
        processing_summary = self.document_pipeline.get_processing_summary(plan_details)
        logger.info(f"Processing summary: {processing_summary}")
        
        # Create chunks using ZERO tokens (pure rule-based)
        raw_text = plan_details.get("raw_document_text", "")
        all_chunks = self.chunker.process_document(raw_text, plan_details)
        
        logger.info(f"Generated {len(all_chunks)} chunks for {plan_id}")
        
        # Debug: Show chunk structure for first chunk
        if all_chunks:
            sample_chunk = all_chunks[0]
            logger.info(f"Sample chunk structure: {list(sample_chunk.keys())}")
            logger.info(f"Sample chunk content preview: {str(sample_chunk.get('content', ''))[:100]}...")
        
        # Store in vector database (ONLY embeddings API calls here - unavoidable)
        chunks_stored = 0
        embedding_tokens_used = 0
        
        if all_chunks:
            logger.info(f"Storing {len(all_chunks)} chunks in ChromaDB...")
            storage_result = self.vector_db.add_chunks_to_vector_db(all_chunks)
            chunks_stored = len(all_chunks) if storage_result else 0
            
            # Check if storage was successful
            collection_info = self.vector_db.get_collection_info()
            logger.info(f"ChromaDB collection info: {collection_info}")
            
            # Estimate embedding tokens (roughly 1 token per 4 chars for embeddings)
            total_chunk_text = sum(len(chunk.get("content", "")) for chunk in all_chunks)
            embedding_tokens_used = total_chunk_text // 4
        else:
            logger.warning(f"No chunks generated for {plan_id}")
        
        # Log ultra-optimization results
        extraction_summary = plan_details.get("extraction_summary", {})
        total_tokens = extraction_summary.get("tokens_used", 0) + embedding_tokens_used
        
        logger.info(f"ULTRA-OPTIMIZED RESULTS for {plan_id}:")
        logger.info(f"  - Extraction tokens: {extraction_summary.get('tokens_used', 0)}")
        logger.info(f"  - Chunking tokens: 0")
        logger.info(f"  - Embedding tokens: ~{embedding_tokens_used}")
        logger.info(f"  - Total tokens: ~{total_tokens}")
        logger.info(f"  - Chunks created: {len(all_chunks)}")
        logger.info(f"  - Features extracted: {extraction_summary.get('features_extracted', 0)}")
        
        return {
            "plan_id": plan_id,
            "chunks_stored": chunks_stored,
            "processing_summary": processing_summary,
            "optimization_stats": {
                "extraction_tokens": extraction_summary.get("tokens_used", 0),
                "chunking_tokens": 0,
                "embedding_tokens_estimate": embedding_tokens_used,
                "total_tokens_estimate": total_tokens,
                "chunks_created": len(all_chunks),
                "features_extracted": extraction_summary.get("features_extracted", 0),
                "optimization_level": "ultra_zero_token"
            }
        }
        
    def query_knowledge_base(self, query: str, plan_id: str = None):
        """Query the knowledge base for information and get LLM response."""
        logger.info(f"Querying knowledge base: '{query}' for plan_id: {plan_id}")
        
        # Check if we have any documents in the database
        collection_info = self.vector_db.get_collection_info()
        logger.info(f"Database status: {collection_info}")
        
        if not collection_info.get("has_documents", False):
            logger.warning("No documents found in vector database!")
            return {
                "answer": "I don't have any insurance plan documents loaded in the knowledge base. Please ensure PDF documents are processed first.",
                "source_documents": [],
                "query_stats": {"estimated_tokens": 0}
            }
        
        # Search for relevant documents
        search_results = self.vector_db.search(query, plan_id)
        logger.info(f"Found {len(search_results)} relevant documents")
        
        # Prepare context from search results
        context = ""
        source_documents = []
        
        for result in search_results:
            context += f"Document: {result['text']}\n\n"
            source_documents.append({
                "page_content": result['text'],
                "metadata": result['metadata']
            })
        
        if not context.strip():
            logger.warning("No relevant context found for query")
            return {
                "answer": "I don't have specific information about that topic in the available insurance plans. Please try rephrasing your question or ask about coverage details, costs, or benefits.",
                "source_documents": [],
                "query_stats": {"estimated_tokens": 0}
            }
        
        # Create optimized prompt for LLM
        prompt = f"""Based on the following insurance plan information, answer the user's question accurately and concisely.

Context:
{context.strip()}

Question: {query}

Please provide a helpful answer based only on the information provided above."""
        
        try:
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheaper model for responses
                messages=[
                    {"role": "system", "content": "You are a helpful insurance plan assistant. Provide accurate, specific answers based only on the provided document context. If the information isn't available, say so clearly."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500  # Reduced for cost efficiency  
            )
            
            answer = response.choices[0].message.content
            
            logger.info(f"Query processed successfully. Response tokens: ~{len(answer)//4}")
            
            return {
                "answer": answer,
                "source_documents": source_documents,
                "query_stats": {
                    "context_documents": len(source_documents),
                    "response_model": "gpt-4o-mini",
                    "estimated_tokens": len(prompt)//4 + len(answer)//4
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": f"I apologize, but I encountered an error while processing your question: {str(e)}",
                "source_documents": source_documents
            }