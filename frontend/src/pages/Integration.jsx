import React, { useState, useEffect } from 'react';
import { Card, Tabs, Button, Badge } from 'flowbite-react';
import { FiRefreshCw, FiPlus, FiLink } from 'react-icons/fi';
import { useQuery } from '@tanstack/react-query';

// Components
import IntegrationList from '../components/integration/IntegrationList';
import IntegrationForm from '../components/integration/IntegrationForm';
import HaloITSMIntegration from '../components/integration/HaloITSMIntegration';
import EntraIDIntegration from '../components/integration/EntraIDIntegration';
import SharePointIntegration from '../components/integration/SharePointIntegration';
import PowerBIIntegration from '../components/integration/PowerBIIntegration';
import ServiceNowIntegration from '../components/integration/ServiceNowIntegration';
import JiraIntegration from '../components/integration/JiraIntegration';

// Services
import { integrationApi } from '../services/api';

const Integration = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedIntegration, setSelectedIntegration] = useState(null);
  const [showForm, setShowForm] = useState(false);

  // Fetch integration configurations
  const { 
    data: integrations, 
    isLoading, 
    error, 
    refetch 
  } = useQuery({
    queryKey: ['integrations'],
    queryFn: integrationApi.getIntegrations,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Handle tab change
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setSelectedIntegration(null);
    setShowForm(false);
  };

  // Handle integration selection
  const handleSelectIntegration = (integration) => {
    setSelectedIntegration(integration);
    setActiveTab(integration.integration_type);
  };

  // Handle add new integration
  const handleAddNew = (integrationType) => {
    setActiveTab(integrationType);
    setSelectedIntegration(null);
    setShowForm(true);
  };

  // Get status badge color
  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'gray';
      case 'error':
        return 'failure';
      default:
        return 'info';
    }
  };

  // Get integration component based on type
  const renderIntegrationComponent = () => {
    if (showForm) {
      return (
        <IntegrationForm 
          type={activeTab} 
          integration={selectedIntegration} 
          onSave={() => {
            refetch();
            setShowForm(false);
          }}
          onCancel={() => setShowForm(false)}
        />
      );
    }

    if (selectedIntegration) {
      return (
        <Card className="mb-4">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-xl font-bold">{selectedIntegration.name || 'Integration Details'}</h3>
              <div className="flex items-center mt-1">
                <Badge color={getStatusColor(selectedIntegration.status)} className="mr-2">
                  {selectedIntegration.status}
                </Badge>
                <span className="text-sm text-gray-500">
                  Last synced: {selectedIntegration.last_sync_at ? new Date(selectedIntegration.last_sync_at).toLocaleString() : 'Never'}
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              <Button color="light" onClick={() => setShowForm(true)}>
                Edit
              </Button>
              <Button 
                color="blue" 
                onClick={() => integrationApi.syncIntegration(selectedIntegration.id).then(refetch)}
              >
                <FiRefreshCw className="mr-2 h-5 w-5" />
                Sync Now
              </Button>
            </div>
          </div>
        </Card>
      );
    }

    switch (activeTab) {
      case 'halo_itsm':
        return <HaloITSMIntegration integration={selectedIntegration} onSave={() => refetch()} />;
      case 'entra_id':
        return <EntraIDIntegration integration={selectedIntegration} onSave={() => refetch()} />;
      case 'sharepoint':
        return <SharePointIntegration integration={selectedIntegration} onSave={() => refetch()} />;
      case 'power_bi':
        return <PowerBIIntegration integration={selectedIntegration} onSave={() => refetch()} />;
      case 'servicenow':
        return <ServiceNowIntegration integration={selectedIntegration} onSave={() => refetch()} />;
      case 'jira':
        return <JiraIntegration integration={selectedIntegration} onSave={() => refetch()} />;
      default:
        return null;
    }
  };

  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-900 min-h-screen">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">System Integrations</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Connect your Enterprise Architecture Solution with other systems
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <Card>
            <h5 className="text-xl font-bold leading-none text-gray-900 dark:text-white mb-4">
              Integrations
            </h5>
            <Button 
              color="gray" 
              className="mb-4 w-full"
              onClick={() => handleAddNew('halo_itsm')}
            >
              <FiPlus className="mr-2 h-5 w-5" />
              Add New Integration
            </Button>
            
            {isLoading ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-700"></div>
              </div>
            ) : error ? (
              <div className="text-center py-4 text-red-500">
                Error loading integrations
              </div>
            ) : (
              <IntegrationList 
                integrations={integrations || []} 
                onSelect={handleSelectIntegration}
                activeId={selectedIntegration?.id}
              />
            )}
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          <Tabs.Group
            aria-label="Integration tabs"
            style="underline"
            onActiveTabChange={handleTabChange}
          >
            <Tabs.Item active={activeTab === 'overview'} title="Overview" icon={FiLink}>
              <Card>
                <h5 className="text-xl font-bold leading-none text-gray-900 dark:text-white mb-4">
                  Available Integrations
                </h5>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <Card className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" onClick={() => handleAddNew('halo_itsm')}>
                    <div className="flex flex-col items-center">
                      <img src="/logos/halo-itsm.svg" alt="Halo ITSM" className="w-16 h-16 mb-3" />
                      <h5 className="text-lg font-bold">Halo ITSM</h5>
                      <p className="text-sm text-gray-500 text-center mt-2">
                        Synchronize with CMDB and IT assets
                      </p>
                    </div>
                  </Card>
                  
                  <Card className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" onClick={() => handleAddNew('entra_id')}>
                    <div className="flex flex-col items-center">
                      <img src="/logos/microsoft.svg" alt="Microsoft Entra ID" className="w-16 h-16 mb-3" />
                      <h5 className="text-lg font-bold">Microsoft Entra ID</h5>
                      <p className="text-sm text-gray-500 text-center mt-2">
                        Manage users and authentication
                      </p>
                    </div>
                  </Card>
                  
                  <Card className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" onClick={() => handleAddNew('sharepoint')}>
                    <div className="flex flex-col items-center">
                      <img src="/logos/sharepoint.svg" alt="SharePoint" className="w-16 h-16 mb-3" />
                      <h5 className="text-lg font-bold">SharePoint</h5>
                      <p className="text-sm text-gray-500 text-center mt-2">
                        Document management and collaboration
                      </p>
                    </div>
                  </Card>
                  
                  <Card className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" onClick={() => handleAddNew('power_bi')}>
                    <div className="flex flex-col items-center">
                      <img src="/logos/power-bi.svg" alt="Power BI" className="w-16 h-16 mb-3" />
                      <h5 className="text-lg font-bold">Power BI</h5>
                      <p className="text-sm text-gray-500 text-center mt-2">
                        Advanced analytics and visualizations
                      </p>
                    </div>
                  </Card>
                  
                  <Card className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" onClick={() => handleAddNew('servicenow')}>
                    <div className="flex flex-col items-center">
                      <img src="/logos/servicenow.svg" alt="ServiceNow" className="w-16 h-16 mb-3" />
                      <h5 className="text-lg font-bold">ServiceNow</h5>
                      <p className="text-sm text-gray-500 text-center mt-2">
                        IT service management integration
                      </p>
                    </div>
                  </Card>
                  
                  <Card className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" onClick={() => handleAddNew('jira')}>
                    <div className="flex flex-col items-center">
                      <img src="/logos/jira.svg" alt="Jira" className="w-16 h-16 mb-3" />
                      <h5 className="text-lg font-bold">Jira</h5>
                      <p className="text-sm text-gray-500 text-center mt-2">
                        Project and issue management
                      </p>
                    </div>
                  </Card>
                </div>
              </Card>
            </Tabs.Item>
            
            <Tabs.Item active={activeTab === 'halo_itsm'} title="Halo ITSM">
              {renderIntegrationComponent()}
            </Tabs.Item>
            
            <Tabs.Item active={activeTab === 'entra_id'} title="Microsoft Entra ID">
              {renderIntegrationComponent()}
            </Tabs.Item>
            
            <Tabs.Item active={activeTab === 'sharepoint'} title="SharePoint">
              {renderIntegrationComponent()}
            </Tabs.Item>
            
            <Tabs.Item active={activeTab === 'power_bi'} title="Power BI">
              {renderIntegrationComponent()}
            </Tabs.Item>
            
            <Tabs.Item active={activeTab === 'servicenow'} title="ServiceNow">
              {renderIntegrationComponent()}
            </Tabs.Item>
            
            <Tabs.Item active={activeTab === 'jira'} title="Jira">
              {renderIntegrationComponent()}
            </Tabs.Item>
          </Tabs.Group>
        </div>
      </div>
    </div>
  );
};

export default Integration;