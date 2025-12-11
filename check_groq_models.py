"""
Check available GROQ models
"""
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

print("Fetching available GROQ models...\n")

try:
    models = client.models.list()

    print("Available Models:")
    print("="*70)

    for model in models.data:
        print(f"\nModel ID: {model.id}")
        if hasattr(model, 'owned_by'):
            print(f"  Owned by: {model.owned_by}")
        if hasattr(model, 'active'):
            print(f"  Active: {model.active}")

    print("\n" + "="*70)
    print(f"\nTotal models: {len(models.data)}")

except Exception as e:
    print(f"Error fetching models: {e}")
