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
import os
import base64
import io
from PIL import Image
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
KNOWN_FACES_DIR = os.path.join(os.getcwd(), 'projects', 'known_faces')
ATTENDANCE_FILE = os.path.join(os.getcwd(), 'attendance.xlsx')
VOICE_DIR = os.path.join(os.getcwd(), 'voice')

# Initialize face recognizer and detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Global variables for face recognition
known_faces = []
known_names = []
face_labels = []
is_trained = False

# Store last attendance time for cooldown
last_attendance = {}

def load_known_faces():
    """Load and train the face recognizer with known faces"""
    global known_faces, known_names, face_labels, is_trained
    
    known_faces = []
    known_names = []
    face_labels = []
    label_counter = 0
    
    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
        return False
    
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            image_path = os.path.join(KNOWN_FACES_DIR, filename)
            image = cv2.imread(image_path)
            
            if image is not None:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                # Improved face detection parameters
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
                
                if len(faces) > 0:
                    # Take the largest face (most likely the main subject)
                    largest_face = max(faces, key=lambda face: face[2] * face[3])
                    x, y, w, h = largest_face
                    
                    face_region = gray[y:y+h, x:x+w]
                    # Standardize face size for better recognition
                    face_region = cv2.resize(face_region, (100, 100))
                    
                    # Apply histogram equalization for better lighting normalization
                    face_region = cv2.equalizeHist(face_region)
                    
                    known_faces.append(face_region)
                    name = filename.split('.')[0]
                    known_names.append(name)
                    face_labels.append(label_counter)
                    
                    print(f"Loaded face for: {name}")
                    label_counter += 1
                else:
                    print(f"No face detected in {filename}")
    
    if len(known_faces) > 0:
        recognizer.train(known_faces, np.array(face_labels))
        is_trained = True
        print(f"Training completed with {len(known_faces)} faces: {list(set(known_names))}")
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

def save_attendance(name, confidence):
    """Save attendance record to Excel file"""
    try:
        now = datetime.now()
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
        
        if not name or not image_data:
            return jsonify({"success": False, "message": "Name and image are required"}), 400
        
        # Convert base64 to OpenCV image
        image = base64_to_cv2(image_data)
        if image is None:
            return jsonify({"success": False, "message": "Invalid image data"}), 400
        
        # Detect faces in the image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Use same detection parameters as recognition
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
        
        if len(faces) == 0:
            return jsonify({"success": False, "message": "No face detected in the image"}), 400
        
        # Save the image
        filename = f"{name}.jpg"
        filepath = os.path.join(KNOWN_FACES_DIR, filename)
        cv2.imwrite(filepath, image)
        
        # Reload faces to include the new person
        load_known_faces()
        
        return jsonify({
            "success": True,
            "message": f"Person '{name}' added successfully",
            "filename": filename
        })
        
    except Exception as e:
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

@app.route('/retrain-model', methods=['POST'])
def retrain_model():
    """Manually retrain the face recognition model"""
    try:
        success = load_known_faces()
        return jsonify({
            "success": success,
            "message": "Model retrained successfully" if success else "Failed to retrain model",
            "known_faces_count": len(known_faces),
            "known_names": list(set(known_names))
        })
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
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
        
        if len(faces) == 0:
            return jsonify({
                "success": False, 
                "message": "No face detected",
                "audio": "person_not_detected"
            })
        
        # Process the largest face (most likely the main subject)
        largest_face = max(faces, key=lambda face: face[2] * face[3])
        x, y, w, h = largest_face
        
        face_region = gray[y:y+h, x:x+w]
        face_region = cv2.resize(face_region, (100, 100))
        # Apply histogram equalization for consistency with training
        face_region = cv2.equalizeHist(face_region)
        
        # Predict
        label, confidence = recognizer.predict(face_region)
        
        print(f"Recognition result - Label: {label}, Confidence: {confidence}")
        
        # Find the name corresponding to the label
        recognized_name = None
        if label < len(known_names):
            # Find the name for this label
            for i, face_label in enumerate(face_labels):
                if face_label == label:
                    recognized_name = known_names[i]
                    break
        
        # Use a stricter confidence threshold for better accuracy
        # LBPH confidence: lower values mean better match
        CONFIDENCE_THRESHOLD = 80  # Adjust this value based on testing
        
        if recognized_name and confidence < CONFIDENCE_THRESHOLD:
            print(f"Person recognized: {recognized_name} with confidence: {confidence}")
            
            # Check cooldown period (1 minute)
            current_time = datetime.now()
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
            attendance_confidence = max(0, (CONFIDENCE_THRESHOLD - confidence) / CONFIDENCE_THRESHOLD)  # Convert to 0-1 scale
            if save_attendance(recognized_name, attendance_confidence):
                last_attendance[recognized_name] = current_time
                return jsonify({
                    "success": True,
                    "name": recognized_name,
                    "confidence": attendance_confidence,
                    "message": f"Attendance marked for {recognized_name}",
                    "audio": "attendance_marked"
                })
            else:
                return jsonify({"success": False, "message": "Failed to save attendance"}), 500
        else:
            print(f"Face not recognized - Confidence: {confidence}, Threshold: {CONFIDENCE_THRESHOLD}")
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
            download_name=f"attendance_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
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
        today = datetime.now().date()
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
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
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
    
    # Load known faces on startup
    load_known_faces()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)
