"""
Face Recognition Service for AI-powered login
Implements face detection, encoding, and recognition for user authentication
"""
import os
import cv2
import numpy as np
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import base64
from io import BytesIO
from PIL import Image


class FaceRecognitionService:
    """
    AI-powered face recognition service for user authentication
    Matches the FaceRecognitionService class in the UML diagram
    """
    
    def __init__(self):
        """Initialize face recognition service with OpenCV"""
        self.face_cascade = None
        self.recognition_threshold = 0.6  # Similarity threshold for face matching
        self._load_models()
    
    def _load_models(self):
        """Load OpenCV face detection models"""
        try:
            # Load Haar Cascade for face detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                print("Warning: Failed to load face cascade classifier")
        except Exception as e:
            print(f"Error loading face detection models: {e}")
    
    def analyze_face(self, video_stream_or_image):
        """
        Analyze face from video stream or image (from UML diagram)
        
        Args:
            video_stream_or_image: Image data (file path, numpy array, or file object)
        
        Returns:
            bool: True if face detected and analyzed successfully
        """
        try:
            face_encoding = self._extract_face_encoding(video_stream_or_image)
            return face_encoding is not None
        except Exception as e:
            print(f"Error analyzing face: {e}")
            return False
    
    def detect_engagement(self, image_data):
        """
        Detect user engagement from facial expressions (from UML diagram)
        
        Args:
            image_data: Image containing face
        
        Returns:
            str: Engagement level description
        """
        try:
            # Load image
            img = self._load_image(image_data)
            if img is None:
                return "No face detected"
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                return "No engagement - face not visible"
            elif len(faces) == 1:
                return "Focused - single face detected"
            else:
                return "Multiple faces detected - distracted"
                
        except Exception as e:
            print(f"Error detecting engagement: {e}")
            return "Error detecting engagement"
    
    def register_face(self, user, image_data):
        """
        Register user's face for future recognition
        
        Args:
            user: Django User object
            image_data: Image containing user's face
        
        Returns:
            tuple: (success, face_encoding or error_message)
        """
        try:
            # Extract face encoding
            face_encoding = self._extract_face_encoding(image_data)
            
            if face_encoding is None:
                return False, "No face detected in image"
            
            # Convert encoding to list for JSON storage
            encoding_list = face_encoding.flatten().tolist()
            
            return True, encoding_list
            
        except Exception as e:
            print(f"Error registering face: {e}")
            return False, str(e)
    
    def recognize_face(self, image_data, stored_encodings):
        """
        Recognize face by comparing with stored encodings
        
        Args:
            image_data: Image containing face to recognize
            stored_encodings: List of tuples (user_id, encoding)
        
        Returns:
            tuple: (matched_user_id, confidence) or (None, 0)
        """
        try:
            # Extract face encoding from input image
            current_encoding = self._extract_face_encoding(image_data)
            
            if current_encoding is None:
                return None, 0
            
            best_match = None
            best_similarity = 0
            
            # Compare with all stored encodings
            for user_id, stored_encoding in stored_encodings:
                similarity = self._compare_faces(current_encoding, np.array(stored_encoding))
                
                if similarity > best_similarity and similarity >= (1 - self.recognition_threshold):
                    best_similarity = similarity
                    best_match = user_id
            
            return best_match, best_similarity
            
        except Exception as e:
            print(f"Error recognizing face: {e}")
            return None, 0
    
    def _load_image(self, image_data):
        """
        Load image from various input formats
        
        Args:
            image_data: File path, numpy array, PIL Image, or file object
        
        Returns:
            numpy.ndarray: OpenCV image or None
        """
        try:
            # If it's a numpy array
            if isinstance(image_data, np.ndarray):
                return image_data
            
            # If it's a file path string
            if isinstance(image_data, str):
                # Check if it's base64 encoded
                if image_data.startswith('data:image'):
                    # Extract base64 data
                    base64_data = image_data.split(',')[1]
                    image_bytes = base64.b64decode(base64_data)
                    if len(image_bytes) == 0:
                        print("Error: Empty base64 image data")
                        return None
                    nparr = np.frombuffer(image_bytes, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is None:
                        print("Error: Failed to decode base64 image")
                    return img
                # Regular file path
                elif os.path.exists(image_data):
                    img = cv2.imread(image_data)
                    if img is None:
                        print(f"Error: Failed to read image from {image_data}")
                    return img
            
            # If it's a file object (Django UploadedFile, etc.)
            elif hasattr(image_data, 'read'):
                # Reset file pointer to beginning if possible
                if hasattr(image_data, 'seek'):
                    image_data.seek(0)
                
                image_bytes = image_data.read()
                
                # Validate we have data
                if not image_bytes or len(image_bytes) == 0:
                    print("Error: Empty image file")
                    return None
                
                # Try decoding with OpenCV
                nparr = np.frombuffer(image_bytes, np.uint8)
                if len(nparr) == 0:
                    print("Error: Failed to create numpy array from image bytes")
                    return None
                
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is None:
                    # Fallback: Try with PIL then convert to OpenCV
                    try:
                        if hasattr(image_data, 'seek'):
                            image_data.seek(0)
                        pil_img = Image.open(BytesIO(image_bytes)).convert('RGB')
                        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                        print("✓ Loaded image using PIL fallback")
                        return img
                    except Exception as e:
                        print(f"Error: PIL fallback failed: {e}")
                        return None
                
                return img
            
            print(f"Error: Unsupported image data type: {type(image_data)}")
            return None
            
        except Exception as e:
            print(f"Error loading image: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_face_encoding(self, image_data):
        """
        Extract face encoding (feature vector) from image
        
        Args:
            image_data: Image containing face
        
        Returns:
            numpy.ndarray: Face encoding vector or None
        """
        try:
            # Load image
            img = self._load_image(image_data)
            if img is None:
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                return None
            
            # Get the largest face
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # Resize to standard size
            face_roi = cv2.resize(face_roi, (128, 128))
            
            # Create simple encoding using histogram features
            # In production, use a proper face recognition model
            encoding = self._create_face_encoding(face_roi)
            
            return encoding
            
        except Exception as e:
            print(f"Error extracting face encoding: {e}")
            return None
    
    def _create_face_encoding(self, face_image):
        """
        Create a feature vector from face image
        This is a simplified version - in production use proper face recognition models
        
        Args:
            face_image: Grayscale face image
        
        Returns:
            numpy.ndarray: Feature vector
        """
        try:
            # Flatten image and normalize
            encoding = face_image.flatten().astype(np.float32)
            encoding = encoding / np.linalg.norm(encoding)  # Normalize
            
            return encoding
            
        except Exception as e:
            print(f"Error creating face encoding: {e}")
            return None
    
    def _compare_faces(self, encoding1, encoding2):
        """
        Compare two face encodings and return similarity score
        
        Args:
            encoding1: First face encoding
            encoding2: Second face encoding
        
        Returns:
            float: Similarity score (0-1, higher is more similar)
        """
        try:
            # Ensure both encodings have the same shape
            if encoding1.shape != encoding2.shape:
                return 0
            
            # Calculate cosine similarity
            dot_product = np.dot(encoding1.flatten(), encoding2.flatten())
            norm1 = np.linalg.norm(encoding1)
            norm2 = np.linalg.norm(encoding2)
            
            similarity = dot_product / (norm1 * norm2)
            
            # Convert to 0-1 range
            similarity = (similarity + 1) / 2
            
            return similarity
            
        except Exception as e:
            print(f"Error comparing faces: {e}")
            return 0


# Global face recognition service instance
face_recognition_service = FaceRecognitionService()
