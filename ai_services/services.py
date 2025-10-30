import os
import json
import requests
import base64
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from celery import shared_task
from course_app.models import Course, AudioQuestion
from .models import GeneratedContent, AnalyticsService
from .face_recognition_service import face_recognition_service

# Optional heavy deps are imported lazily where possible
try:
    import whisper  # optional local fallback
except Exception:
    whisper = None

try:
    import google.generativeai as genai
except Exception:
    genai = None

try:
    from .face_recognition_dlib import dlib_face_service
except Exception:
    dlib_face_service = None

# Import deep learning face recognition service
try:
    from .face_recognition_deep import deep_face_service
except Exception as e:
    print(f"Warning: Deep learning face service not available: {e}")
    deep_face_service = None


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
        self.text_generator_ready = False
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize AI services"""
        try:
            # Whisper (lazy-loaded on first use to reduce startup cost)
            self.whisper_model = None

            # Gemini
            api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            if genai and api_key:
                genai.configure(api_key=api_key)
                # We create the model on demand in generate_text_response
                self.text_generator_ready = True
            else:
                self.text_generator_ready = False
        except Exception as e:
            print(f"Error initializing AI services: {e}")
    
    def transcribe_audio(self, audio_file_path):
        """Transcribe audio.
        Priority:
        1) GROQ API (Whisper-large-v3) if GROQ_API_KEY is set
        2) Local Whisper fallback if installed
        """
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                # Send file to Groq for transcription
                with open(audio_file_path, 'rb') as f:
                    transcription = client.audio.transcriptions.create(
                        file=(os.path.basename(audio_file_path), f),
                        model=os.getenv('GROQ_WHISPER_MODEL', 'whisper-large-v3')
                    )
                return transcription.text.strip()
            except Exception as e:
                print(f"Groq transcription error: {e}")
                # fall through to local fallback
        try:
            if whisper is None:
                return "Speech-to-text not configured. Set GROQ_API_KEY or install 'openai-whisper'."
            if self.whisper_model is None:
                self.whisper_model = whisper.load_model(os.getenv('WHISPER_MODEL', 'base'))
            result = self.whisper_model.transcribe(audio_file_path)
            return result.get('text', '').strip()
        except FileNotFoundError:
            return "ffmpeg not found. Please install ffmpeg and ensure it's on your PATH."
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return None
    
    def generate_text_response(self, prompt, context=""):
        """Generate text response using Groq-hosted models.
        Priority order (auto-fallback):
        - GROQ_LLM_MODEL from env (if set)
        - mixtral-8x7b-32768
        - llama-3.1-8b-instant
        - llama-3.3-70b-versatile
        """
        # Prefer Groq (and only Groq). Gemini fallback removed to avoid 404s.
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                model_candidates = []
                if os.getenv('GROQ_LLM_MODEL'):
                    model_candidates.append(os.getenv('GROQ_LLM_MODEL'))
                # Updated available Groq models
                model_candidates.extend(['mixtral-8x7b-32768', 'llama-3.1-8b-instant', 'llama-3.3-70b-versatile'])
                full_prompt = prompt if not context else f"Context:\n{context}\n\nUser:\n{prompt}"
                last_error = None
                for model_name in model_candidates:
                    try:
                        chat = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": "You are a helpful educational assistant."},
                                {"role": "user", "content": full_prompt},
                            ],
                            temperature=float(os.getenv('LLM_TEMPERATURE', '0.2')),
                            max_tokens=512,
                        )
                        return chat.choices[0].message.content
                    except Exception as e:
                        last_error = e
                        continue
                print(f"Groq text generation error: {last_error}")
            except Exception as e:
                print(f"Error importing or using Groq: {e}")

        # No GROQ_API_KEY configured
        return "Text generation is not configured. Please set GROQ_API_KEY in .env."
    
    def generate_image(self, prompt, provider='openai'):
        """Generate image using ImageGenerationService"""
        try:
            return self.image_generator.generate_image(prompt, provider=provider)
        except Exception as e:
            print(f"Error generating image: {e}")
            return {"success": False, "error": str(e)}
            return None

    # ---------- Course helpers ----------
    def summarize_course_text(self, title: str, description: str, transcript: str | None) -> str:
        """Create a concise, student-friendly summary of a course.
        Uses Groq LLM with structured instructions.
        """
        base_context = f"Course Title: {title}\n\nDescription:\n{description}\n"
        if transcript:
            base_context += f"\nTranscript (may be long; prioritize salient points):\n{transcript[:8000]}"
        prompt = (
            "Write a concise summary of this course for students."
            " Focus on learning goals, key modules, and prerequisites."
            " Output 5-8 bullet points and a short paragraph (≤120 words)."
        )
        return self.generate_text_response(prompt, context=base_context)

    def explain_course_topic(self, title: str, description: str, transcript: str | None, question: str) -> str:
        """Explain a topic or question using the course material as context."""
        base_context = f"Course Title: {title}\n\nDescription:\n{description}\n"
        if transcript:
            base_context += f"\nTranscript excerpt:\n{transcript[:8000]}"
        prompt = (
            "Act as a teaching assistant. Explain the user's question clearly,"
            " with step-by-step reasoning and examples. If math/code is useful,"
            " include it. End with 3 practice questions. User question: " + question
        )
        return self.generate_text_response(prompt, context=base_context)

    def recognize_face(self, image_data):
        """Recognize face in image using the face recognition service"""
        try:
            # Get all user profiles with face encodings
            from course_app.models import UserProfile
            profiles = UserProfile.objects.exclude(face_encoding__isnull=True)

            print(f"\n🔍 Starting face recognition...")
            print(f"📊 Found {profiles.count()} registered face(s) in database")

            if not profiles:
                return None, "No registered faces found"

            # Prepare stored encodings
            stored_encodings = []
            for p in profiles:
                if p.face_encoding:
                    encoding_type = "unknown"
                    if isinstance(p.face_encoding, dict):
                        encoding_type = p.face_encoding.get('model', 'dict')
                    elif isinstance(p.face_encoding, list):
                        encoding_type = f"list[{len(p.face_encoding)}]"
                    print(f"  👤 User: {p.user.username} (ID: {p.user.id}, encoding: {encoding_type})")
                    stored_encodings.append((p.user.id, p.face_encoding))

            if not stored_encodings:
                return None, "No valid face encodings found"

            # Try deep learning service first (highest accuracy)
            user_id, confidence = (None, 0)
            if deep_face_service is not None:
                print(f"\n🤖 Trying Deep Learning (VGG16) recognition...")
                try:
                    user_id, confidence = deep_face_service.recognize_face(image_data, stored_encodings)
                    if user_id is not None:
                        print(f"✅ Deep learning recognition SUCCESS: User {user_id}, confidence {confidence:.2f}")
                except Exception as e:
                    print(f"❌ Deep learning recognition failed: {e}")
                    user_id, confidence = (None, 0)
            else:
                print(f"⚠️  Deep learning service not available")

            # Fallback to dlib-based recognition
            if user_id is None and dlib_face_service is not None:
                print(f"\n🔄 Trying Dlib recognition (fallback)...")
                try:
                    user_id, confidence = dlib_face_service.recognize_face(image_data, stored_encodings)
                    if user_id is not None:
                        print(f"✅ Dlib recognition SUCCESS: User {user_id}, confidence {confidence:.2f}")
                except Exception as e:
                    print(f"❌ Dlib recognition failed: {e}")
                    user_id, confidence = (None, 0)
            else:
                if user_id is None:
                    print(f"⚠️  Dlib service not available")

            # Final fallback to OpenCV service
            if user_id is None:
                print(f"\n🔄 Trying OpenCV recognition (final fallback)...")
                user_id, confidence = face_recognition_service.recognize_face(image_data, stored_encodings)
                if user_id is not None:
                    print(f"✅ OpenCV recognition SUCCESS: User {user_id}, confidence {confidence:.2f}")
                else:
                    print(f"❌ OpenCV recognition failed")

            if user_id:
                from django.contrib.auth.models import User
                user = User.objects.get(id=user_id)
                print(f"🎉 Final result: Recognized as {user.username}\n")
                return user, confidence

            print(f"❌ Final result: Face not recognized by any service\n")
            return None, "Face not recognized"

        except Exception as e:
            print(f"❌ Error recognizing face: {e}")
            import traceback
            traceback.print_exc()
            return None, str(e)
    
    def register_face(self, user, image_data):
        """Register user's face for recognition"""
        try:
            # Try deep learning service first (highest accuracy)
            success, result = (False, None)
            if deep_face_service is not None:
                try:
                    success, result = deep_face_service.register_face(user, image_data)
                    if success:
                        print(f"✓ Deep learning registration successful for user {user.username}")
                except Exception as e:
                    print(f"Deep learning registration failed: {e}")
                    success, result = (False, None)

            # Fallback to dlib-based registration
            if not success and dlib_face_service is not None:
                try:
                    success, result = dlib_face_service.register_face(user, image_data)
                    if success:
                        print(f"✓ Dlib registration successful for user {user.username}")
                except Exception as e:
                    print(f"Dlib registration failed: {e}")
                    success, result = (False, None)

            # Final fallback to OpenCV service
            if not success:
                success, result = face_recognition_service.register_face(user, image_data)
                if success:
                    print(f"✓ OpenCV registration successful for user {user.username}")

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

    # ---------- Course helpers ----------
    def summarize_course_text(self, title: str, description: str, transcript: str | None) -> str:
        """Create a concise, student-friendly summary of a course.
        Uses Groq LLM with structured instructions.
        """
        base_context = f"Course Title: {title}\n\nDescription:\n{description}\n"
        if transcript:
            base_context += f"\nTranscript (may be long; prioritize salient points):\n{transcript[:8000]}"
        prompt = (
            "Write a concise summary of this course for students."
            " Focus on learning goals, key modules, and prerequisites."
            " Output 5-8 bullet points and a short paragraph (≤120 words)."
        )
        return self.generate_text_response(prompt, context=base_context)

    def explain_course_topic(self, title: str, description: str, transcript: str | None, question: str) -> str:
        """Explain a topic or question using the course material as context."""
        base_context = f"Course Title: {title}\n\nDescription:\n{description}\n"
        if transcript:
            base_context += f"\nTranscript excerpt:\n{transcript[:8000]}"
        prompt = (
            "Act as a teaching assistant. Explain the user's question clearly,"
            " with step-by-step reasoning and examples. If math/code is useful,"
            " include it. End with 3 practice questions. User question: " + question
        )
        return self.generate_text_response(prompt, context=base_context)


# Global AI service manager instance
ai_manager = AIServiceManager()


@shared_task
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


@shared_task
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


@shared_task
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
