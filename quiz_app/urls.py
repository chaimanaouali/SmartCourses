from django.urls import path, include
from . import views

app_name = 'quiz_app'

urlpatterns = [
    # Quiz management
    path('', views.quiz_list, name='quiz_list'),
    path('analytics/', views.quiz_analytics, name='quiz_analytics'),
    
    # Quiz generation
    path('generate/<uuid:course_id>/', views.generate_quiz, name='generate_quiz'),
    
    # Quiz taking
    path('quiz/<uuid:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<uuid:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('quiz/<uuid:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    path('attempt/<uuid:attempt_id>/', views.take_quiz, name='take_quiz'),
    path('attempt/<uuid:attempt_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('result/<uuid:attempt_id>/', views.quiz_result, name='quiz_result'),
    
    # API endpoints
    path('api/generate/', views.generate_quiz_api, name='generate_quiz_api'),
    path('api/recommendations/', views.adaptive_quiz_recommendation, name='adaptive_recommendations'),
]
