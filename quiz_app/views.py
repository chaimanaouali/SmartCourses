"""
Views for Quiz functionality
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Avg, Count, Q
import json

from .models import Quiz, QuizAttempt, QuizAnalytics, AnalyticsService
from .ai_services import quiz_generation_ai, quiz_analysis_ai, adaptive_learning_ai
from course_app.models import Course


@login_required
def quiz_list(request):
    """Display list of available quizzes"""
    quizzes = Quiz.objects.filter(is_active=True).select_related('course', 'created_by')
    
    # Get user's attempt history
    user_attempts = QuizAttempt.objects.filter(user=request.user).values_list('quiz_id', flat=True)
    
    # Get all courses for quiz generation
    courses = Course.objects.filter(is_active=True)
    
    context = {
        'quizzes': quizzes,
        'user_attempts': list(user_attempts),
        'courses': courses,  # Add courses to context
    }
    return render(request, 'quiz/quiz_list.html', context)


@login_required
def generate_quiz(request, course_id):
    """Generate a quiz automatically from course content using AI"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        difficulty = request.POST.get('difficulty', 'intermediate')
        num_questions = int(request.POST.get('num_questions', 10))
        
        # Get course content for AI processing
        course_content = f"{course.title}\n{course.description}"
        if course.transcript:
            course_content += f"\n{course.transcript}"
        if course.summary:
            course_content += f"\n{course.summary}"
        
        # Generate quiz using AI
        ai_result = quiz_generation_ai.generate_quiz_from_content(
            course_content=course_content,
            difficulty=difficulty,
            num_questions=num_questions
        )
        
        if ai_result['success']:
            # Create quiz object
            quiz = Quiz.objects.create(
                title=f"AI Generated Quiz - {course.title}",
                description=f"Automatically generated quiz for {course.title}",
                course=course,
                created_by=request.user,
                quiz_type='auto',
                difficulty_level=difficulty,
                questions=ai_result['questions'],
                ai_generated=True,
                generation_prompt=f"Generate {num_questions} {difficulty} questions from course content",
                deadline=timezone.now() + timezone.timedelta(minutes=5),
            )
            
            messages.success(request, f'Quiz generated successfully with {len(ai_result["questions"])} questions!')
            return redirect('quiz_app:quiz_detail', quiz_id=quiz.id)
        else:
            messages.error(request, f'Failed to generate quiz: {ai_result.get("error", "Unknown error")}')
    
    context = {
        'course': course,
        'difficulty_choices': Quiz.DIFFICULTY_LEVELS,
    }
    return render(request, 'quiz/generate_quiz.html', context)


@login_required
def quiz_detail(request, quiz_id):
    """Display quiz details and start quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if user has already attempted this quiz
    user_attempts = QuizAttempt.objects.filter(user=request.user, quiz=quiz)
    can_attempt = user_attempts.count() < quiz.max_attempts
    
    # Get user's best attempt
    best_attempt = user_attempts.order_by('-score').first()
    
    context = {
        'quiz': quiz,
        'user_attempts': user_attempts,
        'can_attempt': can_attempt,
        'best_attempt': best_attempt,
        'questions_count': quiz.get_questions_count(),
    }
    return render(request, 'quiz/quiz_detail.html', context)


@login_required
def start_quiz(request, quiz_id):
    """Start a new quiz attempt"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if user can attempt
    user_attempts = QuizAttempt.objects.filter(user=request.user, quiz=quiz)
    if user_attempts.count() >= quiz.max_attempts:
        messages.error(request, 'You have reached the maximum number of attempts for this quiz.')
        return redirect('quiz_app:quiz_detail', quiz_id=quiz.id)
    
    # Create new attempt
    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        total_questions=quiz.get_questions_count()
    )
    
    return redirect('quiz_app:take_quiz', attempt_id=attempt.id)


@login_required
def take_quiz(request, attempt_id):
    """Take the quiz"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    
    if attempt.is_completed:
        messages.info(request, 'This quiz has already been completed.')
        return redirect('quiz_app:quiz_result', attempt_id=attempt.id)
    
    if request.method == 'POST':
        # Process answers
        answers = {}
        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = key.replace('question_', '')
                answers[question_id] = value
        
        attempt.answers = answers
        attempt.completed_at = timezone.now()
        attempt.is_completed = True
        
        # Calculate score
        correct_answers = 0
        for question in attempt.quiz.questions:
            question_id = question.get('id', '')
            user_answer = answers.get(question_id, '')
            correct_answer = question.get('correct_answer', '')
            
            if user_answer == correct_answer:
                correct_answers += 1
        
        attempt.correct_answers = correct_answers
        attempt.score = attempt.calculate_score_percentage()
        
        # Calculate time taken
        if attempt.started_at and attempt.completed_at:
            time_diff = attempt.completed_at - attempt.started_at
            attempt.time_taken = int(time_diff.total_seconds() / 60)
        
        attempt.save()
        
        # Generate AI analysis
        ai_analysis = quiz_analysis_ai.analyze_quiz_attempt(attempt)
        if ai_analysis['success']:
            analysis = ai_analysis['analysis']
            attempt.ai_feedback = analysis.get('ai_feedback', '')
            attempt.strengths = analysis.get('strengths', [])
            attempt.weaknesses = analysis.get('weaknesses', [])
            attempt.recommendations = analysis.get('recommendations', [])
            attempt.save()
        
        # Update quiz analytics
        quiz_analytics, created = QuizAnalytics.objects.get_or_create(
            user=request.user,
            quiz=attempt.quiz,
            defaults={
                'average_score': attempt.score,
                'total_attempts': 1,
                'best_score': attempt.score,
                'worst_score': attempt.score,
                'improvement_rate': 0.0,
                'time_spent': attempt.time_taken or 0,
                'completion_rate': 100.0,
            }
        )
        
        if not created:
            # Update existing analytics
            quiz_analytics.total_attempts += 1
            quiz_analytics.average_score = (quiz_analytics.average_score + attempt.score) / 2
            quiz_analytics.best_score = max(quiz_analytics.best_score, attempt.score)
            quiz_analytics.worst_score = min(quiz_analytics.worst_score, attempt.score)
            quiz_analytics.time_spent += attempt.time_taken or 0
            quiz_analytics.save()
        
        messages.success(request, f'Quiz completed! Your score: {attempt.score:.1f}%')
        return redirect('quiz_app:quiz_result', attempt_id=attempt.id)
    
    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'questions': attempt.quiz.questions,
    }
    return render(request, 'quiz/take_quiz.html', context)


@login_required
@require_http_methods(["POST"])
def submit_quiz(request, attempt_id):
    """Submit quiz answers and calculate score"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    
    if attempt.is_completed:
        messages.info(request, 'This quiz has already been completed.')
        return redirect('quiz_app:quiz_result', attempt_id=attempt.id)
    
    # Process submitted answers
    answers = []
    for question in attempt.quiz.questions.all():
        answer_key = f'question_{question.id}'
        user_answer = request.POST.get(answer_key, '')
        answers.append({
            'question_id': str(question.id),
            'answer': user_answer
        })
    
    # Save answers and calculate score
    attempt.answers = answers
    attempt.calculate_score()
    attempt.is_completed = True
    attempt.completed_at = timezone.now()
    attempt.save()
    
    # Update analytics
    analytics, created = QuizAnalytics.objects.get_or_create(
        user=request.user,
        quiz=attempt.quiz,
        defaults={
            'total_attempts': 1,
            'average_score': attempt.score,
            'completion_rate': 100.0
        }
    )
    
    if not created:
        analytics.total_attempts += 1
        analytics.average_score = (analytics.average_score * (analytics.total_attempts - 1) + attempt.score) / analytics.total_attempts
        analytics.completion_rate = (analytics.completion_rate * (analytics.total_attempts - 1) + 100.0) / analytics.total_attempts
        analytics.save()
    
    messages.success(request, f'Quiz submitted! Your score: {attempt.score}/{attempt.total_questions}')
    return redirect('quiz_app:quiz_result', attempt_id=attempt.id)


@login_required
def quiz_result(request, attempt_id):
    """Display quiz results with AI analysis"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    
    if not attempt.is_completed:
        messages.error(request, 'This quiz has not been completed yet.')
        return redirect('take_quiz', attempt_id=attempt.id)
    
    # Get user's analytics for this quiz
    analytics = QuizAnalytics.objects.filter(user=request.user, quiz=attempt.quiz).first()
    
    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'analytics': analytics,
        'score_percentage': attempt.calculate_score_percentage(),
        'passed': attempt.calculate_score_percentage() >= attempt.quiz.passing_score,
    }
    return render(request, 'quiz/quiz_result.html', context)


@login_required
def quiz_analytics(request):
    """Display user's quiz analytics and performance insights"""
    user_analytics = QuizAnalytics.objects.filter(user=request.user).select_related('quiz')
    
    # Calculate overall statistics
    total_quizzes = user_analytics.count()
    total_attempts = sum(analytics.total_attempts for analytics in user_analytics)
    average_score = user_analytics.aggregate(avg_score=Avg('average_score'))['avg_score'] or 0
    
    # Get recent attempts
    recent_attempts = QuizAttempt.objects.filter(
        user=request.user, 
        is_completed=True
    ).order_by('-completed_at')[:10]
    
    context = {
        'user_analytics': user_analytics,
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts,
        'average_score': round(average_score, 1),
        'recent_attempts': recent_attempts,
    }
    return render(request, 'quiz/quiz_analytics.html', context)


@login_required
def adaptive_quiz_recommendation(request):
    """Get AI-powered quiz recommendations"""
    # Get user's performance data
    user_attempts = QuizAttempt.objects.filter(user=request.user, is_completed=True)
    
    if not user_attempts.exists():
        return JsonResponse({
            'success': False,
            'message': 'No quiz attempts found. Please take some quizzes first.'
        })
    
    # Analyze performance patterns
    recent_scores = list(user_attempts.order_by('-completed_at')[:5].values_list('score', flat=True))
    user_performance = {
        'recent_scores': recent_scores,
        'average_score': sum(recent_scores) / len(recent_scores) if recent_scores else 0,
        'total_attempts': user_attempts.count()
    }
    
    # Get adaptive learning recommendations
    recommendation = adaptive_learning_ai.recommend_next_quiz(
        user_id=request.user.id,
        course_id=None  # Could be specific course
    )
    
    return JsonResponse({
        'success': True,
        'recommendation': recommendation,
        'user_performance': user_performance
    })


@login_required
@require_http_methods(["POST"])
def generate_quiz_api(request):
    """API endpoint for generating quiz via AJAX"""
    try:
        course_id = request.POST.get('course_id')
        difficulty = request.POST.get('difficulty', 'intermediate')
        num_questions = int(request.POST.get('num_questions', 10))
        
        course = get_object_or_404(Course, id=course_id)
        
        # Generate quiz using AI with comprehensive course content
        course_content = f"Course Title: {course.title}\n"
        course_content += f"Description: {course.description}\n"
        
        if course.transcript:
            course_content += f"Transcript: {course.transcript}\n"
        
        if course.summary:
            course_content += f"Summary: {course.summary}\n"
        
        if course.key_concepts:
            course_content += f"Key Concepts: {', '.join(course.key_concepts)}\n"
        
        # Add PDF content if available (this would require PDF parsing in production)
        if course.pdf_file:
            course_content += f"PDF Content: [PDF file available - {course.pdf_file.name}]\n"
        
        # Add audio content if available
        if course.audio_file:
            course_content += f"Audio Content: [Audio file available - {course.audio_file.name}]\n"
        
        ai_result = quiz_generation_ai.generate_quiz_from_content(
            course_content=course_content,
            difficulty=difficulty,
            num_questions=num_questions
        )
        
        if ai_result['success']:
            # Create quiz
            quiz = Quiz.objects.create(
                title=f"AI Generated Quiz - {course.title}",
                description=f"Auto-generated quiz for {course.title}",
                course=course,
                created_by=request.user,
                quiz_type='auto',
                difficulty_level=difficulty,
                questions=ai_result['questions'],
                ai_generated=True,
                deadline=timezone.now() + timezone.timedelta(minutes=5),
            )
            
            return JsonResponse({
                'success': True,
                'quiz_id': str(quiz.id),
                'message': f'Quiz generated with {len(ai_result["questions"])} questions'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': ai_result.get('error', 'Failed to generate quiz')
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["DELETE"])
def delete_quiz(request, quiz_id):
    """Delete a quiz (only by the creator)"""
    try:
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Check if user is the creator of the quiz
        if quiz.created_by != request.user:
            return JsonResponse({
                'success': False,
                'error': 'You can only delete quizzes that you created.'
            })
        
        # Delete the quiz
        quiz_title = quiz.title
        quiz.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Quiz "{quiz_title}" has been deleted successfully.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })