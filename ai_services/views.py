from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import base64
import cv2
import numpy as np
from .services import ai_manager


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transcribe_audio(request):
    """Transcribe audio using Whisper"""
    try:
        audio_file = request.FILES.get('audio_file')
        if not audio_file:
            return Response({'error': 'No audio file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            for chunk in audio_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        try:
            # Transcribe audio
            transcript = ai_manager.transcribe_audio(tmp_file_path)
            
            if transcript:
                return Response({
                    'transcript': transcript,
                    'success': True
                })
            else:
                return Response({
                    'error': 'Failed to transcribe audio',
                    'success': False
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_text(request):
    """Generate text using Gemini"""
    try:
        data = request.data
        prompt = data.get('prompt')
        context = data.get('context', '')
        
        if not prompt:
            return Response({'error': 'No prompt provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate text response
        response = ai_manager.generate_text_response(prompt, context)
        
        return Response({
            'response': response,
            'success': True
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_image(request):
    """Generate image using Hugging Face"""
    try:
        data = request.data
        prompt = data.get('prompt')
        
        if not prompt:
            return Response({'error': 'No prompt provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate image
        image_result = ai_manager.generate_image(prompt)
        
        if image_result:
            return Response({
                'image_url': str(image_result),  # This would need proper file handling
                'success': True
            })
        else:
            return Response({
                'error': 'Failed to generate image',
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def face_recognition(request):
    """Face recognition service"""
    try:
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            for chunk in image_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        try:
            # Recognize face
            face_encoding = ai_manager.recognize_face(tmp_file_path)
            
            if face_encoding:
                return Response({
                    'face_encoding': face_encoding,
                    'face_detected': True,
                    'success': True
                })
            else:
                return Response({
                    'face_detected': False,
                    'success': True
                })
                
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detect_engagement(request):
    """Detect user engagement from facial expressions"""
    try:
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            for chunk in image_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        try:
            # Detect engagement
            engagement_data = ai_manager.detect_engagement(tmp_file_path)
            
            return Response({
                'engagement_data': engagement_data,
                'success': True
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# CAMERA-BASED FACE RECOGNITION ENDPOINTS (Deep Learning)
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def camera_capture_frame(request):
    """Capture a single frame from the camera"""
    try:
        from .camera_utils import capture_single_frame
        
        camera_index = int(request.data.get('camera_index', 0))
        
        # Capture frame
        frame = capture_single_frame(camera_index)
        
        if frame is None:
            return Response({
                'error': 'Failed to capture frame from camera',
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Convert frame to base64
        _, buffer = cv2.imencode('.jpg', frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return Response({
            'image': f"data:image/jpeg;base64,{img_base64}",
            'success': True
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def camera_recognize_face(request):
    """
    Capture from camera and recognize face using deep learning model
    """
    try:
        from .camera_utils import capture_single_frame
        from .face_recognition_deep import deep_face_service
        
        if deep_face_service is None:
            return Response({
                'error': 'Deep learning face recognition service not available',
                'success': False
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        camera_index = int(request.data.get('camera_index', 0))
        
        # Capture frame
        frame = capture_single_frame(camera_index)
        
        if frame is None:
            return Response({
                'error': 'Failed to capture frame from camera',
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Perform face recognition
        result = deep_face_service.recognize_face_realtime(frame)
        
        if not result['success']:
            return Response({
                'error': result.get('error', 'Recognition failed'),
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Convert annotated frame to base64
        annotated_frame = result['frame']
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return Response({
            'image': f"data:image/jpeg;base64,{img_base64}",
            'faces': result['faces'],
            'face_count': result['face_count'],
            'success': True
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def camera_register_face(request):
    """
    Register user's face from camera using deep learning model
    """
    try:
        from .camera_utils import capture_single_frame
        from course_app.models import UserProfile
        
        camera_index = int(request.data.get('camera_index', 0))
        
        # Capture frame
        frame = capture_single_frame(camera_index)
        
        if frame is None:
            return Response({
                'error': 'Failed to capture frame from camera',
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Register face
        user = request.user
        success, result = ai_manager.register_face(user, frame)
        
        if not success:
            return Response({
                'error': result,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save face encoding to user profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.face_encoding = result
        profile.save()
        
        return Response({
            'message': f'Face registered successfully for {user.username}',
            'model': result.get('model', 'unknown'),
            'success': True
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def camera_stream_base64(request):
    """
    Accept base64 encoded camera frame and perform face recognition
    """
    try:
        from .face_recognition_deep import deep_face_service
        
        if deep_face_service is None:
            return Response({
                'error': 'Deep learning face recognition service not available',
                'success': False
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Get base64 image from request
        image_data = request.data.get('image')
        if not image_data:
            return Response({
                'error': 'No image data provided',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Decode base64 to image
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return Response({
                'error': 'Failed to decode image',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform face recognition
        result = deep_face_service.recognize_face_realtime(frame)
        
        if not result['success']:
            return Response({
                'error': result.get('error', 'Recognition failed'),
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Convert annotated frame to base64
        annotated_frame = result['frame']
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return Response({
            'image': f"data:image/jpeg;base64,{img_base64}",
            'faces': result['faces'],
            'face_count': result['face_count'],
            'success': True
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)