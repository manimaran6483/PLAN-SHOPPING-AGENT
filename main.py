from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import logging
from Embeddings.IFPPlanKnowledgeBase import IFPPlanKnowledgeBase
from token_monitor import get_token_monitor
import shutil
import glob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get token monitor for ultra-optimization tracking
token_monitor = get_token_monitor()

# Initialize FastAPI app
app = FastAPI(
    title="Ultra-Optimized Insurance Plan AI Assistant",
    description="RESTful API for insurance plan processing with ZERO-token extraction and chunking",
    version="2.0.0-ultra"
)

# Add CORS middleware for Angular integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    source_documents: List[Dict[str, Any]] = []

class HealthResponse(BaseModel):
    status: str
    message: str

# Global knowledge base instance
knowledge_base = None

@app.on_event("startup")
async def startup_event():
    """Initialize the ultra-optimized knowledge base on startup"""
    global knowledge_base
    
    try:
        # Get OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY environment variable is not set!")
            raise ValueError("OPENAI_API_KEY is required")
        
        logger.info("Starting ULTRA-OPTIMIZED Insurance Plan API...")
        
        # Create fresh ChromaDB directory
        chroma_db_path = "chroma_db"
        if os.path.exists(chroma_db_path):
            logger.info(f"Removing existing ChromaDB directory: {chroma_db_path}")
            shutil.rmtree(chroma_db_path)
        
        os.makedirs(chroma_db_path, exist_ok=True)
        logger.info(f"Created fresh ChromaDB directory: {chroma_db_path}")
        
        # Initialize ultra-optimized knowledge base
        logger.info("Initializing ULTRA-OPTIMIZED knowledge base (ZERO extraction/chunking tokens)...")
        knowledge_base = IFPPlanKnowledgeBase(openai_api_key, db_directory=chroma_db_path)
        
        # Process PDF documents with ultra-optimization
        plan_documents_dir = "plan_documents"
        if not os.path.exists(plan_documents_dir):
            logger.warning(f"Plan documents directory '{plan_documents_dir}' not found. Creating it...")
            os.makedirs(plan_documents_dir, exist_ok=True)
            logger.info(f"Created directory '{plan_documents_dir}'. Please add your PDF files to this directory.")
        
        if os.path.exists(plan_documents_dir):
            pdf_files = glob.glob(os.path.join(plan_documents_dir, "*.pdf"))
            logger.info(f"Found {len(pdf_files)} PDF files to process with ULTRA-OPTIMIZATION")
            
            if len(pdf_files) == 0:
                logger.warning("No PDF files found in plan_documents directory")
            
            for pdf_file in pdf_files:
                try:
                    plan_id = os.path.splitext(os.path.basename(pdf_file))[0]
                    logger.info(f"Processing {pdf_file} with ZERO-TOKEN pipeline...")
                    
                    # Process with ultra-optimization (ZERO tokens for extraction/chunking)
                    result = knowledge_base.process_and_store_plan(pdf_file, plan_id)
                    
                    # Log token usage
                    if "optimization_stats" in result:
                        token_monitor.log_document_processing(plan_id, result["optimization_stats"])
                        stats = result["optimization_stats"]
                        logger.info(f"ULTRA-OPTIMIZATION RESULTS for {plan_id}:")
                        logger.info(f"   Extraction tokens: {stats.get('extraction_tokens', 0)} (Target: 0)")
                        logger.info(f"   Chunking tokens: {stats.get('chunking_tokens', 0)} (Target: 0)")
                        logger.info(f"   Embedding tokens: ~{stats.get('embedding_tokens_estimate', 0)}")
                        logger.info(f"   Features extracted: {stats.get('features_extracted', 0)}")
                        logger.info(f"   Chunks created: {stats.get('chunks_created', 0)}")
                    
                    logger.info(f"Successfully processed {plan_id}: {result['chunks_stored']} chunks stored")
                    
                except Exception as e:
                    logger.error(f"Error processing {pdf_file}: {str(e)}")
                    continue
        
        # Generate comprehensive optimization report
        logger.info("Generating ULTRA-OPTIMIZATION report...")
        token_monitor.print_optimization_report()
        
        logger.info("ULTRA-OPTIMIZED API startup completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint for health check"""
    return HealthResponse(
        status="healthy", 
        message="Ultra-Optimized Insurance Plan AI Assistant API is running with ZERO-token processing!"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if knowledge_base is None:
        raise HTTPException(status_code=503, detail="Knowledge base not initialized")
    
    return HealthResponse(
        status="healthy",
        message="API is operational with ultra-optimized knowledge base ready"
    )

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """
    Ultra-optimized chat endpoint for querying insurance plans
    Uses minimal tokens - only for final LLM response generation
    """
    try:
        if knowledge_base is None:
            raise HTTPException(status_code=503, detail="Knowledge base not initialized")
        
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info(f"Processing ultra-optimized query: {request.query[:100]}...")
        
        # Query using ultra-optimized knowledge base
        result = knowledge_base.query_knowledge_base(query=request.query)
        
        # Log query token usage
        if "query_stats" in result:
            token_monitor.log_query_processing(request.query, result["query_stats"])
            logger.info(f"Query tokens used: ~{result['query_stats'].get('estimated_tokens', 0)}")
        
        # Format source documents
        formatted_sources = []
        if "source_documents" in result:
            for doc in result["source_documents"]:
                formatted_sources.append({
                    "content": doc.get("page_content", str(doc)),
                    "metadata": doc.get("metadata", {}),
                    "plan_id": doc.get("metadata", {}).get("plan_id", "unknown") if isinstance(doc.get("metadata"), dict) else "unknown"
                })
        
        response = ChatResponse(
            answer=result["answer"],
            source_documents=formatted_sources
        )
        
        logger.info("Ultra-optimized query processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/plans")
async def get_available_plans():
    """Get list of available insurance plan IDs"""
    try:
        if knowledge_base is None:
            raise HTTPException(status_code=503, detail="Knowledge base not initialized")
        
        plan_documents_dir = "plan_documents"
        available_plans = []
        
        if os.path.exists(plan_documents_dir):
            pdf_files = glob.glob(os.path.join(plan_documents_dir, "*.pdf"))
            for pdf_file in pdf_files:
                plan_id = os.path.splitext(os.path.basename(pdf_file))[0]
                available_plans.append({
                    "plan_id": plan_id,
                    "filename": os.path.basename(pdf_file)
                })
        
        return {"available_plans": available_plans}
        
    except Exception as e:
        logger.error(f"Error getting available plans: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/optimization-stats")
async def get_optimization_stats():
    """Get comprehensive ultra-optimization statistics and token usage"""
    try:
        optimization_report = token_monitor.get_optimization_report()
        return {
            "status": "success",
            "optimization_report": optimization_report,
            "message": "Ultra-optimization statistics retrieved - check your token savings!"
        }
    except Exception as e:
        logger.error(f"Error getting optimization stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/database-status")
async def get_database_status():
    """Get ChromaDB collection status and document count"""
    try:
        if knowledge_base is None:
            raise HTTPException(status_code=503, detail="Knowledge base not initialized")
        
        collection_info = knowledge_base.vector_db.get_collection_info()
        
        return {
            "status": "success",
            "database_info": collection_info,
            "message": f"Database has {'documents' if collection_info.get('has_documents') else 'no documents'}"
        }
    except Exception as e:
        logger.error(f"Error getting database status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)