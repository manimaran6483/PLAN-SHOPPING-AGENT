from openai import OpenAI 
try:
    client = OpenAI(api_key="OPENAI_API_KEY")
    models = client.models.list()
    for model in models:
        print(model.id)
    print("OpenAI API connection successful.")
except Exception as e:
    print("OpenAI API connection failed:", e)
    print(e)