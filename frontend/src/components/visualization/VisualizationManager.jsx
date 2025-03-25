import React, { useState, useEffect } from 'react';
import { Card, Button, Tabs, Dropdown, Spinner, Alert } from 'flowbite-react';
import { FiGrid, FiMap, FiCalendar, FiShare2, FiDownload, FiPlus } from 'react-icons/fi';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Import visualization components
import DiagramEditor from './DiagramEditor';
import MatrixEditor from './MatrixEditor';
import HeatmapEditor from './HeatmapEditor';
import RoadmapEditor from './RoadmapEditor';

// Import API services
import { getVisualizations, createVisualization, exportVisualization } from '../../services/api';

const VisualizationManager = ({ modelId }) => {
  const [activeTab, setActiveTab] = useState('diagram');
  const [selectedVisualization, setSelectedVisualization] = useState(null);
  const [showNewVisualizationForm, setShowNewVisualizationForm] = useState(false);
  const [exportFormat, setExportFormat] = useState('svg');
  
  const queryClient = useQueryClient();
  
  // Fetch visualizations for the model
  const { 
    data: visualizations, 
    isLoading: visualizationsLoading,
    error: visualizationsError
  } = useQuery({
    queryKey: ['visualizations', modelId],
    queryFn: () => getVisualizations(modelId)
  });
  
  // Create visualization mutation
  const createVisualizationMutation = useMutation({
    mutationFn: createVisualization,
    onSuccess: () => {
      queryClient.invalidateQueries(['visualizations', modelId]);
      setShowNewVisualizationForm(false);
    }
  });
  
  // Handle visualization selection
  useEffect(() => {
    if (visualizations && visualizations.length > 0 && !selectedVisualization) {
      // Auto-select first visualization by default
      setSelectedVisualization(visualizations[0]);
      // Set activeTab based on the selected visualization type
      setActiveTab(visualizations[0].visualization_type);
    }
  }, [visualizations, selectedVisualization]);
  
  // Handle create new visualization
  const handleCreateVisualization = (visualizationData) => {
    createVisualizationMutation.mutate({
      ...visualizationData,
      model_id: modelId
    });
  };
  
  // Handle export visualization
  const handleExportVisualization = async () => {
    if (!selectedVisualization) return;
    
    try {
      const blob = await exportVisualization(selectedVisualization.id, exportFormat);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${selectedVisualization.name}.${exportFormat}`;
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error exporting visualization:', error);
    }
  };
  
  if (visualizationsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="xl" />
      </div>
    );
  }
  
  if (visualizationsError) {
    return (
      <Alert color="failure">
        <p>Error loading visualizations: {visualizationsError.message}</p>
      </Alert>
    );
  }
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Visualizations</h2>
        <div className="flex space-x-2">
          <Dropdown
            label={
              <div className="flex items-center">
                <FiDownload className="mr-2" />
                Export
              </div>
            }
            disabled={!selectedVisualization}
          >
            <Dropdown.Item onClick={() => { setExportFormat('svg'); handleExportVisualization(); }}>
              SVG
            </Dropdown.Item>
            <Dropdown.Item onClick={() => { setExportFormat('png'); handleExportVisualization(); }}>
              PNG
            </Dropdown.Item>
            <Dropdown.Item onClick={() => { setExportFormat('pdf'); handleExportVisualization(); }}>
              PDF
            </Dropdown.Item>
            <Dropdown.Item onClick={() => { setExportFormat('visio'); handleExportVisualization(); }}>
              Microsoft Visio
            </Dropdown.Item>
          </Dropdown>
          
          <Button 
            color="blue" 
            onClick={() => setShowNewVisualizationForm(true)}
          >
            <FiPlus className="mr-2" />
            New Visualization
          </Button>
        </div>
      </div>
      
      {/* Visualization selector */}
      {visualizations && visualizations.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {visualizations.map((vis) => (
            <Card
              key={vis.id}
              className={`cursor-pointer hover:bg-gray-50 ${selectedVisualization?.id === vis.id ? 'ring-2 ring-blue-500' : ''}`}
              onClick={() => {
                setSelectedVisualization(vis);
                setActiveTab(vis.visualization_type);
              }}
            >
              <div className="flex items-center">
                {vis.visualization_type === 'diagram' && <FiShare2 className="mr-2 h-6 w-6 text-blue-600" />}
                {vis.visualization_type === 'matrix' && <FiGrid className="mr-2 h-6 w-6 text-green-600" />}
                {vis.visualization_type === 'heatmap' && <FiMap className="mr-2 h-6 w-6 text-red-600" />}
                {vis.visualization_type === 'roadmap' && <FiCalendar className="mr-2 h-6 w-6 text-purple-600" />}
                <div>
                  <h5 className="text-lg font-semibold">{vis.name}</h5>
                  <p className="text-sm text-gray-500">
                    Created {new Date(vis.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
      
      {/* No visualizations message */}
      {visualizations && visualizations.length === 0 && !showNewVisualizationForm && (
        <Card>
          <div className="text-center py-8">
            <h3 className="text-lg font-medium mb-2">No Visualizations Found</h3>
            <p className="text-gray-500 mb-4">
              Create your first visualization to start visualizing your architecture model.
            </p>
            <Button color="blue" onClick={() => setShowNewVisualizationForm(true)}>
              <FiPlus className="mr-2" />
              Create Visualization
            </Button>
          </div>
        </Card>
      )}
      
      {/* Visualization editor */}
      {selectedVisualization && !showNewVisualizationForm && (
        <Card>
          <Tabs.Group
            style="underline"
            value={activeTab}
            onValueChange={setActiveTab}
          >
            <Tabs.Item
              active={activeTab === 'diagram'}
              title="Diagram"
              icon={FiShare2}
              disabled={selectedVisualization.visualization_type !== 'diagram'}
            >
              <DiagramEditor 
                visualization={selectedVisualization} 
                modelId={modelId} 
              />
            </Tabs.Item>
            <Tabs.Item
              active={activeTab === 'matrix'}
              title="Matrix"
              icon={FiGrid}
              disabled={selectedVisualization.visualization_type !== 'matrix'}
            >
              <MatrixEditor 
                visualization={selectedVisualization} 
                modelId={modelId} 
              />
            </Tabs.Item>
            <Tabs.Item
              active={activeTab === 'heatmap'}
              title="Heatmap"
              icon={FiMap}
              disabled={selectedVisualization.visualization_type !== 'heatmap'}
            >
              <HeatmapEditor 
                visualization={selectedVisualization} 
                modelId={modelId} 
              />
            </Tabs.Item>
            <Tabs.Item
              active={activeTab === 'roadmap'}
              title="Roadmap"
              icon={FiCalendar}
              disabled={selectedVisualization.visualization_type !== 'roadmap'}
            >
              <RoadmapEditor 
                visualization={selectedVisualization}
                modelId={modelId} 
              />
            </Tabs.Item>
          </Tabs.Group>
        </Card>
      )}
      
      {/* New visualization form */}
      {showNewVisualizationForm && (
        <Card>
          <Card.Header>
            <h3 className="text-xl font-bold">Create New Visualization</h3>
          </Card.Header>
          <Card.Body>
            <VisualizationForm 
              modelId={modelId}
              onSubmit={handleCreateVisualization}
              onCancel={() => setShowNewVisualizationForm(false)}
            />
          </Card.Body>
        </Card>
      )}
    </div>
  );
};

// Visualization Form Component
const VisualizationForm = ({ modelId, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    visualization_type: 'diagram',
    diagram_settings: {
      layout_algorithm: 'hierarchical',
      show_relationships: true,
      show_labels: true,
      group_by_domain: false,
      theme: 'light',
      include_attributes: []
    },
    matrix_settings: {
      row_elements: 'application',
      column_elements: 'technology',
      cell_content: 'relationship',
      highlight_threshold: 5,
      group_rows: null,
      group_columns: null
    },
    heatmap_settings: {
      element_type: 'application',
      metric: 'risk',
      scale_min: 0,
      scale_max: 10,
      color_low: '#00FF00',
      color_high: '#FF0000',
      group_by: null
    },
    roadmap_settings: {
      timeline_start: new Date().toISOString(),
      timeline_end: new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString(),
      swimlanes: 'domain',
      milestone_types: ['project', 'milestone'],
      color_coding: 'status'
    }
  });
  
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  const handleSettingsChange = (type, field, value) => {
    setFormData(prev => ({
      ...prev,
      [`${type}_settings`]: {
        ...prev[`${type}_settings`],
        [field]: value
      }
    }));
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Extract only the settings for the selected visualization type
    const settings = formData[`${formData.visualization_type}_settings`];
    
    onSubmit({
      name: formData.name,
      description: formData.description,
      visualization_type: formData.visualization_type,
      [`${formData.visualization_type}_settings`]: settings
    });
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block mb-2 text-sm font-medium text-gray-900">Visualization Name</label>
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
          required
        />
      </div>
      
      <div>
        <label className="block mb-2 text-sm font-medium text-gray-900">Description</label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
          rows="3"
        />
      </div>
      
      <div>
        <label className="block mb-2 text-sm font-medium text-gray-900">Visualization Type</label>
        <select
          name="visualization_type"
          value={formData.visualization_type}
          onChange={handleChange}
          className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
          required
        >
          <option value="diagram">Diagram</option>
          <option value="matrix">Matrix</option>
          <option value="heatmap">Heatmap</option>
          <option value="roadmap">Roadmap</option>
        </select>
      </div>
      
      {/* Conditional settings based on visualization type */}
      {formData.visualization_type === 'diagram' && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium">Diagram Settings</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Layout Algorithm</label>
              <select
                value={formData.diagram_settings.layout_algorithm}
                onChange={(e) => handleSettingsChange('diagram', 'layout_algorithm', e.target.value)}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              >
                <option value="hierarchical">Hierarchical</option>
                <option value="force">Force-Directed</option>
                <option value="circular">Circular</option>
                <option value="grid">Grid</option>
              </select>
            </div>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Theme</label>
              <select
                value={formData.diagram_settings.theme}
                onChange={(e) => handleSettingsChange('diagram', 'theme', e.target.value)}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="colorful">Colorful</option>
              </select>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="show_relationships"
                checked={formData.diagram_settings.show_relationships}
                onChange={(e) => handleSettingsChange('diagram', 'show_relationships', e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="show_relationships" className="ml-2 text-sm font-medium text-gray-900">
                Show Relationships
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="show_labels"
                checked={formData.diagram_settings.show_labels}
                onChange={(e) => handleSettingsChange('diagram', 'show_labels', e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="show_labels" className="ml-2 text-sm font-medium text-gray-900">
                Show Relationship Labels
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="group_by_domain"
                checked={formData.diagram_settings.group_by_domain}
                onChange={(e) => handleSettingsChange('diagram', 'group_by_domain', e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="group_by_domain" className="ml-2 text-sm font-medium text-gray-900">
                Group Elements by Domain
              </label>
            </div>
          </div>
        </div>
      )}
      
      {formData.visualization_type === 'matrix' && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium">Matrix Settings</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Row Elements</label>
              <select
                value={formData.matrix_settings.row_elements}
                onChange={(e) => handleSettingsChange('matrix', 'row_elements', e.target.value)}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              >
                <option value="application">Applications</option>
                <option value="business_process">Business Processes</option>
                <option value="technology">Technology</option>
                <option value="data">Data Objects</option>
              </select>
            </div>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Column Elements</label>
              <select
                value={formData.matrix_settings.column_elements}
                onChange={(e) => handleSettingsChange('matrix', 'column_elements', e.target.value)}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              >
                <option value="application">Applications</option>
                <option value="business_process">Business Processes</option>
                <option value="technology">Technology</option>
                <option value="data">Data Objects</option>
              </select>
            </div>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Cell Content</label>
              <select
                value={formData.matrix_settings.cell_content}
                onChange={(e) => handleSettingsChange('matrix', 'cell_content', e.target.value)}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              >
                <option value="relationship">Relationship</option>
                <option value="count">Count</option>
                <option value="dependency">Dependency</option>
              </select>
            </div>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Highlight Threshold</label>
              <input
                type="number"
                value={formData.matrix_settings.highlight_threshold}
                onChange={(e) => handleSettingsChange('matrix', 'highlight_threshold', parseInt(e.target.value))}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                min="0"
              />
            </div>
          </div>
        </div>
      )}
      
      {formData.visualization_type === 'heatmap' && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium">Heatmap Settings</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Element Type</label>
              <select
                value={formData.heatmap_settings.element_type}
                onChange={(e) => handleSettingsChange('heatmap', 'element_type', e.target.value)}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              >
                <option value="application">Applications</option>
                <option value="business_process">Business Processes</option>
                <option value="technology">Technology</option>
                <option value="data">Data Objects</option>
              </select>
            </div>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Metric</label>
              <select
                value={formData.heatmap_settings.metric}
                onChange={(e) => handleSettingsChange('heatmap', 'metric', e.target.value)}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              >
                <option value="risk">Risk</option>
                <option value="performance">Performance</option>
                <option value="cost">Cost</option>
                <option value="business_value">Business Value</option>
                <option value="technical_fit">Technical Fit</option>
              </select>
            </div>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Scale Minimum</label>
              <input
                type="number"
                value={formData.heatmap_settings.scale_min}
                onChange={(e) => handleSettingsChange('heatmap', 'scale_min', parseFloat(e.target.value))}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              />
            </div>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Scale Maximum</label>
              <input
                type="number"
                value={formData.heatmap_settings.scale_max}
                onChange={(e) => handleSettingsChange('heatmap', 'scale_max', parseFloat(e.target.value))}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              />
            </div>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Group By</label>
              <select
                value={formData.heatmap_settings.group_by || ''}
                onChange={(e) => handleSettingsChange('heatmap', 'group_by', e.target.value || null)}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              >
                <option value="">No Grouping</option>
                <option value="domain">Domain</option>
                <option value="status">Status</option>
                <option value="owner">Owner</option>
              </select>
            </div>
          </div>
        </div>
      )}
      
      {formData.visualization_type === 'roadmap' && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium">Roadmap Settings</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Timeline Start</label>
              <input
                type="date"
                value={formData.roadmap_settings.timeline_start.split('T')[0]}
                onChange={(e) => handleSettingsChange('roadmap', 'timeline_start', e.target.value)}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              />
            </div>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Timeline End</label>
              <input
                type="date"
                value={formData.roadmap_settings.timeline_end.split('T')[0]}
                onChange={(e) => handleSettingsChange('roadmap', 'timeline_end', e.target.value)}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              />
            </div>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Swimlanes</label>
              <select
                value={formData.roadmap_settings.swimlanes || ''}
                onChange={(e) => handleSettingsChange('roadmap', 'swimlanes', e.target.value || null)}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              >
                <option value="">No Swimlanes</option>
                <option value="domain">Domain</option>
                <option value="owner">Owner</option>
                <option value="status">Status</option>
                <option value="priority">Priority</option>
              </select>
            </div>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-900">Color Coding</label>
              <select
                value={formData.roadmap_settings.color_coding}
                onChange={(e) => handleSettingsChange('roadmap', 'color_coding', e.target.value)}
                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              >
                <option value="status">Status</option>
                <option value="domain">Domain</option>
                <option value="priority">Priority</option>
                <option value="risk">Risk</option>
              </select>
            </div>
          </div>
        </div>
      )}
      
      <div className="flex justify-end space-x-2">
        <Button
          color="gray"
          onClick={onCancel}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          color="blue"
        >
          Create Visualization
        </Button>
      </div>
    </form>
  );
};

export default VisualizationManager;
