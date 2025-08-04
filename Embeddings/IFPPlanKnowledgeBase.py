from Embeddings.VectorDatabaseManager import VectorDatabaseManager
from Embeddings.DocumentChunker import DocumentChunker
from Extraction.PlanDocumentPipeline import PlanDocumentPipeline


class IFPPlanKnowledgeBase:
    def __init__(self, openai_api_key: str, db_directory: str = "chroma_db"):
        print(openai_api_key)
        self.document_pipeline = PlanDocumentPipeline(openai_api_key)
        self.chunker = DocumentChunker()
        self.vector_db = VectorDatabaseManager(openai_api_key, db_directory)
        
    def process_and_store_plan(self, pdf_path: str, plan_id: str):
        """Process plan document and store in vector database."""
        # Extract structured information
        plan_details = self.document_pipeline.process_plan_document(pdf_path, plan_id)
        
        # Create text chunks
        chunks = self.chunker.chunk_plan_document(plan_details)
        
        # Store in vector database
        self.vector_db.add_chunks_to_vector_db(chunks)
        
        return {
            "plan_id": plan_id,
            "chunks_stored": len(chunks),
            "plan_details": plan_details
        }
    
    def query_knowledge_base(self, query: str, plan_id: str = None):
        """Query the knowledge base for information."""
        results = self.vector_db.search(query, plan_id)
        return results