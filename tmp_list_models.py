import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

response = requests.get(url)
if response.status_code == 200:
    models = response.json().get("models", [])
    model_names = [m['name'] for m in models]
    with open('tmp_models.json', 'w', encoding='utf-8') as f:
        json.dump(model_names, f, indent=4)
