import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  Card,
  Stack,
  CircularProgress
} from '@mui/material';
import { PersonAdd, CheckCircle } from '@mui/icons-material';
import axios from 'axios';
import { API_BASE_URL } from '../config';

function AddPerson() {
  const webcamRef = useRef<Webcam>(null);
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

  const playAudio = useCallback((audioFile: string) => {
    try {
      const audio = new Audio(`${API_BASE_URL}/audio/${audioFile}`);
      audio.volume = 0.8;
      audio.play().catch(err => {
        console.warn('Audio playback failed:', err);
        // Fallback to text-to-speech if audio fails
        if ('speechSynthesis' in window) {
          let text = '';
          switch(audioFile) {
            case 'person_added_successfully.wav':
              text = 'Person added successfully';
              break;
            case 'person_not_detected.wav':
              text = 'Person not detected';
              break;
            default:
              text = 'Operation completed';
          }
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.rate = 0.9;
          utterance.pitch = 1;
          utterance.volume = 0.8;
          speechSynthesis.speak(utterance);
        }
      });
    } catch (err) {
      console.warn('Audio creation failed:', err);
    }
  }, []);

  const handleAddPerson = async () => {
    if (!name.trim()) {
      setMessage('Please enter a name');
      setIsSuccess(false);
      return;
    }

    const imageSrc = webcamRef.current?.getScreenshot();
    if (!imageSrc) {
      setMessage('Please make sure camera is working');
      setIsSuccess(false);
      return;
    }

    setIsLoading(true);
    setMessage('');

    try {
      await axios.post(`${API_BASE_URL}/add-person`, {
        name: name.trim(),
        image: imageSrc
      });

      setMessage(`Successfully added ${name} to the system!`);
      setIsSuccess(true);
      setName('');
      playAudio('person_added_successfully.wav');
    } catch (error: any) {
      setMessage(error.response?.data?.message || 'Failed to add person');
      setIsSuccess(false);
      playAudio('person_not_detected.wav');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: { xs: '100%', sm: 500, md: 600 }, mx: 'auto' }}>
      <Typography 
        variant="h5" 
        gutterBottom 
        sx={{ 
          textAlign: 'center', 
          mb: { xs: 2, sm: 3 }, 
          fontWeight: 600,
          fontSize: { xs: '1.25rem', sm: '1.5rem' }
        }}
      >
         Add New Person
      </Typography>

      <Card sx={{ p: { xs: 2, sm: 3 } }}>
        <Stack spacing={{ xs: 2, sm: 3 }}>
          {/* Name Input */}
          <TextField
            label="Full Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            fullWidth
            placeholder="Enter person's name"
            variant="outlined"
            size={window.innerWidth < 600 ? 'medium' : 'medium'}
          />

          {/* Camera */}
          <Box>
            <Typography 
              variant="subtitle1" 
              gutterBottom 
              sx={{ 
                fontWeight: 500,
                fontSize: { xs: '1rem', sm: '1.125rem' }
              }}
            >
               Take Photo
            </Typography>
            <Box sx={{ 
              borderRadius: 2, 
              overflow: 'hidden',
              border: '2px solid #e0e0e0',
              maxWidth: { xs: '100%', sm: 400 },
              mx: 'auto'
            }}>
              <Webcam
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                width="100%"
                style={{ display: 'block' }}
                videoConstraints={{
                  width: { ideal: 640 },
                  height: { ideal: 480 },
                  facingMode: "user"
                }}
              />
            </Box>
          </Box>

          {/* Add Button */}
          <Button
            variant="contained"
            onClick={handleAddPerson}
            disabled={isLoading || !name.trim()}
            startIcon={isLoading ? <CircularProgress size={20} /> : <PersonAdd />}
            size="large"
            fullWidth
            sx={{ 
              py: { xs: 1.5, sm: 1.25 },
              fontSize: { xs: '1rem', sm: '0.875rem' }
            }}
          >
            {isLoading ? 'Adding Person...' : 'Add Person'}
          </Button>
        </Stack>
      </Card>

      {/* Result Message */}
      {message && (
        <Alert 
          severity={isSuccess ? "success" : "error"}
          icon={isSuccess ? <CheckCircle /> : undefined}
          sx={{ mt: 2 }}
          onClose={() => setMessage('')}
        >
          <Typography sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
            {message}
          </Typography>
        </Alert>
      )}

      {/* Instructions */}
      <Card sx={{ p: { xs: 1.5, sm: 2 }, bgcolor: 'grey.50', mt: 2 }}>
        <Typography 
          variant="body2" 
          color="text.secondary" 
          sx={{ 
            textAlign: 'center',
            fontSize: { xs: '0.75rem', sm: '0.875rem' },
            lineHeight: 1.4
          }}
        >
           <strong>Tips:</strong> Make sure your face is clearly visible and well-lit. 
          Look directly at the camera when taking the photo.
        </Typography>
      </Card>
    </Box>
  );
}

export default AddPerson;
