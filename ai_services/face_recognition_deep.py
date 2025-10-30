"""
Deep Learning Face Recognition Service using VGG16
Provides advanced face recognition with trained CNN model
"""
import os
import base64
import io
import pickle
import numpy as np
import cv2
from typing import List, Tuple, Optional, Any, Dict
from pathlib import Path


class DeepFaceRecognitionService:
    """
    Advanced face recognition using VGG16-based deep learning model
    """
    
    def __init__(self, model_dir=None):
        """
        Initialize the deep learning face recognition service
        
        Args:
            model_dir: Directory containing the trained model and encoders
        """
        self.model = None
        self.label_encoder = None
        self.face_cascade = None
        self.model_loaded = False
        
        # Set model directory
        if model_dir is None:
            base_dir = Path(__file__).resolve().parent.parent
            self.model_dir = base_dir / 'face-recognition-model'
        else:
            self.model_dir = Path(model_dir)
        
        self.model_path = self.model_dir / 'face_recognition_model.h5'
        self.encoder_path = self.model_dir / 'label_encoder.pkl'
        self.cascade_path = self.model_dir / 'haarcascade_frontalface_default.xml'
        
        # Lazy loading
        self._lazy_load()
    
    def _lazy_load(self):
        """Lazy load TensorFlow and the model"""
        if self.model_loaded:
            return True
        
        try:
            # Import TensorFlow
            import tensorflow as tf
            from tensorflow.keras.models import load_model
            
            # Load the trained model
            if self.model_path.exists():
                self.model = load_model(str(self.model_path))
                print(f"✓ Loaded VGG16 face recognition model from {self.model_path}")
            else:
                print(f"✗ Model not found at {self.model_path}")
                return False
            
            # Load label encoder
            if self.encoder_path.exists():
                with open(self.encoder_path, 'rb') as f:
                    self.label_encoder = pickle.load(f)
                print(f"✓ Loaded label encoder with {len(self.label_encoder.classes_)} classes")
            else:
                print(f"✗ Label encoder not found at {self.encoder_path}")
                return False
            
            # Load Haar Cascade for face detection
            if self.cascade_path.exists():
                self.face_cascade = cv2.CascadeClassifier(str(self.cascade_path))
            else:
                # Fallback to OpenCV's default cascade
                self.face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
            
            self.model_loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading deep learning model: {e}")
            return False
    
    def _load_image(self, image_data: Any) -> Optional[np.ndarray]:
        """
        Load image from various sources
        
        Args:
            image_data: Can be file path, base64 string, or file-like object
            
        Returns:
            numpy array of the image in BGR format (OpenCV format)
        """
        try:
            from PIL import Image
            
            # numpy array
            if isinstance(image_data, np.ndarray):
                return image_data
            
            # File path or base64 string
            if isinstance(image_data, str):
                # Base64 data URI
                if image_data.startswith('data:image'):
                    b64 = image_data.split(',')[1]
                    img_bytes = base64.b64decode(b64)
                    if len(img_bytes) == 0:
                        print("Error: Empty base64 image data")
                        return None
                    im = Image.open(io.BytesIO(img_bytes)).convert('RGB')
                    # Convert RGB to BGR for OpenCV
                    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
                # File path
                elif os.path.exists(image_data):
                    img = cv2.imread(image_data)
                    if img is None:
                        print(f"Error: Failed to read image from {image_data}")
                    return img
            
            # File-like object (Django UploadedFile, etc.)
            if hasattr(image_data, 'read'):
                # Reset file pointer to beginning if possible
                if hasattr(image_data, 'seek'):
                    image_data.seek(0)
                
                content = image_data.read()
                
                # Validate we have data
                if not content or len(content) == 0:
                    print("Error: Empty image file")
                    return None
                
                # Try with PIL
                try:
                    im = Image.open(io.BytesIO(content)).convert('RGB')
                    img = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
                    print("✓ Loaded image successfully")
                    return img
                except Exception as e:
                    print(f"Error: PIL image loading failed: {e}")
                    # Fallback to OpenCV
                    if hasattr(image_data, 'seek'):
                        image_data.seek(0)
                    nparr = np.frombuffer(content, np.uint8)
                    if len(nparr) == 0:
                        print("Error: Failed to create numpy array from image bytes")
                        return None
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is None:
                        print("Error: OpenCV fallback failed to decode image")
                    return img
                    
        except Exception as e:
            print(f"Error loading image: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        print(f"Error: Unsupported image data type: {type(image_data)}")
        return None
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in an image
        
        Args:
            image: BGR image (OpenCV format)
            
        Returns:
            List of (x, y, w, h) tuples for detected faces
        """
        if not self._lazy_load():
            return []
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            return faces
        except Exception as e:
            print(f"Error detecting faces: {e}")
            return []
    
    def preprocess_face(self, face_img: np.ndarray) -> np.ndarray:
        """
        Preprocess face image for VGG16 model
        
        Args:
            face_img: Cropped face image in BGR format
            
        Returns:
            Preprocessed image ready for model prediction
        """
        # Resize to VGG16 input size
        face_resized = cv2.resize(face_img, (224, 224))
        
        # Convert BGR to RGB
        face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
        
        # Normalize pixel values (0-255 -> 0-1)
        face_normalized = face_rgb.astype('float32') / 255.0
        
        # Add batch dimension
        face_batch = np.expand_dims(face_normalized, axis=0)
        
        return face_batch
    
    def register_face(self, user, image_data: Any) -> Tuple[bool, Any]:
        """
        Register a user's face
        
        Args:
            user: User object
            image_data: Image containing the user's face
            
        Returns:
            Tuple of (success, result)
            - If success: result is dict with user_id and encoding info
            - If failure: result is error message string
        """
        if not self._lazy_load():
            return False, 'Deep learning model not loaded'
        
        try:
            image = self._load_image(image_data)
            if image is None:
                return False, 'Could not load image'
            
            # Detect faces
            faces = self.detect_faces(image)
            if len(faces) == 0:
                return False, 'No face detected in image'
            
            if len(faces) > 1:
                return False, 'Multiple faces detected. Please ensure only one face is visible'
            
            # Get the face region
            x, y, w, h = faces[0]
            face_img = image[y:y+h, x:x+w]
            
            # Preprocess for prediction
            face_preprocessed = self.preprocess_face(face_img)
            
            # Get prediction from model to verify it's recognizable
            prediction = self.model.predict(face_preprocessed, verbose=0)
            confidence = float(np.max(prediction))
            
            # Store encoding information
            encoding_data = {
                'model': 'vgg16_deep',
                'user_id': user.id,
                'username': user.username,
                'encoding': face_preprocessed.flatten().tolist(),  # Flattened features
                'confidence': confidence,
                'face_region': [int(x), int(y), int(w), int(h)]
            }
            
            return True, encoding_data
            
        except Exception as e:
            print(f"Error registering face: {e}")
            return False, str(e)
    
    def recognize_face(self, image_data: Any, stored_encodings: List[Tuple[int, Any]]) -> Tuple[Optional[int], float]:
        """
        Recognize a face from stored encodings
        
        Args:
            image_data: Image containing a face to recognize
            stored_encodings: List of (user_id, encoding_dict) tuples
            
        Returns:
            Tuple of (user_id, confidence)
            - user_id is None if no match found
            - confidence is between 0 and 1
        """
        if not self._lazy_load():
            print("  VGG16: Model not loaded")
            return None, 0.0
        
        try:
            image = self._load_image(image_data)
            if image is None:
                print("  VGG16: Failed to load image")
                return None, 0.0
            
            print(f"  VGG16: Image loaded, shape: {image.shape}")
            
            # Detect faces
            faces = self.detect_faces(image)
            if len(faces) == 0:
                print(f"  VGG16: No faces detected in image")
                return None, 0.0
            
            print(f"  VGG16: Found {len(faces)} face(s)")
            
            # Use the largest face (assuming it's the main subject)
            faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            x, y, w, h = faces_sorted[0]
            face_img = image[y:y+h, x:x+w]
            
            # Preprocess for prediction
            face_preprocessed = self.preprocess_face(face_img)
            
            # Get prediction
            print(f"  VGG16: Running model prediction...")
            prediction = self.model.predict(face_preprocessed, verbose=0)[0]
            predicted_class = np.argmax(prediction)
            confidence = float(prediction[predicted_class])
            
            print(f"  VGG16: Predicted class: {predicted_class}, confidence: {confidence:.4f}")
            
            # Get the predicted label
            if predicted_class < len(self.label_encoder.classes_):
                predicted_name = self.label_encoder.inverse_transform([predicted_class])[0]
                print(f"  VGG16: Predicted name: '{predicted_name}'")
                
                # Match with stored encodings
                print(f"  VGG16: Comparing with {len(stored_encodings)} stored encoding(s)...")
                for user_id, stored_data in stored_encodings:
                    if isinstance(stored_data, dict):
                        stored_username = stored_data.get('username', '')
                        print(f"  VGG16: Checking user {user_id}, stored username: '{stored_username}'")
                        if stored_username == predicted_name:
                            # Apply confidence threshold
                            if confidence >= 0.5:  # 50% confidence threshold
                                print(f"  VGG16: Match ACCEPTED - User {user_id} (confidence {confidence:.2f} >= 0.5)")
                                return user_id, confidence
                            else:
                                print(f"  VGG16: Match REJECTED - Confidence {confidence:.2f} < 0.5")
                print(f"  VGG16: No matching username found for '{predicted_name}'")
                # Heuristic: if only one encoding exists and confidence is high, assume match
                if len(stored_encodings) == 1 and confidence >= 0.8:
                    sole_user_id, _ = stored_encodings[0]
                    print(f"  VGG16: Single encoding present and high confidence; accepting user {sole_user_id}")
                    return sole_user_id, confidence
            else:
                print(f"  VGG16: Predicted class {predicted_class} out of range (max: {len(self.label_encoder.classes_)-1})")
                    
            return None, confidence
            
        except Exception as e:
            print(f"  VGG16: Error recognizing face: {e}")
            import traceback
            traceback.print_exc()
            return None, 0.0
    
    def recognize_face_realtime(self, frame: np.ndarray) -> Dict:
        """
        Real-time face recognition for camera frames
        
        Args:
            frame: Camera frame in BGR format
            
        Returns:
            Dict with recognition results and annotated frame
        """
        if not self._lazy_load():
            return {
                'success': False,
                'frame': frame,
                'faces': [],
                'error': 'Model not loaded'
            }
        
        try:
            # Detect faces
            faces = self.detect_faces(frame)
            
            results = []
            annotated_frame = frame.copy()
            
            for (x, y, w, h) in faces:
                face_img = frame[y:y+h, x:x+w]
                
                # Preprocess and predict
                face_preprocessed = self.preprocess_face(face_img)
                prediction = self.model.predict(face_preprocessed, verbose=0)[0]
                
                predicted_class = np.argmax(prediction)
                confidence = float(prediction[predicted_class])
                
                # Get label
                if predicted_class < len(self.label_encoder.classes_):
                    label = self.label_encoder.inverse_transform([predicted_class])[0]
                else:
                    label = "Unknown"
                
                # Draw rectangle and label
                color = (0, 255, 0) if confidence > 0.5 else (0, 165, 255)
                cv2.rectangle(annotated_frame, (x, y), (x+w, y+h), color, 2)
                
                # Draw label with background
                label_text = f"{label} ({confidence*100:.1f}%)"
                (text_width, text_height), _ = cv2.getTextSize(
                    label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                )
                cv2.rectangle(
                    annotated_frame,
                    (x, y - text_height - 10),
                    (x + text_width, y),
                    color,
                    -1
                )
                cv2.putText(
                    annotated_frame,
                    label_text,
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )
                
                results.append({
                    'label': label,
                    'confidence': confidence,
                    'bbox': [int(x), int(y), int(w), int(h)]
                })
            
            return {
                'success': True,
                'frame': annotated_frame,
                'faces': results,
                'face_count': len(faces)
            }
            
        except Exception as e:
            print(f"Error in real-time recognition: {e}")
            return {
                'success': False,
                'frame': frame,
                'faces': [],
                'error': str(e)
            }


# Global instance
deep_face_service = DeepFaceRecognitionService()
