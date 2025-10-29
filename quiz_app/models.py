from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json


class Quiz(models.Model):
    """Model representing a quiz in the educational hub"""
    QUIZ_TYPES = [
        ('auto', 'Auto-generated'),
        ('manual', 'Manual'),
        ('adaptive', 'Adaptive'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey('course_app.Course', on_delete=models.CASCADE, related_name='quizzes')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quizzes')
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    # Quiz settings
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES, default='auto')
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='intermediate')
    time_limit = models.IntegerField(default=30, help_text="Time limit in minutes")
    passing_score = models.IntegerField(default=70, help_text="Passing score percentage")
    max_attempts = models.IntegerField(default=3, help_text="Maximum number of attempts")
    
    # AI-generated content
    questions = models.JSONField(default=list, help_text="List of quiz questions with answers")
    ai_generated = models.BooleanField(default=False)
    generation_prompt = models.TextField(blank=True, help_text="Prompt used for AI generation")
    
    # Analytics
    total_attempts = models.IntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    completion_rate = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_questions_count(self):
        """Return the number of questions in the quiz"""
        return len(self.questions) if self.questions else 0
    
    def get_difficulty_score(self):
        """Return difficulty score for analytics"""
        difficulty_scores = {'beginner': 1, 'intermediate': 2, 'advanced': 3}
        return difficulty_scores.get(self.difficulty_level, 2)


class QuizQuestion(models.Model):
    """Model for individual quiz questions"""
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('open_ended', 'Open Ended'),
        ('fill_blank', 'Fill in the Blank'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='question_objects')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    options = models.JSONField(default=list, help_text="Answer options for multiple choice")
    correct_answer = models.TextField()
    explanation = models.TextField(blank=True, help_text="Explanation for the correct answer")
    points = models.IntegerField(default=1)
    difficulty = models.CharField(max_length=20, choices=Quiz.DIFFICULTY_LEVELS, default='intermediate')
    order = models.IntegerField(default=0)
    
    # AI metadata
    ai_generated = models.BooleanField(default=False)
    confidence_score = models.FloatField(default=0.0, help_text="AI confidence in question quality")
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.quiz.title} - Question {self.order + 1}"


class QuizAttempt(models.Model):
    """Model representing a user's attempt at a quiz"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    time_taken = models.IntegerField(null=True, blank=True, help_text="Time taken in minutes")
    
    # Detailed results
    answers = models.JSONField(default=dict, help_text="User's answers to questions")
    correct_answers = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    
    # AI Analysis
    ai_feedback = models.TextField(blank=True, help_text="AI-generated feedback")
    strengths = models.JSONField(default=list, help_text="Identified strengths")
    weaknesses = models.JSONField(default=list, help_text="Identified weaknesses")
    recommendations = models.JSONField(default=list, help_text="AI recommendations")
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title}"
    
    def calculate_score_percentage(self):
        """Calculate score as percentage"""
        if self.total_questions > 0:
            return (self.correct_answers / self.total_questions) * 100
        return 0


class QuizAnalytics(models.Model):
    """Model for storing quiz analytics and performance data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_analytics')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='analytics')
    
    # Performance metrics
    average_score = models.FloatField()
    total_attempts = models.IntegerField()
    best_score = models.FloatField()
    worst_score = models.FloatField()
    improvement_rate = models.FloatField(help_text="Percentage improvement over time")
    
    # Detailed analytics
    time_spent = models.IntegerField(default=0, help_text="Total time spent in minutes")
    completion_rate = models.FloatField(default=0.0)
    difficulty_progression = models.JSONField(default=list, help_text="Difficulty progression over time")
    
    # AI Insights
    learning_patterns = models.JSONField(default=list, help_text="Identified learning patterns")
    knowledge_gaps = models.JSONField(default=list, help_text="Identified knowledge gaps")
    recommended_topics = models.JSONField(default=list, help_text="AI recommended topics to study")
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Analytics for {self.user.username} - {self.quiz.title}"


class AnalyticsService(models.Model):
    """Model for AI analytics service configuration"""
    SERVICE_TYPES = [
        ('quiz_generation', 'Quiz Generation'),
        ('performance_analysis', 'Performance Analysis'),
        ('recommendation_engine', 'Recommendation Engine'),
        ('adaptive_learning', 'Adaptive Learning'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPES)
    is_active = models.BooleanField(default=True)
    api_endpoint = models.URLField(blank=True)
    api_key = models.CharField(max_length=200, blank=True)
    configuration = models.JSONField(default=dict, help_text="Service configuration parameters")
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.service_type})"