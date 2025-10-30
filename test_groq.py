import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_hub.settings')
django.setup()

# Now test the ai_manager
from ai_services.services import ai_manager

print("="*60)
print("Testing GROQ API Key in Django Environment")
print("="*60)

# Check if GROQ_API_KEY is loaded
groq_key = os.getenv('GROQ_API_KEY')
if groq_key:
    print(f"✅ GROQ_API_KEY loaded: {groq_key[:10]}... ({len(groq_key)} chars)")
else:
    print("❌ GROQ_API_KEY NOT loaded")

print("\n" + "="*60)
print("Testing Text Generation")
print("="*60)

# Test text generation
try:
    response = ai_manager.generate_text_response("Say hello!")
    print(f"Response: {response}")
    
    if "not configured" in response.lower():
        print("\n❌ API key is not being detected by ai_manager")
    else:
        print("\n✅ Text generation working!")
except Exception as e:
    print(f"❌ Error: {e}")

print("="*60)
