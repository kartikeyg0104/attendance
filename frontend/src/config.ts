// API Configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 
  (process.env.NODE_ENV === 'production' 
    ? 'https://attendance-backend-y0rt.onrender.com'
    : 'http://localhost:5002');

export const AUDIO_BASE_URL = `${API_BASE_URL}/audio`;
export const IMAGES_BASE_URL = `${API_BASE_URL}/images`;

// Debug logging
console.log('Environment:', process.env.NODE_ENV);
console.log('API_BASE_URL:', API_BASE_URL);
console.log('REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
