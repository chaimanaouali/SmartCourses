import os
import json
import requests
from django.conf import settings
from course_app.models import Course, AudioQuestion
from .models import GeneratedContent, AnalyticsService
from .face_recognition_service import face_recognition_service
try:
    from .face_recognition_dlib import dlib_face_service
except Exception:
    dlib_face_service = None


class AIServiceManager:
    """Central manager for all AI services"""
    
    def __init__(self):
        self.whisper_model = None
        self.image_generator = None
        self.text_generator = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize AI services"""
        try:
            # Initialize services will be added later when packages are installed
            pass
        except Exception as e:
            print(f"Error initializing AI services: {e}")
    
    def transcribe_audio(self, audio_file_path):
        """Transcribe audio using Whisper"""
        try:
            # Placeholder for Whisper transcription
            return "This is a placeholder transcription. Install Whisper to enable real transcription."
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return None
    
    def generate_text_response(self, prompt, context=""):
        """Generate text response using Gemini"""
        try:
            # Placeholder for Gemini text generation
            return f"This is a placeholder AI response for: {prompt}. Install Gemini API to enable real responses."
        except Exception as e:
            print(f"Error generating text response: {e}")
            return "Sorry, I couldn't generate a response at this time."
    
    def generate_image(self, prompt):
        """Generate image using Hugging Face"""
        try:
            # Placeholder for image generation
            return None
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
    
    def recognize_face(self, image_data):
        """Recognize face in image using the face recognition service"""
        try:
            # Get all user profiles with face encodings
            from course_app.models import UserProfile
            profiles = UserProfile.objects.exclude(face_encoding__isnull=True)
            
            if not profiles:
                return None, "No registered faces found"
            
            # Prepare stored encodings
            stored_encodings = [(p.user.id, p.face_encoding) for p in profiles if p.face_encoding]
            
            # Prefer dlib-based recognition if available
            user_id, confidence = (None, 0)
            if dlib_face_service is not None:
                try:
                    user_id, confidence = dlib_face_service.recognize_face(image_data, stored_encodings)
                except Exception:
                    user_id, confidence = (None, 0)
            
            # Fallback to OpenCV service
            if user_id is None:
                user_id, confidence = face_recognition_service.recognize_face(image_data, stored_encodings)
            
            if user_id:
                from django.contrib.auth.models import User
                user = User.objects.get(id=user_id)
                return user, confidence
            
            return None, "Face not recognized"
            
        except Exception as e:
            print(f"Error recognizing face: {e}")
            return None, str(e)
    
    def register_face(self, user, image_data):
        """Register user's face for recognition"""
        try:
            # Prefer dlib-based registration if available
            success, result = (False, None)
            if dlib_face_service is not None:
                try:
                    success, result = dlib_face_service.register_face(user, image_data)
                except Exception:
                    success, result = (False, None)
            
            # Fallback to OpenCV service
            if not success:
                success, result = face_recognition_service.register_face(user, image_data)
            return success, result
        except Exception as e:
            print(f"Error registering face: {e}")
            return False, str(e)
    
    def detect_engagement(self, image_data):
        """Detect user engagement from facial expressions"""
        try:
            engagement_status = face_recognition_service.detect_engagement(image_data)
            
            # Convert to score-based format
            if "Focused" in engagement_status:
                score = 0.9
            elif "Multiple" in engagement_status:
                score = 0.4
            elif "No" in engagement_status:
                score = 0.0
            else:
                score = 0.5
            
            return {
                'engagement_score': score,
                'face_detected': "No" not in engagement_status,
                'status': engagement_status
            }
        except Exception as e:
            print(f"Error detecting engagement: {e}")
            return {'engagement_score': 0.0, 'face_detected': False, 'status': 'Error'}


# Global AI service manager instance
ai_manager = AIServiceManager()


def process_audio_question_task(question_id):
    """Process audio questions"""
    try:
        question = AudioQuestion.objects.get(id=question_id)
        
        # Transcribe audio
        transcript = ai_manager.transcribe_audio(question.audio_file.path)
        if transcript:
            question.transcript = transcript
            question.question_text = transcript
            question.save()
            
            # Generate AI response
            response = ai_manager.generate_text_response(transcript)
            question.ai_response = response
            
            question.is_processed = True
            question.save()
            
        return f"Processed question {question_id}"
    except Exception as e:
        return f"Error processing question {question_id}: {e}"


def process_course_content_task(course_id):
    """Process course content"""
    try:
        course = Course.objects.get(id=course_id)
        
        # Process audio file if exists
        if course.audio_file:
            transcript = ai_manager.transcribe_audio(course.audio_file.path)
            if transcript:
                course.transcript = transcript
                
                # Generate summary
                summary_prompt = f"Please provide a comprehensive summary of this educational content:\n\n{transcript}"
                summary = ai_manager.generate_text_response(summary_prompt)
                course.summary = summary
                
                # Extract key concepts
                concepts_prompt = f"Extract the main key concepts from this educational content:\n\n{transcript}"
                concepts_response = ai_manager.generate_text_response(concepts_prompt)
                course.key_concepts = concepts_response.split('\n')[:10]  # Top 10 concepts
                
                course.save()
        
        return f"Processed course {course_id}"
    except Exception as e:
        return f"Error processing course {course_id}: {e}"


def generate_quiz_from_course_task(course_id):
    """Generate quiz from course content"""
    try:
        from quiz_app.models import Quiz
        
        course = Course.objects.get(id=course_id)
        
        if not course.transcript:
            return f"No transcript available for course {course_id}"
        
        # Generate quiz questions using AI
        quiz_prompt = f"""
        Based on this educational content, generate 10 quiz questions with multiple choice answers.
        Content: {course.transcript}
        
        Format the response as JSON with this structure:
        {{
            "questions": [
                {{
                    "question": "Question text",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "explanation": "Why this answer is correct"
                }}
            ]
        }}
        """
        
        quiz_response = ai_manager.generate_text_response(quiz_prompt)
        
        # Parse the response (in a real implementation, you'd want better JSON parsing)
        try:
            quiz_data = json.loads(quiz_response)
            questions = quiz_data.get('questions', [])
            
            # Create quiz
            quiz = Quiz.objects.create(
                course=course,
                title=f"Quiz for {course.title}",
                description="AI-generated quiz based on course content",
                questions=questions
            )
            
            return f"Generated quiz {quiz.id} for course {course_id}"
        except json.JSONDecodeError:
            return f"Failed to parse quiz response for course {course_id}"
            
    except Exception as e:
        return f"Error generating quiz for course {course_id}: {e}"
