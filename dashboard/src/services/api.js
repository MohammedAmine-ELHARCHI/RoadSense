import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || '';

const detectionAPI = axios.create({
  baseURL: `${API_BASE}/api/detection`,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

const severityAPI = axios.create({
  baseURL: `${API_BASE}/api/severity`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Detection Service APIs
export const detectDefects = async (imageFile) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  
  const response = await detectionAPI.post('/detect', formData);
  return response.data;
};

export const getDetectionModels = async () => {
  const response = await detectionAPI.get('/models');
  return response.data;
};

// Severity Service APIs
export const computeSeverity = async (features) => {
  const response = await severityAPI.post('/compute', features);
  return response.data;
};

export const getSeverityModelInfo = async () => {
  const response = await severityAPI.get('/model/info');
  return response.data;
};

// Mock data for development (when backend is not available)
export const getMockDetections = () => {
  return [
    {
      id: '1',
      type: 'D40',
      confidence: 0.95,
      bbox: [100, 100, 200, 200],
      severity: 9.5,
      severity_level: 'CRITICAL',
      timestamp: new Date().toISOString(),
      location: { lat: 33.5731, lng: -7.5898 }
    },
    {
      id: '2',
      type: 'D20',
      confidence: 0.88,
      bbox: [300, 150, 450, 280],
      severity: 8.5,
      severity_level: 'HIGH',
      timestamp: new Date().toISOString(),
      location: { lat: 33.5941, lng: -7.6028 }
    },
    {
      id: '3',
      type: 'D00',
      confidence: 0.82,
      bbox: [150, 250, 220, 320],
      severity: 6.5,
      severity_level: 'MEDIUM',
      timestamp: new Date().toISOString(),
      location: { lat: 33.5731, lng: -7.6118 }
    }
  ];
};

export default {
  detectDefects,
  getDetectionModels,
  computeSeverity,
  getSeverityModelInfo,
  getMockDetections
};
