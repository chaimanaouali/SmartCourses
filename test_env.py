import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check API keys
groq_key = os.getenv('GROQ_API_KEY')

print("="*50)
print("Environment Variable Check")
print("="*50)

if groq_key:
    print(f"✅ GROQ_API_KEY is loaded")
    print(f"   Length: {len(groq_key)} characters")
    print(f"   Starts with: {groq_key[:10]}...")
else:
    print("❌ GROQ_API_KEY is NOT loaded")
    print("   Make sure .env file exists in the project root")

print("="*50)
