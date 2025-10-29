# Face Recognition Login - AI Integration Guide

## Overview
This project implements AI-powered face recognition login functionality based on the class diagram requirements. The system allows users to authenticate using facial recognition instead of traditional passwords.

## Architecture

### Class Diagram Implementation

#### 1. **User Entity**
- **Location**: `course_app/models.py` - `User` (Django default) + `UserProfile`
- **Key Fields**:
  - `id`, `name`, `email`, `password` (Django User)
  - `face_encoding` (UserProfile) - Stores facial features as JSON

#### 2. **FaceRecognitionService**
- **Location**: `ai_services/face_recognition_service.py`
- **Methods Implemented**:
  - `analyzeFace(videoStream)` → `analyze_face(video_stream_or_image)`: Detects and analyzes faces
  - `detectEngagement()` → `detect_engagement(image_data)`: Monitors user engagement during learning
  - `register_face(user, image_data)`: Registers user's face for authentication
  - `recognize_face(image_data, stored_encodings)`: Matches face against database

## Features

### 1. Face Registration
**Endpoint**: `POST /api/face-register/`
```javascript
// JavaScript example
const formData = new FormData();
formData.append('image', imageBlob);

fetch('/api/face-register/', {
  method: 'POST',
  headers: {'X-CSRFToken': csrftoken},
  body: formData
});
```

**How it works**:
1. User captures their face image via webcam
2. System extracts facial features (face encoding)
3. Encoding is stored in `UserProfile.face_encoding` as JSON
4. Can be accessed from profile page after login

### 2. Face Recognition Login
**Endpoint**: `POST /api/face-login/`
**Page**: `/face-login/` 

**How it works**:
1. User visits `/face-login/` page
2. Webcam activates automatically
3. User positions face in camera view
4. Clicks "Login with Face" button
5. System:
   - Captures image
   - Extracts facial features
   - Compares with all registered faces
   - Returns match with confidence score
   - Logs user in if match found

**Confidence Threshold**: 0.6 (adjustable in `FaceRecognitionService`)

### 3. Engagement Detection
Monitors user attention during learning sessions:
- **Focused**: Single face detected, high engagement
- **Distracted**: Multiple faces or no face
- **Engagement Score**: 0.0 to 1.0

## Technology Stack

### AI/ML Components
- **OpenCV** (4.8.0.76): Face detection using Haar Cascades
- **NumPy** (2.3.4): Face encoding mathematical operations
- **Face Detection Model**: Haar Cascade Classifier (built into OpenCV)

### Why OpenCV Instead of face_recognition library?
- ✅ Easier installation (no dlib compilation required)
- ✅ Cross-platform compatibility
- ✅ Sufficient for educational purposes
- ✅ Can be upgraded to deep learning models later

## Setup Instructions

### 1. Install Dependencies
```bash
.\venv\Scripts\pip install -r requirements-minimal.txt
```

### 2. Run Migrations
```bash
.\venv\Scripts\python manage.py migrate
```

### 3. Create Superuser
```bash
.\venv\Scripts\python manage.py createsuperuser
```

### 4. Start Development Server
```bash
.\venv\Scripts\python manage.py runserver
```

### 5. Access Face Login
Navigate to: `http://127.0.0.1:8000/face-login/`

## Usage Workflow

### For New Users:
1. Sign up at `/signup/`
2. Log in with password at `/signin/`
3. Go to profile page at `/profile/`
4. Register face for future logins
5. Next time, use `/face-login/` for passwordless login

### For Existing Users (with registered face):
1. Go directly to `/face-login/`
2. Allow camera permissions
3. Position face in camera
4. Click "Login with Face"
5. Automatic login if face matches

## API Endpoints

### Face Recognition APIs

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/face-login/` | POST | No | Login using face recognition |
| `/api/face-register/` | POST | Yes | Register user's face |
| `/face-login/` | GET | No | Face login page (UI) |

### Request/Response Examples

#### Face Login
**Request**:
```javascript
POST /api/face-login/
Content-Type: multipart/form-data

{
  "image": <image file>
}
```

**Success Response**:
```json
{
  "success": true,
  "user": "john_doe",
  "email": "john@example.com",
  "confidence": 0.92,
  "message": "Face recognition login successful"
}
```

**Error Response**:
```json
{
  "error": "Face not recognized",
  "message": "No registered faces found"
}
```

## Security Considerations

### Current Implementation:
1. **Face encodings stored as JSON** in database
2. **HTTPS recommended** for production
3. **CSRF protection** enabled
4. **Confidence threshold** prevents false positives

### Production Recommendations:
1. **Encrypt face encodings** at rest
2. **Rate limiting** on login attempts
3. **Liveness detection** to prevent photo spoofing
4. **Multi-factor authentication** option
5. **Audit logging** for face login attempts

## Upgrading to Production-Ready Solution

### Option 1: Use Face Recognition Library
```bash
pip install face_recognition dlib
```
Replace `FaceRecognitionService` methods with `face_recognition` library calls.

### Option 2: Use Deep Learning Models
- **FaceNet**: More accurate face embeddings
- **ArcFace**: State-of-the-art face recognition
- **MediaPipe**: Google's ML solution

### Option 3: Use Cloud Services
- **AWS Rekognition**
- **Azure Face API**
- **Google Cloud Vision API**

## Troubleshooting

### Camera Not Working
- **Check browser permissions**: Allow camera access
- **HTTPS required**: Some browsers block camera on HTTP
- **Try different browser**: Chrome/Firefox recommended

### Face Not Detected
- **Lighting**: Ensure good lighting
- **Distance**: Position face 30-60cm from camera
- **Angle**: Face camera directly
- **Remove obstructions**: Glasses/masks may interfere

### Low Recognition Accuracy
- **Adjust threshold**: Lower `recognition_threshold` in `FaceRecognitionService`
- **Re-register face**: Capture in better conditions
- **Multiple registrations**: Register from different angles

## File Structure

```
SmartCourses/
├── ai_services/
│   ├── face_recognition_service.py  # Core face recognition logic
│   └── services.py                  # AI service manager (integration)
├── course_app/
│   ├── models.py                    # User & UserProfile models
│   ├── views.py                     # Login/registration views
│   └── urls.py                      # URL routing
├── templates/pages/
│   └── face-login.html              # Face login UI
└── docs/
    └── FACE_RECOGNITION_GUIDE.md    # This file
```

## Future Enhancements

1. **Liveness Detection**: Prevent photo attacks
2. **Multi-angle Registration**: Register from multiple angles
3. **Facial Expression Analysis**: Emotion detection during learning
4. **Age/Gender Detection**: For demographic analytics
5. **Attendance Tracking**: Automatic attendance via face recognition

## License & Credits
- OpenCV: BSD License
- Django: BSD License
- This implementation: Part of Educational Hub project

## Support
For issues or questions, please refer to the main project README or create an issue in the repository.
