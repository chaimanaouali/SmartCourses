import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_hub.settings')
django.setup()

from course_app.models import Illustration
from ai_services.services import ImageGenerationService

print("Regenerating illustrations with real AI images...")
print("=" * 60)

service = ImageGenerationService()
illustrations = Illustration.objects.filter(
    image_url="https://via.placeholder.com/1024x1024?text=AI+Image+Generation+Pending"
)

print(f"Found {illustrations.count()} placeholder illustrations to regenerate\n")

for illustration in illustrations:
    print(f"\nRegenerating: {illustration.description[:60]}...")
    
    # Generate image with Hugging Face
    result = service.generate_image(
        text_description=illustration.description,
        provider='huggingface'
    )
    
    if result["success"]:
        # Update illustration with real image
        if result.get('image_data'):
            from django.core.files.base import ContentFile
            image_content = ContentFile(result['image_data'])
            filename = f"illustration_{illustration.id}.png"
            illustration.image_file.save(filename, image_content, save=False)
        
        if result.get('image_url'):
            illustration.image_url = result['image_url']
        
        illustration.generation_service = result.get('service', 'Stable Diffusion XL (Hugging Face)')
        illustration.save()
        
        print(f"✅ Success! Image generated and saved.")
    else:
        print(f"❌ Failed: {result.get('error')}")
        if result.get('placeholder'):
            print("   → API key might not be configured correctly")

print("\n" + "=" * 60)
print("Regeneration complete!")
print("\nRefresh your browser to see the real images.")
