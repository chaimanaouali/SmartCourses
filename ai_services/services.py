import os
import json
import requests
import base64
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from course_app.models import Course, AudioQuestion
from .models import GeneratedContent, AnalyticsService


class ImageGenerationService:
    """Service for AI-powered image generation"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
        self.stability_api_key = os.getenv('STABILITY_API_KEY')
    
    def generate_image(self, text_description, provider='openai', size='1024x1024', quality='standard'):
        """Generate image from text description using specified AI provider
        
        Args:
            text_description (str): Text description to generate image from
            provider (str): AI provider ('openai', 'huggingface', 'stability')
            size (str): Image size (e.g., '1024x1024', '512x512')
            quality (str): Quality level ('standard', 'hd')
            
        Returns:
            dict: {"success": bool, "image_url": str, "image_data": bytes, "error": str}
        """
        if provider == 'openai':
            return self._generate_with_openai(text_description, size, quality)
        elif provider == 'huggingface':
            return self._generate_with_huggingface(text_description)
        elif provider == 'stability':
            return self._generate_with_stability(text_description)
        else:
            return {"success": False, "error": "Unknown provider"}
    
    def _generate_with_openai(self, prompt, size='1024x1024', quality='standard'):
        """Generate image using OpenAI DALL-E API"""
        if not self.openai_api_key or self.openai_api_key == 'your_openai_api_key_here':
            return {
                "success": False,
                "error": "OpenAI API key not configured",
                "placeholder": True
            }
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
            
            image_url = response.data[0].url
            
            # Download the image
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                return {
                    "success": True,
                    "image_url": image_url,
                    "image_data": image_response.content,
                    "service": "DALL-E 3 (OpenAI)"
                }
            else:
                return {"success": False, "error": "Failed to download generated image"}
                
        except Exception as e:
            return {"success": False, "error": f"OpenAI generation error: {str(e)}"}
    
    def _generate_with_huggingface(self, prompt):
        """Generate image using Hugging Face Stable Diffusion"""
        if not self.huggingface_api_key or self.huggingface_api_key == 'your_huggingface_api_key_here':
            return {
                "success": False,
                "error": "Hugging Face API key not configured",
                "placeholder": True
            }
        
        try:
            API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
            headers = {"Authorization": f"Bearer {self.huggingface_api_key}"}
            
            response = requests.post(
                API_URL,
                headers=headers,
                json={"inputs": prompt}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "image_data": response.content,
                    "image_url": "",
                    "service": "Stable Diffusion XL (Hugging Face)"
                }
            else:
                return {"success": False, "error": f"Hugging Face API error: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Hugging Face generation error: {str(e)}"}
    
    def _generate_with_stability(self, prompt):
        """Generate image using Stability AI"""
        if not self.stability_api_key:
            return {
                "success": False,
                "error": "Stability AI API key not configured",
                "placeholder": True
            }
        
        try:
            API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            headers = {
                "Authorization": f"Bearer {self.stability_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
                "steps": 30,
            }
            
            response = requests.post(API_URL, headers=headers, json=data)
            
            if response.status_code == 200:
                data = response.json()
                image_data = base64.b64decode(data["artifacts"][0]["base64"])
                return {
                    "success": True,
                    "image_data": image_data,
                    "image_url": "",
                    "service": "Stable Diffusion XL (Stability AI)"
                }
            else:
                return {"success": False, "error": f"Stability AI error: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Stability AI generation error: {str(e)}"}
    
    def create_illustration_from_description(self, course, description, provider='openai', tags=None):
        """Create an Illustration object with AI-generated image
        
        Args:
            course: Course object
            description (str): Text description for image generation
            provider (str): AI provider to use
            tags (list): Optional list of tags
            
        Returns:
            Illustration object or None if generation failed
        """
        from course_app.models import Illustration
        
        # Generate the image
        result = self.generate_image(description, provider=provider)
        
        if not result["success"]:
            print(f"Image generation failed: {result.get('error')}")
            # Return placeholder illustration if API not configured
            if result.get('placeholder'):
                illustration = Illustration.objects.create(
                    course=course,
                    description=description,
                    ai_generated=True,
                    generation_prompt=description,
                    generation_service=provider,
                    tags=tags or [],
                    image_url="https://via.placeholder.com/1024x1024?text=AI+Image+Generation+Pending"
                )
                return illustration
            return None
        
        # Create Illustration object
        illustration = Illustration.objects.create(
            course=course,
            description=description,
            image_url=result.get('image_url', ''),
            ai_generated=True,
            generation_prompt=description,
            generation_service=result.get('service', provider),
            generation_timestamp=timezone.now(),
            tags=tags or []
        )
        
        # Save image file if we have image data
        if result.get('image_data'):
            image_content = ContentFile(result['image_data'])
            filename = f"illustration_{illustration.id}.png"
            illustration.image_file.save(filename, image_content, save=True)
        
        return illustration


class AIServiceManager:
    """Central manager for all AI services"""
    
    def __init__(self):
        self.whisper_model = None
        self.image_generator = ImageGenerationService()
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
    
    def generate_image(self, prompt, provider='openai'):
        """Generate image using ImageGenerationService"""
        try:
            return self.image_generator.generate_image(prompt, provider=provider)
        except Exception as e:
            print(f"Error generating image: {e}")
            return {"success": False, "error": str(e)}
    
    def recognize_face(self, image_path):
        """Recognize face in image"""
        try:
            # Placeholder for face recognition
            return None
        except Exception as e:
            print(f"Error recognizing face: {e}")
            return None
    
    def detect_engagement(self, image_path):
        """Detect user engagement from facial expressions"""
        try:
            # Placeholder for engagement detection
            return {
                'engagement_score': 0.5,
                'face_detected': True,
                'face_count': 1
            }
        except Exception as e:
            print(f"Error detecting engagement: {e}")
            return {'engagement_score': 0.0, 'face_detected': False, 'face_count': 0}


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
