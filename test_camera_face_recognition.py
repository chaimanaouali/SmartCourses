"""
Test Camera-Based Deep Learning Face Recognition
Run this standalone script to test the camera and face recognition model
"""
import sys
import os
from pathlib import Path

# Add the project to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartCourses.settings')

try:
    import django
    django.setup()
except Exception as e:
    print(f"Note: Django setup skipped: {e}")


def test_deep_learning_model():
    """Test if the deep learning model loads correctly"""
    print("\n" + "="*70)
    print("🧪 TEST 1: Deep Learning Model Loading")
    print("="*70)
    
    try:
        from ai_services.face_recognition_deep import deep_face_service
        
        # Test lazy loading
        if deep_face_service._lazy_load():
            print("✅ SUCCESS: Deep learning model loaded successfully")
            print(f"   📁 Model path: {deep_face_service.model_path}")
            print(f"   📊 Label encoder classes: {len(deep_face_service.label_encoder.classes_)}")
            print(f"   👤 Registered users: {list(deep_face_service.label_encoder.classes_)}")
            return True
        else:
            print("❌ FAILED: Could not load deep learning model")
            print("   Please ensure the model files exist in face-recognition-model/")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_camera_access():
    """Test if camera can be accessed"""
    print("\n" + "="*70)
    print("🧪 TEST 2: Camera Access")
    print("="*70)
    
    try:
        import cv2
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ FAILED: Cannot access camera")
            print("   Please check if camera is connected and not in use")
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            print("✅ SUCCESS: Camera is accessible")
            print(f"   📐 Frame shape: {frame.shape}")
            print(f"   📸 Resolution: {frame.shape[1]}x{frame.shape[0]}")
            return True
        else:
            print("❌ FAILED: Could not capture frame from camera")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_face_detection():
    """Test face detection on a single frame"""
    print("\n" + "="*70)
    print("🧪 TEST 3: Face Detection")
    print("="*70)
    
    try:
        from ai_services.camera_utils import capture_single_frame
        from ai_services.face_recognition_deep import deep_face_service
        
        print("📸 Capturing frame from camera...")
        frame = capture_single_frame(0)
        
        if frame is None:
            print("❌ FAILED: Could not capture frame")
            return False
        
        print("🔍 Detecting faces...")
        faces = deep_face_service.detect_faces(frame)
        
        if len(faces) > 0:
            print(f"✅ SUCCESS: Detected {len(faces)} face(s)")
            for i, (x, y, w, h) in enumerate(faces, 1):
                print(f"   👤 Face {i}: Position ({x}, {y}), Size {w}x{h}")
            return True
        else:
            print("⚠️  WARNING: No faces detected in frame")
            print("   Please ensure someone is visible in the camera")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_realtime_recognition():
    """Test real-time face recognition"""
    print("\n" + "="*70)
    print("🧪 TEST 4: Real-Time Face Recognition")
    print("="*70)
    
    try:
        from ai_services.camera_utils import capture_single_frame
        from ai_services.face_recognition_deep import deep_face_service
        
        print("📸 Capturing and analyzing frame...")
        frame = capture_single_frame(0)
        
        if frame is None:
            print("❌ FAILED: Could not capture frame")
            return False
        
        print("🤖 Running face recognition...")
        result = deep_face_service.recognize_face_realtime(frame)
        
        if result['success']:
            print(f"✅ SUCCESS: Recognition completed")
            print(f"   👥 Faces detected: {result['face_count']}")
            
            for i, face_data in enumerate(result['faces'], 1):
                label = face_data['label']
                confidence = face_data['confidence']
                bbox = face_data['bbox']
                print(f"   {i}. Name: {label}")
                print(f"      Confidence: {confidence*100:.2f}%")
                print(f"      Bounding box: {bbox}")
            
            return True
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def launch_interactive_camera():
    """Launch interactive camera window with face recognition"""
    print("\n" + "="*70)
    print("🎥 INTERACTIVE MODE: Live Camera with Face Recognition")
    print("="*70)
    print("\nControls:")
    print("  • Press 'q' to quit")
    print("  • Press 's' to save current frame")
    print("  • Press 'r' to toggle recognition on/off")
    print("\nStarting camera in 2 seconds...")
    print("="*70)
    
    import time
    time.sleep(2)
    
    try:
        from ai_services.camera_utils import display_camera_window
        from ai_services.face_recognition_deep import deep_face_service
        
        display_camera_window(deep_face_service)
        
        print("\n✅ Camera closed successfully")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🚀 DEEP LEARNING FACE RECOGNITION TEST SUITE")
    print("="*70)
    
    results = {
        "Model Loading": test_deep_learning_model(),
        "Camera Access": test_camera_access(),
        "Face Detection": test_face_detection(),
        "Real-Time Recognition": test_realtime_recognition()
    }
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✨ All tests passed! System is ready.")
        
        # Ask if user wants to launch interactive mode
        print("\n" + "="*70)
        response = input("Would you like to launch interactive camera mode? (y/n): ")
        if response.lower() in ['y', 'yes']:
            launch_interactive_camera()
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Deep Learning Face Recognition System')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Launch interactive camera mode directly')
    parser.add_argument('--test', '-t', type=str,
                       help='Run specific test: model, camera, detection, recognition')
    
    args = parser.parse_args()
    
    if args.interactive:
        launch_interactive_camera()
    elif args.test:
        test_map = {
            'model': test_deep_learning_model,
            'camera': test_camera_access,
            'detection': test_face_detection,
            'recognition': test_realtime_recognition
        }
        
        test_func = test_map.get(args.test.lower())
        if test_func:
            test_func()
        else:
            print(f"Unknown test: {args.test}")
            print(f"Available tests: {', '.join(test_map.keys())}")
    else:
        run_all_tests()
