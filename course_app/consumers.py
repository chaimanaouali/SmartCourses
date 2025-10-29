import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Course, AudioQuestion, EngagementSession
from ai_services.services import ai_manager


class CourseConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for course interactions"""
    
    async def connect(self):
        self.course_id = self.scope['url_route']['kwargs']['course_id']
        self.course_group_name = f'course_{self.course_id}'
        
        # Join course group
        await self.channel_layer.group_add(
            self.course_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave course group
        await self.channel_layer.group_discard(
            self.course_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'audio_question':
                await self.handle_audio_question(data)
            elif message_type == 'engagement_update':
                await self.handle_engagement_update(data)
            elif message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'quiz_answer':
                await self.handle_quiz_answer(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def handle_audio_question(self, data):
        """Handle audio question submission"""
        try:
            user = self.scope['user']
            if not user.is_authenticated:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Authentication required'
                }))
                return
            
            # Process audio question
            question_data = await self.process_audio_question(data, user)
            
            # Send response to course group
            await self.channel_layer.group_send(
                self.course_group_name,
                {
                    'type': 'audio_question_response',
                    'data': question_data
                }
            )
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing audio question: {str(e)}'
            }))
    
    async def handle_engagement_update(self, data):
        """Handle engagement tracking updates"""
        try:
            user = self.scope['user']
            if not user.is_authenticated:
                return
            
            session_id = data.get('session_id')
            engagement_data = data.get('engagement_data', {})
            
            # Update engagement session
            await self.update_engagement_session(session_id, engagement_data, user)
            
        except Exception as e:
            print(f"Error updating engagement: {e}")
    
    async def handle_chat_message(self, data):
        """Handle chat messages"""
        try:
            user = self.scope['user']
            if not user.is_authenticated:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Authentication required'
                }))
                return
            
            message = data.get('message', '')
            
            # Generate AI response
            ai_response = await self.generate_ai_response(message)
            
            # Send to course group
            await self.channel_layer.group_send(
                self.course_group_name,
                {
                    'type': 'chat_message_response',
                    'data': {
                        'user': user.username,
                        'message': message,
                        'ai_response': ai_response,
                        'timestamp': data.get('timestamp')
                    }
                }
            )
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing chat message: {str(e)}'
            }))
    
    async def handle_quiz_answer(self, data):
        """Handle quiz answer submission"""
        try:
            user = self.scope['user']
            if not user.is_authenticated:
                return
            
            quiz_id = data.get('quiz_id')
            answer = data.get('answer')
            question_index = data.get('question_index')
            
            # Process quiz answer
            result = await self.process_quiz_answer(quiz_id, answer, question_index, user)
            
            # Send response
            await self.send(text_data=json.dumps({
                'type': 'quiz_answer_response',
                'data': result
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing quiz answer: {str(e)}'
            }))
    
    @database_sync_to_async
    def process_audio_question(self, data, user):
        """Process audio question and return response data"""
        try:
            # Create audio question record
            audio_question = AudioQuestion.objects.create(
                user=user,
                course_id=self.course_id,
                question_text=data.get('transcript', ''),
                ai_response=data.get('ai_response', ''),
                is_processed=True
            )
            
            return {
                'question_id': str(audio_question.id),
                'user': user.username,
                'transcript': audio_question.question_text,
                'ai_response': audio_question.ai_response,
                'timestamp': audio_question.created_at.isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    @database_sync_to_async
    def update_engagement_session(self, session_id, engagement_data, user):
        """Update engagement session data"""
        try:
            if session_id:
                session = EngagementSession.objects.get(
                    id=session_id,
                    user=user,
                    is_active=True
                )
                
                current_data = session.engagement_data or []
                current_data.append(engagement_data)
                session.engagement_data = current_data
                
                if engagement_data.get('engagement_score'):
                    session.attention_score = engagement_data['engagement_score']
                
                session.save()
        except EngagementSession.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error updating engagement session: {e}")
    
    @database_sync_to_async
    def generate_ai_response(self, message):
        """Generate AI response to chat message"""
        try:
            # Get course context
            course = Course.objects.get(id=self.course_id)
            context = f"Course: {course.title}\nDescription: {course.description}"
            
            # Generate response using AI service
            response = ai_manager.generate_text_response(message, context)
            return response
        except Exception as e:
            return f"Sorry, I couldn't generate a response: {str(e)}"
    
    @database_sync_to_async
    def process_quiz_answer(self, quiz_id, answer, question_index, user):
        """Process quiz answer and return result"""
        try:
            from quiz_app.models import Quiz, QuizAttempt
            
            quiz = Quiz.objects.get(id=quiz_id)
            
            # Get or create quiz attempt
            attempt, created = QuizAttempt.objects.get_or_create(
                user=user,
                quiz=quiz,
                is_completed=False,
                defaults={'answers': []}
            )
            
            # Update answers
            answers = attempt.answers or []
            while len(answers) <= question_index:
                answers.append(None)
            answers[question_index] = answer
            attempt.answers = answers
            attempt.save()
            
            # Check if answer is correct
            question = quiz.questions[question_index] if question_index < len(quiz.questions) else None
            is_correct = question and answer == question.get('correct_answer')
            
            return {
                'is_correct': is_correct,
                'correct_answer': question.get('correct_answer') if question else None,
                'explanation': question.get('explanation') if question else None,
                'question_index': question_index
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # WebSocket event handlers
    async def audio_question_response(self, event):
        """Send audio question response to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'audio_question_response',
            'data': event['data']
        }))
    
    async def chat_message_response(self, event):
        """Send chat message response to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message_response',
            'data': event['data']
        }))
    
    async def engagement_update(self, event):
        """Send engagement update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'engagement_update',
            'data': event['data']
        }))


class QuizConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for quiz interactions"""
    
    async def connect(self):
        self.quiz_id = self.scope['url_route']['kwargs']['quiz_id']
        self.quiz_group_name = f'quiz_{self.quiz_id}'
        
        # Join quiz group
        await self.channel_layer.group_add(
            self.quiz_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave quiz group
        await self.channel_layer.group_discard(
            self.quiz_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'quiz_start':
                await self.handle_quiz_start(data)
            elif message_type == 'quiz_answer':
                await self.handle_quiz_answer(data)
            elif message_type == 'quiz_complete':
                await self.handle_quiz_complete(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def handle_quiz_start(self, data):
        """Handle quiz start"""
        try:
            user = self.scope['user']
            if not user.is_authenticated:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Authentication required'
                }))
                return
            
            # Get quiz data
            quiz_data = await self.get_quiz_data()
            
            await self.send(text_data=json.dumps({
                'type': 'quiz_started',
                'data': quiz_data
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error starting quiz: {str(e)}'
            }))
    
    async def handle_quiz_answer(self, data):
        """Handle quiz answer submission"""
        try:
            user = self.scope['user']
            if not user.is_authenticated:
                return
            
            answer = data.get('answer')
            question_index = data.get('question_index')
            
            # Process answer
            result = await self.process_answer(answer, question_index, user)
            
            await self.send(text_data=json.dumps({
                'type': 'answer_result',
                'data': result
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing answer: {str(e)}'
            }))
    
    async def handle_quiz_complete(self, data):
        """Handle quiz completion"""
        try:
            user = self.scope['user']
            if not user.is_authenticated:
                return
            
            # Calculate final score
            final_score = await self.calculate_final_score(user)
            
            await self.send(text_data=json.dumps({
                'type': 'quiz_completed',
                'data': final_score
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error completing quiz: {str(e)}'
            }))
    
    @database_sync_to_async
    def get_quiz_data(self):
        """Get quiz data"""
        try:
            from quiz_app.models import Quiz
            quiz = Quiz.objects.get(id=self.quiz_id)
            
            return {
                'quiz_id': str(quiz.id),
                'title': quiz.title,
                'description': quiz.description,
                'questions': quiz.questions,
                'difficulty_level': quiz.difficulty_level
            }
        except Exception as e:
            return {'error': str(e)}
    
    @database_sync_to_async
    def process_answer(self, answer, question_index, user):
        """Process quiz answer"""
        try:
            from quiz_app.models import Quiz, QuizAttempt
            
            quiz = Quiz.objects.get(id=self.quiz_id)
            
            # Get or create attempt
            attempt, created = QuizAttempt.objects.get_or_create(
                user=user,
                quiz=quiz,
                is_completed=False,
                defaults={'answers': []}
            )
            
            # Update answers
            answers = attempt.answers or []
            while len(answers) <= question_index:
                answers.append(None)
            answers[question_index] = answer
            attempt.answers = answers
            attempt.save()
            
            # Check correctness
            question = quiz.questions[question_index] if question_index < len(quiz.questions) else None
            is_correct = question and answer == question.get('correct_answer')
            
            return {
                'is_correct': is_correct,
                'correct_answer': question.get('correct_answer') if question else None,
                'explanation': question.get('explanation') if question else None,
                'question_index': question_index
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @database_sync_to_async
    def calculate_final_score(self, user):
        """Calculate final quiz score"""
        try:
            from quiz_app.models import Quiz, QuizAttempt
            
            quiz = Quiz.objects.get(id=self.quiz_id)
            attempt = QuizAttempt.objects.get(user=user, quiz=quiz, is_completed=False)
            
            # Calculate score
            score = attempt.calculate_score()
            attempt.is_completed = True
            attempt.save()
            
            return {
                'score': score,
                'max_score': attempt.max_score,
                'percentage': (score / attempt.max_score * 100) if attempt.max_score > 0 else 0
            }
            
        except Exception as e:
            return {'error': str(e)}




