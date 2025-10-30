"""
Fix username mismatch between VGG16 model and database
Run with: python fix_username_mismatch.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_hub.settings')
django.setup()

from course_app.models import UserProfile
from django.contrib.auth.models import User

print("\n" + "="*70)
print("FIX: VGG16 Username Mismatch")
print("="*70 + "\n")

# Get the user
try:
    user = User.objects.get(username='amenn')
    print(f"✓ Found user: {user.username} (ID: {user.id})")
    
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if profile.face_encoding:
        print(f"\n📊 Current face encoding:")
        if isinstance(profile.face_encoding, dict):
            print(f"   Model: {profile.face_encoding.get('model', 'unknown')}")
            print(f"   Username in encoding: {profile.face_encoding.get('username', 'N/A')}")
        
        # Update the username in the encoding to match what VGG16 expects
        print(f"\n🔧 Updating encoding username to 'Muhammad Shaharyar'...")
        
        if isinstance(profile.face_encoding, dict):
            profile.face_encoding['username'] = 'Muhammad Shaharyar'
            profile.save()
            print(f"✅ SUCCESS: Updated encoding username!")
            print(f"\n   Database username: {user.username} (remains 'amenn')")
            print(f"   Encoding username: Muhammad Shaharyar (for VGG16 matching)")
            print(f"\n💡 Now the VGG16 model will recognize you and log you in as '{user.username}'")
        else:
            print(f"❌ ERROR: Encoding is not in expected format")
    else:
        print(f"❌ ERROR: No face encoding found for user")
        
except User.DoesNotExist:
    print(f"❌ ERROR: User 'amenn' not found")

print("\n" + "="*70)
print("Try face login again after running this script!")
print("="*70 + "\n")
