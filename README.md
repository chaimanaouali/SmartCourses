# Educational Hub - AI-Powered Learning Platform

A comprehensive multimodal educational platform built with Django 4.2 and integrated with the Argon Dashboard template. This platform provides AI-powered features including voice questions, automatic quiz generation, facial recognition authentication, and real-time engagement tracking.

## 🚀 Features

### Core Educational Features
- **Course Management**: Upload and manage educational content (audio, PDF)
- **AI-Powered Transcription**: Automatic speech-to-text using Whisper
- **Smart Quiz Generation**: AI-generated quizzes from course content
- **Voice Questions**: Students can ask questions using voice input
- **Real-time AI Responses**: Get instant AI-generated answers and explanations

### AI Integrations
- **Whisper Integration**: Speech-to-text transcription for audio content
- **Gemini AI**: Text generation for responses and summaries
- **Hugging Face**: Image generation for educational illustrations
- **Face Recognition**: User authentication and engagement detection

### Advanced Features
- **WebSocket Support**: Real-time interactions and live updates
- **Engagement Tracking**: Monitor student attention and participation
- **Analytics Dashboard**: Track learning progress and quiz performance
- **Responsive Design**: Beautiful UI using Argon Dashboard template

## 🛠️ Technology Stack

- **Backend**: Django 4.2, Django REST Framework
- **Frontend**: Bootstrap 5, Argon Dashboard Template
- **Real-time**: Django Channels, WebSockets
- **AI Services**: 
  - Whisper (Speech-to-Text)
  - Google Gemini (Text Generation)
  - Hugging Face (Image Generation)
  - OpenCV + Face Recognition
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Task Queue**: Celery with Redis
- **Authentication**: Django Auth + Face Recognition

## 📋 Prerequisites

- Python 3.14+
- pip (Python package manager)
- Redis (for Celery and Channels)
- Git

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd argon-dashboard-master
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Copy the example environment file and configure your API keys:
```bash
cp env.example .env
```

Edit `.env` file with your API keys:
```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# AI API Keys
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Database (Optional - defaults to SQLite)
# DATABASE_URL=postgresql://user:password@localhost:5432/educational_hub

# Redis (for Celery and Channels)
REDIS_URL=redis://localhost:6379
```

### 5. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6. Collect Static Files
```bash
python manage.py collectstatic
```

## 🎯 Usage

### Starting the Development Server
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

### Starting Background Services (Optional)
For full functionality, start Redis and Celery:

```bash
# Start Redis (if not running as service)
redis-server

# Start Celery worker (in another terminal)
celery -A educational_hub worker --loglevel=info

# Start Celery beat for scheduled tasks (in another terminal)
celery -A educational_hub beat --loglevel=info
```

## 📱 Key Features Walkthrough

### 1. Course Upload
- Navigate to "Upload Course" in the sidebar
- Fill in course details (title, description)
- Upload audio files for AI transcription
- Upload PDF files for content analysis
- AI automatically processes and generates summaries

### 2. Voice Questions
- Use the voice recording interface on the dashboard
- Click "Record Question" to start recording
- Ask questions about course content
- Get AI-generated responses with explanations
- View generated illustrations (when AI services are configured)

### 3. Quiz Generation
- Courses automatically generate quizzes from content
- Take quizzes with real-time feedback
- View detailed analytics and performance metrics
- Track learning progress over time

### 4. Face Recognition Login
- Upload a profile photo during registration
- Use face recognition for quick login
- System detects engagement during learning sessions

## 🔧 Configuration

### AI Services Setup

#### Whisper (Speech-to-Text)
```bash
pip install openai-whisper
```

#### Gemini AI (Text Generation)
1. Get API key from Google AI Studio
2. Add to `.env` file: `GEMINI_API_KEY=your_key_here`

#### Hugging Face (Image Generation)
1. Get API token from Hugging Face
2. Add to `.env` file: `HUGGINGFACE_API_KEY=your_token_here`

#### Face Recognition
```bash
pip install face-recognition opencv-python
```

### Database Configuration
For production, configure PostgreSQL:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'educational_hub',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 📊 API Endpoints

### Course Management
- `GET /api/user-courses/` - Get user's enrolled courses
- `POST /api/audio-question/` - Upload voice question
- `GET /api/audio-question/{id}/status/` - Get question processing status

### Quiz System
- `GET /quiz/` - List all quizzes
- `GET /quiz/{id}/` - Quiz details
- `POST /quiz/{id}/attempt/` - Start quiz attempt

### AI Services
- `POST /ai/transcribe/` - Transcribe audio
- `POST /ai/generate-text/` - Generate text response
- `POST /ai/generate-image/` - Generate image
- `POST /ai/face-recognition/` - Face recognition
- `POST /ai/engagement-detection/` - Detect engagement

### WebSocket Endpoints
- `ws/course/{course_id}/` - Course interaction WebSocket
- `ws/quiz/{quiz_id}/` - Quiz interaction WebSocket

## 🎨 Customization

### Styling
The application uses the Argon Dashboard template. Customize by:
1. Modifying CSS files in `assets/css/`
2. Updating templates in `templates/pages/`
3. Adding custom JavaScript in template files

### Adding New AI Services
1. Create service class in `ai_services/services.py`
2. Add API endpoint in `ai_services/views.py`
3. Update frontend to use new service

## 🚀 Deployment

### Production Checklist
1. Set `DEBUG=False` in settings
2. Configure production database
3. Set up Redis server
4. Configure Celery workers
5. Set up static file serving
6. Configure HTTPS
7. Set up monitoring and logging

### Docker Deployment (Optional)
```dockerfile
FROM python:3.14
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the example configurations

## 🔮 Future Enhancements

- [ ] Mobile app integration
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Integration with LMS platforms
- [ ] Advanced AI tutoring features
- [ ] Collaborative learning tools
- [ ] Gamification elements

---

**Built with ❤️ using Django 4.2 and Argon Dashboard**