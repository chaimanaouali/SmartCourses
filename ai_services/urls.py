from django.urls import path
from . import views

app_name = 'ai_services'

urlpatterns = [
    path('transcribe/', views.transcribe_audio, name='transcribe'),
    path('generate-text/', views.generate_text, name='generate_text'),
    path('generate-image/', views.generate_image, name='generate_image'),
    path('face-recognition/', views.face_recognition, name='face_recognition'),
    path('engagement-detection/', views.detect_engagement, name='engagement_detection'),
    
    # Camera-based face recognition endpoints (Deep Learning)
    path('camera/capture/', views.camera_capture_frame, name='camera_capture'),
    path('camera/recognize/', views.camera_recognize_face, name='camera_recognize'),
    path('camera/register/', views.camera_register_face, name='camera_register'),
    path('camera/stream/', views.camera_stream_base64, name='camera_stream'),
]



