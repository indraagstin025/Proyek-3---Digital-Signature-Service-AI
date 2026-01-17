from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("Daftar Model yang Tersedia:")
for m in client.models.list():
    # Filter only models that support generate content, check name usually contains 'gemini'
    if "gemini" in m.name:
         print(f"- {m.name}")
