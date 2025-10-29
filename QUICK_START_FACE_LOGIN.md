# Quick Start: Face Recognition Login

## ✅ Complete Setup Instructions

### Step 1: Restart the Server

Make sure your development server is running with the latest changes:

```bash
.\venv\Scripts\python manage.py runserver
```

### Step 2: Create a User Account

1. Go to: `http://127.0.0.1:8000/signup/`
2. Create a new account with username and password
3. You'll be automatically logged in after signup

### Step 3: Register Your Face

1. Go to your profile: `http://127.0.0.1:8000/profile/`
2. Scroll down to the "AI Face Recognition Login" section
3. Click **"Register Face"** button
4. Allow camera permissions when prompted
5. Position your face in the camera view
6. Click **"Capture"** to register your face
7. Wait for confirmation message

### Step 4: Test Face Login

1. **Logout** from your account
2. Go to the sign-in page: `http://127.0.0.1:8000/signin/`
3. Click the **"Face Recognition Login"** button
4. You'll be redirected to: `http://127.0.0.1:8000/face-login/`
5. Allow camera permissions
6. Position your face in the camera
7. Click **"Login with Face"**
8. You'll be automatically logged in!

## 📁 How It Works

### User Flow:

```
Sign Up → Login → Profile → Register Face → Logout → Face Login
```

### Technical Flow:

1. **Face Registration**:
   - Captures your face via webcam
   - Extracts facial features using OpenCV
   - Stores face encoding in database (JSON)

2. **Face Login**:
   - Captures your current face
   - Compares with all registered faces
   - Matches using cosine similarity
   - Logs you in if confidence > 60%

## 🎯 Key Pages

| Page | URL | Description |
|------|-----|-------------|
| Sign In | `/signin/` | Traditional login + Face login button |
| Face Login | `/face-login/` | AI-powered face recognition login |
| Profile | `/profile/` | Register or update your face |
| Sign Up | `/signup/` | Create new account |

## 🔧 Troubleshooting

### Camera Not Working
- **Chrome/Edge**: Allow camera permissions in browser settings
- **HTTPS Required**: Some browsers require HTTPS (use localhost for development)
- **Already in Use**: Close other apps using the camera

### Face Not Detected
- **Lighting**: Ensure good lighting conditions
- **Distance**: Stay 30-60cm from camera
- **Angle**: Face the camera directly
- **Obstructions**: Remove glasses/masks if needed

### Face Not Recognized
- **First time**: You must register your face first in Profile
- **Low confidence**: Try re-registering in better lighting
- **Different conditions**: Face encodings are affected by lighting/angle

### Browser Permissions
If camera is blocked:
1. Click the lock icon in address bar
2. Set Camera to "Allow"
3. Refresh the page

## 🧪 Testing Tips

### Best Practices:
1. **Register in good lighting** - Natural light works best
2. **Face the camera directly** - Avoid extreme angles
3. **Stay still** - Hold steady during capture
4. **Neutral expression** - Works best with normal expression

### Re-registration:
- You can re-register your face anytime from profile
- Useful if conditions change (new glasses, beard, etc.)
- Previous registration is overwritten

## 🔐 Security Notes

- Face encodings are stored securely in the database
- No actual images are stored, only feature vectors
- Confidence threshold is set to 60% (adjustable)
- CSRF protection is enabled

## 📊 Technical Stack

- **Face Detection**: OpenCV Haar Cascades
- **Face Encoding**: Custom feature extraction
- **Face Matching**: Cosine similarity
- **Backend**: Django REST Framework
- **Frontend**: Vanilla JavaScript + WebRTC

## 🚀 Next Steps

Want to enhance the system?
1. Add liveness detection (anti-spoofing)
2. Implement multi-angle registration
3. Add facial expression analysis
4. Upgrade to deep learning models (FaceNet, ArcFace)
5. Integrate cloud services (AWS Rekognition, Azure Face API)

## 📞 Support

For issues, check:
- Browser console (F12) for JavaScript errors
- Django server logs for backend errors
- Camera permissions in browser settings

Enjoy your AI-powered face recognition login! 🎉
