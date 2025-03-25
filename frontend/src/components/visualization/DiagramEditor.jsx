import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Spinner, Alert, Tooltip } from 'flowbite-react';
import { FiZoomIn, FiZoomOut, FiMaximize, FiSave, FiRefreshCw, FiFilter, FiSliders } from 'react-icons/fi';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Import API services
import { getVisualizationData, updateVisualization } from '../../services/api';

// Diagram rendering libraries would be imported here
// For now, we'll create a simple implementation

const DiagramEditor = ({ visualization, modelId }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [diagramData, setDiagramData] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState(visualization?.diagram_settings || {});
  const [selectedElement, setSelectedElement] = useState(null);
  
  const canvasRef = useRef(null);
  const queryClient = useQueryClient();
  
  // Fetch visualization data
  const { data, isLoading: dataLoading, error: dataError } = useQuery({
    queryKey: ['visualizationData', visualization?.id],
    queryFn: () => getVisualizationData(visualization?.id),
    enabled: !!visualization?.id
  });
  
  // Update visualization mutation
  const updateVisualizationMutation = useMutation({
    mutationFn: updateVisualization,
    onSuccess: () => {
      queryClient.invalidateQueries(['visualizations', modelId]);
      queryClient.invalidateQueries(['visualizationData', visualization?.id]);
    }
  });
  
  // Initialize diagram when data is loaded
  useEffect(() => {
    if (data && !dataLoading) {
      setDiagramData(data);
      renderDiagram(data);
      setIsLoading(false);
    }
  }, [data, dataLoading]);
  
  // Handle errors
  useEffect(() => {
    if (dataError) {
      setError(dataError);
      setIsLoading(false);
    }
  }, [dataError]);
  
  // Re-render diagram when settings change
  useEffect(() => {
    if (diagramData) {
      renderDiagram(diagramData);
    }
  }, [settings, zoom]);
  
  // Handle zoom in
  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.1, 2));
  };
  
  // Handle zoom out
  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.1, 0.5));
  };
  
  // Handle reset zoom
  const handleResetZoom = () => {
    setZoom(1);
  };
  
  // Handle save settings
  const handleSaveSettings = () => {
    updateVisualizationMutation.mutate({
      id: visualization.id,
      diagram_settings: settings
    });
    setShowSettings(false);
  };
  
  // Handle setting change
  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };
  
  // Handle element selection
  const handleElementClick = (elementId) => {
    const element = diagramData.nodes.find(node => node.id === elementId);
    setSelectedElement(element);
  };
  
  // Render diagram function
  const renderDiagram = (data) => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Set scaling based on zoom
    ctx.save();
    ctx.scale(zoom, zoom);
    
    // This is a simplified rendering implementation
    // In a real application, you would use a proper diagram rendering library
    // such as react-flow, vis.js, or D3.js
    
    // Calculate center position
    const centerX = canvas.width / (2 * zoom);
    const centerY = canvas.height / (2 * zoom);
    
    // Draw nodes
    data.nodes.forEach((node, index) => {
      // Place nodes in a circle around the center
      const angle = (index / data.nodes.length) * Math.PI * 2;
      const radius = 150;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      
      // Store node position for edge rendering
      node.x = x;
      node.y = y;
      
      // Draw node
      ctx.beginPath();
      ctx.fillStyle = getNodeColor(node.type);
      ctx.arc(x, y, 30, 0, Math.PI * 2);
      ctx.fill();
      
      // Draw node border
      ctx.strokeStyle = node.id === selectedElement?.id ? '#3b82f6' : '#000000';
      ctx.lineWidth = node.id === selectedElement?.id ? 3 : 1;
      ctx.stroke();
      
      // Draw node label
      ctx.fillStyle = '#ffffff';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.label, x, y);
    });
    
    // Draw edges if show relationships is enabled
    if (settings.show_relationships) {
      data.edges.forEach(edge => {
        const sourceNode = data.nodes.find(node => node.id === edge.source);
        const targetNode = data.nodes.find(node => node.id === edge.target);
        
        if (sourceNode && targetNode) {
          // Draw edge
          ctx.beginPath();
          ctx.strokeStyle = '#555555';
          ctx.lineWidth = 1;
          ctx.moveTo(sourceNode.x, sourceNode.y);
          ctx.lineTo(targetNode.x, targetNode.y);
          ctx.stroke();
          
          // Draw edge label if show labels is enabled
          if (settings.show_labels && edge.label) {
            const midX = (sourceNode.x + targetNode.x) / 2;
            const midY = (sourceNode.y + targetNode.y) / 2;
            
            ctx.fillStyle = '#000000';
            ctx.font = '10px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            // Draw label background
            const labelWidth = ctx.measureText(edge.label).width + 4;
            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.fillRect(midX - labelWidth / 2, midY - 8, labelWidth, 16);
            
            // Draw label text
            ctx.fillStyle = '#000000';
            ctx.fillText(edge.label, midX, midY);
          }
        }
      });
    }
    
    ctx.restore();
  };
  
  // Get color for different node types
  const getNodeColor = (type) => {
    const colors = {
      application: '#3b82f6', // blue
      business_process: '#10b981', // green
      technology: '#f59e0b', // amber
      data: '#8b5cf6', // purple
      default: '#6b7280' // gray
    };
    
    return colors[type] || colors.default;
  };
  
  // Handle canvas click for element selection
  const handleCanvasClick = (e) => {
    if (!canvasRef.current || !diagramData) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / zoom;
    const y = (e.clientY - rect.top) / zoom;
    
    // Check if a node was clicked
    for (const node of diagramData.nodes) {
      const dx = x - node.x;
      const dy = y - node.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance <= 30) {
        handleElementClick(node.id);
        return;
      }
    }
    
    // No node was clicked, clear selection
    setSelectedElement(null);
  };
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="xl" />
      </div>
    );
  }
  
  if (error) {
    return (
      <Alert color="failure">
        <p>Error loading diagram: {error.message}</p>
      </Alert>
    );
  }
  
  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex space-x-2">
          <Tooltip content="Zoom In">
            <Button size="sm" color="light" onClick={handleZoomIn}>
              <FiZoomIn />
            </Button>
          </Tooltip>
          <Tooltip content="Zoom Out">
            <Button size="sm" color="light" onClick={handleZoomOut}>
              <FiZoomOut />
            </Button>
          </Tooltip>
          <Tooltip content="Reset Zoom">
            <Button size="sm" color="light" onClick={handleResetZoom}>
              <FiMaximize />
            </Button>
          </Tooltip>
          <span className="text-sm font-medium text-gray-700">
            {Math.round(zoom * 100)}%
          </span>
        </div>
        
        <div className="flex space-x-2">
          <Tooltip content="Refresh">
            <Button 
              size="sm" 
              color="light" 
              onClick={() => queryClient.invalidateQueries(['visualizationData', visualization?.id])}
            >
              <FiRefreshCw />
            </Button>
          </Tooltip>
          <Tooltip content="Filter Elements">
            <Button size="sm" color="light">
              <FiFilter />
            </Button>
          </Tooltip>
          <Tooltip content="Diagram Settings">
            <Button 
              size="sm" 
              color="light"
              onClick={() => setShowSettings(!showSettings)}
            >
              <FiSliders />
            </Button>
          </Tooltip>
        </div>
      </div>
      
      <div className="flex space-x-4">
        {/* Diagram Canvas */}
        <div className="flex-grow">
          <Card className="h-full">
            <div className="h-96 w-full relative overflow-hidden">
              <canvas
                ref={canvasRef}
                width={800}
                height={600}
                className="w-full h-full"
                onClick={handleCanvasClick}
              />
            </div>
          </Card>
        </div>
        
        {/* Settings Panel */}
        {showSettings && (
          <Card className="w-80">
            <Card.Header>
              <h3 className="text-lg font-medium">Diagram Settings</h3>
            </Card.Header>
            <Card.Body className="space-y-4">
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-900">
                  Layout Algorithm
                </label>
                <select
                  value={settings.layout_algorithm}
                  onChange={(e) => handleSettingChange('layout_algorithm', e.target.value)}
                  className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                >
                  <option value="hierarchical">Hierarchical</option>
                  <option value="force">Force-Directed</option>
                  <option value="circular">Circular</option>
                  <option value="grid">Grid</option>
                </select>
              </div>
              
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-900">
                  Theme
                </label>
                <select
                  value={settings.theme}
                  onChange={(e) => handleSettingChange('theme', e.target.value)}
                  className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="colorful">Colorful</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center">
                  <input
                    id="show_relationships"
                    type="checkbox"
                    checked={settings.show_relationships}
                    onChange={(e) => handleSettingChange('show_relationships', e.target.checked)}
                    className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="show_relationships" className="ml-2 text-sm font-medium text-gray-900">
                    Show Relationships
                  </label>
                </div>
                
                <div className="flex items-center">
                  <input
                    id="show_labels"
                    type="checkbox"
                    checked={settings.show_labels}
                    onChange={(e) => handleSettingChange('show_labels', e.target.checked)}
                    className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="show_labels" className="ml-2 text-sm font-medium text-gray-900">
                    Show Relationship Labels
                  </label>
                </div>
                
                <div className="flex items-center">
                  <input
                    id="group_by_domain"
                    type="checkbox"
                    checked={settings.group_by_domain}
                    onChange={(e) => handleSettingChange('group_by_domain', e.target.checked)}
                    className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="group_by_domain" className="ml-2 text-sm font-medium text-gray-900">
                    Group by Domain
                  </label>
                </div>
              </div>
              
              <Button
                color="blue"
                onClick={handleSaveSettings}
                className="w-full"
              >
                <FiSave className="mr-2" />
                Save Settings
              </Button>
            </Card.Body>
          </Card>
        )}
        
        {/* Element Details Panel */}
        {selectedElement && !showSettings && (
          <Card className="w-80">
            <Card.Header>
              <h3 className="text-lg font-medium">Element Details</h3>
            </Card.Header>
            <Card.Body className="space-y-4">
              <div>
                <h4 className="text-sm font-semibold text-gray-500">Name</h4>
                <p className="text-gray-900">{selectedElement.label}</p>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold text-gray-500">Type</h4>
                <p className="text-gray-900">{selectedElement.type}</p>
              </div>
              
              {selectedElement.data && Object.keys(selectedElement.data).length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-500">Properties</h4>
                  <div className="mt-2 space-y-2">
                    {Object.entries(selectedElement.data).map(([key, value]) => (
                      <div key={key}>
                        <h5 className="text-xs font-medium text-gray-500">{key}</h5>
                        <p className="text-sm text-gray-900">{value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <Button
                color="light"
                onClick={() => setSelectedElement(null)}
                className="w-full"
              >
                Close
              </Button>
            </Card.Body>
          </Card>
        )}
      </div>
    </div>
  );
};

export default DiagramEditor;
