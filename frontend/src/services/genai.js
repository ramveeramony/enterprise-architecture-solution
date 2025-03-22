/**
 * Enterprise Architecture Solution - GenAI Service
 * 
 * This module provides functions for interacting with the GenAI API endpoints.
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Create an API client with proper headers
 * @returns {Object} Axios instance
 */
const createApiClient = () => {
  const token = localStorage.getItem('auth_token');
  
  return axios.create({
    baseURL: `${API_URL}/api/genai`,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
    },
  });
};

/**
 * Generate documentation for an EA artifact
 * @param {Object} params - Documentation parameters
 * @param {string} params.contentType - Type of content (element, model, view, policy)
 * @param {string} params.contentId - UUID of the content
 * @param {string} params.format - Output format (markdown, html, docx)
 * @param {boolean} params.includeDiagrams - Whether to include diagrams
 * @param {boolean} params.includeRelationships - Whether to include relationships
 * @param {string} params.style - Style of documentation (technical, business, executive)
 * @returns {Promise<Object>} Generated documentation and metadata
 */
export const generateDocumentation = async ({
  contentType, 
  contentId, 
  format = 'markdown',
  includeDiagrams = true,
  includeRelationships = true,
  style = 'technical'
}) => {
  try {
    const apiClient = createApiClient();
    const response = await apiClient.post('/documentation', {
      content_type: contentType,
      content_id: contentId,
      format,
      include_diagrams: includeDiagrams,
      include_relationships: includeRelationships,
      style
    });
    
    return response.data;
  } catch (error) {
    console.error('Error generating documentation:', error);
    throw error;
  }
};

/**
 * Analyze the impact of a proposed change to an architecture element
 * @param {Object} params - Impact analysis parameters
 * @param {string} params.elementId - UUID of the element being changed
 * @param {string} params.changeDescription - Description of the proposed change
 * @param {string} params.changeType - Type of change (modify, replace, remove)
 * @param {number} params.analysisDepth - Depth of impact analysis (1=direct, 2=indirect, 3=comprehensive)
 * @returns {Promise<Object>} Impact analysis results
 */
export const analyzeImpact = async ({
  elementId,
  changeDescription,
  changeType,
  analysisDepth = 2
}) => {
  try {
    const apiClient = createApiClient();
    const response = await apiClient.post('/impact-analysis', {
      element_id: elementId,
      change_description: changeDescription,
      change_type: changeType,
      analysis_depth: analysisDepth
    });
    
    return response.data;
  } catch (error) {
    console.error('Error analyzing impact:', error);
    throw error;
  }
};

/**
 * Recognize patterns in architecture elements
 * @param {Object} params - Pattern recognition parameters
 * @param {string} params.modelId - UUID of the model to analyze
 * @param {Array<string>} params.elementIds - Optional list of specific element IDs to analyze
 * @param {string} params.domainFilter - Optional domain to filter by
 * @param {Array<string>} params.patternTypes - Optional list of pattern types to look for
 * @returns {Promise<Object>} Recognized patterns
 */
export const recognizePatterns = async ({
  modelId,
  elementIds,
  domainFilter,
  patternTypes
}) => {
  try {
    const apiClient = createApiClient();
    const response = await apiClient.post('/pattern-recognition', {
      model_id: modelId,
      element_ids: elementIds,
      domain_filter: domainFilter,
      pattern_types: patternTypes
    });
    
    return response.data;
  } catch (error) {
    console.error('Error recognizing patterns:', error);
    throw error;
  }
};

/**
 * Run the EA Assistant with the given conversation
 * @param {Array<Object>} messages - List of conversation messages with role and content
 * @returns {Promise<Object>} Assistant's response
 */
export const runAssistant = async (messages) => {
  try {
    const apiClient = createApiClient();
    const response = await apiClient.post('/assistant', {
      messages: messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))
    });
    
    return response.data;
  } catch (error) {
    console.error('Error running assistant:', error);
    throw error;
  }
};

/**
 * Helper function to export GenAI services
 */
export default {
  generateDocumentation,
  analyzeImpact,
  recognizePatterns,
  runAssistant
};
