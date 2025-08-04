from .VectorDatabaseManager import VectorDatabaseManager
from .DocumentChunkerV2 import DocumentChunkerV2
from Extraction.PlanDocumentPipeline import PlanDocumentPipeline
from openai import OpenAI


class IFPPlanKnowledgeBase:
    def __init__(self, openai_api_key: str, db_directory: str = "chroma_db"):
        self.openai_api_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key)
        self.document_pipeline = PlanDocumentPipeline(openai_api_key)
        self.chunker = DocumentChunkerV2(openai_api_key)
        self.vector_db = VectorDatabaseManager(openai_api_key, db_directory)
        
    def process_and_store_plan(self, pdf_path: str, plan_id: str):
        """Process plan document and store in vector database."""
        # Extract structured information
        plan_details = self.document_pipeline.process_plan_document(pdf_path, plan_id)
        
        # Create proposition-based chunks from structured data
        structured_chunks = self.chunker.chunk_structured_plan_data(plan_details)
        
        # Also process the raw PDF text for comprehensive coverage
        raw_text = self.document_pipeline.processor.extract_text_from_pdf(pdf_path)
        if raw_text and raw_text.strip():
            raw_text_chunks = self.chunker.chunk_insurance_document(
                raw_text, 
                plan_id, 
                metadata={"source": "raw_pdf_text"}
            )
            # Combine both types of chunks
            all_chunks = structured_chunks + raw_text_chunks
        else:
            all_chunks = structured_chunks
        
        # Store in vector database
        self.vector_db.add_chunks_to_vector_db(all_chunks)
        
        return {
            "plan_id": plan_id,
            "chunks_stored": len(all_chunks),
            "structured_chunks": len(structured_chunks),
            "raw_text_chunks": len(all_chunks) - len(structured_chunks),
            "plan_details": plan_details
        }
    
    def query_knowledge_base(self, query: str, plan_id: str = None):
        """Query the knowledge base for information and get LLM response."""
        # Search for relevant documents
        search_results = self.vector_db.search(query, plan_id)
        
        # Prepare context from search results
        context = ""
        source_documents = []
        
        for result in search_results:
            context += f"Document: {result['text']}\n\n"
            source_documents.append({
                "page_content": result['text'],
                "metadata": result['metadata']
            })
        
        # Create prompt for LLM
        prompt = f"""
        You are an insurance plan assistant. Based on the following document excerpts, 
        answer the user's question about insurance plans. Be specific, accurate, and helpful.
        
        Document Context:
        {context}
        
        User Question: {query}
        
        Answer:
        """
        
        try:
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful insurance plan assistant. Provide accurate, specific answers based on the provided document context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            return {
                "answer": answer,
                "source_documents": source_documents
            }
            
        except Exception as e:
            return {
                "answer": f"I apologize, but I encountered an error while processing your question: {str(e)}",
                "source_documents": source_documents
            }