from Embeddings.IFPPlanKnowledgeBase import IFPPlanKnowledgeBase
import dotenv
import os
def main():

    # Load environment variables from .env file
    dotenv.load_dotenv()

    # Initialize with your OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:  # Check if the API key is set
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    knowledge_base = IFPPlanKnowledgeBase(openai_api_key)
    
    # Process plans
    plans_directory = "plan_documents/"
    for filename in os.listdir(plans_directory):
        if filename.endswith(".pdf"):
            plan_id = filename.replace(".pdf", "")
            pdf_path = os.path.join(plans_directory, filename)
            
            print(f"Processing plan: {plan_id}")
            result = knowledge_base.process_and_store_plan(pdf_path, plan_id)
            print(f"Stored {result['chunks_stored']} chunks for plan {plan_id}")
    
    # Query example
    # instead of hardcoding, you can use a user input
    query = input("Enter your query: ")
    plan_id = input("Enter your plans: ")
    results = knowledge_base.query_knowledge_base(query, plan_id)

    for result in results:
        print(f"Relevance: {result['distance']}")
        print(f"Content: {result['text']}")
        print("---")

if __name__ == "__main__":
    main()