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
        Generate quiz questions from course content using AI.
        Priority:
        1) Groq LLM via ai_manager.generate_text_response to produce strict JSON questions
        2) Fallback to local content-based heuristic generation
        """
        try:
            # Try Groq first for content-specific generation
            try:
                from ai_services.services import ai_manager  # local import to avoid cycles
                sys_prompt = (
                    "You are an assessment generator. Create quiz questions strictly from the given course content. "
                    "Do NOT invent facts outside the content. Use only information that appears in the content."
                )
                # Build a strong, content-bound instruction
                seed = str(abs(hash(course_content)) % 10_000_000)
                user_prompt = (
                    "COURSE_TITLE: " + (course_content.split("\n", 1)[0][:120]) + "\n"  # best-effort title from the first line
                    + "CONTENT:\n" + course_content[:12000] + "\n\n"
                    + "TASK: Generate exactly " + str(num_questions) + " quiz questions in strict JSON. "
                    + "Every question MUST be grounded in CONTENT and include at least TWO literal keywords from CONTENT or COURSE_TITLE. "
                    + "Forbidden: placeholders like 'Title', 'context', 'important', or generic phrasing like 'why is it important in this context'. "
                    + "Vary question wording and types. Explanations must quote a phrase from CONTENT or mention COURSE_TITLE explicitly.\n"
                    + "SCHEMA (NO MARKDOWN, PURE JSON):\n"
                    + "{\n  \"questions\": [\n    {\n      \"id\": \"q1\",\n      \"question_text\": \"...\",\n      \"question_type\": \"multiple_choice\"|\"true_false\"|\"open_ended\",\n      \"options\": [\"A\",\"B\",\"C\",\"D\"] (omit for open_ended),\n      \"correct_answer\": \"...\",\n      \"explanation\": \"reference COURSE_TITLE or quoted phrase from CONTENT\",\n      \"points\": 1,\n      \"difficulty\": \"" + difficulty + "\"\n    }\n  ]\n}\n"
                    + "Return ONLY JSON. Include diverse questions and vary wording. SEED: " + seed + "\n"
                )
                raw = ai_manager.generate_text_response(prompt=user_prompt, context=sys_prompt)
                # Extract JSON
                import json, re
                match = re.search(r"\{[\s\S]*\}$", raw.strip())
                payload = raw if match is None else match.group(0)
                data = json.loads(payload)
                questions = data.get('questions', [])
                if not questions:
                    raise ValueError('Empty questions from LLM')
                # enforce content specificity
                first_line = (course_content.split("\n", 1)[0] or '')
                questions = self._enforce_content_keywords(first_line, course_content, questions)
                return {
                    'success': True,
                    'questions': questions[:num_questions],
                    'total_questions': len(questions),
                    'difficulty': difficulty,
                    'ai_confidence': 0.9,
                    'content_analyzed': True
                }
            except Exception as e:
                # Fall back to heuristic generator
                pass

            # Heuristic fallback path
            key_concepts = self._extract_key_concepts(course_content)
            important_points = self._extract_important_points(course_content)
            questions = self._generate_content_based_questions(
                course_content, key_concepts, important_points, difficulty, num_questions
            )
            first_line = (course_content.split("\n", 1)[0] or '')
            questions = self._enforce_content_keywords(first_line, course_content, questions)
            return {
                'success': True,
                'questions': questions,
                'total_questions': len(questions),
                'difficulty': difficulty,
                'ai_confidence': 0.75,
                'content_analyzed': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'questions': []
            }
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from course content (keyword-based, content-specific)."""
        import re
        from collections import Counter

        if not content:
            return []

        # Normalize
        text = re.sub(r"[^A-Za-z0-9\-\s]", " ", content)
        words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.lower())

        # Simple stopwords list (no external deps)
        stopwords = {
            'the','and','for','with','that','this','from','your','you','are','was','were','will','shall','into','onto','about','above','below','under','over',
            'a','an','of','to','in','on','at','by','it','as','be','is','am','or','if','but','not','no','yes','do','does','did','can','could','should','would',
            'have','has','had','we','they','them','their','our','us','i','me','my','mine','yours','his','her','its','also','more','most','least','than','such',
            'course','content','material','section','chapter','topic','introduction','overview'
        }

        filtered = [w for w in words if w not in stopwords and len(w) >= 4]
        if not filtered:
            return []

        counts = Counter(filtered)
        top = [w for w, _ in counts.most_common(12)]
        # Return capitalized display concepts
        return [w.replace('-', ' ').title() for w in top]

    def _extract_important_points(self, content: str) -> List[str]:
        """Extract important points and facts from content (prioritize sentences with keywords and bullet lines)."""
        import re
        if not content:
            return []

        # Break into candidate sentences/lines
        sentences = re.split(r"[.!?\n]+", content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 0]

        # Heuristics for importance
        indicators = ['important','key','main','primary','essential','critical','significant','definition','concept','principle','rule','note']
        keyword_based = []
        for s in sentences:
            score = 0
            sl = s.lower()
            # bullet-like lines get a boost
            if re.match(r"^[-*•]", s):
                score += 2
            # indicator words
            score += sum(1 for ind in indicators if ind in sl)
            # length boost
            if len(s) > 40:
                score += 1
            if score > 0:
                keyword_based.append((score, s))

        keyword_based.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in keyword_based[:6]]
    
    def _split_sentences(self, content: str) -> List[str]:
        import re
        if not content:
            return []
        # Split on punctuation and newlines; keep longer sentences only
        parts = re.split(r"(?<=[.!?])\s+|\n+", content)
        sentences = [p.strip() for p in parts if len(p.strip()) >= 40]
        # Deduplicate while preserving order
        seen = set()
        ordered = []
        for s in sentences:
            key = s.lower()
            if key not in seen:
                seen.add(key)
                ordered.append(s)
        return ordered[:50]

    def _make_distractors(self, sentence: str, count: int = 3) -> List[str]:
        # crude distractor generation by negation and mild paraphrase
        s = sentence.strip()
        variants = []
        neg = s
        for term in [" is ", " are ", " was ", " were "]:
            if term in s:
                neg = s.replace(term, " is not ", 1)
                break
        if neg == s:
            neg = "It is not true that " + s[0].lower() + s[1:]
        variants.append(neg)
        variants.append("This statement is unrelated to the course content.")
        variants.append("The course explicitly contradicts this statement.")
        return variants[:count]

    def _generate_content_based_questions(self, content: str, key_concepts: List[str], 
                                        important_points: List[str], difficulty: str, 
                                        num_questions: int) -> List[Dict]:
        """Generate questions directly from course content sentences/snippets"""
        questions = []
        sentences = self._split_sentences(content)
        order_counter = 1
        # 1) True/False directly from sentences
        for s in sentences[: max(1, num_questions // 3)]:
            questions.append({
                'id': f"tf_{order_counter}",
                'question_text': f"True or False: '{s[:160]}'",
                'question_type': 'true_false',
                'correct_answer': 'True',
                'explanation': "This is quoted from the course content.",
                'points': 1,
                'difficulty': difficulty,
                'order': order_counter,
                'ai_generated': True,
                'confidence_score': 0.9,
            })
            order_counter += 1
            if len(questions) >= num_questions:
                return questions[:num_questions]
        # 2) Multiple choice based on sentence being the only correct option
        for s in sentences[len(questions): len(questions) + max(1, num_questions // 2)]:
            distractors = self._make_distractors(s)
            options = [s] + distractors
            questions.append({
                'id': f"mc_{order_counter}",
                'question_text': "According to the course, which statement is correct?",
                'question_type': 'multiple_choice',
                'options': options,
                'correct_answer': s,
                'explanation': "The correct option reproduces a statement from the course.",
                'points': 1,
                'difficulty': difficulty,
                'order': order_counter,
                'ai_generated': True,
                'confidence_score': 0.85,
            })
            order_counter += 1
            if len(questions) >= num_questions:
                return questions[:num_questions]
        # 3) Open-ended referencing a snippet
        idx = 0
        while len(questions) < num_questions and sentences:
            snippet = sentences[idx % len(sentences)][:140]
            questions.append({
                'id': f"open_{order_counter}",
                'question_text': f"Explain the meaning of this course snippet and give an example: '{snippet}'",
                'question_type': 'open_ended',
                'correct_answer': "Learner should interpret the snippet using concepts present in the content and give a relevant example.",
                'explanation': "Open-ended—graded for alignment with the quoted snippet.",
                'points': 2,
                'difficulty': difficulty,
                'order': order_counter,
                'ai_generated': True,
                'confidence_score': 0.8,
            })
            order_counter += 1
            idx += 1
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

    def _extract_keywords(self, content: str, limit: int = 12) -> List[str]:
        import re
        from collections import Counter
        if not content:
            return []
        text = re.sub(r"[^A-Za-z0-9\-\s]", " ", content)
        words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.lower())
        stop = {
            'the','and','for','with','that','this','from','your','you','are','was','were','will','shall','into','onto','about','above','below','under','over',
            'a','an','of','to','in','on','at','by','it','as','be','is','am','or','if','but','not','no','yes','do','does','did','can','could','should','would',
            'have','has','had','we','they','them','their','our','us','i','me','my','mine','yours','his','her','its','also','more','most','least','than','such',
            'course','content','material','section','chapter','topic','introduction','overview','based','according','using','use','title','context','important','question'
        }
        filtered = [w for w in words if w not in stop and len(w) >= 4]
        if not filtered:
            return []
        counts = Counter(filtered)
        return [w for w, _ in counts.most_common(limit)]

    def _enforce_content_keywords(self, course_title: str, content: str, questions: List[Dict]) -> List[Dict]:
        """Ensure each question references course-specific keywords; adjust if missing."""
        keywords = self._extract_keywords(course_title + "\n" + content, limit=20)
        if not keywords:
            return questions
        patched = []
        for idx, q in enumerate(questions):
            qt = q.get('question_text', '') or ''
            expl = q.get('explanation', '') or ''
            # Ensure at least one keyword exists in question and explanation
            if not any(k.lower() in qt.lower() for k in keywords):
                qt = f"In the context of {course_title}, {qt}"
                # append one keyword to force specificity
                qt = qt.rstrip('.') + f" ({keywords[idx % len(keywords)]})."
            if not any(k.lower() in expl.lower() for k in keywords):
                expl = (expl + f" (Reference: {course_title}, keyword: {keywords[(idx+1) % len(keywords)]}).").strip()
            q['question_text'] = qt
            q['explanation'] = expl
            patched.append(q)
        return patched


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

