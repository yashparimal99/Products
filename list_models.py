import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("\nAvailable models for your API key:\n")
models = genai.list_models()

for m in models:
    print(m.name)
