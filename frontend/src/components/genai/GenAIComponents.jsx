// GenAI Integration Components for Enterprise Architecture Solution

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  TextInput, 
  Textarea, 
  Select, 
  Spinner, 
  Toast,
  Badge
} from 'flowbite-react';
import { FiCpu, FiBook, FiActivity, FiTarget, FiSend, FiCheckCircle } from 'react-icons/fi';

import { useSupabaseClient } from '../../hooks/useSupabase';
import { useAuth } from '../../services/auth';

/**
 * GenAI Assistant component for Enterprise Architecture
 * This component integrates with the OpenAI Agents backend to provide
 * intelligent assistance for EA tasks.
 */
export const GenAIAssistant = () => {
  const [query, setQuery] = useState('');
  const [responses, setResponses] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const supabase = useSupabaseClient();
  const { user } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      setIsLoading(true);
      
      // Add user query to responses
      setResponses(prev => [...prev, { role: 'user', content: query }]);
      
      // Call backend API to process the request
      const { data, error } = await supabase.functions.invoke('ea-genai-assistant', {
        body: { query, userId: user?.id }
      });
      
      if (error) {
        throw new Error(error.message);
      }
      
      // Add assistant response
      setResponses(prev => [...prev, { 
        role: 'assistant', 
        content: data.response.final_output,
        fullResponse: data.response
      }]);
      
      // Clear the input
      setQuery('');
    } catch (error) {
      console.error('Error calling GenAI assistant:', error);
      setToastMessage(`Error: ${error.message}`);
      setShowToast(true);
    } finally {
      setIsLoading(false);
    }
  };

  // Scroll to bottom when responses update
  useEffect(() => {
    const messagesContainer = document.getElementById('messages-container');
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }, [responses]);

  return (
    <div className="h-full flex flex-col">
      <Card className="mb-4">
        <div className="flex items-center mb-4">
          <FiCpu className="mr-2 h-6 w-6 text-blue-600" />
          <h2 className="text-xl font-bold">Enterprise Architecture Assistant</h2>
        </div>
        <p className="text-gray-600 mb-2">
          Ask questions about your enterprise architecture, get recommendations, analyze impacts, and more.
        </p>
        <div className="flex flex-wrap gap-2">
          <Badge color="info" className="cursor-pointer" onClick={() => setQuery("What are best practices for data architecture?")}>
            Data Architecture Best Practices
          </Badge>
          <Badge color="success" className="cursor-pointer" onClick={() => setQuery("Analyze the impact of replacing our CRM system")}>
            Impact Analysis
          </Badge>
          <Badge color="warning" className="cursor-pointer" onClick={() => setQuery("Identify anti-patterns in our application architecture")}>
            Anti-Pattern Detection
          </Badge>
          <Badge color="purple" className="cursor-pointer" onClick={() => setQuery("Generate documentation for our business domain model")}>
            Documentation Generation
          </Badge>
        </div>
      </Card>
      
      <div 
        id="messages-container"
        className="flex-grow overflow-y-auto mb-4 bg-white rounded-lg border border-gray-200 p-4"
        style={{ maxHeight: 'calc(100vh - 400px)', minHeight: '300px' }}
      >
        {responses.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-500">
            <FiCpu className="h-10 w-10 mb-4" />
            <p>Ask the EA Assistant a question to get started</p>
          </div>
        ) : (
          responses.map((message, index) => (
            <div 
              key={index}
              className={`mb-4 p-3 rounded-lg ${
                message.role === 'user' 
                  ? 'bg-blue-50 ml-12' 
                  : 'bg-gray-50 mr-12'
              }`}
            >
              <div className="flex items-start">
                <div className={`rounded-full p-2 mr-3 ${
                  message.role === 'user' 
                    ? 'bg-blue-200' 
                    : 'bg-gray-200'
                }`}>
                  {message.role === 'user' ? 'You' : 'AI'}
                </div>
                <div className="whitespace-pre-line">{message.content}</div>
              </div>
            </div>
          ))
        )}
      </div>
      
      <form onSubmit={handleSubmit} className="mt-auto">
        <div className="flex">
          <TextInput
            className="flex-grow"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about enterprise architecture..."
            disabled={isLoading}
          />
          <Button 
            type="submit" 
            disabled={isLoading || !query.trim()}
            className="ml-2"
          >
            {isLoading ? <Spinner size="sm" /> : <FiSend />}
          </Button>
        </div>
      </form>
      
      {showToast && (
        <Toast className="fixed bottom-4 right-4" onClose={() => setShowToast(false)}>
          <div className="text-sm font-normal">{toastMessage}</div>
          <Toast.Toggle />
        </Toast>
      )}
    </div>
  );
};

/**
 * GenAI Documentation Generator component
 * Allows users to automatically generate documentation for EA artifacts
 */
export const DocumentationGenerator = () => {
  const [artifactType, setArtifactType] = useState('element');
  const [artifactId, setArtifactId] = useState('');
  const [format, setFormat] = useState('markdown');
  const [audience, setAudience] = useState('technical');
  const [includeDiagrams, setIncludeDiagrams] = useState(true);
  const [includeRelated, setIncludeRelated] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [documentation, setDocumentation] = useState(null);
  const [artifactOptions, setArtifactOptions] = useState([]);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const supabase = useSupabaseClient();

  // Load artifact options based on selected type
  useEffect(() => {
    const fetchArtifacts = async () => {
      try {
        let table;
        switch (artifactType) {
          case 'element':
            table = 'ea_elements';
            break;
          case 'model':
            table = 'ea_models';
            break;
          case 'view':
            table = 'ea_views';
            break;
          case 'domain':
            table = 'ea_domains';
            break;
          default:
            table = 'ea_elements';
        }
        
        const { data, error } = await supabase
          .from(table)
          .select('id, name')
          .order('name', { ascending: true });
          
        if (error) throw error;
        
        setArtifactOptions(data);
        if (data.length > 0) {
          setArtifactId(data[0].id);
        } else {
          setArtifactId('');
        }
      } catch (error) {
        console.error(`Error loading ${artifactType} options:`, error);
        setToastMessage(`Error loading options: ${error.message}`);
        setShowToast(true);
      }
    };
    
    fetchArtifacts();
  }, [artifactType, supabase]);

  const handleGenerate = async (e) => {
    e.preventDefault();
    try {
      setIsGenerating(true);
      
      // Call backend API to generate documentation
      const { data, error } = await supabase.functions.invoke('ea-documentation-generator', {
        body: {
          artifactType,
          artifactId,
          format,
          audience,
          includeDiagrams,
          includeRelated
        }
      });
      
      if (error) {
        throw new Error(error.message);
      }
      
      setDocumentation(data);
      setToastMessage('Documentation generated successfully!');
      setShowToast(true);
    } catch (error) {
      console.error('Error generating documentation:', error);
      setToastMessage(`Error: ${error.message}`);
      setShowToast(true);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!documentation) return;
    
    const fileExtension = format === 'markdown' ? 'md' : format;
    const fileName = `documentation_${artifactType}_${artifactId}.${fileExtension}`;
    const mimeTypes = {
      markdown: 'text/markdown',
      html: 'text/html',
      docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    };
    
    const blob = new Blob([documentation.content], { type: mimeTypes[format] });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full">
      <Card className="mb-4">
        <div className="flex items-center mb-4">
          <FiBook className="mr-2 h-6 w-6 text-green-600" />
          <h2 className="text-xl font-bold">Documentation Generator</h2>
        </div>
        <p className="text-gray-600">
          Automatically generate professional documentation for your enterprise architecture artifacts.
        </p>
      </Card>
      
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
        <Card className="md:col-span-2">
          <form onSubmit={handleGenerate} className="space-y-4">
            <div>
              <label htmlFor="artifactType" className="block mb-2 text-sm font-medium text-gray-900">
                Artifact Type
              </label>
              <Select 
                id="artifactType" 
                value={artifactType}
                onChange={(e) => setArtifactType(e.target.value)}
              >
                <option value="element">Element</option>
                <option value="model">Model</option>
                <option value="view">View</option>
                <option value="domain">Domain</option>
              </Select>
            </div>
            
            <div>
              <label htmlFor="artifactId" className="block mb-2 text-sm font-medium text-gray-900">
                Artifact
              </label>
              <Select 
                id="artifactId" 
                value={artifactId}
                onChange={(e) => setArtifactId(e.target.value)}
                disabled={artifactOptions.length === 0}
              >
                {artifactOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.name}
                  </option>
                ))}
              </Select>
            </div>
            
            <div>
              <label htmlFor="format" className="block mb-2 text-sm font-medium text-gray-900">
                Format
              </label>
              <Select 
                id="format" 
                value={format}
                onChange={(e) => setFormat(e.target.value)}
              >
                <option value="markdown">Markdown</option>
                <option value="html">HTML</option>
                <option value="docx">Word Document</option>
              </Select>
            </div>
            
            <div>
              <label htmlFor="audience" className="block mb-2 text-sm font-medium text-gray-900">
                Target Audience
              </label>
              <Select 
                id="audience" 
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
              >
                <option value="technical">Technical</option>
                <option value="business">Business</option>
                <option value="executive">Executive</option>
              </Select>
            </div>
            
            <div className="flex items-center space-x-2">
              <input
                id="includeDiagrams"
                type="checkbox"
                checked={includeDiagrams}
                onChange={(e) => setIncludeDiagrams(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <label htmlFor="includeDiagrams" className="text-sm font-medium text-gray-900">
                Include Diagrams
              </label>
            </div>
            
            <div className="flex items-center space-x-2">
              <input
                id="includeRelated"
                type="checkbox"
                checked={includeRelated}
                onChange={(e) => setIncludeRelated(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <label htmlFor="includeRelated" className="text-sm font-medium text-gray-900">
                Include Related Artifacts
              </label>
            </div>
            
            <Button 
              type="submit" 
              disabled={isGenerating || !artifactId}
              className="w-full"
            >
              {isGenerating ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  <FiBook className="mr-2" />
                  Generate Documentation
                </>
              )}
            </Button>
          </form>
        </Card>
        
        <Card className="md:col-span-3 max-h-96 overflow-y-auto">
          {documentation ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">Generated Documentation</h3>
                <Button size="sm" onClick={handleDownload}>
                  Download
                </Button>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg h-64 overflow-y-auto">
                <pre className="whitespace-pre-wrap font-mono text-sm">
                  {documentation.content}
                </pre>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-500">
              <FiBook className="h-10 w-10 mb-4" />
              <p>Generated documentation will appear here</p>
            </div>
          )}
        </Card>
      </div>
      
      {showToast && (
        <Toast className="fixed bottom-4 right-4" onClose={() => setShowToast(false)}>
          <div className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-green-100 text-green-500">
            <FiCheckCircle className="h-5 w-5" />
          </div>
          <div className="ml-3 text-sm font-normal">{toastMessage}</div>
          <Toast.Toggle />
        </Toast>
      )}
    </div>
  );
};

/**
 * Impact Analysis component
 * Allows users to analyze the impact of changes to EA elements
 */
export const ImpactAnalysis = () => {
  const [elementId, setElementId] = useState('');
  const [changeType, setChangeType] = useState('modify');
  const [changeDescription, setChangeDescription] = useState('');
  const [analysisDepth, setAnalysisDepth] = useState(2);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [elementOptions, setElementOptions] = useState([]);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const supabase = useSupabaseClient();

  // Load element options
  useEffect(() => {
    const fetchElements = async () => {
      try {
        const { data, error } = await supabase
          .from('ea_elements')
          .select('id, name, domain, type')
          .order('name', { ascending: true });
          
        if (error) throw error;
        
        setElementOptions(data);
        if (data.length > 0) {
          setElementId(data[0].id);
        }
      } catch (error) {
        console.error('Error loading elements:', error);
        setToastMessage(`Error loading elements: ${error.message}`);
        setShowToast(true);
      }
    };
    
    fetchElements();
  }, [supabase]);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!elementId || !changeDescription) return;
    
    try {
      setIsAnalyzing(true);
      
      // Call backend API to perform impact analysis
      const { data, error } = await supabase.functions.invoke('ea-impact-analysis', {
        body: {
          elementId,
          changeType,
          changeDescription,
          analysisDepth
        }
      });
      
      if (error) {
        throw new Error(error.message);
      }
      
      setAnalysisResult(data);
      setToastMessage('Impact analysis completed!');
      setShowToast(true);
    } catch (error) {
      console.error('Error performing impact analysis:', error);
      setToastMessage(`Error: ${error.message}`);
      setShowToast(true);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Get element name from ID
  const getElementName = (id) => {
    const element = elementOptions.find(el => el.id === id);
    return element ? element.name : 'Unknown';
  };

  // Get risk level color
  const getRiskColor = (level) => {
    switch (level) {
      case 'high': return 'text-red-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="flex flex-col h-full">
      <Card className="mb-4">
        <div className="flex items-center mb-4">
          <FiActivity className="mr-2 h-6 w-6 text-red-600" />
          <h2 className="text-xl font-bold">Impact Analysis</h2>
        </div>
        <p className="text-gray-600">
          Analyze the potential impact of changes to your enterprise architecture elements.
        </p>
      </Card>
      
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
        <Card className="md:col-span-2">
          <form onSubmit={handleAnalyze} className="space-y-4">
            <div>
              <label htmlFor="elementId" className="block mb-2 text-sm font-medium text-gray-900">
                Element to Change
              </label>
              <Select 
                id="elementId" 
                value={elementId}
                onChange={(e) => setElementId(e.target.value)}
                disabled={elementOptions.length === 0}
              >
                {elementOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.name} ({option.domain} - {option.type})
                  </option>
                ))}
              </Select>
            </div>
            
            <div>
              <label htmlFor="changeType" className="block mb-2 text-sm font-medium text-gray-900">
                Change Type
              </label>
              <Select 
                id="changeType" 
                value={changeType}
                onChange={(e) => setChangeType(e.target.value)}
              >
                <option value="add">Add new capabilities</option>
                <option value="modify">Modify existing capabilities</option>
                <option value="replace">Replace with new system</option>
                <option value="remove">Remove/Retire system</option>
              </Select>
            </div>
            
            <div>
              <label htmlFor="changeDescription" className="block mb-2 text-sm font-medium text-gray-900">
                Change Description
              </label>
              <Textarea
                id="changeDescription"
                value={changeDescription}
                onChange={(e) => setChangeDescription(e.target.value)}
                rows={4}
                placeholder="Describe the proposed changes..."
                required
              />
            </div>
            
            <div>
              <label htmlFor="analysisDepth" className="block mb-2 text-sm font-medium text-gray-900">
                Analysis Depth
              </label>
              <Select 
                id="analysisDepth" 
                value={analysisDepth}
                onChange={(e) => setAnalysisDepth(parseInt(e.target.value))}
              >
                <option value="1">Level 1 - Direct impacts only</option>
                <option value="2">Level 2 - Direct and indirect impacts</option>
                <option value="3">Level 3 - Comprehensive analysis</option>
              </Select>
            </div>
            
            <Button 
              type="submit" 
              disabled={isAnalyzing || !elementId || !changeDescription}
              className="w-full"
            >
              {isAnalyzing ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Analyzing...
                </>
              ) : (
                <>
                  <FiActivity className="mr-2" />
                  Analyze Impact
                </>
              )}
            </Button>
          </form>
        </Card>
        
        <Card className="md:col-span-3">
          {analysisResult ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">Impact Analysis Results</h3>
                <Badge 
                  color={
                    analysisResult.risk_level === 'high' ? 'failure' : 
                    analysisResult.risk_level === 'medium' ? 'warning' : 'success'
                  }
                >
                  {analysisResult.risk_level.toUpperCase()} RISK
                </Badge>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg overflow-y-auto max-h-80">
                <h4 className="font-medium mb-2">Summary</h4>
                <p className="mb-4">{analysisResult.analysis_text}</p>
                
                <h4 className="font-medium mb-2">Affected Elements ({analysisResult.affected_elements})</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left text-gray-500">
                    <thead className="text-xs text-gray-700 uppercase bg-gray-100">
                      <tr>
                        <th className="px-4 py-2">Element</th>
                        <th className="px-4 py-2">Impact Level</th>
                        <th className="px-4 py-2">Risk</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(analysisResult.risk_scores).map(([id, score]) => (
                        <tr key={id} className="border-b">
                          <td className="px-4 py-2">{score.element_name}</td>
                          <td className="px-4 py-2">{score.impact_level}</td>
                          <td className={`px-4 py-2 ${getRiskColor(score.risk_level)}`}>
                            {score.risk_level.toUpperCase()} ({score.risk_score})
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-500">
              <FiActivity className="h-10 w-10 mb-4" />
              <p>Impact analysis results will appear here</p>
            </div>
          )}
        </Card>
      </div>
      
      {showToast && (
        <Toast className="fixed bottom-4 right-4" onClose={() => setShowToast(false)}>
          <div className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-green-100 text-green-500">
            <FiCheckCircle className="h-5 w-5" />
          </div>
          <div className="ml-3 text-sm font-normal">{toastMessage}</div>
          <Toast.Toggle />
        </Toast>
      )}
    </div>
  );
};

/**
 * Pattern Recognition component
 * Identifies patterns and anti-patterns in the EA repository
 */
export const PatternRecognition = () => {
  const [modelId, setModelId] = useState('');
  const [domain, setDomain] = useState('all');
  const [patternTypes, setPatternTypes] = useState(['best_practice', 'anti_pattern', 'optimization']);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [modelOptions, setModelOptions] = useState([]);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const supabase = useSupabaseClient();

  // Load model options
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const { data, error } = await supabase
          .from('ea_models')
          .select('id, name')
          .order('name', { ascending: true });
          
        if (error) throw error;
        
        setModelOptions(data);
        if (data.length > 0) {
          setModelId(data[0].id);
        }
      } catch (error) {
        console.error('Error loading models:', error);
        setToastMessage(`Error loading models: ${error.message}`);
        setShowToast(true);
      }
    };
    
    fetchModels();
  }, [supabase]);

  const handlePatternTypeChange = (type) => {
    if (patternTypes.includes(type)) {
      setPatternTypes(patternTypes.filter(t => t !== type));
    } else {
      setPatternTypes([...patternTypes, type]);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!modelId || patternTypes.length === 0) return;
    
    try {
      setIsAnalyzing(true);
      
      // Call backend API to perform pattern recognition
      const { data, error } = await supabase.functions.invoke('ea-pattern-recognition', {
        body: {
          modelId,
          domain,
          patternTypes
        }
      });
      
      if (error) {
        throw new Error(error.message);
      }
      
      setAnalysisResult(data);
      setToastMessage('Pattern analysis completed!');
      setShowToast(true);
    } catch (error) {
      console.error('Error performing pattern recognition:', error);
      setToastMessage(`Error: ${error.message}`);
      setShowToast(true);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Get pattern type display name
  const getPatternTypeDisplay = (type) => {
    switch (type) {
      case 'best_practice': return 'Best Practices';
      case 'anti_pattern': return 'Anti-Patterns';
      case 'optimization': return 'Optimization Opportunities';
      case 'security': return 'Security Patterns';
      case 'integration': return 'Integration Patterns';
      default: return type;
    }
  };

  // Get pattern type color
  const getPatternTypeColor = (type) => {
    switch (type) {
      case 'best_practice': return 'bg-green-100 text-green-800';
      case 'anti_pattern': return 'bg-red-100 text-red-800';
      case 'optimization': return 'bg-blue-100 text-blue-800';
      case 'security': return 'bg-purple-100 text-purple-800';
      case 'integration': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="flex flex-col h-full">
      <Card className="mb-4">
        <div className="flex items-center mb-4">
          <FiTarget className="mr-2 h-6 w-6 text-purple-600" />
          <h2 className="text-xl font-bold">Pattern Recognition</h2>
        </div>
        <p className="text-gray-600">
          Identify architecture patterns, anti-patterns, and optimization opportunities in your EA models.
        </p>
      </Card>
      
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
        <Card className="md:col-span-2">
          <form onSubmit={handleAnalyze} className="space-y-4">
            <div>
              <label htmlFor="modelId" className="block mb-2 text-sm font-medium text-gray-900">
                Model to Analyze
              </label>
              <Select 
                id="modelId" 
                value={modelId}
                onChange={(e) => setModelId(e.target.value)}
                disabled={modelOptions.length === 0}
              >
                {modelOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.name}
                  </option>
                ))}
              </Select>
            </div>
            
            <div>
              <label htmlFor="domain" className="block mb-2 text-sm font-medium text-gray-900">
                Domain Filter
              </label>
              <Select 
                id="domain" 
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
              >
                <option value="all">All Domains</option>
                <option value="business">Business</option>
                <option value="data">Data</option>
                <option value="application">Application</option>
                <option value="technology">Technology</option>
                <option value="performance">Performance</option>
              </Select>
            </div>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">
                Pattern Types to Identify
              </label>
              <div className="space-y-2">
                {['best_practice', 'anti_pattern', 'optimization', 'security', 'integration'].map((type) => (
                  <div key={type} className="flex items-center">
                    <input
                      id={`pattern-${type}`}
                      type="checkbox"
                      checked={patternTypes.includes(type)}
                      onChange={() => handlePatternTypeChange(type)}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                    <label htmlFor={`pattern-${type}`} className="ml-2 text-sm font-medium text-gray-900">
                      {getPatternTypeDisplay(type)}
                    </label>
                  </div>
                ))}
              </div>
            </div>
            
            <Button 
              type="submit" 
              disabled={isAnalyzing || !modelId || patternTypes.length === 0}
              className="w-full"
            >
              {isAnalyzing ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Analyzing...
                </>
              ) : (
                <>
                  <FiTarget className="mr-2" />
                  Identify Patterns
                </>
              )}
            </Button>
          </form>
        </Card>
        
        <Card className="md:col-span-3">
          {analysisResult ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">Pattern Analysis Results</h3>
                <Badge color="info">
                  {analysisResult.pattern_count} PATTERNS FOUND
                </Badge>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg overflow-y-auto max-h-96">
                {patternTypes.map((type) => (
                  analysisResult.patterns[type] && analysisResult.patterns[type].length > 0 ? (
                    <div key={type} className="mb-6">
                      <h4 className="font-medium mb-2">{getPatternTypeDisplay(type)}</h4>
                      <div className="space-y-3">
                        {analysisResult.patterns[type].map((pattern, index) => (
                          <div key={index} className="bg-white p-3 rounded border">
                            <div className="flex items-center mb-2">
                              <span className={`text-xs font-semibold px-2 py-1 rounded ${getPatternTypeColor(type)}`}>
                                {type.replace('_', ' ')}
                              </span>
                              <h5 className="ml-2 font-medium">{pattern.name}</h5>
                            </div>
                            <p className="text-sm">{pattern.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null
                ))}
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-500">
              <FiTarget className="h-10 w-10 mb-4" />
              <p>Pattern analysis results will appear here</p>
            </div>
          )}
        </Card>
      </div>
      
      {showToast && (
        <Toast className="fixed bottom-4 right-4" onClose={() => setShowToast(false)}>
          <div className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-green-100 text-green-500">
            <FiCheckCircle className="h-5 w-5" />
          </div>
          <div className="ml-3 text-sm font-normal">{toastMessage}</div>
          <Toast.Toggle />
        </Toast>
      )}
    </div>
  );
};

// Main GenAI Features container component
export const GenAIFeaturesContainer = () => {
  const [activeTab, setActiveTab] = useState('assistant');
  
  const tabs = [
    { id: 'assistant', label: 'AI Assistant', icon: <FiCpu className="mr-2" /> },
    { id: 'documentation', label: 'Documentation', icon: <FiBook className="mr-2" /> },
    { id: 'impact', label: 'Impact Analysis', icon: <FiActivity className="mr-2" /> },
    { id: 'patterns', label: 'Patterns', icon: <FiTarget className="mr-2" /> }
  ];
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">GenAI-Powered Enterprise Architecture Tools</h1>
      
      <div className="flex mb-4 overflow-x-auto">
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            color={activeTab === tab.id ? "primary" : "gray"}
            className="mr-2 whitespace-nowrap"
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon}
            {tab.label}
          </Button>
        ))}
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-4 min-h-screen">
        {activeTab === 'assistant' && <GenAIAssistant />}
        {activeTab === 'documentation' && <DocumentationGenerator />}
        {activeTab === 'impact' && <ImpactAnalysis />}
        {activeTab === 'patterns' && <PatternRecognition />}
      </div>
    </div>
  );
};

export default GenAIFeaturesContainer;
