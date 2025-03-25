import axios from 'axios';

// Get API URL from environment or use default
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Create axios instance with base URL and default headers
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add auth token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Authentication API functions
export const login = async (credentials) => {
  const response = await apiClient.post('/auth/login', credentials);
  return response.data;
};

export const logout = async () => {
  const response = await apiClient.post('/auth/logout');
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};

// Models API functions
export const getModels = async () => {
  const response = await apiClient.get('/models');
  return response.data;
};

export const getModel = async (id) => {
  const response = await apiClient.get(`/models/${id}`);
  return response.data;
};

export const createModel = async (modelData) => {
  const response = await apiClient.post('/models', modelData);
  return response.data;
};

export const updateModel = async (id, modelData) => {
  const response = await apiClient.put(`/models/${id}`, modelData);
  return response.data;
};

export const deleteModel = async (id) => {
  const response = await apiClient.delete(`/models/${id}`);
  return response.data;
};

// Elements API functions
export const getElements = async (modelId, filters = {}) => {
  const response = await apiClient.get(`/elements`, {
    params: {
      model_id: modelId,
      ...filters,
    },
  });
  return response.data;
};

export const getElement = async (id) => {
  const response = await apiClient.get(`/elements/${id}`);
  return response.data;
};

export const createElement = async (elementData) => {
  const response = await apiClient.post('/elements', elementData);
  return response.data;
};

export const updateElement = async (id, elementData) => {
  const response = await apiClient.put(`/elements/${id}`, elementData);
  return response.data;
};

export const deleteElement = async (id) => {
  const response = await apiClient.delete(`/elements/${id}`);
  return response.data;
};

// Relationships API functions
export const getRelationships = async (modelId, filters = {}) => {
  const response = await apiClient.get(`/relationships`, {
    params: {
      model_id: modelId,
      ...filters,
    },
  });
  return response.data;
};

export const getRelationship = async (id) => {
  const response = await apiClient.get(`/relationships/${id}`);
  return response.data;
};

export const createRelationship = async (relationshipData) => {
  const response = await apiClient.post('/relationships', relationshipData);
  return response.data;
};

export const updateRelationship = async (id, relationshipData) => {
  const response = await apiClient.put(`/relationships/${id}`, relationshipData);
  return response.data;
};

export const deleteRelationship = async (id) => {
  const response = await apiClient.delete(`/relationships/${id}`);
  return response.data;
};

// Visualization API functions
export const getVisualizations = async (modelId) => {
  const response = await apiClient.get(`/visualizations/model/${modelId}`);
  return response.data;
};

export const getVisualization = async (id) => {
  const response = await apiClient.get(`/visualizations/${id}`);
  return response.data;
};

export const getVisualizationData = async (id) => {
  const response = await apiClient.get(`/visualizations/${id}/data`);
  return response.data;
};

export const createVisualization = async (visualizationData) => {
  const response = await apiClient.post('/visualizations', visualizationData);
  return response.data;
};

export const updateVisualization = async (visualizationData) => {
  const { id, ...data } = visualizationData;
  const response = await apiClient.put(`/visualizations/${id}`, data);
  return response.data;
};

export const deleteVisualization = async (id) => {
  const response = await apiClient.delete(`/visualizations/${id}`);
  return response.data;
};

export const exportVisualization = async (id, format) => {
  const response = await apiClient.get(`/visualizations/${id}/export`, {
    params: { format },
    responseType: 'blob', // Important: This tells axios to handle the response as a binary blob
  });
  return response.data;
};

// Integration API functions
export const getIntegrationConfig = async (integrationType) => {
  const response = await apiClient.get(`/integrations/${integrationType}/config`);
  return response.data;
};

export const updateIntegrationConfig = async (integrationType, configData) => {
  const response = await apiClient.put(`/integrations/${integrationType}/config`, configData);
  return response.data;
};

export const testIntegration = async (integrationType, configData) => {
  const response = await apiClient.post(`/integrations/${integrationType}/test`, configData);
  return response.data;
};

export const syncIntegration = async (integrationType) => {
  const response = await apiClient.post(`/integrations/${integrationType}/sync`);
  return response.data;
};

// GenAI API functions
export const generateDocumentation = async (params) => {
  const response = await apiClient.post('/genai/generate-documentation', params);
  return response.data;
};

export const analyzeImpact = async (params) => {
  const response = await apiClient.post('/genai/analyze-impact', params);
  return response.data;
};

export const recognizePatterns = async (params) => {
  const response = await apiClient.post('/genai/recognize-patterns', params);
  return response.data;
};

export const suggestImprovements = async (params) => {
  const response = await apiClient.post('/genai/suggest-improvements', params);
  return response.data;
};

// Error handler
export const handleApiError = (error) => {
  let errorMessage = 'An unexpected error occurred';

  if (error.response) {
    // The request was made and the server responded with a status code
    // that falls out of the range of 2xx
    const data = error.response.data;
    errorMessage = data.detail || data.message || String(data);
  } else if (error.request) {
    // The request was made but no response was received
    errorMessage = 'No response received from server';
  } else {
    // Something happened in setting up the request that triggered an Error
    errorMessage = error.message;
  }

  return errorMessage;
};

export default apiClient;
