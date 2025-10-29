from django.contrib import admin
from .models import Quiz, QuizQuestion, QuizAttempt, QuizAnalytics, AnalyticsService


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'quiz_type', 'difficulty_level', 'total_attempts', 'average_score', 'created_at', 'is_active']
    list_filter = ['quiz_type', 'difficulty_level', 'ai_generated', 'is_active', 'created_at']
    search_fields = ['title', 'course__title', 'created_by__username']
    readonly_fields = ['total_attempts', 'average_score', 'completion_rate']
    filter_horizontal = []


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'question_text', 'question_type', 'difficulty', 'points', 'ai_generated', 'confidence_score']
    list_filter = ['question_type', 'difficulty', 'ai_generated']
    search_fields = ['question_text', 'quiz__title']
    ordering = ['quiz', 'order']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'correct_answers', 'total_questions', 'is_completed', 'started_at', 'time_taken']
    list_filter = ['is_completed', 'started_at', 'quiz__difficulty_level']
    search_fields = ['user__username', 'quiz__title']
    readonly_fields = ['score', 'correct_answers', 'total_questions', 'time_taken']


@admin.register(QuizAnalytics)
class QuizAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'average_score', 'total_attempts', 'best_score', 'improvement_rate', 'updated_at']
    list_filter = ['updated_at', 'quiz__difficulty_level']
    search_fields = ['user__username', 'quiz__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AnalyticsService)
class AnalyticsServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_type', 'is_active', 'usage_count', 'last_used']
    list_filter = ['service_type', 'is_active']
    search_fields = ['name', 'service_type']
    readonly_fields = ['usage_count', 'last_used']