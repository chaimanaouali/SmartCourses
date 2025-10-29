from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/course/<uuid:course_id>/', consumers.CourseConsumer.as_asgi()),
    path('ws/quiz/<uuid:quiz_id>/', consumers.QuizConsumer.as_asgi()),
]



