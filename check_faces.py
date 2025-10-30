"""
Quick script to check which users have registered face encodings
Run with: python check_faces.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_hub.settings')
django.setup()

from course_app.models import UserProfile
from django.contrib.auth.models import User

print("\n" + "="*60)
print("CHECKING REGISTERED FACES IN DATABASE")
print("="*60 + "\n")

# Get all users
all_users = User.objects.all()
print(f"📊 Total users in database: {all_users.count()}\n")

# Get users with profiles
profiles_with_faces = UserProfile.objects.exclude(face_encoding__isnull=True)
print(f"✅ Users with registered face encodings: {profiles_with_faces.count()}\n")

if profiles_with_faces.exists():
    print("Registered users:")
    print("-" * 60)
    for profile in profiles_with_faces:
        encoding_type = "Unknown"
        if isinstance(profile.face_encoding, dict):
            encoding_type = profile.face_encoding.get('model', 'dict format')
        elif isinstance(profile.face_encoding, list):
            encoding_type = f"list ({len(profile.face_encoding)} values)"
        
        print(f"  👤 {profile.user.username}")
        print(f"     Email: {profile.user.email}")
        print(f"     Encoding type: {encoding_type}")
        print()
else:
    print("⚠️  NO USERS WITH REGISTERED FACES FOUND!")
    print("\nYou need to register your face first:")
    print("  1. Login with username/password")
    print("  2. Go to your profile settings")
    print("  3. Register your face for AI login")
    print()

# Check users without profiles
users_without_profiles = []
for user in all_users:
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        users_without_profiles.append(user)

if users_without_profiles:
    print(f"\n⚠️  {len(users_without_profiles)} user(s) without profile:")
    for user in users_without_profiles:
        print(f"  - {user.username}")
    print()

print("="*60)
