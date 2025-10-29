from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


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


class GeneratedContent(models.Model):
    """Model for storing AI-generated content"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.CharField(
        max_length=50,
        choices=[
            ('image', 'Image'),
            ('text', 'Text'),
            ('audio', 'Audio'),
            ('video', 'Video'),
        ]
    )
    source_course = models.ForeignKey('course_app.Course', on_delete=models.CASCADE, related_name='generated_content', null=True, blank=True)
    source_question = models.ForeignKey('course_app.AudioQuestion', on_delete=models.CASCADE, related_name='generated_content', null=True, blank=True)
    content_data = models.JSONField(default=dict)
    file_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    ai_service_used = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.content_type} - {self.created_at}"