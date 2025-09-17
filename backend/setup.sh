#!/bin/bash

# Face Attendance Web Backend Startup Script

echo "Starting Face Attendance Backend Setup..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before running the server."
fi

# Check if known_faces directory exists
KNOWN_FACES_DIR="../projects/known_faces"
if [ ! -d "$KNOWN_FACES_DIR" ]; then
    echo "Creating known_faces directory..."
    mkdir -p "$KNOWN_FACES_DIR"
fi

echo "Setup complete! Run 'python app.py' to start the server."
echo "Make sure to configure .env file with your settings first."