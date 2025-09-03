# Face Recognition Attendance Web Application

A modern web-based face recognition attendance system with React frontend and Flask backend.

## 🚀 Features

- **Web-based Interface**: Modern React UI with Material-UI components
- **Real-time Face Recognition**: Live camera feed for attendance marking
- **Person Management**: Add new people to the system via web interface
- **Attendance Tracking**: View and download attendance records
- **Face Database**: Manage known faces and statistics
- **API Backend**: RESTful Flask API for all operations

## 📁 Project Structure

```
face-attendance-web/
├── frontend/          # React TypeScript application
│   ├── src/
│   │   ├── components/
│   │   │   ├── AttendanceCapture.tsx
│   │   │   ├── AddPerson.tsx
│   │   │   ├── AttendanceView.tsx
│   │   │   └── KnownFaces.tsx
│   │   └── App.tsx
│   └── package.json
├── backend/           # Flask Python API
│   ├── app.py
│   └── requirements.txt
└── README.md
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+ with virtual environment
- Node.js 16+ and npm
- Webcam access

### Backend Setup (Flask API)

1. **Activate your Python virtual environment**:
   ```bash
   source /Users/kartikey0104/Documents/opencv_learn/.venv/bin/activate
   ```

2. **Navigate to backend directory**:
   ```bash
   cd /Users/kartikey0104/Documents/opencv_learn/face-attendance-web/backend
   ```

3. **Install Python dependencies** (already installed in your venv):
   ```bash
   pip install flask flask-cors opencv-contrib-python pandas openpyxl pillow numpy
   ```

4. **Start the Flask API server**:
   ```bash
   python app.py
   ```
   
   The API will run on `http://localhost:5000`

### Frontend Setup (React App)

1. **Open a new terminal** and navigate to frontend directory:
   ```bash
   cd /Users/kartikey0104/Documents/opencv_learn/face-attendance-web/frontend
   ```

2. **Install Node.js dependencies** (already installed):
   ```bash
   npm install
   ```

3. **Start the React development server**:
   ```bash
   npm start
   ```
   
   The web app will open on `http://localhost:3000`

## 🎯 How to Use

### 1. **Mark Attendance**
- Go to the "Mark Attendance" tab
- Position your face in front of the camera
- Click "Capture Attendance"
- System recognizes you and marks attendance

### 2. **Add New Person**
- Go to the "Add Person" tab
- Enter the person's full name
- Capture their photo using the camera
- Click "Add Person" to register them

### 3. **View Attendance Records**
- Go to the "View Attendance" tab
- See all attendance records in a table
- View statistics and summary
- Download Excel file of records

### 4. **Manage Known Faces**
- Go to the "Known Faces" tab
- View all registered people
- See database statistics
- Reload face database after changes

## 🔧 API Endpoints

The Flask backend provides these REST endpoints:

- `GET /api/health` - Health check
- `POST /api/load-faces` - Load and train face recognizer
- `GET /api/known-faces` - Get list of known faces
- `POST /api/add-face` - Add new person to system
- `POST /api/recognize-face` - Recognize face from image
- `POST /api/mark-attendance` - Mark attendance for recognized person
- `GET /api/attendance` - Get attendance records
- `GET /api/attendance/download` - Download attendance Excel file

## 🎨 Technologies Used

### Frontend
- **React 18** with TypeScript
- **Material-UI (MUI)** for modern UI components
- **react-webcam** for camera integration
- **axios** for API communication

### Backend
- **Flask** Python web framework
- **OpenCV** for face detection and recognition
- **pandas** for data management
- **Flask-CORS** for cross-origin requests

## 🚀 Running the Complete System

1. **Start Backend** (Terminal 1):
   ```bash
   cd /Users/kartikey0104/Documents/opencv_learn/face-attendance-web/backend
   source /Users/kartikey0104/Documents/opencv_learn/.venv/bin/activate
   python app.py
   ```

2. **Start Frontend** (Terminal 2):
   ```bash
   cd /Users/kartikey0104/Documents/opencv_learn/face-attendance-web/frontend
   npm start
   ```

3. **Open your browser** and go to `http://localhost:3000`

## 📊 Current Status

- ✅ Flask API backend created and configured
- ✅ React frontend with Material-UI components
- ✅ Face recognition and attendance marking
- ✅ Person management and database
- ✅ Attendance viewing and download
- ✅ Integration with existing face data
- ✅ Web-based camera capture

## 🔍 Troubleshooting

### Camera Issues
- Grant camera permissions to your browser
- Check if other applications are using the camera
- Try refreshing the page

### API Connection Issues
- Ensure Flask server is running on port 5000
- Check CORS settings if requests fail
- Verify API endpoints are accessible

### Face Recognition Issues
- Ensure good lighting when adding/recognizing faces
- Make sure known_faces directory has face images
- Click "Reload Face Database" after adding people

**Your web-based face recognition system is ready! 🎉**

Access it at: http://localhost:3000
# attendance
