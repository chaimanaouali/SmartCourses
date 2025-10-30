import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_hub.settings')
django.setup()

from course_app.models import Illustration

illustrations = Illustration.objects.all()
print(f"Total illustrations: {illustrations.count()}")
print("\n")

for i in illustrations:
    print(f"ID: {i.id}")
    print(f"Description: {i.description[:50]}...")
    print(f"Has image_file: {bool(i.image_file)}")
    print(f"Has image_url: {bool(i.image_url)}")
    print(f"Image URL: {i.image_url}")
    print(f"AI Generated: {i.ai_generated}")
    print(f"Service: {i.generation_service}")
    print("-" * 50)
