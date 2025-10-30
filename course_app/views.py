from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import json
import os
import uuid
from .models import Course, AudioQuestion, UserProfile, EngagementSession
from ai_services.services import ai_manager, process_audio_question_task, process_course_content_task
from quiz_app.models import Quiz, QuizAttempt


def home(request):
    """Home page with course overview"""
    courses = Course.objects.filter(is_active=True)[:6]
    context = {
        'courses': courses,
        'user': request.user,
    }
    return render(request, 'pages/dashboard.html', context)


def signup(request):
    """User registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'pages/sign-up.html', {'form': form})


def signin(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'pages/sign-in.html')


def face_login_page(request):
    """Face recognition login page"""
    return render(request, 'pages/face-login.html')


def logout_view(request):
    """User logout"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('signin')


@login_required
def profile(request):
    """User profile page"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user information
        user = request.user
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()
        
        # Update user profile
        user_profile.preferred_language = request.POST.get('preferred_language', user_profile.preferred_language)
        user_profile.bio = request.POST.get('bio', user_profile.bio)
        
        # Handle profile image upload
        if 'profile_image' in request.FILES:
            user_profile.profile_image = request.FILES['profile_image']
        
        user_profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    # Get user data for display
    enrolled_courses = Course.objects.filter(students=request.user)
    created_courses = Course.objects.filter(instructor=request.user)
    audio_questions = AudioQuestion.objects.filter(user=request.user)
    engagement_sessions = EngagementSession.objects.filter(user=request.user)
    
    context = {
        'user_profile': user_profile,
        'enrolled_courses': enrolled_courses,
        'created_courses': created_courses,
        'audio_questions': audio_questions,
        'engagement_sessions': engagement_sessions,
    }
    return render(request, 'pages/profile.html', context)


@login_required
def course_detail(request, course_id):
    """Course detail page"""
    course = get_object_or_404(Course, id=course_id)
    quizzes = Quiz.objects.filter(course=course, is_active=True)
    is_enrolled = request.user in course.students.all()
    
    context = {
        'course': course,
        'quizzes': quizzes,
        'is_enrolled': is_enrolled,
    }
    return render(request, 'pages/course_detail.html', context)


@login_required
def enroll_course(request, course_id):
    """Enroll in a course"""
    course = get_object_or_404(Course, id=course_id)
    course.students.add(request.user)
    messages.success(request, f'Successfully enrolled in {course.title}')
    return redirect('course_detail', course_id=course_id)


@login_required
def start_learning(request, course_id):
    """Start learning course content"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    if request.user not in course.students.all():
        messages.error(request, 'You must be enrolled in this course to start learning.')
        return redirect('course_detail', course_id=course_id)
    
    # Get course content (PDF, audio, video files)
    course_files = []
    if course.pdf_file:
        course_files.append({
            'name': 'Course PDF',
            'type': 'PDF',
            'file': course.pdf_file,
            'url': course.pdf_file.url
        })
    if course.audio_file:
        course_files.append({
            'name': 'Course Audio',
            'type': 'Audio',
            'file': course.audio_file,
            'url': course.audio_file.url
        })
    
    # Get related quizzes
    quizzes = Quiz.objects.filter(course=course, is_active=True)
    
    context = {
        'course': course,
        'course_files': course_files,
        'quizzes': quizzes,
    }
    return render(request, 'pages/start_learning.html', context)


@login_required
def upload_course_content(request):
    """Upload course content (audio/PDF)"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        audio_file = request.FILES.get('audio_file')
        pdf_file = request.FILES.get('pdf_file')
        
        course = Course.objects.create(
            title=title,
            description=description,
            instructor=request.user,
            audio_file=audio_file,
            pdf_file=pdf_file
        )
        
        # Process content asynchronously
        if audio_file:
            process_course_content_task.delay(str(course.id))
        
        messages.success(request, 'Course created successfully!')
        return redirect('course_detail', course_id=course.id)
    
    return render(request, 'pages/upload_course.html')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_audio_question(request):
    """API endpoint for uploading audio questions"""
    try:
        audio_file = request.FILES.get('audio_file')
        course_id = request.data.get('course_id')
        
        if not audio_file:
            return Response({'error': 'No audio file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create audio question
        audio_question = AudioQuestion.objects.create(
            user=request.user,
            audio_file=audio_file,
            course_id=course_id if course_id else None
        )
        
        # Process audio asynchronously
        process_audio_question_task.delay(str(audio_question.id))
        
        return Response({
            'question_id': str(audio_question.id),
            'message': 'Audio question uploaded successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_audio_question_status(request, question_id):
    """Get processing status of audio question"""
    try:
        question = get_object_or_404(AudioQuestion, id=question_id, user=request.user)
        
        return Response({
            'question_id': str(question.id),
            'is_processed': question.is_processed,
            'transcript': question.transcript,
            'question_text': question.question_text,
            'ai_response': question.ai_response,
            'generated_image': question.generated_image,
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_engagement_session(request):
    """Start engagement tracking session"""
    try:
        course_id = request.data.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        # End any existing active session
        EngagementSession.objects.filter(
            user=request.user,
            course=course,
            is_active=True
        ).update(is_active=False)
        
        # Create new session
        session = EngagementSession.objects.create(
            user=request.user,
            course=course
        )
        
        return Response({
            'session_id': str(session.id),
            'message': 'Engagement session started'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_engagement(request, session_id):
    """Update engagement data during session"""
    try:
        session = get_object_or_404(EngagementSession, id=session_id, user=request.user)
        
        # Get engagement data from request
        engagement_data = request.data.get('engagement_data', {})
        
        # Update session data
        current_data = session.engagement_data or []
        current_data.append(engagement_data)
        session.engagement_data = current_data
        
        # Calculate attention score
        if engagement_data.get('engagement_score'):
            session.attention_score = engagement_data['engagement_score']
        
        session.save()
        
        return Response({'message': 'Engagement updated successfully'})
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_engagement_session(request, session_id):
    """End engagement tracking session"""
    try:
        session = get_object_or_404(EngagementSession, id=session_id, user=request.user)
        session.is_active = False
        session.save()
        
        return Response({'message': 'Engagement session ended'})
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def face_recognition_login(request):
    """Face recognition login endpoint - AI-powered login using face"""
    try:
        # Get image from request (either file upload or base64)
        image_data = request.FILES.get('image')
        if not image_data:
            # Try to get base64 image from JSON
            image_base64 = request.data.get('image')
            if image_base64:
                image_data = image_base64
            else:
                return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate image data
        if hasattr(image_data, 'size') and image_data.size == 0:
            return Response({
                'error': 'Empty image file',
                'message': 'The uploaded image file is empty'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"📸 Received image for face login: type={type(image_data)}, size={getattr(image_data, 'size', 'N/A')}")
        
        # Use AI service to recognize face
        user, confidence = ai_manager.recognize_face(image_data)
        
        if user:
            # Log the user in
            login(request, user)
            print(f"✅ Face recognition successful: {user.username} (confidence: {confidence:.2f})")
            return Response({
                'success': True,
                'user': user.username,
                'email': user.email,
                'confidence': float(confidence),
                'message': 'Face recognition login successful'
            })
        else:
            error_msg = confidence if isinstance(confidence, str) else 'Face not recognized'
            print(f"❌ Face recognition failed: {error_msg}")
            return Response({
                'error': 'Face not recognized',
                'message': error_msg
            }, status=status.HTTP_401_UNAUTHORIZED)
        
    except Exception as e:
        print(f"❌ Face recognition error: {e}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_face(request):
    """Register user's face for AI-powered login"""
    try:
        # Get image from request
        image_data = request.FILES.get('image')
        if not image_data:
            image_base64 = request.data.get('image')
            if image_base64:
                image_data = image_base64
            else:
                return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Register face using AI service
        success, result = ai_manager.register_face(request.user, image_data)
        
        if success:
            # Save face encoding to user profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.face_encoding = result  # result contains the face encoding list
            profile.save()
            
            return Response({
                'success': True,
                'message': 'Face registered successfully for AI login'
            })
        else:
            return Response({
                'error': 'Face registration failed',
                'message': result  # result contains error message
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_courses(request):
    """Get user's enrolled courses"""
    courses = Course.objects.filter(students=request.user, is_active=True)
    course_data = []
    
    for course in courses:
        course_data.append({
            'id': str(course.id),
            'title': course.title,
            'description': course.description,
            'instructor': course.instructor.username,
            'created_at': course.created_at,
            'has_audio': bool(course.audio_file),
            'has_pdf': bool(course.pdf_file),
        })
    
    return Response({'courses': course_data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_course_quizzes(request, course_id):
    """Get quizzes for a specific course"""
    course = get_object_or_404(Course, id=course_id)
    quizzes = Quiz.objects.filter(course=course, is_active=True)
    
    quiz_data = []
    for quiz in quizzes:
        quiz_data.append({
            'id': str(quiz.id),
            'title': quiz.title,
            'description': quiz.description,
            'difficulty_level': quiz.difficulty_level,
            'question_count': len(quiz.questions),
            'created_at': quiz.created_at,
        })
    
    return Response({'quizzes': quiz_data})


# ----------------------
# Illustration & Media Views
# ----------------------

def test_static(request):
    """Test page for debugging static files"""
    return render(request, 'pages/test_static.html')


@login_required
def course_illustrations(request, course_id):
    """View course illustrations gallery"""
    from .models import Illustration
    
    course = get_object_or_404(Course, id=course_id)
    illustrations = Illustration.objects.filter(course=course, is_active=True)
    
    context = {
        'course': course,
        'illustrations': illustrations,
    }
    return render(request, 'pages/illustrations_gallery.html', context)


@login_required
def generate_illustration(request, course_id):
    """Generate AI illustration for a course"""
    from .models import Illustration
    from ai_services.services import ai_manager
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is instructor or has access
    if course.instructor != request.user and request.user not in course.students.all():
        messages.error(request, 'You do not have permission to add illustrations to this course.')
        return redirect('course_detail', course_id=course_id)
    
    if request.method == 'POST':
        description = request.POST.get('description', '')
        provider = request.POST.get('provider', 'huggingface')  # Default to free Hugging Face
        tags_str = request.POST.get('tags', '')
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        
        if not description:
            messages.error(request, 'Please provide a description for the illustration.')
            return redirect('generate_illustration', course_id=course_id)
        
        try:
            # Generate illustration using AI
            illustration = ai_manager.image_generator.create_illustration_from_description(
                course=course,
                description=description,
                provider=provider,
                tags=tags
            )
            
            if illustration:
                messages.success(request, 'Illustration generated successfully!')
                return redirect('course_illustrations', course_id=course_id)
            else:
                messages.error(request, 'Failed to generate illustration. Please check your API keys.')
        except Exception as e:
            messages.error(request, f'Error generating illustration: {str(e)}')
    
    context = {
        'course': course,
    }
    return render(request, 'pages/generate_illustration.html', context)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_illustration_api(request):
    """API endpoint to generate illustration"""
    from .models import Illustration
    from ai_services.services import ai_manager
    
    course_id = request.data.get('course_id')
    description = request.data.get('description')
    provider = request.data.get('provider', 'huggingface')  # Default to free Hugging Face
    tags = request.data.get('tags', [])
    
    if not course_id or not description:
        return Response(
            {'error': 'course_id and description are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check permissions
    if course.instructor != request.user and request.user not in course.students.all():
        return Response(
            {'error': 'You do not have permission to add illustrations to this course'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        illustration = ai_manager.image_generator.create_illustration_from_description(
            course=course,
            description=description,
            provider=provider,
            tags=tags
        )
        
        if illustration:
            return Response({
                'success': True,
                'illustration': {
                    'id': str(illustration.id),
                    'description': illustration.description,
                    'image_url': illustration.image_url,
                    'image_file': illustration.image_file.url if illustration.image_file else None,
                    'ai_generated': illustration.ai_generated,
                    'generation_service': illustration.generation_service,
                    'tags': illustration.tags,
                }
            })
        else:
            return Response(
                {'error': 'Failed to generate illustration'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_course_illustrations(request, course_id):
    """Get all illustrations for a course"""
    from .models import Illustration
    
    course = get_object_or_404(Course, id=course_id)
    illustrations = Illustration.objects.filter(course=course, is_active=True)
    
    illustration_data = []
    for illustration in illustrations:
        illustration_data.append({
            'id': str(illustration.id),
            'description': illustration.description,
            'image_url': illustration.image_url,
            'image_file': illustration.image_file.url if illustration.image_file else None,
            'ai_generated': illustration.ai_generated,
            'generation_service': illustration.generation_service,
            'tags': illustration.tags,
            'created_at': illustration.created_at,
        })
    
    return Response({'illustrations': illustration_data})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_illustration(request, illustration_id):
    """Delete an illustration"""
    from .models import Illustration
    
    illustration = get_object_or_404(Illustration, id=illustration_id)
    course = illustration.course
    
    # Check permissions
    if course.instructor != request.user:
        return Response(
            {'error': 'Only the course instructor can delete illustrations'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    illustration.delete()
    return Response({'success': True, 'message': 'Illustration deleted successfully'})