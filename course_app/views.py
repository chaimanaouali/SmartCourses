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
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import os
import uuid
from .models import Course, AudioQuestion, UserProfile, EngagementSession, Workspace, Workshop
from django.utils.text import slugify
from ai_services.services import ai_manager, process_audio_question_task, process_course_content_task
from quiz_app.models import Quiz, QuizAttempt


def home(request):
    """Home page with course overview"""
    courses = Course.objects.filter(is_active=True)
    # Group courses by workspace (including unassigned)
    workspaces = Workspace.objects.filter(courses__in=courses).distinct().order_by('name')
    workspace_to_courses = []
    for ws in workspaces:
        workspace_to_courses.append({
            'workspace': ws,
            'courses': list(ws.courses.filter(is_active=True)),
        })
    # Unassigned courses (no workspace)
    unassigned = courses.filter(workspace__isnull=True)
    if unassigned.exists():
        workspace_to_courses.insert(0, {
            'workspace': None,
            'courses': list(unassigned),
        })
    # Get recent workshops for the dashboard
    recent_workshops = Workshop.objects.filter(
        course__in=courses
    ).order_by('-created_at')[:6]  # Show last 6 workshops
    
    # Add totals for dashboard metrics
    total_courses = Course.objects.filter(is_active=True).count()
    total_workspaces = Workspace.objects.count()
    total_workshops = Workshop.objects.count()
    
    workspaces_all = Workspace.objects.all().order_by('name')
    courses_all = Course.objects.filter(is_active=True).order_by('-created_at')
    
    context = {
        'grouped_courses': workspace_to_courses,
        'recent_workshops': recent_workshops,
        'user': request.user,
        'total_courses': total_courses,
        'total_workspaces': total_workspaces,
        'total_workshops': total_workshops,
        'workspaces_all': workspaces_all,
        'courses_all': courses_all,
    }
    return render(request, 'pages/dashboard.html', context)


# -------------------- Workshops CRUD --------------------
from django.forms import ModelForm
from django import forms


class WorkshopForm(ModelForm):
    class Meta:
        model = Workshop
        fields = ['course', 'title', 'description', 'scheduled_at', 'location', 'capacity', 'cover_image']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., UML Basics Workshop'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Overview, agenda, prerequisites...'}),
            'scheduled_at': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Room 101 or Zoom link'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure datetime-local value renders correctly when editing
        if self.instance and self.instance.scheduled_at:
            self.initial['scheduled_at'] = self.instance.scheduled_at.strftime('%Y-%m-%dT%H:%M')


@login_required
def workshop_list(request):
    """List workshops created by the current user or for their courses"""
    # Instructor sees their own created workshops; students see all active course workshops
    created = Workshop.objects.filter(created_by=request.user).select_related('course')
    return render(request, 'pages/workshop_list.html', { 'workshops': created })


@login_required
def workshop_create(request):
    """Create a new workshop"""
    if request.method == 'POST':
        form = WorkshopForm(request.POST, request.FILES)
        if form.is_valid():
            workshop = form.save(commit=False)
            # Only allow selecting courses the user instructs
            if workshop.course.instructor != request.user:
                messages.error(request, 'You can only create workshops for your own courses.')
            else:
                workshop.created_by = request.user
                workshop.save()
                messages.success(request, 'Workshop created successfully!')
                return redirect('workshop_detail', workshop_id=workshop.id)
    else:
        # Limit course choices to instructor's courses
        form = WorkshopForm()
        form.fields['course'].queryset = Course.objects.filter(instructor=request.user)
    return render(request, 'pages/workshop_form.html', { 'form': form })


@login_required
def workshop_detail(request, workshop_id):
    ws = get_object_or_404(Workshop, id=workshop_id)
    hide_crud = request.GET.get('from') == 'dashboard'
    return render(request, 'pages/workshop_detail.html', { 'workshop': ws, 'hide_crud': hide_crud })


@login_required
def workshop_update(request, workshop_id):
    ws = get_object_or_404(Workshop, id=workshop_id, created_by=request.user)
    if request.method == 'POST':
        form = WorkshopForm(request.POST, request.FILES, instance=ws)
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.course.instructor != request.user:
                messages.error(request, 'You can only attach workshops to your own courses.')
            else:
                updated.save()
                messages.success(request, 'Workshop updated successfully!')
                return redirect('workshop_detail', workshop_id=ws.id)
    else:
        form = WorkshopForm(instance=ws)
        form.fields['course'].queryset = Course.objects.filter(instructor=request.user)
    return render(request, 'pages/workshop_form.html', { 'form': form, 'workshop': ws })


@login_required
def workshop_delete(request, workshop_id):
    ws = get_object_or_404(Workshop, id=workshop_id, created_by=request.user)
    if request.method == 'POST':
        ws.delete()
        messages.success(request, 'Workshop deleted successfully!')
        return redirect('workshop_list')
    return render(request, 'pages/workshop_confirm_delete.html', { 'workshop': ws })


class WorkspaceForm(ModelForm):
    class Meta:
        model = Workspace
        fields = ['name', 'cover_image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Web 5EME'}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

@login_required
def workspace_list(request):
    """List workspaces for the current user"""
    workspaces = Workspace.objects.filter(owner=request.user)
    return render(request, 'pages/workspace_list.html', { 'workspaces': workspaces })

@login_required
def workspace_create(request):
    if request.method == 'POST':
        form = WorkspaceForm(request.POST, request.FILES)
        if form.is_valid():
            ws = form.save(commit=False)
            ws.owner = request.user
            # Slug logic: same as before
            base_slug = slugify(ws.name)
            slug = base_slug
            i = 2
            while Workspace.objects.filter(owner=request.user, slug=slug).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            ws.slug = slug
            ws.save()
            messages.success(request, 'Workspace created successfully!')
            return redirect('workspace_detail', slug=ws.slug)
    else:
        form = WorkspaceForm()
    return render(request, 'pages/workspace_form.html', {'form': form})

@login_required
def workspace_detail(request, slug):
    """View a workspace and its courses (publicly accessible)"""
    ws = get_object_or_404(Workspace, slug=slug)  # No owner filter
    courses = ws.courses.order_by('-created_at')
    return render(request, 'pages/workspace_detail.html', { 'workspace': ws, 'courses': courses })

@login_required
def workspace_update(request, slug):
    ws = get_object_or_404(Workspace, slug=slug, owner=request.user)
    if request.method == 'POST':
        form = WorkspaceForm(request.POST, request.FILES, instance=ws)
        if form.is_valid():
            ws = form.save()
            messages.success(request, 'Workspace updated!')
            return redirect('workspace_detail', slug=ws.slug)
    else:
        form = WorkspaceForm(instance=ws)
    return render(request, 'pages/workspace_form.html', {'form': form, 'workspace': ws})


@login_required
def workspace_delete(request, slug):
    ws = get_object_or_404(Workspace, slug=slug, owner=request.user)
    if request.method == 'POST':
        ws.delete()
        messages.success(request, 'Workspace deleted.')
        return redirect('workspace_list')
    return render(request, 'pages/workspace_confirm_delete.html', { 'workspace': ws })


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
            messages.error(request, 'Invalid credentials')
    return render(request, 'pages/sign-in.html')


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
    # Ensure user has a workspace
    user_workspaces = Workspace.objects.filter(owner=request.user)
    if not user_workspaces.exists():
        messages.info(request, 'Please create a workspace first.')
        return redirect('workspace_create')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        audio_file = request.FILES.get('audio_file')
        pdf_file = request.FILES.get('pdf_file')
        workspace_slug = request.POST.get('workspace')
        workspace = get_object_or_404(Workspace, slug=workspace_slug, owner=request.user)
        
        course = Course.objects.create(
            title=title,
            description=description,
            instructor=request.user,
            workspace=workspace,
            audio_file=audio_file,
            pdf_file=pdf_file
        )
        
        # Process content (synchronously for now)
        if audio_file:
            process_course_content_task(str(course.id))
        
        messages.success(request, 'Course created successfully!')
        return redirect('course_detail', course_id=course.id)
    
    return render(request, 'pages/upload_course.html', { 'workspaces': user_workspaces })


@login_required
def update_course(request, course_id):
    """Update an existing course (instructor only)"""
    course = get_object_or_404(Course, id=course_id)
    if request.user != course.instructor:
        messages.error(request, 'You do not have permission to edit this course.')
        return redirect('course_detail', course_id=course_id)

    if request.method == 'POST':
        course.title = request.POST.get('title', course.title)
        course.description = request.POST.get('description', course.description)
        # Allow moving between user's workspaces
        workspace_slug = request.POST.get('workspace')
        if workspace_slug:
            ws = get_object_or_404(Workspace, slug=workspace_slug, owner=request.user)
            course.workspace = ws

        # Optional file replacements
        if 'audio_file' in request.FILES:
            course.audio_file = request.FILES['audio_file']
        if 'pdf_file' in request.FILES:
            course.pdf_file = request.FILES['pdf_file']

        course.save()
        messages.success(request, 'Course updated successfully!')
        return redirect('course_detail', course_id=course.id)

    user_workspaces = Workspace.objects.filter(owner=request.user)
    context = {
        'course': course,
        'workspaces': user_workspaces,
    }
    return render(request, 'pages/edit_course.html', context)


@login_required
@require_http_methods(["POST", "GET"])
def delete_course(request, course_id):
    """Delete a course (instructor only, with confirmation)"""
    course = get_object_or_404(Course, id=course_id)
    if request.user != course.instructor:
        messages.error(request, 'You do not have permission to delete this course.')
        return redirect('course_detail', course_id=course_id)

    if request.method == 'POST':
        title = course.title
        course.delete()
        messages.success(request, f'Course "{title}" deleted successfully!')
        return redirect('home')

    return render(request, 'pages/confirm_delete_course.html', { 'course': course })


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
        
        # Process audio (synchronously for now)
        process_audio_question_task(str(audio_question.id))
        
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
@permission_classes([IsAuthenticated])
def face_recognition_login(request):
    """Face recognition login endpoint"""
    try:
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get face encoding from uploaded image
        face_encoding = ai_manager.recognize_face(image_file.temporary_file_path())
        
        if not face_encoding:
            return Response({'error': 'No face detected'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find matching user profile
        profiles = UserProfile.objects.exclude(face_encoding__isnull=True)
        for profile in profiles:
            if profile.face_encoding:
                # Compare face encodings (simplified comparison)
                stored_encoding = np.array(profile.face_encoding)
                current_encoding = np.array(face_encoding)
                
                # Calculate distance between encodings
                distance = np.linalg.norm(stored_encoding - current_encoding)
                
                if distance < 0.6:  # Threshold for face match
                    login(request, profile.user)
                    return Response({
                        'success': True,
                        'user': profile.user.username,
                        'message': 'Face recognition successful'
                    })
        
        return Response({'error': 'Face not recognized'}, status=status.HTTP_401_UNAUTHORIZED)
        
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


# ---------- AI Assistant for Courses (Groq) ----------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def summarize_course_api(request, course_id):
    """Generate and store a concise summary for the course using Groq LLM."""
    course = get_object_or_404(Course, id=course_id)

    # Allow if ?from=workshop or POST JSON/data 'from':'workshop', else instructor/enrolled only
    can_any_user = request.GET.get('from') == 'workshop' or request.data.get('from') == 'workshop'
    if not can_any_user and request.user != course.instructor and request.user not in course.students.all():
        return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

    try:
        summary = ai_manager.summarize_course_text(
            title=course.title,
            description=course.description,
            transcript=course.transcript or ''
        )
        # Persist summary on the course
        course.summary = summary or course.summary
        course.save(update_fields=['summary'])
        return Response({'summary': summary})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def explain_course_api(request, course_id):
    """Answer a user question with explanations based on course content."""
    course = get_object_or_404(Course, id=course_id)

    can_any_user = request.GET.get('from') == 'workshop' or request.data.get('from') == 'workshop'
    if not can_any_user and request.user != course.instructor and request.user not in course.students.all():
        return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

    question = request.data.get('question') or request.POST.get('question')
    if not question:
        return Response({'error': 'question is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        answer = ai_manager.explain_course_topic(
            title=course.title,
            description=course.description,
            transcript=course.transcript or '',
            question=question.strip()
        )
        return Response({'answer': answer})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)