from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import logging
from Embeddings.IFPPlanKnowledgeBase import IFPPlanKnowledgeBase
import shutil
import glob
# from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Insurance Plan AI Assistant API",
    description="REST API for Insurance Plan Shopping Agent with AI capabilities",
    version="1.0.0"
)

# Add CORS middleware for Angular integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],  # Angular default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
knowledge_base: Optional[IFPPlanKnowledgeBase] = None

# Request/Response models
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    source_documents: List[dict] = []

class HealthResponse(BaseModel):
    status: str
    message: str

@app.on_event("startup")
async def startup_event():
    """Initialize the knowledge base and load documents on startup"""
    global knowledge_base

    # Load environment variables from .env file
    # load_dotenv()
    
    try:
        logger.info("Starting Insurance Plan AI Assistant API...")
        
        # Get OpenAI API key
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            raise ValueError("OPENAI_API_KEY is required")
        
        # Clear existing ChromaDB
        chroma_db_path = "./chroma_db"
        if os.path.exists(chroma_db_path):
            logger.info("Clearing existing ChromaDB...")
            shutil.rmtree(chroma_db_path)
        
        # Initialize knowledge base
        logger.info("Initializing knowledge base...")
        knowledge_base = IFPPlanKnowledgeBase(openai_api_key, db_directory=chroma_db_path)
        
        # Load all PDF documents from plan_documents directory
        plan_documents_dir = "plan_documents"
        if os.path.exists(plan_documents_dir):
            pdf_files = glob.glob(os.path.join(plan_documents_dir, "*.pdf"))
            logger.info(f"Found {len(pdf_files)} PDF files to process")
            
            for pdf_file in pdf_files:
                try:
                    # Extract plan ID from filename
                    plan_id = os.path.splitext(os.path.basename(pdf_file))[0]
                    logger.info(f"Processing document: {pdf_file} with plan_id: {plan_id}")
                    
                    # Process and store the plan
                    result = knowledge_base.process_and_store_plan(pdf_file, plan_id)
                    logger.info(f"Successfully processed {plan_id}: {result['chunks_stored']} chunks stored")
                    
                except Exception as e:
                    logger.error(f"Error processing {pdf_file}: {str(e)}")
                    continue
        else:
            logger.warning(f"Plan documents directory '{plan_documents_dir}' not found")
        
        logger.info("API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint for health check"""
    return HealthResponse(
        status="healthy", 
        message="Insurance Plan AI Assistant API is running"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if knowledge_base is None:
        raise HTTPException(status_code=503, detail="Knowledge base not initialized")
    
    return HealthResponse(
        status="healthy",
        message="API is operational and knowledge base is ready"
    )

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """
    Chat endpoint for querying the AI assistant about insurance plans
    """
    try:
        if knowledge_base is None:
            raise HTTPException(status_code=503, detail="Knowledge base not initialized")
        
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info(f"Processing query: {request.query[:100]}...")
        
        # Query the knowledge base across all plans (no plan_id filter)
        result = knowledge_base.query_knowledge_base(query=request.query)
        
        # Format source documents for response
        formatted_sources = []
        if "source_documents" in result:
            for doc in result["source_documents"]:
                formatted_sources.append({
                    "content": doc.page_content if hasattr(doc, 'page_content') else str(doc),
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {},
                    "plan_id": doc.metadata.get("plan_id", "unknown") if hasattr(doc, 'metadata') else "unknown"
                })
        
        response = ChatResponse(
            answer=result["answer"],
            source_documents=formatted_sources
        )
        
        logger.info("Query processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/plans")
async def get_available_plans():
    """Get list of available plan IDs"""
    try:
        if knowledge_base is None:
            raise HTTPException(status_code=503, detail="Knowledge base not initialized")
        
        # Get available plans from the documents directory
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
        
        return {"plans": available_plans}
        
    except Exception as e:
        logger.error(f"Error getting available plans: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
