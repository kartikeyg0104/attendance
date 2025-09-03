import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  Slider,
  TextField,
  Button,
  Alert,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Save,
  VolumeUp,
  Security,
  Timer,
  Refresh
} from '@mui/icons-material';

interface SystemSettings {
  autoRecognition: boolean;
  soundEnabled: boolean;
  soundVolume: number;
  confidenceThreshold: number;
  attendanceCooldown: number;
  autoRefresh: boolean;
  refreshInterval: number;
  notifications: boolean;
  theme: 'light' | 'dark' | 'auto';
  language: string;
}

function Settings() {
  const [settings, setSettings] = useState<SystemSettings>({
    autoRecognition: true,
    soundEnabled: true,
    soundVolume: 80,
    confidenceThreshold: 0.7,
    attendanceCooldown: 60,
    autoRefresh: true,
    refreshInterval: 30,
    notifications: true,
    theme: 'light',
    language: 'en'
  });
  
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [testAudio, setTestAudio] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = () => {
    try {
      const savedSettings = localStorage.getItem('attendanceSettings');
      if (savedSettings) {
        setSettings({ ...settings, ...JSON.parse(savedSettings) });
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = async () => {
    try {
      setSaveStatus('saving');
      localStorage.setItem('attendanceSettings', JSON.stringify(settings));
      
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (error) {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  };

  const resetSettings = () => {
    const defaultSettings: SystemSettings = {
      autoRecognition: true,
      soundEnabled: true,
      soundVolume: 80,
      confidenceThreshold: 0.7,
      attendanceCooldown: 60,
      autoRefresh: true,
      refreshInterval: 30,
      notifications: true,
      theme: 'light',
      language: 'en'
    };
    setSettings(defaultSettings);
  };

  const testAudioFunction = () => {
    setTestAudio(true);
    try {
      const audio = new Audio('http://localhost:5001/audio/attendance_marked.wav');
      audio.volume = settings.soundVolume / 100;
      audio.play().catch(console.error);
    } catch (error) {
      console.error('Failed to play test audio:', error);
    }
    setTimeout(() => setTestAudio(false), 2000);
  };

  const handleSettingChange = (key: keyof SystemSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
        <SettingsIcon />
        System Settings
      </Typography>

      {saveStatus === 'success' && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Settings saved successfully!
        </Alert>
      )}

      {saveStatus === 'error' && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to save settings. Please try again.
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Recognition Settings */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Security color="primary" />
              Recognition Settings
            </Typography>
            <Divider sx={{ mb: 3 }} />

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 3 }}>
              <Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.autoRecognition}
                      onChange={(e) => handleSettingChange('autoRecognition', e.target.checked)}
                    />
                  }
                  label="Auto Recognition Mode"
                />
                <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                  Automatically detect and mark attendance
                </Typography>
              </Box>

              <Box>
                <Typography gutterBottom>
                  Confidence Threshold: {(settings.confidenceThreshold * 100).toFixed(0)}%
                </Typography>
                <Slider
                  value={settings.confidenceThreshold * 100}
                  onChange={(_, value) => handleSettingChange('confidenceThreshold', (value as number) / 100)}
                  min={50}
                  max={95}
                  step={5}
                  marks
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${value}%`}
                />
                <Typography variant="body2" color="text.secondary">
                  Minimum confidence required for recognition
                </Typography>
              </Box>

              <Box>
                <TextField
                  fullWidth
                  label="Attendance Cooldown (seconds)"
                  type="number"
                  value={settings.attendanceCooldown}
                  onChange={(e) => handleSettingChange('attendanceCooldown', parseInt(e.target.value))}
                  InputProps={{
                    endAdornment: <Timer sx={{ color: 'text.secondary' }} />
                  }}
                  helperText="Minimum time between attendance marks for same person"
                />
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Audio Settings */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <VolumeUp color="primary" />
              Audio Settings
            </Typography>
            <Divider sx={{ mb: 3 }} />

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 3 }}>
              <Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.soundEnabled}
                      onChange={(e) => handleSettingChange('soundEnabled', e.target.checked)}
                    />
                  }
                  label="Enable Sound Notifications"
                />
                <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                  Play audio feedback for attendance actions
                </Typography>
              </Box>

              <Box>
                <Typography gutterBottom>
                  Volume: {settings.soundVolume}%
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Slider
                    value={settings.soundVolume}
                    onChange={(_, value) => handleSettingChange('soundVolume', value as number)}
                    min={0}
                    max={100}
                    step={10}
                    disabled={!settings.soundEnabled}
                    sx={{ flex: 1 }}
                  />
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={testAudioFunction}
                    disabled={!settings.soundEnabled || testAudio}
                  >
                    {testAudio ? 'Testing...' : 'Test'}
                  </Button>
                </Box>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* System Settings */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Refresh color="primary" />
              System Settings
            </Typography>
            <Divider sx={{ mb: 3 }} />

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 3 }}>
              <Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.autoRefresh}
                      onChange={(e) => handleSettingChange('autoRefresh', e.target.checked)}
                    />
                  }
                  label="Auto Refresh Data"
                />
                <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                  Automatically refresh attendance data
                </Typography>
              </Box>

              <Box>
                <TextField
                  fullWidth
                  label="Refresh Interval (seconds)"
                  type="number"
                  value={settings.refreshInterval}
                  onChange={(e) => handleSettingChange('refreshInterval', parseInt(e.target.value))}
                  disabled={!settings.autoRefresh}
                  helperText="How often to refresh data automatically"
                />
              </Box>

              <Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications}
                      onChange={(e) => handleSettingChange('notifications', e.target.checked)}
                    />
                  }
                  label="Browser Notifications"
                />
                <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                  Show browser notifications for events
                </Typography>
              </Box>

              <Box>
                <FormControl fullWidth>
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={settings.theme}
                    label="Theme"
                    onChange={(e) => handleSettingChange('theme', e.target.value)}
                  >
                    <MenuItem value="light">Light</MenuItem>
                    <MenuItem value="dark">Dark</MenuItem>
                    <MenuItem value="auto">Auto</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Current Configuration Summary */}
        <Card sx={{ bgcolor: 'grey.50' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Current Configuration
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              <Chip
                label={`Auto Recognition: ${settings.autoRecognition ? 'ON' : 'OFF'}`}
                color={settings.autoRecognition ? 'success' : 'default'}
                size="small"
              />
              <Chip
                label={`Sound: ${settings.soundEnabled ? 'ON' : 'OFF'}`}
                color={settings.soundEnabled ? 'success' : 'default'}
                size="small"
              />
              <Chip
                label={`Confidence: ${(settings.confidenceThreshold * 100).toFixed(0)}%`}
                color="primary"
                size="small"
              />
              <Chip
                label={`Cooldown: ${settings.attendanceCooldown}s`}
                color="primary"
                size="small"
              />
              <Chip
                label={`Auto Refresh: ${settings.autoRefresh ? 'ON' : 'OFF'}`}
                color={settings.autoRefresh ? 'success' : 'default'}
                size="small"
              />
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 4 }}>
        <Button
          variant="contained"
          size="large"
          onClick={saveSettings}
          disabled={saveStatus === 'saving'}
          startIcon={<Save />}
        >
          {saveStatus === 'saving' ? 'Saving...' : 'Save Settings'}
        </Button>
        
        <Button
          variant="outlined"
          size="large"
          onClick={resetSettings}
          disabled={saveStatus === 'saving'}
        >
          Reset to Defaults
        </Button>
      </Box>
    </Box>
  );
}

export default Settings;
