import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Tabs,
  Tab,
  ThemeProvider,
  createTheme,
  CssBaseline,
  Paper,
  Badge,
  IconButton,
  Menu,
  MenuItem,
  Tooltip
} from '@mui/material';
import { 
  CameraAlt, 
  PersonAdd, 
  List, 
  People,
  Assessment,
  Settings as SettingsIcon,
  Notifications,
  MoreVert
} from '@mui/icons-material';
import AttendanceCapture from './components/AttendanceCapture';
import AddPerson from './components/AddPerson';
import AttendanceView from './components/AttendanceView';
import KnownFaces from './components/KnownFaces';
import Reports from './components/Reports';
import Settings from './components/Settings';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#4caf50',
    },
    background: {
      default: '#f8fafc',
    },
  },
  typography: {
    fontFamily: '"Inter", "Segoe UI", "Roboto", sans-serif',
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      xl: 1536,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiContainer: {
      styleOverrides: {
        root: {
          paddingLeft: 8,
          paddingRight: 8,
          '@media (min-width: 600px)': {
            paddingLeft: 16,
            paddingRight: 16,
          },
        },
      },
    },
  },
});

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: { xs: 2, sm: 3 }, px: { xs: 1, sm: 2, md: 3 } }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function App() {
  const [tabValue, setTabValue] = useState(0);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notifications] = useState(3); // Mock notification count

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const tabLabels = [
    { icon: <CameraAlt />, label: 'Mark Attendance', shortLabel: 'Attendance' },
    { icon: <PersonAdd />, label: 'Add Person', shortLabel: 'Add' },
    { icon: <List />, label: 'View Records', shortLabel: 'Records' },
    { icon: <People />, label: 'Manage People', shortLabel: 'People' },
    { icon: <Assessment />, label: 'Reports', shortLabel: 'Reports' },
    { icon: <SettingsIcon />, label: 'Settings', shortLabel: 'Settings' }
  ];

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
        <AppBar position="static" elevation={0} sx={{ bgcolor: 'white', color: 'text.primary' }}>
          <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1, sm: 2 }, flex: 1 }}>
              <Box
                sx={{
                  width: { xs: 32, sm: 40 },
                  height: { xs: 32, sm: 40 },
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <CameraAlt sx={{ color: 'white', fontSize: { xs: 18, sm: 24 } }} />
              </Box>
              <Typography 
                variant="h6" 
                component="div" 
                sx={{ 
                  fontWeight: 600,
                  fontSize: { xs: '1rem', sm: '1.25rem' },
                  display: { xs: 'none', sm: 'block' }
                }}
              >
                Smart Attendance System
              </Typography>
              <Typography 
                variant="h6" 
                component="div" 
                sx={{ 
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  display: { xs: 'block', sm: 'none' }
                }}
              >
                Attendance
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 0.5, sm: 1 } }}>
              <Tooltip title="Notifications">
                <IconButton color="inherit" size={window.innerWidth < 600 ? 'small' : 'medium'}>
                  <Badge badgeContent={notifications} color="error">
                    <Notifications />
                  </Badge>
                </IconButton>
              </Tooltip>
              
              <Tooltip title="More options">
                <IconButton 
                  color="inherit" 
                  onClick={handleMenuClick}
                  size={window.innerWidth < 600 ? 'small' : 'medium'}
                >
                  <MoreVert />
                </IconButton>
              </Tooltip>
              
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
              >
                <MenuItem onClick={handleMenuClose}>About</MenuItem>
                <MenuItem onClick={handleMenuClose}>Help</MenuItem>
                <MenuItem onClick={handleMenuClose}>Feedback</MenuItem>
              </Menu>
            </Box>
          </Toolbar>
        </AppBar>

        <Container maxWidth="lg" sx={{ py: { xs: 1, sm: 2, md: 3 } }}>
          <Paper elevation={1} sx={{ borderRadius: 2, overflow: 'hidden' }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs 
                value={tabValue} 
                onChange={handleTabChange} 
                variant="scrollable"
                scrollButtons="auto"
                allowScrollButtonsMobile
                sx={{
                  '& .MuiTab-root': {
                    fontWeight: 500,
                    textTransform: 'none',
                    fontSize: { xs: '0.75rem', sm: '0.875rem', md: '0.9rem' },
                    py: { xs: 1, sm: 2 },
                    minHeight: { xs: 48, sm: 60 },
                    minWidth: { xs: 80, sm: 120 },
                    '& .MuiTab-iconWrapper': {
                      marginBottom: { xs: '2px', sm: '4px' },
                    },
                  },
                  '& .MuiTabs-scrollButtons': {
                    '&.Mui-disabled': {
                      opacity: 0.3,
                    },
                  },
                }}
              >
                {tabLabels.map((tab, index) => (
                  <Tab 
                    key={index} 
                    icon={tab.icon} 
                    label={
                      <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
                        {tab.label}
                      </Box>
                    }
                    aria-label={tab.label}
                  />
                ))}
              </Tabs>
            </Box>

            <TabPanel value={tabValue} index={0}>
              <AttendanceCapture />
            </TabPanel>
            <TabPanel value={tabValue} index={1}>
              <AddPerson />
            </TabPanel>
            <TabPanel value={tabValue} index={2}>
              <AttendanceView />
            </TabPanel>
            <TabPanel value={tabValue} index={3}>
              <KnownFaces />
            </TabPanel>
            <TabPanel value={tabValue} index={4}>
              <Reports />
            </TabPanel>
            <TabPanel value={tabValue} index={5}>
              <Settings />
            </TabPanel>
          </Paper>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
