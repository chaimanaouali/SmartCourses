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

            # File path
            if isinstance(image_data, str) and os.path.exists(image_data):
                return fr.load_image_file(image_data)

            # Base64 data URI
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                b64 = image_data.split(',')[1]
                img_bytes = base64.b64decode(b64)
                import io
                from PIL import Image
                im = Image.open(io.BytesIO(img_bytes)).convert('RGB')
                return np.array(im)

            # File-like
            if hasattr(image_data, 'read'):
                content = image_data.read()
                import io
                from PIL import Image
                im = Image.open(io.BytesIO(content)).convert('RGB')
                return np.array(im)
        except Exception:
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
                return None, 0

            boxes = fr.face_locations(image, model='hog')
            if not boxes:
                return None, 0
            encodings = fr.face_encodings(image, known_face_locations=boxes)
            if not encodings:
                return None, 0
            probe = encodings[0]

            best_user = None
            best_dist = 1e9

            for user_id, stored in stored_encodings:
                vec = None
                if isinstance(stored, dict) and stored.get('model') == 'dlib' and isinstance(stored.get('encoding'), list):
                    vec = np.array(stored['encoding'], dtype=np.float32)
                elif isinstance(stored, list) and len(stored) == 128:
                    vec = np.array(stored, dtype=np.float32)
                else:
                    continue  # skip non-dlib or incompatible encodings

                # Euclidean distance (face_recognition default)
                dist = np.linalg.norm(vec - probe)
                if dist < best_dist:
                    best_dist = dist
                    best_user = user_id

            if best_user is None:
                return None, 0

            # Convert distance to confidence roughly (inverse mapping)
            # Typical threshold ~0.6. We map confidence as 1 - (dist / 0.6) clipped to [0,1]
            confidence = max(0.0, min(1.0, 1.0 - (best_dist / 0.6)))
            # Accept only if below threshold
            if best_dist <= 0.6:
                return best_user, confidence
            return None, confidence
        except Exception:
            return None, 0


# Global instance (import may fail if lib not installed; handled in services.py)
dlib_face_service = DlibFaceRecognitionService()
