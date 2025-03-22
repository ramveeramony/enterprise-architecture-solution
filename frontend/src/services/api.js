import axios from 'axios';
import { createClient } from '@supabase/supabase-js';

// Create Supabase client
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;
export const supabase = createClient(supabaseUrl, supabaseKey);

// Create axios instance for API requests
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
api.interceptors.request.use(
  async (config) => {
    // Get the current session
    const { data } = await supabase.auth.getSession();
    const session = data.session;

    // If we have a session, add the token to the request
    if (session) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Model related API calls
export const modelApi = {
  // Get all models
  getModels: async (params = {}) => {
    try {
      const { data } = await api.get('/api/models', { params });
      return data;
    } catch (error) {
      console.error('Error fetching models:', error);
      throw error;
    }
  },

  // Get model by ID
  getModel: async (id) => {
    try {
      const { data } = await api.get(`/api/models/${id}`);
      return data;
    } catch (error) {
      console.error(`Error fetching model ${id}:`, error);
      throw error;
    }
  },

  // Create new model
  createModel: async (modelData) => {
    try {
      const { data } = await api.post('/api/models', modelData);
      return data;
    } catch (error) {
      console.error('Error creating model:', error);
      throw error;
    }
  },

  // Update model
  updateModel: async (id, modelData) => {
    try {
      const { data } = await api.put(`/api/models/${id}`, modelData);
      return data;
    } catch (error) {
      console.error(`Error updating model ${id}:`, error);
      throw error;
    }
  },

  // Delete model
  deleteModel: async (id) => {
    try {
      const { data } = await api.delete(`/api/models/${id}`);
      return data;
    } catch (error) {
      console.error(`Error deleting model ${id}:`, error);
      throw error;
    }
  },
};

// Element related API calls
export const elementApi = {
  // Get all elements for a model
  getElements: async (modelId, params = {}) => {
    try {
      const { data } = await api.get(`/api/models/${modelId}/elements`, { params });
      return data;
    } catch (error) {
      console.error(`Error fetching elements for model ${modelId}:`, error);
      throw error;
    }
  },

  // Get element by ID
  getElement: async (id) => {
    try {
      const { data } = await api.get(`/api/elements/${id}`);
      return data;
    } catch (error) {
      console.error(`Error fetching element ${id}:`, error);
      throw error;
    }
  },

  // Create new element
  createElement: async (modelId, elementData) => {
    try {
      const { data } = await api.post(`/api/models/${modelId}/elements`, elementData);
      return data;
    } catch (error) {
      console.error('Error creating element:', error);
      throw error;
    }
  },

  // Update element
  updateElement: async (id, elementData) => {
    try {
      const { data } = await api.put(`/api/elements/${id}`, elementData);
      return data;
    } catch (error) {
      console.error(`Error updating element ${id}:`, error);
      throw error;
    }
  },

  // Delete element
  deleteElement: async (id) => {
    try {
      const { data } = await api.delete(`/api/elements/${id}`);
      return data;
    } catch (error) {
      console.error(`Error deleting element ${id}:`, error);
      throw error;
    }
  },
};

// Integration related API calls
export const integrationApi = {
  // Get all integration configurations
  getIntegrations: async () => {
    try {
      const { data } = await api.get('/api/integrations');
      return data;
    } catch (error) {
      console.error('Error fetching integrations:', error);
      throw error;
    }
  },

  // Get integration by ID
  getIntegration: async (id) => {
    try {
      const { data } = await api.get(`/api/integrations/${id}`);
      return data;
    } catch (error) {
      console.error(`Error fetching integration ${id}:`, error);
      throw error;
    }
  },

  // Configure integration
  configureIntegration: async (type, configData) => {
    try {
      const { data } = await api.post(`/api/integrations/${type}/configure`, configData);
      return data;
    } catch (error) {
      console.error(`Error configuring ${type} integration:`, error);
      throw error;
    }
  },

  // Test integration
  testIntegration: async (id) => {
    try {
      const { data } = await api.post(`/api/integrations/${id}/test`);
      return data;
    } catch (error) {
      console.error(`Error testing integration ${id}:`, error);
      throw error;
    }
  },

  // Run integration sync
  syncIntegration: async (id) => {
    try {
      const { data } = await api.post(`/api/integrations/${id}/sync`);
      return data;
    } catch (error) {
      console.error(`Error syncing integration ${id}:`, error);
      throw error;
    }
  },
};

// GenAI related API calls
export const genAiApi = {
  // Get AI suggestions for an element
  getSuggestions: async (elementId) => {
    try {
      const { data } = await api.get(`/api/genai/suggestions/element/${elementId}`);
      return data;
    } catch (error) {
      console.error(`Error getting suggestions for element ${elementId}:`, error);
      throw error;
    }
  },

  // Generate documentation
  generateDocumentation: async (params) => {
    try {
      const { data } = await api.post('/api/genai/documentation', params);
      return data;
    } catch (error) {
      console.error('Error generating documentation:', error);
      throw error;
    }
  },

  // Analyze impact
  analyzeImpact: async (params) => {
    try {
      const { data } = await api.post('/api/genai/impact-analysis', params);
      return data;
    } catch (error) {
      console.error('Error analyzing impact:', error);
      throw error;
    }
  },

  // Recognize patterns
  recognizePatterns: async (modelId, params = {}) => {
    try {
      const { data } = await api.post(`/api/genai/pattern-recognition/${modelId}`, params);
      return data;
    } catch (error) {
      console.error(`Error recognizing patterns for model ${modelId}:`, error);
      throw error;
    }
  },
};