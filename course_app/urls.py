from django.urls import path, include
from . import views

urlpatterns = [
    # Web pages
    path('', views.home, name='home'),
    # Workshops
    path('workshops/', views.workshop_list, name='workshop_list'),
    path('workshops/new/', views.workshop_create, name='workshop_create'),
    path('workshops/<uuid:workshop_id>/', views.workshop_detail, name='workshop_detail'),
    path('workshops/<uuid:workshop_id>/edit/', views.workshop_update, name='workshop_update'),
    path('workshops/<uuid:workshop_id>/delete/', views.workshop_delete, name='workshop_delete'),
    # Workspaces
    path('workspaces/', views.workspace_list, name='workspace_list'),
    path('workspaces/new/', views.workspace_create, name='workspace_create'),
    path('workspaces/<slug:slug>/', views.workspace_detail, name='workspace_detail'),
    path('workspaces/<slug:slug>/edit/', views.workspace_update, name='workspace_update'),
    path('workspaces/<slug:slug>/delete/', views.workspace_delete, name='workspace_delete'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('face-login/', views.face_login_page, name='face_login_page'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('course/<uuid:course_id>/', views.course_detail, name='course_detail'),
    path('course/<uuid:course_id>/edit/', views.update_course, name='update_course'),
    path('course/<uuid:course_id>/delete/', views.delete_course, name='delete_course'),
    path('course/<uuid:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('course/<uuid:course_id>/learn/', views.start_learning, name='start_learning'),
    path('upload-course/', views.upload_course_content, name='upload_course'),
    
    # Illustrations
    path('course/<uuid:course_id>/illustrations/', views.course_illustrations, name='course_illustrations'),
    path('course/<uuid:course_id>/generate-illustration/', views.generate_illustration, name='generate_illustration'),
    path('test-static/', views.test_static, name='test_static'),

    # API endpoints
    path('api/audio-question/', views.upload_audio_question, name='upload_audio_question'),
    path('api/audio-question/<uuid:question_id>/status/', views.get_audio_question_status, name='audio_question_status'),
    path('api/engagement/start/', views.start_engagement_session, name='start_engagement'),
    path('api/engagement/<uuid:session_id>/update/', views.update_engagement, name='update_engagement'),
    path('api/engagement/<uuid:session_id>/end/', views.end_engagement_session, name='end_engagement'),
    path('api/face-login/', views.face_recognition_login, name='face_login'),
    path('api/face-register/', views.register_face, name='face_register'),
    path('api/user-courses/', views.get_user_courses, name='user_courses'),
    path('api/course/<uuid:course_id>/quizzes/', views.get_course_quizzes, name='course_quizzes'),
    # AI Assistant endpoints
    path('api/course/<uuid:course_id>/summary/', views.summarize_course_api, name='course_summary_api'),
    path('api/course/<uuid:course_id>/explain/', views.explain_course_api, name='course_explain_api'),

    # Illustration API endpoints
    path('api/generate-illustration/', views.generate_illustration_api, name='generate_illustration_api'),
    path('api/course/<uuid:course_id>/illustrations/', views.get_course_illustrations, name='get_course_illustrations'),
    path('api/illustration/<uuid:illustration_id>/delete/', views.delete_illustration, name='delete_illustration'),
]
