"""
AI Services for Quiz Generation and Analysis
"""
import json
import random
from typing import List, Dict, Any, Optional
from django.conf import settings
from .models import Quiz, QuizQuestion, QuizAttempt, QuizAnalytics, AnalyticsService


class QuizGenerationAI:
    """AI service for generating quizzes from course content"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.huggingface_key = getattr(settings, 'HUGGINGFACE_API_KEY', None)
    
    def generate_quiz_from_content(self, course_content: str, difficulty: str = 'intermediate', 
                                 num_questions: int = 10) -> Dict[str, Any]:
        """
        Generate quiz questions from course content using AI
        """
        try:
            # Analyze course content and extract key concepts
            key_concepts = self._extract_key_concepts(course_content)
            important_points = self._extract_important_points(course_content)
            
            # Generate questions based on actual content
            questions = self._generate_content_based_questions(
                course_content, key_concepts, important_points, difficulty, num_questions
            )
            
            return {
                'success': True,
                'questions': questions,
                'total_questions': len(questions),
                'difficulty': difficulty,
                'ai_confidence': 0.85,
                'content_analyzed': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'questions': []
            }
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from course content"""
        # Simple keyword extraction (in production, use NLP libraries)
        import re
        
        # Extract important terms (capitalized words, technical terms)
        concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        
        # Remove common words and get unique concepts
        common_words = {'The', 'This', 'That', 'These', 'Those', 'Course', 'Content', 'Material'}
        concepts = [c for c in set(concepts) if c not in common_words and len(c) > 3]
        
        return concepts[:10]  # Return top 10 concepts
    
    def _extract_important_points(self, content: str) -> List[str]:
        """Extract important points and facts from content"""
        import re
        
        # Split content into sentences
        sentences = re.split(r'[.!?]+', content)
        
        # Filter for important sentences (containing key indicators)
        important_indicators = ['important', 'key', 'main', 'primary', 'essential', 'critical', 'significant']
        important_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(indicator in sentence.lower() for indicator in important_indicators):
                important_sentences.append(sentence)
        
        return important_sentences[:5]  # Return top 5 important points
    
    def _generate_content_based_questions(self, content: str, key_concepts: List[str], 
                                        important_points: List[str], difficulty: str, 
                                        num_questions: int) -> List[Dict]:
        """Generate questions based on actual course content"""
        questions = []
        
        # Generate questions from key concepts
        for i, concept in enumerate(key_concepts[:num_questions//2]):
            question = {
                'id': f"concept_q_{i+1}",
                'question_text': f"What is {concept} and why is it important in this context?",
                'question_type': 'multiple_choice',
                'options': [
                    f"{concept} is a fundamental concept discussed in the material",
                    f"{concept} is mentioned but not important",
                    f"{concept} is a secondary topic",
                    f"{concept} is not covered in this content"
                ],
                'correct_answer': f"{concept} is a fundamental concept discussed in the material",
                'explanation': f"This concept is clearly explained in the course material.",
                'points': 1,
                'difficulty': difficulty,
                'order': i + 1,
                'ai_generated': True,
                'confidence_score': 0.9
            }
            questions.append(question)
        
        # Generate questions from important points
        for i, point in enumerate(important_points[:num_questions//2]):
            question = {
                'id': f"point_q_{i+1}",
                'question_text': f"According to the course material: {point[:100]}...",
                'question_type': 'true_false',
                'correct_answer': "True",
                'explanation': "This information is directly stated in the course content.",
                'points': 1,
                'difficulty': difficulty,
                'order': len(questions) + i + 1,
                'ai_generated': True,
                'confidence_score': 0.85
            }
            questions.append(question)
        
        # Generate open-ended questions about the content
        if len(questions) < num_questions:
            remaining = num_questions - len(questions)
            for i in range(remaining):
                question = {
                    'id': f"open_q_{i+1}",
                    'question_text': f"Explain one of the main concepts discussed in this course material.",
                    'question_type': 'open_ended',
                    'correct_answer': "Student should demonstrate understanding of the key concepts from the material",
                    'explanation': "Look for accurate explanation of concepts covered in the course content.",
                    'points': 2,
                    'difficulty': difficulty,
                    'order': len(questions) + i + 1,
                    'ai_generated': True,
                    'confidence_score': 0.8
                }
                questions.append(question)
        
        return questions[:num_questions]
    
    def _generate_questions_placeholder(self, content: str, difficulty: str, num_questions: int) -> List[Dict]:
        """Placeholder method for generating questions - replace with actual AI API calls"""
        
        # Sample question templates based on content analysis
        question_templates = {
            'multiple_choice': [
                {
                    'question': f"Based on the course content, what is the main concept discussed?",
                    'options': [
                        "Option A: Primary concept",
                        "Option B: Secondary concept", 
                        "Option C: Supporting detail",
                        "Option D: Background information"
                    ],
                    'correct_answer': "Option A: Primary concept",
                    'explanation': "The main concept is clearly identified in the content."
                },
                {
                    'question': f"What is the most important point mentioned in this section?",
                    'options': [
                        "Point A: Key insight",
                        "Point B: Supporting evidence",
                        "Point C: Example",
                        "Point D: Conclusion"
                    ],
                    'correct_answer': "Point A: Key insight",
                    'explanation': "This is the most significant point highlighted in the material."
                }
            ],
            'true_false': [
                {
                    'question': f"The content discusses advanced concepts that require prior knowledge.",
                    'correct_answer': "True",
                    'explanation': "The material builds upon previous concepts."
                },
                {
                    'question': f"This section provides practical examples for better understanding.",
                    'correct_answer': "True", 
                    'explanation': "Multiple examples are provided to illustrate the concepts."
                }
            ],
            'open_ended': [
                {
                    'question': f"Explain the main concept discussed in this section in your own words.",
                    'correct_answer': "Student should demonstrate understanding of the key concepts",
                    'explanation': "Look for accurate explanation of the main points."
                }
            ]
        }
        
        questions = []
        for i in range(min(num_questions, 10)):  # Limit to 10 questions
            question_type = random.choice(['multiple_choice', 'true_false', 'open_ended'])
            template = random.choice(question_templates[question_type])
            
            question = {
                'id': f"q_{i+1}",
                'question_text': template['question'],
                'question_type': question_type,
                'points': 1,
                'difficulty': difficulty,
                'order': i + 1
            }
            
            if question_type == 'multiple_choice':
                question['options'] = template['options']
                question['correct_answer'] = template['correct_answer']
            else:
                question['correct_answer'] = template['correct_answer']
            
            question['explanation'] = template['explanation']
            question['ai_generated'] = True
            question['confidence_score'] = random.uniform(0.7, 0.95)
            
            questions.append(question)
        
        return questions
    
    def generate_with_openai(self, content: str, difficulty: str, num_questions: int) -> List[Dict]:
        """Generate questions using OpenAI API"""
        # Implementation for OpenAI API
        # This would make actual API calls to OpenAI
        pass
    
    def generate_with_gemini(self, content: str, difficulty: str, num_questions: int) -> List[Dict]:
        """Generate questions using Google Gemini API"""
        # Implementation for Gemini API
        # This would make actual API calls to Gemini
        pass


class QuizAnalysisAI:
    """AI service for analyzing quiz results and providing insights"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    
    def analyze_quiz_attempt(self, attempt: QuizAttempt) -> Dict[str, Any]:
        """
        Analyze a quiz attempt and provide AI insights
        """
        try:
            # Calculate basic metrics
            score_percentage = attempt.calculate_score_percentage()
            
            # Analyze patterns
            analysis = {
                'score_percentage': score_percentage,
                'performance_level': self._get_performance_level(score_percentage),
                'strengths': self._identify_strengths(attempt),
                'weaknesses': self._identify_weaknesses(attempt),
                'recommendations': self._generate_recommendations(attempt),
                'ai_feedback': self._generate_feedback(attempt),
                'learning_suggestions': self._suggest_learning_paths(attempt)
            }
            
            return {
                'success': True,
                'analysis': analysis
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'analysis': {}
            }
    
    def _get_performance_level(self, score: float) -> str:
        """Determine performance level based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Satisfactory"
        elif score >= 60:
            return "Needs Improvement"
        else:
            return "Requires Attention"
    
    def _identify_strengths(self, attempt: QuizAttempt) -> List[str]:
        """Identify areas of strength based on correct answers"""
        strengths = []
        
        # Analyze correct answers to identify patterns
        if attempt.score and attempt.total_questions:
            score_ratio = attempt.score / attempt.total_questions
            
            if score_ratio >= 0.8:
                strengths.append("Strong conceptual understanding")
            if score_ratio >= 0.7:
                strengths.append("Good knowledge retention")
            if score_ratio >= 0.6:
                strengths.append("Basic comprehension skills")
        
        return strengths
    
    def _identify_weaknesses(self, attempt: QuizAttempt) -> List[str]:
        """Identify areas needing improvement"""
        weaknesses = []
        
        if attempt.score and attempt.total_questions:
            score_ratio = attempt.score / attempt.total_questions
            
            if score_ratio < 0.6:
                weaknesses.append("Fundamental concepts need review")
            if score_ratio < 0.7:
                weaknesses.append("Application skills need development")
            if score_ratio < 0.8:
                weaknesses.append("Advanced concepts require more study")
        
        return weaknesses
    
    def _generate_recommendations(self, attempt: QuizAttempt) -> List[str]:
        """Generate personalized learning recommendations"""
        recommendations = []
        
        if attempt.score and attempt.total_questions:
            score_ratio = attempt.score / attempt.total_questions
            
            if score_ratio < 0.7:
                recommendations.append("Review the course material thoroughly")
                recommendations.append("Practice with additional exercises")
                recommendations.append("Seek help from instructor or peers")
            elif score_ratio < 0.9:
                recommendations.append("Focus on advanced topics")
                recommendations.append("Practice application problems")
            else:
                recommendations.append("Explore advanced materials")
                recommendations.append("Consider mentoring others")
        
        return recommendations
    
    def _generate_feedback(self, attempt: QuizAttempt) -> str:
        """Generate personalized feedback message"""
        score_percentage = attempt.calculate_score_percentage()
        
        if score_percentage >= 90:
            return "Excellent work! You have a strong understanding of the material. Keep up the great work!"
        elif score_percentage >= 80:
            return "Good job! You understand most of the concepts well. Consider reviewing the areas you missed."
        elif score_percentage >= 70:
            return "You're on the right track! Focus on the concepts you missed and practice more."
        elif score_percentage >= 60:
            return "You need to review the material more thoroughly. Consider seeking additional help."
        else:
            return "This material requires more study. Please review the course content and consider getting help."
    
    def _suggest_learning_paths(self, attempt: QuizAttempt) -> List[str]:
        """Suggest specific learning paths based on performance"""
        suggestions = []
        
        if attempt.score and attempt.total_questions:
            score_ratio = attempt.score / attempt.total_questions
            
            if score_ratio < 0.6:
                suggestions.append("Start with basic concepts and work your way up")
                suggestions.append("Use additional learning resources")
                suggestions.append("Practice with simpler problems first")
            elif score_ratio < 0.8:
                suggestions.append("Focus on problem-solving techniques")
                suggestions.append("Practice with medium-difficulty problems")
            else:
                suggestions.append("Challenge yourself with advanced topics")
                suggestions.append("Consider teaching others to reinforce learning")
        
        return suggestions


class AdaptiveLearningAI:
    """AI service for adaptive learning and difficulty adjustment"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
    
    def adjust_difficulty(self, user_performance: Dict, current_difficulty: str) -> str:
        """
        Adjust quiz difficulty based on user performance
        """
        try:
            # Analyze performance patterns
            recent_scores = user_performance.get('recent_scores', [])
            average_score = sum(recent_scores) / len(recent_scores) if recent_scores else 0
            
            # Difficulty adjustment logic
            if average_score >= 85 and current_difficulty != 'advanced':
                return 'advanced'
            elif average_score >= 70 and current_difficulty == 'beginner':
                return 'intermediate'
            elif average_score < 60 and current_difficulty != 'beginner':
                return 'beginner'
            else:
                return current_difficulty
                
        except Exception as e:
            return current_difficulty
    
    def recommend_next_quiz(self, user_id: int, course_id: int) -> Optional[Dict]:
        """
        Recommend the next quiz based on user's learning progress
        """
        try:
            # This would analyze user's learning history and recommend appropriate quizzes
            # For now, return a placeholder recommendation
            return {
                'recommended_quiz_id': None,
                'reason': "Based on your performance, we recommend focusing on the current material",
                'difficulty': 'intermediate',
                'estimated_time': 15
            }
        except Exception as e:
            return None


# Global instances
quiz_generation_ai = QuizGenerationAI()
quiz_analysis_ai = QuizAnalysisAI()
adaptive_learning_ai = AdaptiveLearningAI()

