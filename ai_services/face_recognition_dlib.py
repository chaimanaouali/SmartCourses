"""
Dlib-based face recognition service using the 'face_recognition' library.
Provides robust, pre-trained deep learning embeddings (128-d) for recognition.
"""
import os
import base64
from typing import List, Tuple, Optional, Any

import numpy as np


class DlibFaceRecognitionService:
    def __init__(self):
        self._fr = None  # lazy import face_recognition

    def _lazy_import(self):
        if self._fr is None:
            import importlib
            self._fr = importlib.import_module('face_recognition')

    def _load_image(self, image_data: Any) -> Optional[np.ndarray]:
        try:
            self._lazy_import()
            fr = self._fr
            import io
            from PIL import Image

            # File path
            if isinstance(image_data, str) and os.path.exists(image_data):
                return fr.load_image_file(image_data)

            # Base64 data URI
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                b64 = image_data.split(',')[1]
                img_bytes = base64.b64decode(b64)
                if len(img_bytes) == 0:
                    print("Dlib: Empty base64 image data")
                    return None
                im = Image.open(io.BytesIO(img_bytes)).convert('RGB')
                return np.array(im, dtype=np.uint8)

            # File-like (Django UploadedFile, etc.)
            if hasattr(image_data, 'read'):
                # Reset file pointer to beginning if possible
                if hasattr(image_data, 'seek'):
                    image_data.seek(0)
                
                content = image_data.read()
                
                # Validate we have data
                if not content or len(content) == 0:
                    print("Dlib: Empty image file")
                    return None
                
                im = Image.open(io.BytesIO(content)).convert('RGB')
                # Convert to numpy array with correct format for dlib
                img_array = np.array(im, dtype=np.uint8)
                print(f"✓ Dlib loaded image successfully (shape: {img_array.shape}, dtype: {img_array.dtype})")
                return img_array
        except Exception as e:
            print(f"Dlib: Error loading image: {e}")
            return None
        return None

    def register_face(self, user, image_data: Any):
        try:
            self._lazy_import()
            fr = self._fr
            image = self._load_image(image_data)
            if image is None:
                return False, 'Could not load image'

            boxes = fr.face_locations(image, model='hog')  # hog for speed without GPU
            if not boxes:
                return False, 'No face detected'

            encodings = fr.face_encodings(image, known_face_locations=boxes)
            if not encodings:
                return False, 'Failed to compute encoding'

            encoding = encodings[0]
            return True, {'model': 'dlib', 'encoding': encoding.tolist()}
        except Exception as e:
            return False, str(e)

    def recognize_face(self, image_data: Any, stored_encodings: List[Tuple[int, Any]]):
        """
        stored_encodings: list of (user_id, profile.face_encoding)
        profile.face_encoding may be:
        - dict: {'model': 'dlib', 'encoding': [128 floats]}
        - list of 128 floats (legacy)
        - other formats are ignored
        """
        try:
            self._lazy_import()
            fr = self._fr
            image = self._load_image(image_data)
            if image is None:
                print("  Dlib: Failed to load image")
                return None, 0

            print(f"  Dlib: Detecting faces in image...")
            boxes = fr.face_locations(image, model='hog')
            if not boxes:
                print(f"  Dlib: No faces detected in image")
                return None, 0
            
            print(f"  Dlib: Found {len(boxes)} face(s), computing encodings...")
            encodings = fr.face_encodings(image, known_face_locations=boxes)
            if not encodings:
                print(f"  Dlib: Failed to compute face encodings")
                return None, 0
            probe = encodings[0]

            best_user = None
            best_dist = 1e9
            compatible_count = 0

            print(f"  Dlib: Comparing with {len(stored_encodings)} stored encoding(s)...")
            for user_id, stored in stored_encodings:
                vec = None
                if isinstance(stored, dict) and stored.get('model') == 'dlib' and isinstance(stored.get('encoding'), list):
                    vec = np.array(stored['encoding'], dtype=np.float32)
                    compatible_count += 1
                elif isinstance(stored, list) and len(stored) == 128:
                    vec = np.array(stored, dtype=np.float32)
                    compatible_count += 1
                else:
                    print(f"  Dlib: Skipping incompatible encoding for user {user_id}")
                    continue  # skip non-dlib or incompatible encodings

                # Euclidean distance (face_recognition default)
                dist = np.linalg.norm(vec - probe)
                print(f"  Dlib: User {user_id} - distance: {dist:.4f}")
                if dist < best_dist:
                    best_dist = dist
                    best_user = user_id

            print(f"  Dlib: Checked {compatible_count} compatible encoding(s)")
            
            if best_user is None:
                print(f"  Dlib: No compatible encodings found")
                return None, 0

            # Convert distance to confidence roughly (inverse mapping)
            # Typical threshold ~0.6. We map confidence as 1 - (dist / 0.6) clipped to [0,1]
            confidence = max(0.0, min(1.0, 1.0 - (best_dist / 0.6)))
            print(f"  Dlib: Best match - User {best_user}, distance: {best_dist:.4f}, confidence: {confidence:.2f}")
            
            # Accept only if below threshold
            if best_dist <= 0.6:
                print(f"  Dlib: Match ACCEPTED (distance {best_dist:.4f} <= 0.6)")
                return best_user, confidence
            
            print(f"  Dlib: Match REJECTED (distance {best_dist:.4f} > 0.6)")
            return None, confidence
        except Exception as e:
            print(f"  Dlib: Exception during recognition: {e}")
            import traceback
            traceback.print_exc()
            return None, 0


# Global instance (import may fail if lib not installed; handled in services.py)
dlib_face_service = DlibFaceRecognitionService()
