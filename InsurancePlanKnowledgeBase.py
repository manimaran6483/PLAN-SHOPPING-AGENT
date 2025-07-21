from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
import os

class InsurancePlanKnowledgeBase:
    def __init__(self, openai_api_key, persist_directory="./chroma_db"):
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize components
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        self.persist_directory = persist_directory
        
        # Initialize vector store if it exists
        if os.path.exists(persist_directory):
            self.vector_db = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings
            )
        else:
            self.vector_db = None
            
        # Initialize LLM
        self.llm = ChatOpenAI(model_name="gpt-4")
        
    def process_and_store_plan(self, pdf_path, plan_id):
        """Process plan document and store in vector database."""
        # Load document
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # Add plan_id to metadata
        for doc in documents:
            doc.metadata["plan_id"] = plan_id
            
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        # Store or update in vector database
        if self.vector_db is None:
            self.vector_db = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
        else:
            self.vector_db.add_documents(chunks)
            
        # Persist to disk
        self.vector_db.persist()
        
        return {
            "plan_id": plan_id,
            "chunks_stored": len(chunks)
        }
    
    def query_knowledge_base(self, query, plan_id=None):
        """Query the knowledge base for information."""
        # Create filter if plan_id is provided
        filter_dict = {"plan_id": plan_id} if plan_id else None
        
        # Create retriever with metadata filter
        retriever = self.vector_db.as_retriever(
            search_kwargs={"filter": filter_dict, "k": 5}
        )
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        # Get response
        result = qa_chain({"query": query})
        
        return {
            "answer": result["result"],
            "source_documents": result["source_documents"]
        }