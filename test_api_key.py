import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Testing API Key Configuration")
print("=" * 60)

# Check if .env file exists
env_path = os.path.join(os.getcwd(), '.env')
print(f"\n.env file exists: {os.path.exists(env_path)}")
print(f".env file path: {env_path}")

# Get the API key
hf_key = os.getenv('HUGGINGFACE_API_KEY')
print(f"\nHUGGINGFACE_API_KEY found: {bool(hf_key)}")
if hf_key:
    print(f"Key starts with: {hf_key[:10]}...")
    print(f"Key length: {len(hf_key)}")
    print(f"Is placeholder: {hf_key == 'your_huggingface_api_key_here'}")
else:
    print("❌ API key is None or empty!")

print("\n" + "=" * 60)

# Now test with Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_hub.settings')
django.setup()

from ai_services.services import ImageGenerationService

print("\nTesting ImageGenerationService:")
service = ImageGenerationService()
print(f"Service API key: {service.huggingface_api_key[:10] if service.huggingface_api_key else 'None'}...")

# Test a simple generation
print("\nTesting image generation...")
result = service.generate_image("a red apple", provider='huggingface')
print(f"Success: {result.get('success')}")
print(f"Error: {result.get('error')}")
print(f"Is placeholder: {result.get('placeholder')}")
