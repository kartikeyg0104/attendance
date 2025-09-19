import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import {
  Box,
  Button,
  Typography,
  Alert,
  Card,
  Switch,
  FormControlLabel,
  Chip,
  CircularProgress,
  Stack,
  Divider
} from '@mui/material';
import { 
  CameraAlt, 
  Stop, 
  CheckCircle, 
  ErrorOutline,
  AutoMode 
} from '@mui/icons-material';
import axios from 'axios';
import { API_BASE_URL, AUDIO_BASE_URL } from '../config';

interface AttendanceResponse {
  name: string;
  confidence: number;
  timestamp: string;
  success: boolean;
  message: string;
  cooldown?: boolean;
  remaining_seconds?: number;
  audio?: string;
}

function AttendanceCapture() {
  const webcamRef = useRef<Webcam>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isAutoMode, setIsAutoMode] = useState(false);
  const [lastResult, setLastResult] = useState<AttendanceResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const recognitionIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Check backend connection on component mount
  React.useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/health`, { timeout: 5000 });
        if (response.data.status === 'healthy') {
          setConnectionStatus('connected');
        } else {
          setConnectionStatus('disconnected');
        }
      } catch (error) {
        setConnectionStatus('disconnected');
        console.error('Backend connection failed:', error);
      }
    };

    checkConnection();
    // Check connection every 30 seconds
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

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
            case 'attendance_marked.wav':
              text = 'Attendance marked successfully';
              break;
            case 'person_not_detected.wav':
              text = 'Person not detected';
              break;
            case 'attendance_is_already_marked.wav':
              text = 'Attendance is already marked';
              break;
            case 'person_added_successfully.wav':
              text = 'Person added successfully';
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

  const speak = useCallback((text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 0.8;
      speechSynthesis.speak(utterance);
    }
  }, []);

  const performRecognition = useCallback(async () => {
    if (!webcamRef.current) return;

    try {
      setIsLoading(true);
      setError(null);
      
      const imageSrc = webcamRef.current.getScreenshot();
      if (!imageSrc) {
        throw new Error('Failed to capture image');
      }

      const response = await axios.post<AttendanceResponse>(
        `${API_BASE_URL}/api/mark-attendance`,
        { image: imageSrc },
        { timeout: 10000 }
      );

      setLastResult(response.data);
      
      // Play audio based on the backend response
      if (response.data.audio) {
        playAudio(`${response.data.audio}.wav`);
      } else if (response.data.success) {
        playAudio('attendance_marked.wav');
      } else {
        playAudio('person_not_detected.wav');
      }
    } catch (err: any) {
      let errorMessage = 'Recognition failed';
      
      if (err.code === 'ECONNABORTED' || err.message.includes('timeout')) {
        errorMessage = 'Request timeout - Please check your connection';
        setConnectionStatus('disconnected');
      } else if (err.response?.status === 500) {
        errorMessage = 'Server error - Please try again';
      } else if (err.response?.status === 404) {
        errorMessage = 'Service not found - Please check backend deployment';
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      console.error('Recognition error:', err);
      setError(errorMessage);
      
      // Set a failed result to show in UI
      setLastResult({
        name: '',
        confidence: 0,
        timestamp: new Date().toISOString(),
        success: false,
        message: errorMessage
      });
      
      playAudio('person_not_detected.wav');
    } finally {
      setIsLoading(false);
    }
  }, [playAudio]);

  const startAutoRecognition = useCallback(() => {
    if (recognitionIntervalRef.current) return;
    
    recognitionIntervalRef.current = setInterval(() => {
      performRecognition();
    }, 3000);
  }, [performRecognition]);

  const stopAutoRecognition = useCallback(() => {
    if (recognitionIntervalRef.current) {
      clearInterval(recognitionIntervalRef.current);
      recognitionIntervalRef.current = null;
    }
  }, []);

  const handleAutoModeToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    const enabled = event.target.checked;
    setIsAutoMode(enabled);
    
    if (enabled) {
      setIsCapturing(true);
      startAutoRecognition();
    } else {
      stopAutoRecognition();
    }
  };

  const handleManualCapture = () => {
    if (isAutoMode) return;
    performRecognition();
  };

  const handleStopCapture = () => {
    setIsCapturing(false);
    setIsAutoMode(false);
    stopAutoRecognition();
    setLastResult(null);
    setError(null);
  };

  React.useEffect(() => {
    return () => {
      stopAutoRecognition();
    };
  }, [stopAutoRecognition]);

  return (
    <Box sx={{ maxWidth: { xs: '100%', sm: 600, md: 800 }, mx: 'auto' }}>
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
         Mark Attendance
      </Typography>

      {/* Connection Status */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
        <Chip
          icon={connectionStatus === 'connected' ? <CheckCircle /> : <ErrorOutline />}
          label={
            connectionStatus === 'connected' ? 'Backend Connected' :
            connectionStatus === 'disconnected' ? 'Backend Disconnected' :
            'Checking Connection...'
          }
          color={
            connectionStatus === 'connected' ? 'success' :
            connectionStatus === 'disconnected' ? 'error' :
            'default'
          }
          size="small"
        />
      </Box>

      <Card sx={{ p: { xs: 2, sm: 3 }, mb: { xs: 2, sm: 3 } }}>
        <Stack spacing={{ xs: 2, sm: 3 }}>
          {/* Controls */}
          <Box sx={{ 
            display: 'flex', 
            flexDirection: { xs: 'column', sm: 'row' },
            justifyContent: 'space-between', 
            alignItems: { xs: 'stretch', sm: 'center' },
            gap: { xs: 2, sm: 0 }
          }}>
            <FormControlLabel
              control={
                <Switch
                  checked={isAutoMode}
                  onChange={handleAutoModeToggle}
                  color="primary"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AutoMode fontSize="small" />
                  <Typography fontSize={{ xs: '0.875rem', sm: '1rem' }}>
                    Auto Recognition
                  </Typography>
                </Box>
              }
            />
            
            <Box sx={{ 
              display: 'flex', 
              gap: 1, 
              justifyContent: { xs: 'center', sm: 'flex-end' },
              flexWrap: 'wrap'
            }}>
              {isAutoMode && (
                <Chip 
                  label="Auto Mode Active" 
                  color="success" 
                  size="small"
                  icon={<CircularProgress size={12} color="inherit" />}
                />
              )}
              {isLoading && (
                <Chip 
                  label="Processing..." 
                  color="info" 
                  size="small"
                  icon={<CircularProgress size={12} color="inherit" />}
                />
              )}
            </Box>
          </Box>

          <Divider />

          {/* Camera */}
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Box sx={{ 
              position: 'relative', 
              borderRadius: 2, 
              overflow: 'hidden',
              maxWidth: { xs: '100%', sm: 400, md: 500 },
              width: '100%'
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
              {isLoading && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    bgcolor: 'rgba(0,0,0,0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <CircularProgress color="primary" size={40} />
                </Box>
              )}
            </Box>
          </Box>

          {/* Action Buttons */}
          <Box sx={{ 
            display: 'flex', 
            flexDirection: { xs: 'column', sm: 'row' },
            gap: 2, 
            justifyContent: 'center' 
          }}>
            {!isAutoMode && (
              <Button
                variant="contained"
                onClick={handleManualCapture}
                disabled={isLoading}
                startIcon={isLoading ? <CircularProgress size={20} /> : <CameraAlt />}
                sx={{ 
                  minWidth: { xs: '100%', sm: 160 },
                  py: { xs: 1.5, sm: 1 }
                }}
                size={window.innerWidth < 600 ? 'large' : 'medium'}
              >
                {isLoading ? 'Processing...' : 'Capture & Mark'}
              </Button>
            )}
            
            {(isCapturing || isAutoMode) && (
              <Button
                variant="outlined"
                onClick={handleStopCapture}
                startIcon={<Stop />}
                color="error"
                sx={{ 
                  minWidth: { xs: '100%', sm: 120 },
                  py: { xs: 1.5, sm: 1 }
                }}
                size={window.innerWidth < 600 ? 'large' : 'medium'}
              >
                Stop
              </Button>
            )}
          </Box>
        </Stack>
      </Card>

      {/* Results */}
      {error && (
        <Alert 
          severity="error" 
          icon={<ErrorOutline />}
          sx={{ mb: 2 }}
          onClose={() => setError(null)}
        >
          <Typography variant="body2" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
            {error}
          </Typography>
        </Alert>
      )}

      {lastResult && (
        <Alert 
          severity={lastResult.success ? "success" : lastResult.cooldown ? "info" : "warning"}
          icon={lastResult.success ? <CheckCircle /> : <ErrorOutline />}
          sx={{ mb: 2 }}
        >
          <Typography 
            variant="body1" 
            sx={{ 
              fontWeight: 500,
              fontSize: { xs: '0.875rem', sm: '1rem' }
            }}
          >
            {lastResult.success 
              ? `✅ Welcome, ${lastResult.name}! Attendance marked at ${new Date(lastResult.timestamp).toLocaleTimeString()}`
              : lastResult.cooldown 
                ? `⏱️ ${lastResult.message} ${lastResult.remaining_seconds ? `(${lastResult.remaining_seconds}s remaining)` : ''}`
                : `❌ ${lastResult.message || 'Face not recognized'}`
            }
          </Typography>
          {lastResult.confidence && (
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              Confidence: {(lastResult.confidence * 100).toFixed(1)}%
            </Typography>
          )}
        </Alert>
      )}

      {/* Instructions */}
      <Card sx={{ p: { xs: 1.5, sm: 2 }, bgcolor: 'grey.50' }}>
        <Typography 
          variant="body2" 
          color="text.secondary" 
          sx={{ 
            textAlign: 'center',
            fontSize: { xs: '0.75rem', sm: '0.875rem' },
            lineHeight: 1.4
          }}
        >
           <strong>How to use:</strong> Turn on Auto Recognition for continuous scanning, 
          or use manual capture for one-time recognition. Make sure your face is clearly visible and well-lit.
        </Typography>
      </Card>
    </Box>
  );
}

export default AttendanceCapture;
