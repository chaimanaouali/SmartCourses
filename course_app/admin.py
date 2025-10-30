from django.contrib import admin
from .models import Course, AudioQuestion, UserProfile, EngagementSession, AnalyticsService, Illustration

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description', 'instructor__username']
    filter_horizontal = ['students']

@admin.register(AudioQuestion)
class AudioQuestionAdmin(admin.ModelAdmin):
    list_display = ['user', 'question_text', 'is_processed', 'created_at']
    list_filter = ['is_processed', 'created_at']
    search_fields = ['user__username', 'question_text']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_language', 'created_at']
    search_fields = ['user__username']

@admin.register(EngagementSession)
class EngagementSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'session_start', 'is_active', 'attention_score']
    list_filter = ['is_active', 'session_start']
    search_fields = ['user__username', 'course__title']

@admin.register(AnalyticsService)
class AnalyticsServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_type', 'is_active', 'usage_count']
    list_filter = ['service_type', 'is_active']

@admin.register(Illustration)
class IllustrationAdmin(admin.ModelAdmin):
    list_display = ['course', 'description_preview', 'ai_generated', 'generation_service', 'is_active', 'created_at']
    list_filter = ['ai_generated', 'is_active', 'generation_service', 'created_at']
    search_fields = ['description', 'course__title', 'tags']
    readonly_fields = ['generation_timestamp', 'created_at', 'updated_at']

    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'