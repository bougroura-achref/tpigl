import os
import traceback
from dotenv import load_dotenv
import google.generativeai as genai

# Load env variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

print(f"--- DIAGNOSIS START (Legacy SDK) ---")
print(f"API Key present: {bool(api_key)}")
genai.configure(api_key=api_key)

try:
    print("Listing models with google.generativeai...")
    models = list(genai.list_models())
    print(f"Success! Found {len(models)} models.")
    
    print("Attempting generate_content...")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Hello")
    print("--- SUCCESS ---")
    print(response.text)

except Exception as e:
    print("--- FAILURE ---")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    traceback.print_exc()
