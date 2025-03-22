import React, { useState } from 'react';
import { Card, Button, Tabs, TextInput, Textarea, Select, Checkbox, Alert } from 'flowbite-react';
import { FiFileText, FiBarChart, FiGitPull, FiMessageSquare, FiInfo } from 'react-icons/fi';

import genaiService from '../../services/genai';

/**
 * GenAI Features component provides access to all GenAI capabilities
 * from a unified interface.
 */
const GenAIFeatures = () => {
  const [activeTab, setActiveTab] = useState('documentation');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  // Documentation form state
  const [docForm, setDocForm] = useState({
    contentType: 'element',
    contentId: '',
    format: 'markdown',
    includeDiagrams: true,
    includeRelationships: true,
    style: 'technical'
  });
  
  // Impact analysis form state
  const [impactForm, setImpactForm] = useState({
    elementId: '',
    changeDescription: '',
    changeType: 'modify',
    analysisDepth: 2
  });
  
  // Pattern recognition form state
  const [patternForm, setPatternForm] = useState({
    modelId: '',
    elementIds: '',
    domainFilter: '',
    patternTypes: ['best_practice', 'anti_pattern']
  });
  
  // Assistant form state
  const [assistantForm, setAssistantForm] = useState({
    message: ''
  });
  const [conversation, setConversation] = useState([
    { role: 'system', content: 'You are an Enterprise Architecture assistant.' }
  ]);
  
  // Handle documentation form changes
  const handleDocFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setDocForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  // Handle impact form changes
  const handleImpactFormChange = (e) => {
    const { name, value, type } = e.target;
    setImpactForm(prev => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value) : value
    }));
  };
  
  // Handle pattern form changes
  const handlePatternFormChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'patternTypes') {
      // Handle multiple select
      const options = e.target.options;
      const values = [];
      for (let i = 0; i < options.length; i++) {
        if (options[i].selected) {
          values.push(options[i].value);
        }
      }
      setPatternForm(prev => ({ ...prev, [name]: values }));
    } else if (name === 'elementIds') {
      // Convert comma-separated string to array when needed
      setPatternForm(prev => ({ ...prev, [name]: value }));
    } else {
      setPatternForm(prev => ({ ...prev, [name]: value }));
    }
  };
  
  // Handle assistant form changes
  const handleAssistantFormChange = (e) => {
    const { name, value } = e.target;
    setAssistantForm(prev => ({ ...prev, [name]: value }));
  };
  
  // Generate documentation
  const handleGenerateDocumentation = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const result = await genaiService.generateDocumentation({
        contentType: docForm.contentType,
        contentId: docForm.contentId,
        format: docForm.format,
        includeDiagrams: docForm.includeDiagrams,
        includeRelationships: docForm.includeRelationships,
        style: docForm.style
      });
      
      setResult(result);
    } catch (error) {
      console.error('Error generating documentation:', error);
      setError(error.response?.data?.detail || 'Error generating documentation');
    } finally {
      setLoading(false);
    }
  };
  
  // Analyze impact
  const handleAnalyzeImpact = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const result = await genaiService.analyzeImpact({
        elementId: impactForm.elementId,
        changeDescription: impactForm.changeDescription,
        changeType: impactForm.changeType,
        analysisDepth: impactForm.analysisDepth
      });
      
      setResult(result);
    } catch (error) {
      console.error('Error analyzing impact:', error);
      setError(error.response?.data?.detail || 'Error analyzing impact');
    } finally {
      setLoading(false);
    }
  };
  
  // Recognize patterns
  const handleRecognizePatterns = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      // Convert elementIds string to array if not empty
      const elementIds = patternForm.elementIds ? 
        patternForm.elementIds.split(',').map(id => id.trim()) : 
        undefined;
      
      const result = await genaiService.recognizePatterns({
        modelId: patternForm.modelId,
        elementIds,
        domainFilter: patternForm.domainFilter || undefined,
        patternTypes: patternForm.patternTypes
      });
      
      setResult(result);
    } catch (error) {
      console.error('Error recognizing patterns:', error);
      setError(error.response?.data?.detail || 'Error recognizing patterns');
    } finally {
      setLoading(false);
    }
  };
  
  // Send message to assistant
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!assistantForm.message.trim()) return;
    
    setLoading(true);
    setError(null);
    
    // Add user message to conversation
    const newMessage = { role: 'user', content: assistantForm.message };
    const updatedConversation = [...conversation, newMessage];
    setConversation(updatedConversation);
    
    try {
      const result = await genaiService.runAssistant(updatedConversation);
      
      // Add assistant response to conversation
      const assistantResponse = { role: 'assistant', content: result.result };
      setConversation([...updatedConversation, assistantResponse]);
      
      // Clear the form
      setAssistantForm({ message: '' });
    } catch (error) {
      console.error('Error running assistant:', error);
      setError(error.response?.data?.detail || 'Error running assistant');
    } finally {
      setLoading(false);
    }
  };
  
  // Reset everything
  const handleReset = () => {
    setResult(null);
    setError(null);
  };
  
  return (
    <div className="p-4">
      <Card>
        <div className="mb-4">
          <h2 className="text-2xl font-bold">GenAI Features</h2>
          <p className="text-gray-600">
            Access AI-powered capabilities for your Enterprise Architecture
          </p>
        </div>
        
        {error && (
          <Alert color="failure" className="mb-4">
            <div className="flex items-center gap-2">
              <FiInfo className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </Alert>
        )}
        
        <Tabs 
          aria-label="GenAI features"
          style="underline"
          className="mb-4"
          onActiveTabChange={tab => {
            setActiveTab(tab);
            setResult(null);
            setError(null);
          }}
        >
          <Tabs.Item 
            title="Documentation" 
            icon={FiFileText}
            active={activeTab === 'documentation'}
          >
            <form onSubmit={handleGenerateDocumentation}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <div className="mb-4">
                    <label htmlFor="contentType" className="block mb-2 text-sm font-medium text-gray-900">
                      Content Type
                    </label>
                    <Select 
                      id="contentType"
                      name="contentType"
                      value={docForm.contentType}
                      onChange={handleDocFormChange}
                      required
                    >
                      <option value="element">Element</option>
                      <option value="model">Model</option>
                      <option value="view">View</option>
                      <option value="policy">Policy</option>
                    </Select>
                  </div>
                  
                  <div className="mb-4">
                    <label htmlFor="contentId" className="block mb-2 text-sm font-medium text-gray-900">
                      Content ID
                    </label>
                    <TextInput
                      id="contentId"
                      name="contentId"
                      placeholder="Enter content ID"
                      value={docForm.contentId}
                      onChange={handleDocFormChange}
                      required
                    />
                  </div>
                  
                  <div className="mb-4">
                    <label htmlFor="format" className="block mb-2 text-sm font-medium text-gray-900">
                      Format
                    </label>
                    <Select 
                      id="format"
                      name="format"
                      value={docForm.format}
                      onChange={handleDocFormChange}
                    >
                      <option value="markdown">Markdown</option>
                      <option value="html">HTML</option>
                      <option value="docx">DOCX</option>
                    </Select>
                  </div>
                </div>
                
                <div>
                  <div className="mb-4">
                    <label htmlFor="style" className="block mb-2 text-sm font-medium text-gray-900">
                      Style
                    </label>
                    <Select 
                      id="style"
                      name="style"
                      value={docForm.style}
                      onChange={handleDocFormChange}
                    >
                      <option value="technical">Technical</option>
                      <option value="business">Business</option>
                      <option value="executive">Executive</option>
                    </Select>
                  </div>
                  
                  <div className="flex items-center mb-4">
                    <Checkbox
                      id="includeDiagrams"
                      name="includeDiagrams"
                      checked={docForm.includeDiagrams}
                      onChange={handleDocFormChange}
                    />
                    <label htmlFor="includeDiagrams" className="ml-2 text-sm font-medium text-gray-900">
                      Include Diagrams
                    </label>
                  </div>
                  
                  <div className="flex items-center mb-4">
                    <Checkbox
                      id="includeRelationships"
                      name="includeRelationships"
                      checked={docForm.includeRelationships}
                      onChange={handleDocFormChange}
                    />
                    <label htmlFor="includeRelationships" className="ml-2 text-sm font-medium text-gray-900">
                      Include Relationships
                    </label>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button 
                  color="light" 
                  onClick={handleReset}
                  disabled={loading}
                >
                  Reset
                </Button>
                <Button 
                  type="submit" 
                  color="blue"
                  isProcessing={loading}
                >
                  Generate Documentation
                </Button>
              </div>
            </form>
          </Tabs.Item>
          
          <Tabs.Item 
            title="Impact Analysis" 
            icon={FiBarChart}
            active={activeTab === 'impact'}
          >
            <form onSubmit={handleAnalyzeImpact}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <div className="mb-4">
                    <label htmlFor="elementId" className="block mb-2 text-sm font-medium text-gray-900">
                      Element ID
                    </label>
                    <TextInput
                      id="elementId"
                      name="elementId"
                      placeholder="Enter element ID"
                      value={impactForm.elementId}
                      onChange={handleImpactFormChange}
                      required
                    />
                  </div>
                  
                  <div className="mb-4">
                    <label htmlFor="changeType" className="block mb-2 text-sm font-medium text-gray-900">
                      Change Type
                    </label>
                    <Select 
                      id="changeType"
                      name="changeType"
                      value={impactForm.changeType}
                      onChange={handleImpactFormChange}
                    >
                      <option value="modify">Modify</option>
                      <option value="replace">Replace</option>
                      <option value="remove">Remove</option>
                    </Select>
                  </div>
                  
                  <div className="mb-4">
                    <label htmlFor="analysisDepth" className="block mb-2 text-sm font-medium text-gray-900">
                      Analysis Depth
                    </label>
                    <Select 
                      id="analysisDepth"
                      name="analysisDepth"
                      value={impactForm.analysisDepth}
                      onChange={handleImpactFormChange}
                    >
                      <option value={1}>1 - Direct impacts only</option>
                      <option value={2}>2 - Include indirect impacts</option>
                      <option value={3}>3 - Comprehensive analysis</option>
                    </Select>
                  </div>
                </div>
                
                <div>
                  <div className="mb-4">
                    <label htmlFor="changeDescription" className="block mb-2 text-sm font-medium text-gray-900">
                      Change Description
                    </label>
                    <Textarea
                      id="changeDescription"
                      name="changeDescription"
                      placeholder="Describe the proposed change"
                      value={impactForm.changeDescription}
                      onChange={handleImpactFormChange}
                      rows={5}
                      required
                    />
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button 
                  color="light" 
                  onClick={handleReset}
                  disabled={loading}
                >
                  Reset
                </Button>
                <Button 
                  type="submit" 
                  color="blue"
                  isProcessing={loading}
                >
                  Analyze Impact
                </Button>
              </div>
            </form>
          </Tabs.Item>
          
          <Tabs.Item 
            title="Pattern Recognition" 
            icon={FiGitPull}
            active={activeTab === 'patterns'}
          >
            <form onSubmit={handleRecognizePatterns}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <div className="mb-4">
                    <label htmlFor="modelId" className="block mb-2 text-sm font-medium text-gray-900">
                      Model ID
                    </label>
                    <TextInput
                      id="modelId"
                      name="modelId"
                      placeholder="Enter model ID"
                      value={patternForm.modelId}
                      onChange={handlePatternFormChange}
                      required
                    />
                  </div>
                  
                  <div className="mb-4">
                    <label htmlFor="elementIds" className="block mb-2 text-sm font-medium text-gray-900">
                      Element IDs (comma-separated, optional)
                    </label>
                    <TextInput
                      id="elementIds"
                      name="elementIds"
                      placeholder="id1, id2, id3"
                      value={patternForm.elementIds}
                      onChange={handlePatternFormChange}
                    />
                  </div>
                </div>
                
                <div>
                  <div className="mb-4">
                    <label htmlFor="domainFilter" className="block mb-2 text-sm font-medium text-gray-900">
                      Domain Filter (optional)
                    </label>
                    <Select 
                      id="domainFilter"
                      name="domainFilter"
                      value={patternForm.domainFilter}
                      onChange={handlePatternFormChange}
                    >
                      <option value="">All Domains</option>
                      <option value="performance">Performance</option>
                      <option value="business">Business</option>
                      <option value="services">Services</option>
                      <option value="data">Data</option>
                      <option value="technology">Technology</option>
                    </Select>
                  </div>
                  
                  <div className="mb-4">
                    <label htmlFor="patternTypes" className="block mb-2 text-sm font-medium text-gray-900">
                      Pattern Types
                    </label>
                    <Select 
                      id="patternTypes"
                      name="patternTypes"
                      value={patternForm.patternTypes}
                      onChange={handlePatternFormChange}
                      multiple
                      size={5}
                    >
                      <option value="best_practice">Best Practices</option>
                      <option value="anti_pattern">Anti-Patterns</option>
                      <option value="optimization">Optimization Opportunities</option>
                      <option value="security">Security Concerns</option>
                      <option value="integration">Integration Patterns</option>
                    </Select>
                    <p className="mt-1 text-sm text-gray-500">
                      Hold Ctrl/Cmd to select multiple
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button 
                  color="light" 
                  onClick={handleReset}
                  disabled={loading}
                >
                  Reset
                </Button>
                <Button 
                  type="submit" 
                  color="blue"
                  isProcessing={loading}
                >
                  Recognize Patterns
                </Button>
              </div>
            </form>
          </Tabs.Item>
          
          <Tabs.Item 
            title="EA Assistant" 
            icon={FiMessageSquare}
            active={activeTab === 'assistant'}
          >
            <div className="mb-4 bg-gray-50 p-4 rounded-lg h-64 overflow-y-auto">
              {conversation.filter(m => m.role !== 'system').map((message, index) => (
                <div 
                  key={index} 
                  className={`mb-4 ${message.role === 'user' ? 'text-right' : 'text-left'}`}
                >
                  <div 
                    className={`inline-block p-3 rounded-lg ${
                      message.role === 'user' 
                        ? 'bg-blue-500 text-white' 
                        : 'bg-gray-200 text-gray-900'
                    }`}
                  >
                    {message.content}
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="flex justify-center">
                  <div className="animate-pulse flex space-x-1">
                    <div className="h-2 w-2 bg-gray-500 rounded-full"></div>
                    <div className="h-2 w-2 bg-gray-500 rounded-full"></div>
                    <div className="h-2 w-2 bg-gray-500 rounded-full"></div>
                  </div>
                </div>
              )}
            </div>
            
            <form onSubmit={handleSendMessage} className="flex space-x-2">
              <div className="flex-grow">
                <TextInput
                  id="message"
                  name="message"
                  placeholder="Ask the EA Assistant a question..."
                  value={assistantForm.message}
                  onChange={handleAssistantFormChange}
                  required
                />
              </div>
              <Button 
                type="submit" 
                color="blue"
                isProcessing={loading}
              >
                Send
              </Button>
            </form>
          </Tabs.Item>
        </Tabs>
        
        {result && activeTab !== 'assistant' && (
          <div className="mt-6">
            <Card>
              <h3 className="text-xl font-semibold mb-2">Result</h3>
              
              {activeTab === 'documentation' && (
                <div>
                  <div className="mb-4">
                    <h4 className="font-medium text-gray-900">Documentation</h4>
                    <div className="mt-2 p-4 bg-gray-50 rounded-lg">
                      {result.documentation?.format === 'html' ? (
                        <div dangerouslySetInnerHTML={{ __html: result.documentation?.documentation }} />
                      ) : (
                        <pre className="whitespace-pre-wrap font-mono text-sm">{result.documentation?.documentation}</pre>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900">Metadata</h4>
                    <pre className="mt-2 p-4 bg-gray-50 rounded-lg whitespace-pre-wrap font-mono text-sm">
                      {JSON.stringify(result.metadata, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
              
              {activeTab === 'impact' && (
                <div>
                  {result.impact_analysis?.structured_analysis ? (
                    <div>
                      <div className="mb-4">
                        <h4 className="font-medium text-gray-900">Direct Impacts</h4>
                        <ul className="mt-2 list-disc list-inside">
                          {result.impact_analysis.structured_analysis.direct_impacts?.map((impact, index) => (
                            <li key={index} className="mb-1">
                              <span className="font-semibold">{impact.area}</span> ({impact.severity}): {impact.description}
                            </li>
                          ))}
                        </ul>
                      </div>
                      
                      <div className="mb-4">
                        <h4 className="font-medium text-gray-900">Risk Assessment</h4>
                        <div className="mt-2">
                          <p className="font-semibold">
                            Overall Risk: {result.impact_analysis.structured_analysis.risk_assessment?.overall_risk}
                          </p>
                          <p>{result.impact_analysis.structured_analysis.risk_assessment?.explanation}</p>
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-medium text-gray-900">Mitigation Strategies</h4>
                        <ul className="mt-2 list-disc list-inside">
                          {result.impact_analysis.structured_analysis.mitigation_strategies?.map((strategy, index) => (
                            <li key={index} className="mb-1">
                              <span className="font-semibold">{strategy.strategy}</span>: {strategy.description}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <pre className="whitespace-pre-wrap font-mono text-sm">
                        {result.impact_analysis?.text_analysis || JSON.stringify(result, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
              
              {activeTab === 'patterns' && (
                <div>
                  {result.patterns?.structured_patterns?.patterns ? (
                    <div>
                      {result.patterns.structured_patterns.patterns.map((pattern, index) => (
                        <div key={index} className="mb-4 p-4 border rounded-lg">
                          <h4 className="font-semibold text-lg">
                            {pattern.name}
                            <span className={`ml-2 text-sm px-2 py-1 rounded ${
                              pattern.is_positive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {pattern.type}
                            </span>
                          </h4>
                          
                          <p className="mt-2">{pattern.description}</p>
                          
                          {pattern.elements && pattern.elements.length > 0 && (
                            <div className="mt-2">
                              <p className="font-medium">Elements Involved:</p>
                              <ul className="list-disc list-inside">
                                {pattern.elements.map((element, i) => (
                                  <li key={i}>{element}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {pattern.recommendations && pattern.recommendations.length > 0 && (
                            <div className="mt-2">
                              <p className="font-medium">Recommendations:</p>
                              <ul className="list-disc list-inside">
                                {pattern.recommendations.map((rec, i) => (
                                  <li key={i}>{rec}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div>
                      <pre className="whitespace-pre-wrap font-mono text-sm">
                        {result.patterns?.text_analysis || JSON.stringify(result, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>
        )}
      </Card>
    </div>
  );
};

export default GenAIFeatures;
