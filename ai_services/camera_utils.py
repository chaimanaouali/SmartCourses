"""
Camera utilities for real-time face recognition
Provides camera capture and streaming functionality
"""
import cv2
import base64
import numpy as np
from typing import Optional, Callable, Dict, Any
import threading
import time


class CameraStream:
    """
    Real-time camera streaming with face recognition
    """
    
    def __init__(self, camera_index=0, fps=30):
        """
        Initialize camera stream
        
        Args:
            camera_index: Camera device index (0 for default camera)
            fps: Target frames per second
        """
        self.camera_index = camera_index
        self.fps = fps
        self.capture = None
        self.is_running = False
        self.current_frame = None
        self.lock = threading.Lock()
        
    def start(self) -> bool:
        """
        Start the camera stream
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.capture = cv2.VideoCapture(self.camera_index)
            if not self.capture.isOpened():
                print(f"Failed to open camera {self.camera_index}")
                return False
            
            # Set camera properties
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            
            self.is_running = True
            print(f"✓ Camera {self.camera_index} started successfully")
            return True
            
        except Exception as e:
            print(f"Error starting camera: {e}")
            return False
    
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a single frame from the camera
        
        Returns:
            Frame as numpy array or None if failed
        """
        if not self.capture or not self.is_running:
            return None
        
        try:
            ret, frame = self.capture.read()
            if ret:
                with self.lock:
                    self.current_frame = frame
                return frame
            return None
        except Exception as e:
            print(f"Error reading frame: {e}")
            return None
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recent frame
        
        Returns:
            Current frame or None
        """
        with self.lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def stop(self):
        """Stop the camera stream"""
        self.is_running = False
        if self.capture:
            self.capture.release()
            self.capture = None
        print("✓ Camera stopped")
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


class FaceRecognitionCamera:
    """
    Camera with integrated face recognition
    """
    
    def __init__(self, face_service, camera_index=0):
        """
        Initialize face recognition camera
        
        Args:
            face_service: Face recognition service instance
            camera_index: Camera device index
        """
        self.face_service = face_service
        self.camera = CameraStream(camera_index)
        self.recognition_thread = None
        self.stop_recognition = False
        self.last_results = None
        self.results_lock = threading.Lock()
    
    def start(self) -> bool:
        """Start camera and recognition"""
        return self.camera.start()
    
    def stop(self):
        """Stop camera and recognition"""
        self.stop_recognition = True
        if self.recognition_thread:
            self.recognition_thread.join(timeout=2)
        self.camera.stop()
    
    def capture_and_recognize(self) -> Dict[str, Any]:
        """
        Capture a frame and perform face recognition
        
        Returns:
            Dictionary with recognition results
        """
        frame = self.camera.read_frame()
        if frame is None:
            return {
                'success': False,
                'error': 'Failed to capture frame',
                'frame': None,
                'faces': []
            }
        
        # Perform recognition
        results = self.face_service.recognize_face_realtime(frame)
        
        with self.results_lock:
            self.last_results = results
        
        return results
    
    def get_last_results(self) -> Optional[Dict]:
        """Get the last recognition results"""
        with self.results_lock:
            return self.last_results
    
    def start_continuous_recognition(self, callback: Optional[Callable] = None, interval=0.5):
        """
        Start continuous face recognition in background thread
        
        Args:
            callback: Function to call with results (optional)
            interval: Time between recognition attempts in seconds
        """
        def recognition_loop():
            while not self.stop_recognition:
                results = self.capture_and_recognize()
                
                if callback:
                    try:
                        callback(results)
                    except Exception as e:
                        print(f"Error in callback: {e}")
                
                time.sleep(interval)
        
        self.stop_recognition = False
        self.recognition_thread = threading.Thread(target=recognition_loop, daemon=True)
        self.recognition_thread.start()
    
    def frame_to_base64(self, frame: np.ndarray, format='.jpg') -> str:
        """
        Convert frame to base64 encoded string
        
        Args:
            frame: Frame as numpy array
            format: Image format (.jpg, .png, etc.)
            
        Returns:
            Base64 encoded string with data URI
        """
        try:
            _, buffer = cv2.imencode(format, frame)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{img_base64}"
        except Exception as e:
            print(f"Error encoding frame: {e}")
            return ""
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


def capture_single_frame(camera_index=0) -> Optional[np.ndarray]:
    """
    Capture a single frame from camera
    
    Args:
        camera_index: Camera device index
        
    Returns:
        Captured frame or None
    """
    try:
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return None
        
        ret, frame = cap.read()
        cap.release()
        
        return frame if ret else None
    except Exception as e:
        print(f"Error capturing single frame: {e}")
        return None


def save_frame(frame: np.ndarray, filename: str) -> bool:
    """
    Save a frame to file
    
    Args:
        frame: Frame to save
        filename: Output filename
        
    Returns:
        True if successful, False otherwise
    """
    try:
        return cv2.imwrite(filename, frame)
    except Exception as e:
        print(f"Error saving frame: {e}")
        return False


def display_camera_window(
    face_service,
    camera_index=0,
    window_name="Face Recognition",
    show_fps=True
):
    """
    Display a live camera window with face recognition
    
    Args:
        face_service: Face recognition service
        camera_index: Camera device index
        window_name: Name of the display window
        show_fps: Whether to show FPS counter
    """
    camera = FaceRecognitionCamera(face_service, camera_index)
    
    if not camera.start():
        print("Failed to start camera")
        return
    
    print(f"\n{'='*60}")
    print("🎥 Face Recognition Camera Active")
    print(f"{'='*60}")
    print("Controls:")
    print("  • Press 'q' to quit")
    print("  • Press 's' to save current frame")
    print("  • Press 'r' to toggle recognition")
    print(f"{'='*60}\n")
    
    frame_count = 0
    start_time = time.time()
    recognition_enabled = True
    
    try:
        while True:
            if recognition_enabled:
                results = camera.capture_and_recognize()
                frame = results.get('frame')
                faces = results.get('faces', [])
            else:
                frame = camera.camera.read_frame()
                faces = []
            
            if frame is None:
                continue
            
            # Calculate FPS
            frame_count += 1
            if show_fps:
                elapsed_time = time.time() - start_time
                fps = frame_count / elapsed_time if elapsed_time > 0 else 0
                
                cv2.putText(
                    frame,
                    f"FPS: {fps:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
            
            # Show face count
            if recognition_enabled:
                status_text = f"Faces: {len(faces)} | Recognition: ON"
                color = (0, 255, 0)
            else:
                status_text = "Recognition: OFF"
                color = (0, 0, 255)
            
            cv2.putText(
                frame,
                status_text,
                (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )
            
            # Display frame
            cv2.imshow(window_name, frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n👋 Exiting...")
                break
            elif key == ord('s'):
                filename = f"capture_{int(time.time())}.jpg"
                if save_frame(frame, filename):
                    print(f"💾 Frame saved: {filename}")
            elif key == ord('r'):
                recognition_enabled = not recognition_enabled
                status = "ON" if recognition_enabled else "OFF"
                print(f"🔄 Recognition {status}")
    
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    
    finally:
        camera.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # Demo: Test camera with face recognition
    print("Testing camera with face recognition...")
    
    try:
        from face_recognition_deep import deep_face_service
        
        # Display live camera window
        display_camera_window(deep_face_service)
        
    except ImportError as e:
        print(f"Error importing face recognition service: {e}")
        print("Please ensure the deep learning model is set up correctly.")
