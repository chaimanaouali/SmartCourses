import os
import json
import requests
from django.conf import settings
from course_app.models import Course, AudioQuestion
from .models import GeneratedContent, AnalyticsService

# Optional heavy deps are imported lazily where possible
try:
    import whisper  # optional local fallback
except Exception:
    whisper = None

try:
    import google.generativeai as genai
except Exception:
    genai = None


class AIServiceManager:
    """Central manager for all AI services"""
    
    def __init__(self):
        self.whisper_model = None
        self.image_generator = None
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
        if groq_key and genai is not None:  # genai not required, just using env here
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
            from groq import Groq
            client = Groq(api_key=groq_key)
            model_candidates = []
            if os.getenv('GROQ_LLM_MODEL'):
                model_candidates.append(os.getenv('GROQ_LLM_MODEL'))
            # Updated available Groq models (prefer Mistral 7B Instruct if available)
            model_candidates.extend(['mistral-7b-instruct', 'mixtral-8x7b-32768', 'llama-3.1-8b-instant', 'llama-3.3-70b-versatile'])
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
            return "Sorry, I couldn't generate a response at this time."

        # No GROQ_API_KEY configured
        return "Text generation is not configured. Please set GROQ_API_KEY in .env."
    
    def generate_image(self, prompt):
        """Generate image using Hugging Face"""
        try:
            # Placeholder for image generation
            return None
        except Exception as e:
            print(f"Error generating image: {e}")
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
