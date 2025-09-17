#!/usr/bin/env python3
"""
Flask API Backend for Face Recognition Attendance System
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os
import base64
import io
from PIL import Image
import json
from imagekitio import ImageKit

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Environment variables loaded from .env file")
except ImportError:
    print("python-dotenv not installed. Using system environment variables only.")
    print("Run 'pip install python-dotenv' to use .env file configuration.")

print("Starting Face Attendance Backend Server...")
print("Loading dependencies...done")

app = Flask(__name__)

# Configure CORS for production
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,https://attendance-frontend-mkwg.onrender.com').split(',')
# Clean up any whitespace
allowed_origins = [origin.strip() for origin in allowed_origins]
CORS(app, origins=allowed_origins)  # Enable CORS for specified origins

print(f"CORS configured for origins: {allowed_origins}")

print("Flask app initialized")

# ImageKit Configuration - Use environment variables for security
imagekit = None
try:
    imagekit_private_key = os.getenv('IMAGEKIT_PRIVATE_KEY')
    imagekit_public_key = os.getenv('IMAGEKIT_PUBLIC_KEY')
    imagekit_url_endpoint = os.getenv('IMAGEKIT_URL_ENDPOINT')
    
    if imagekit_private_key and imagekit_public_key and imagekit_url_endpoint:
        imagekit = ImageKit(
            private_key=imagekit_private_key,
            public_key=imagekit_public_key,
            url_endpoint=imagekit_url_endpoint
        )
        print("ImageKit initialized successfully")
    else:
        print("ImageKit credentials not found in environment variables. Image upload will use local storage only.")
except Exception as e:
    print(f"ImageKit initialization failed: {e}. Continuing with local storage only.")
    imagekit = None

print("ImageKit initialized")

# Configuration
KNOWN_FACES_DIR = os.path.join(os.path.dirname(__file__), '..', 'projects', 'known_faces')
ATTENDANCE_FILE = os.path.join(os.path.dirname(__file__), '..', 'attendance.xlsx')
VOICE_DIR = os.path.join(os.path.dirname(__file__), '..', 'voice')

# Get port from environment variable or use default
PORT = int(os.getenv('PORT', 5000))

print("Configuration loaded")

# Initialize face detector
print("Loading face cascade...")
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
print("Face cascade loaded successfully")

# Alternative face recognition using template matching and feature extraction
# This approach works with standard OpenCV without the opencv-contrib extras
print("Initializing face recognition system...")
print("Face recognition modules loaded")

# Global variables for face recognition
known_faces = []
known_names = []
face_labels = []
face_descriptors = []  # Store face feature descriptors
is_trained = False

# Store last attendance time for cooldown
last_attendance = {}

def extract_face_features(face_region):
    """Extract features from a face region using ORB detector"""
    orb = cv2.ORB_create(nfeatures=500)
    keypoints, descriptors = orb.detectAndCompute(face_region, None)
    return keypoints, descriptors

def compute_face_histogram(face_region):
    """Compute histogram features for face comparison"""
    # Convert to different color spaces and compute histograms
    hist_gray = cv2.calcHist([face_region], [0], None, [256], [0, 256])
    
    # Normalize histogram
    hist_gray = cv2.normalize(hist_gray, hist_gray).flatten()
    
    return hist_gray

def compare_faces(face1, face2):
    """Compare two faces using multiple similarity metrics"""
    # Method 1: Template matching
    result = cv2.matchTemplate(face1, face2, cv2.TM_CCOEFF_NORMED)
    template_score = np.max(result)
    
    # Method 2: Histogram comparison
    hist1 = compute_face_histogram(face1)
    hist2 = compute_face_histogram(face2)
    hist_score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    
    # Method 3: Simple pixel difference (alternative to SSIM)
    # Normalize images to same size if needed
    if face1.shape != face2.shape:
        face2 = cv2.resize(face2, (face1.shape[1], face1.shape[0]))
    
    # Calculate mean squared error
    mse = np.mean((face1.astype(np.float32) - face2.astype(np.float32)) ** 2)
    # Convert MSE to similarity score (lower MSE = higher similarity)
    mse_score = max(0, 1 - (mse / 10000))  # Normalize MSE to 0-1 range
    
    # Combine scores (weighted average)
    combined_score = (template_score * 0.5 + hist_score * 0.3 + mse_score * 0.2)
    
    return combined_score

def find_best_match(face_region):
    """Find the best matching face from known faces"""
    if len(known_faces) == 0:
        return None, 0.0
    
    best_score = 0.0
    best_match_idx = -1
    
    for i, known_face in enumerate(known_faces):
        try:
            score = compare_faces(face_region, known_face)
            if score > best_score:
                best_score = score
                best_match_idx = i
        except Exception as e:
            print(f"Error comparing with face {i}: {e}")
            continue
    
    if best_match_idx >= 0 and best_score > 0.6:  # Threshold for recognition
        return best_match_idx, best_score
    
    return None, best_score

def get_indian_time():
    """Get current time in Indian Standard Time (IST)"""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist)

def load_known_faces():
    """Load and train the face recognizer with known faces"""
    global known_faces, known_names, face_labels, is_trained
    
    known_faces = []
    known_names = []
    face_labels = []
    
    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
        return False
    
    label_counter = 0
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            image_path = os.path.join(KNOWN_FACES_DIR, filename)
            image = cv2.imread(image_path)
            
            if image is not None:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                # Improved face detection parameters
                faces = face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1, 
                    minNeighbors=5, 
                    minSize=(30, 30),
                    maxSize=(300, 300)
                )
                
                if len(faces) > 0:
                    # Take the largest face (most likely the main subject)
                    largest_face = max(faces, key=lambda face: face[2] * face[3])
                    x, y, w, h = largest_face
                    
                    # Add some padding around the face
                    padding = 10
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    w = min(gray.shape[1] - x, w + 2 * padding)
                    h = min(gray.shape[0] - y, h + 2 * padding)
                    
                    face_region = gray[y:y+h, x:x+w]
                    # Standardize face size for better recognition
                    face_region = cv2.resize(face_region, (150, 150))
                    
                    # Apply histogram equalization for better lighting normalization
                    face_region = cv2.equalizeHist(face_region)
                    # Apply Gaussian blur to reduce noise
                    face_region = cv2.GaussianBlur(face_region, (3, 3), 0)
                    
                    known_faces.append(face_region)
                    name = filename.split('.')[0]
                    known_names.append(name)
                    face_labels.append(label_counter)
                    
                    print(f"Loaded face for: {name} (Label: {label_counter})")
                    label_counter += 1
                else:
                    print(f"No face detected in {filename}. Trying with different parameters...")
                    # Try with more relaxed parameters for difficult images
                    faces_relaxed = face_cascade.detectMultiScale(
                        gray, 
                        scaleFactor=1.05, 
                        minNeighbors=3, 
                        minSize=(20, 20),
                        maxSize=(400, 400)
                    )
                    
                    if len(faces_relaxed) > 0:
                        print(f"Face detected with relaxed parameters for {filename}")
                        largest_face = max(faces_relaxed, key=lambda face: face[2] * face[3])
                        x, y, w, h = largest_face
                        
                        # Add some padding around the face
                        padding = 10
                        x = max(0, x - padding)
                        y = max(0, y - padding)
                        w = min(gray.shape[1] - x, w + 2 * padding)
                        h = min(gray.shape[0] - y, h + 2 * padding)
                        
                        face_region = gray[y:y+h, x:x+w]
                        face_region = cv2.resize(face_region, (150, 150))
                        face_region = cv2.equalizeHist(face_region)
                        face_region = cv2.GaussianBlur(face_region, (3, 3), 0)
                        
                        known_faces.append(face_region)
                        name = filename.split('.')[0]
                        known_names.append(name)
                        face_labels.append(label_counter)
                        
                        print(f"Loaded face for: {name} (Label: {label_counter}) with relaxed detection")
                        label_counter += 1
                    else:
                        print(f"Still no face detected in {filename}. Skipping...")
    
    if len(known_faces) > 0:
        print(f"Face database loaded with {len(known_faces)} faces...")
        is_trained = True
        print(f"Training completed. Names: {known_names}")
        print(f"Labels: {face_labels}")
        return True
    
    print("No faces found for training")
    return False

def base64_to_cv2(base64_str):
    """Convert base64 string to OpenCV image"""
    try:
        # Remove data URL prefix if present
        if 'data:image' in base64_str:
            base64_str = base64_str.split(',')[1]
        
        # Decode base64
        img_data = base64.b64decode(base64_str)
        img_array = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Error converting base64 to CV2: {e}")
        return None

def upload_image_to_imagekit(image, filename):
    """Upload image to ImageKit and return the CDN URL"""
    if not imagekit:
        print("ImageKit not configured, using local storage only")
        return "local_storage_fallback"
    
    try:
        # Convert OpenCV image to bytes
        _, buffer = cv2.imencode('.jpg', image)
        image_bytes = buffer.tobytes()
        
        print(f"Uploading {filename} to ImageKit...")
        
        # Try upload without options first
        try:
            upload_result = imagekit.upload(
                file=image_bytes,
                file_name=filename
            )
        except Exception as e1:
            print(f"Simple upload failed: {e1}")
            # Try with options as kwargs instead of dict
            try:
                upload_result = imagekit.upload(
                    file=image_bytes,
                    file_name=filename,
                    is_private_file=False,
                    folder="known_faces"
                )
            except Exception as e2:
                print(f"Upload with kwargs failed: {e2}")
                return "local_storage_fallback"
        
        print(f"Upload result type: {type(upload_result)}")
        print(f"Upload result: {upload_result}")
        
        # Extract URL from the response
        if hasattr(upload_result, 'url'):
            url = upload_result.url
            print(f"Upload successful: {url}")
            return url
        elif hasattr(upload_result, 'response_metadata'):
            response_data = upload_result.response_metadata
            if hasattr(response_data, 'url'):
                url = response_data.url
                print(f"Upload successful: {url}")
                return url
        
        print(f"Could not extract URL from upload result: {upload_result}")
        return "local_storage_fallback"
        
    except Exception as e:
        print(f"Error uploading to ImageKit: {e}")
        import traceback
        traceback.print_exc()
        
        # For now, let's skip ImageKit upload and just save locally
        print("Falling back to local storage only...")
        return "local_storage_fallback"

def save_attendance(name, confidence):
    """Save attendance record to Excel file"""
    try:
        now = get_indian_time()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        # Check if file exists
        if os.path.exists(ATTENDANCE_FILE):
            df = pd.read_excel(ATTENDANCE_FILE)
        else:
            df = pd.DataFrame(columns=['Name', 'Date', 'Time'])
        
        # Create new record
        new_record = {
            'Name': name,
            'Date': date_str,
            'Time': time_str
        }
        
        # Add record using pd.concat
        new_df = pd.DataFrame([new_record])
        df = pd.concat([df, new_df], ignore_index=True)
        
        # Save to Excel
        df.to_excel(ATTENDANCE_FILE, index=False)
        print(f"Attendance saved: {name} at {date_str} {time_str}")
        return True
        
    except Exception as e:
        print(f"Error saving attendance: {e}")
        return False

# Routes
@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Face Recognition API is running"})

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio files"""
    try:
        audio_path = os.path.join(VOICE_DIR, filename)
        if os.path.exists(audio_path):
            return send_file(audio_path, mimetype='audio/wav')
        else:
            return jsonify({"error": "Audio file not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Error serving audio: {str(e)}"}), 500

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve face images"""
    try:
        image_path = os.path.join(KNOWN_FACES_DIR, filename)
        if os.path.exists(image_path):
            # Determine MIME type based on file extension
            if filename.lower().endswith('.png'):
                mimetype = 'image/png'
            elif filename.lower().endswith(('.jpg', '.jpeg')):
                mimetype = 'image/jpeg'
            else:
                mimetype = 'image/jpeg'  # Default to JPEG
            
            return send_file(image_path, mimetype=mimetype)
        else:
            return jsonify({"error": "Image file not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Error serving image: {str(e)}"}), 500

@app.route('/add-person', methods=['POST'])
def add_person():
    """Add a new person to the system"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        image_data = data.get('image')
        
        print(f"Add person request received - Name: {name}")
        print(f"Known faces directory: {KNOWN_FACES_DIR}")
        print(f"Directory exists: {os.path.exists(KNOWN_FACES_DIR)}")
        
        if not name or not image_data:
            return jsonify({"success": False, "message": "Name and image are required"}), 400
        
        # Convert base64 to OpenCV image
        image = base64_to_cv2(image_data)
        if image is None:
            return jsonify({"success": False, "message": "Invalid image data"}), 400
        
        print(f"Image converted successfully, size: {image.shape}")
        
        # Detect faces in the image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Use same detection parameters as training and recognition
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30),
            maxSize=(300, 300)
        )
        
        print(f"Faces detected: {len(faces)}")
        
        if len(faces) == 0:
            return jsonify({"success": False, "message": "No face detected in the image"}), 400
        
        # Upload image to ImageKit instead of saving locally
        filename = f"{name}.jpg"
        imagekit_url = upload_image_to_imagekit(image, filename)
        
        if not imagekit_url or imagekit_url == "local_storage_fallback":
            print("ImageKit upload failed or not available, continuing with local storage...")
            imagekit_url = "Local storage only"
        else:
            print(f"Image uploaded to ImageKit: {imagekit_url}")
        
        # Also save locally for face recognition training (always required)
        filepath = os.path.join(KNOWN_FACES_DIR, filename)
        print(f"Saving local copy for training: {filepath}")
        
        # Ensure directory exists
        os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
        
        success = cv2.imwrite(filepath, image)
        print(f"Local save successful: {success}")
        
        if not success:
            return jsonify({"success": False, "message": "Failed to save local training copy"}), 500
        
        # Reload faces to include the new person
        load_success = load_known_faces()
        print(f"Model retraining successful: {load_success}")
        
        return jsonify({
            "success": True,
            "message": f"Person '{name}' added successfully",
            "filename": filename,
            "imagekit_url": imagekit_url,
            "local_filepath": filepath
        })
        
    except Exception as e:
        print(f"Error in add_person: {str(e)}")
        return jsonify({"success": False, "message": f"Error adding person: {str(e)}"}), 500

@app.route('/model-status', methods=['GET'])
def get_model_status():
    """Get the current status of the face recognition model"""
    try:
        return jsonify({
            "is_trained": is_trained,
            "known_faces_count": len(known_faces),
            "known_names": list(set(known_names)),
            "labels": face_labels,
            "known_faces_dir": KNOWN_FACES_DIR,
            "files_in_dir": os.listdir(KNOWN_FACES_DIR) if os.path.exists(KNOWN_FACES_DIR) else []
        })
    except Exception as e:
        return jsonify({"error": f"Error getting model status: {str(e)}"}), 500

@app.route('/api/debug-model', methods=['GET'])
def debug_model():
    """Debug endpoint to check model status"""
    try:
        return jsonify({
            "is_trained": is_trained,
            "num_known_faces": len(known_faces),
            "known_names": known_names,
            "face_labels": face_labels,
            "known_faces_dir": KNOWN_FACES_DIR,
            "files_in_dir": os.listdir(KNOWN_FACES_DIR) if os.path.exists(KNOWN_FACES_DIR) else []
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/retrain-model', methods=['POST'])
def retrain_model():
    """Manually retrain the face recognition model"""
    try:
        success = load_known_faces()
        if success:
            return jsonify({
                "success": True,
                "message": f"Model retrained successfully with {len(known_faces)} faces",
                "known_names": known_names
            })
        else:
            return jsonify({
                "success": False,
                "message": "No faces found for training"
            }), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Error retraining model: {str(e)}"}), 500

@app.route('/mark-attendance', methods=['POST'])
def mark_attendance():
    """Mark attendance from webcam image"""
    try:
        data = request.json
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({"success": False, "message": "Image data is required"}), 400
        
        if not is_trained:
            return jsonify({"success": False, "message": "No known faces available for recognition"}), 400
        
        # Convert base64 to OpenCV image
        image = base64_to_cv2(image_data)
        if image is None:
            return jsonify({"success": False, "message": "Invalid image data"}), 400
        
        # Convert to grayscale and detect faces
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Improved face detection parameters
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30),
            maxSize=(300, 300)
        )
        
        if len(faces) == 0:
            return jsonify({
                "success": False, 
                "message": "No face detected",
                "audio": "person_not_detected"
            })
        
        # Process the largest face (most likely the main subject)
        largest_face = max(faces, key=lambda face: face[2] * face[3])
        x, y, w, h = largest_face
        
        # Add some padding around the face
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(gray.shape[1] - x, w + 2 * padding)
        h = min(gray.shape[0] - y, h + 2 * padding)
        
        face_region = gray[y:y+h, x:x+w]
        face_region = cv2.resize(face_region, (150, 150))
        # Apply histogram equalization for consistency with training
        face_region = cv2.equalizeHist(face_region)
        # Apply Gaussian blur to reduce noise
        face_region = cv2.GaussianBlur(face_region, (3, 3), 0)
        
        # Find best match using our custom face recognition
        match_idx, confidence_score = find_best_match(face_region)
        
        print(f"Recognition result - Match Index: {match_idx}, Confidence: {confidence_score}")
        print(f"Available faces: {len(known_faces)}")
        print(f"Available names: {known_names}")
        
        # Recognition threshold
        CONFIDENCE_THRESHOLD = 0.6  # Similarity score threshold
        
        if match_idx is not None and confidence_score >= CONFIDENCE_THRESHOLD:
            recognized_name = known_names[match_idx]
            print(f"Person recognized: {recognized_name} with confidence: {confidence_score}")
            
            # Check cooldown period (1 minute)
            current_time = get_indian_time()
            last_time = last_attendance.get(recognized_name)
            
            if last_time and (current_time - last_time).total_seconds() < 60:
                remaining_seconds = 60 - int((current_time - last_time).total_seconds())
                return jsonify({
                    "success": False,
                    "message": f"Attendance already marked. Please wait {remaining_seconds} seconds.",
                    "cooldown": True,
                    "remaining_seconds": remaining_seconds,
                    "audio": "attendance_is_already_marked"
                })
            
            # Save attendance
            if save_attendance(recognized_name, confidence_score):
                last_attendance[recognized_name] = current_time
                return jsonify({
                    "success": True,
                    "name": recognized_name,
                    "confidence": confidence_score,
                    "message": f"Attendance marked for {recognized_name}",
                    "audio": "attendance_marked"
                })
            else:
                return jsonify({"success": False, "message": "Failed to save attendance"}), 500
        else:
            print(f"Face not recognized - Confidence: {confidence_score}, Threshold: {CONFIDENCE_THRESHOLD}")
            return jsonify({
                "success": False, 
                "message": "Face not recognized",
                "audio": "person_not_detected"
            })
        
        return jsonify({
            "success": False, 
            "message": "No recognizable face found",
            "audio": "person_not_detected"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error marking attendance: {str(e)}"}), 500

@app.route('/attendance-records', methods=['GET'])
def get_attendance_records():
    """Get attendance records"""
    try:
        if not os.path.exists(ATTENDANCE_FILE):
            return jsonify({"records": [], "count": 0})
        
        df = pd.read_excel(ATTENDANCE_FILE)
        records = df.to_dict('records')
        
        # Convert datetime objects to strings and normalize field names
        normalized_records = []
        for record in records:
            normalized_record = {}
            for key, value in record.items():
                # Normalize key names to lowercase
                normalized_key = key.lower()
                
                if pd.isna(value):
                    normalized_record[normalized_key] = None
                elif isinstance(value, (pd.Timestamp, datetime)):
                    normalized_record[normalized_key] = value.strftime("%Y-%m-%d") if 'date' in normalized_key else value.strftime("%H:%M:%S")
                else:
                    normalized_record[normalized_key] = str(value)
            
            # Add confidence if not present
            if 'confidence' not in normalized_record:
                normalized_record['confidence'] = 0.9  # Default confidence
                
            normalized_records.append(normalized_record)
        
        return jsonify({"records": normalized_records, "count": len(normalized_records)})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error getting attendance: {str(e)}"}), 500

@app.route('/download-attendance', methods=['GET'])
def download_attendance():
    """Download attendance records as Excel file"""
    try:
        if not os.path.exists(ATTENDANCE_FILE):
            return jsonify({"success": False, "message": "No attendance records found"}), 404
        
        # Send the Excel file
        return send_file(
            ATTENDANCE_FILE,
            as_attachment=True,
            download_name=f"attendance_records_{get_indian_time().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error downloading file: {str(e)}"}), 500

@app.route('/known-faces', methods=['GET'])
def get_known_faces_list():
    """Get list of known faces"""
    try:
        people = []
        if os.path.exists(KNOWN_FACES_DIR):
            for filename in os.listdir(KNOWN_FACES_DIR):
                if filename.endswith('.jpg') or filename.endswith('.png'):
                    filepath = os.path.join(KNOWN_FACES_DIR, filename)
                    stat = os.stat(filepath)
                    people.append({
                        "name": filename.split('.')[0],
                        "image_path": filename,
                        "date_added": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
        
        return jsonify({"people": people, "count": len(people)})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error getting known faces: {str(e)}"}), 500

@app.route('/delete-person', methods=['DELETE'])
def delete_person():
    """Delete a person from the system"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({"success": False, "message": "Name is required"}), 400
        
        # Find and delete the image file
        deleted = False
        for filename in os.listdir(KNOWN_FACES_DIR):
            if filename.startswith(name + '.') and (filename.endswith('.jpg') or filename.endswith('.png')):
                filepath = os.path.join(KNOWN_FACES_DIR, filename)
                os.remove(filepath)
                deleted = True
                break
        
        if not deleted:
            return jsonify({"success": False, "message": f"Person '{name}' not found"}), 404
        
        # Reload faces
        load_known_faces()
        
        return jsonify({
            "success": True,
            "message": f"Person '{name}' deleted successfully"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error deleting person: {str(e)}"}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get attendance statistics"""
    try:
        if not os.path.exists(ATTENDANCE_FILE):
            return jsonify({
                "total_records": 0,
                "unique_people": 0,
                "today_attendance": 0,
                "this_week": 0,
                "this_month": 0,
                "average_confidence": 0,
                "most_active_person": None,
                "peak_hours": []
            })
        
        df = pd.read_excel(ATTENDANCE_FILE)
        today = get_indian_time().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Convert Date column to datetime for filtering
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        
        # Basic statistics
        total_records = len(df)
        unique_people = df['Name'].nunique()
        today_attendance = len(df[df['Date'] == today])
        this_week = len(df[df['Date'] >= week_start])
        this_month = len(df[df['Date'] >= month_start])
        
        # Most active person
        person_counts = df['Name'].value_counts()
        most_active_person = person_counts.index[0] if len(person_counts) > 0 else None
        
        # Peak hours analysis
        if 'Time' in df.columns:
            df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.hour
            hour_counts = df['Hour'].value_counts().head(3)
            peak_hours = [{"hour": int(hour), "count": int(count)} for hour, count in hour_counts.items()]
        else:
            peak_hours = []
        
        return jsonify({
            "total_records": total_records,
            "unique_people": unique_people,
            "today_attendance": today_attendance,
            "this_week": this_week,
            "this_month": this_month,
            "average_confidence": 0.85,  # Default confidence
            "most_active_person": most_active_person,
            "peak_hours": peak_hours
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error getting statistics: {str(e)}"}), 500

@app.route('/api/backup', methods=['POST'])
def backup_data():
    """Create a backup of attendance data"""
    try:
        backup_dir = os.path.join(os.path.dirname(ATTENDANCE_FILE), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = get_indian_time().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'attendance_backup_{timestamp}.xlsx')
        
        if os.path.exists(ATTENDANCE_FILE):
            import shutil
            shutil.copy2(ATTENDANCE_FILE, backup_file)
            
            return jsonify({
                "success": True,
                "message": "Backup created successfully",
                "backup_file": backup_file,
                "timestamp": timestamp
            })
        else:
            return jsonify({"success": False, "message": "No attendance file to backup"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Error creating backup: {str(e)}"}), 500

if __name__ == '__main__':
    print("Face Recognition API starting...")
    print(f"Known faces directory: {KNOWN_FACES_DIR}")
    print(f"Attendance file: {ATTENDANCE_FILE}")
    print(f"Starting server on port {PORT}")
    
    # Load known faces on startup
    load_known_faces()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=PORT, debug=False)
