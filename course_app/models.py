from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Course(models.Model):
    """Model representing a course in the educational hub"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    students = models.ManyToManyField(User, related_name='courses_enrolled', blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Course content
    audio_file = models.FileField(upload_to='courses/audio/', null=True, blank=True)
    pdf_file = models.FileField(upload_to='courses/pdf/', null=True, blank=True)
    transcript = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    
    # AI-generated content
    generated_images = models.JSONField(default=list, blank=True)
    key_concepts = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class AudioQuestion(models.Model):
    """Model for storing voice questions from users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audio_questions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='audio_questions', null=True, blank=True)
    audio_file = models.FileField(upload_to='questions/audio/')
    transcript = models.TextField(blank=True)
    question_text = models.TextField()
    ai_response = models.TextField(blank=True)
    generated_image = models.URLField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_processed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.question_text[:50]}..."


class UserProfile(models.Model):
    """Extended user profile with facial recognition data"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    face_encoding = models.JSONField(null=True, blank=True)  # Store face encoding for recognition
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    learning_goals = models.TextField(blank=True)
    preferred_language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} Profile"


class EngagementSession(models.Model):
    """Model for tracking user engagement during learning sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='engagement_sessions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='engagement_sessions')
    session_start = models.DateTimeField(default=timezone.now)
    session_end = models.DateTimeField(null=True, blank=True)
    engagement_data = models.JSONField(default=list)  # Facial expressions, attention data
    attention_score = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-session_start']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} Session"


class AnalyticsService(models.Model):
    """Model for storing analytics and AI service configurations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    service_type = models.CharField(
        max_length=50,
        choices=[
            ('whisper', 'Whisper (Speech-to-Text)'),
            ('gemini', 'Gemini (Text Generation)'),
            ('huggingface', 'Hugging Face (Image Generation)'),
            ('face_recognition', 'Face Recognition'),
        ]
    )
    is_active = models.BooleanField(default=True)
    configuration = models.JSONField(default=dict)
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.name} ({self.service_type})"

