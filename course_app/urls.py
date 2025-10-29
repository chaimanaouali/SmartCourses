from django.urls import path, include
from . import views

urlpatterns = [
    # Web pages
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('course/<uuid:course_id>/', views.course_detail, name='course_detail'),
    path('course/<uuid:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('course/<uuid:course_id>/learn/', views.start_learning, name='start_learning'),
    path('upload-course/', views.upload_course_content, name='upload_course'),
    
    # API endpoints
    path('api/audio-question/', views.upload_audio_question, name='upload_audio_question'),
    path('api/audio-question/<uuid:question_id>/status/', views.get_audio_question_status, name='audio_question_status'),
    path('api/engagement/start/', views.start_engagement_session, name='start_engagement'),
    path('api/engagement/<uuid:session_id>/update/', views.update_engagement, name='update_engagement'),
    path('api/engagement/<uuid:session_id>/end/', views.end_engagement_session, name='end_engagement'),
    path('api/face-login/', views.face_recognition_login, name='face_login'),
    path('api/user-courses/', views.get_user_courses, name='user_courses'),
    path('api/course/<uuid:course_id>/quizzes/', views.get_course_quizzes, name='course_quizzes'),
]
