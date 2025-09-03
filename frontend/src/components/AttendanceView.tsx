import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  CircularProgress,
  Button
} from '@mui/material';
import { CheckCircle, AccessTime, Download } from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5001';

interface AttendanceRecord {
  name: string;
  date: string;
  time: string;
  confidence: number;
}

function AttendanceView() {
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAttendanceRecords();
  }, []);

  const fetchAttendanceRecords = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await axios.get(`${API_BASE_URL}/attendance-records`);
      setRecords(response.data.records || []);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch attendance records');
    } finally {
      setIsLoading(false);
    }
  };

  const downloadExcel = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/download-attendance`, {
        responseType: 'blob'
      });
      
      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Get filename from response headers or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'attendance_records.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to download attendance records');
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ maxWidth: 800, mx: 'auto', textAlign: 'center', py: 4 }}>
        <CircularProgress size={40} />
        <Typography variant="body1" sx={{ mt: 2 }}>Loading attendance records...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
           Attendance Records
        </Typography>
        
        {records.length > 0 && (
          <Button
            variant="contained"
            startIcon={<Download />}
            onClick={downloadExcel}
            sx={{ minWidth: 'auto' }}
          >
            Download Excel
          </Button>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card sx={{ p: 3 }}>
        {records.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body1" color="text.secondary">
              No attendance records found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Start marking attendance to see records here
            </Typography>
          </Box>
        ) : (
          <>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">
                Total Records: {records.length}
              </Typography>
              <Chip 
                label={`Today: ${records.filter(r => r.date === new Date().toLocaleDateString()).length}`}
                color="primary" 
                size="small"
              />
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow sx={{ bgcolor: 'grey.50' }}>
                    <TableCell sx={{ fontWeight: 600 }}>Name</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Date</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Time</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Confidence</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {records.map((record, index) => (
                    <TableRow key={index} hover>
                      <TableCell sx={{ fontWeight: 500 }}>
                        {record.name}
                      </TableCell>
                      <TableCell>
                        {record.date}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <AccessTime fontSize="small" color="primary" />
                          {record.time}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={`${(record.confidence * 100).toFixed(1)}%`}
                          color={record.confidence > 0.7 ? "success" : "warning"}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          icon={<CheckCircle />}
                          label="Present" 
                          color="success" 
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </Card>

      {/* Summary */}
      <Card sx={{ p: 2, bgcolor: 'grey.50', mt: 2 }}>
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
          <strong>Summary:</strong> Attendance records are automatically saved when faces are recognized. 
          Records include confidence scores for verification purposes.
        </Typography>
      </Card>
    </Box>
  );
}

export default AttendanceView;
