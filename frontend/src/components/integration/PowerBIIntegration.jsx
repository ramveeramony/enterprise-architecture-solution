import React, { useState, useEffect } from 'react';
import { Card, Button, Table, Badge, Spinner, Alert, Tabs, TextInput, Label } from 'flowbite-react';
import { FiRefreshCw, FiEdit, FiPlus, FiAlertCircle, FiCheckCircle, FiPieChart, FiBarChart2, FiExternalLink, FiEye } from 'react-icons/fi';
import { useQuery } from '@tanstack/react-query';

import IntegrationForm from './IntegrationForm';
import { integrationApi } from '../../services/api';

const PowerBIIntegration = ({ integration, onSave }) => {
  const [isConfiguring, setIsConfiguring] = useState(!integration);
  const [activeTab, setActiveTab] = useState('summary');
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [syncResult, setSyncResult] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedReport, setSelectedReport] = useState(null);

  // Fetch Power BI reports
  const { 
    data: reports, 
    isLoading: reportsLoading, 
    refetch: refetchReports 
  } = useQuery({
    queryKey: ['powerbi-reports', integration?.id],
    queryFn: () => integration?.id ? integrationApi.getPowerBIReports(integration.id) : Promise.resolve([]),
    enabled: !!integration?.id && activeTab === 'reports',
  });

  // Fetch Power BI dashboards
  const { 
    data: dashboards, 
    isLoading: dashboardsLoading, 
    refetch: refetchDashboards 
  } = useQuery({
    queryKey: ['powerbi-dashboards', integration?.id],
    queryFn: () => integration?.id ? integrationApi.getPowerBIDashboards(integration.id) : Promise.resolve([]),
    enabled: !!integration?.id && activeTab === 'dashboards',
  });

  // Fetch synchronization history
  const { 
    data: syncHistory, 
    isLoading: historyLoading, 
    refetch: refetchHistory 
  } = useQuery({
    queryKey: ['integration-history', integration?.id],
    queryFn: () => integration?.id ? integrationApi.getIntegrationHistory(integration.id) : Promise.resolve([]),
    enabled: !!integration?.id && activeTab === 'history',
  });

  // Handle sync button click
  const handleSync = async () => {
    if (!integration?.id) return;
    
    setSyncInProgress(true);
    setSyncResult(null);
    
    try {
      const result = await integrationApi.syncIntegration(integration.id);
      setSyncResult({
        success: true,
        message: `Synchronization completed successfully. ${result.stats?.reports_synced || 0} reports and ${result.stats?.dashboards_synced || 0} dashboards synchronized.`
      });
      
      // Refetch data after sync
      if (activeTab === 'history') refetchHistory();
      if (activeTab === 'reports') refetchReports();
      if (activeTab === 'dashboards') refetchDashboards();
      
      // Call parent onSave if provided to refresh the integration
      if (onSave) onSave();
    } catch (error) {
      setSyncResult({
        success: false,
        message: error.message || 'Synchronization failed'
      });
    } finally {
      setSyncInProgress(false);
    }
  };

  // Handle embedding a report
  const handleEmbedReport = (report) => {
    setSelectedReport(report);
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  // Filter reports or dashboards based on search query
  const filterItems = (items) => {
    if (!items) return [];
    if (!searchQuery) return items;
    
    return items.filter(item => 
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.description && item.description.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  };

  // Filtered items based on active tab
  const filteredItems = activeTab === 'reports' 
    ? filterItems(reports) 
    : activeTab === 'dashboards' 
      ? filterItems(dashboards) 
      : [];

  if (isConfiguring) {
    return (
      <IntegrationForm 
        type="power_bi" 
        integration={integration}
        onSave={(savedIntegration) => {
          setIsConfiguring(false);
          if (onSave) onSave(savedIntegration);
        }}
        onCancel={() => setIsConfiguring(false)}
      />
    );
  }

  if (!integration) {
    return (
      <Card>
        <div className="text-center py-8">
          <FiBarChart2 className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h5 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            No Power BI Integration Configured
          </h5>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Connect to Power BI to integrate your analytics and visualization capabilities.
          </p>
          <Button onClick={() => setIsConfiguring(true)}>
            <FiPlus className="mr-2 h-5 w-5" />
            Configure Integration
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              {integration.name || 'Power BI Integration'}
            </h3>
            <div className="flex items-center mt-1">
              <Badge 
                color={integration.status === 'active' ? 'success' : 'gray'} 
                className="mr-2"
              >
                {integration.status}
              </Badge>
              <span className="text-sm text-gray-500">
                Last synced: {formatDate(integration.last_sync_at)}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <Button color="light" onClick={() => setIsConfiguring(true)}>
              <FiEdit className="mr-2 h-5 w-5" />
              Edit
            </Button>
            <Button 
              color="blue" 
              onClick={handleSync}
              disabled={syncInProgress}
            >
              {syncInProgress ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Syncing...
                </>
              ) : (
                <>
                  <FiRefreshCw className="mr-2 h-5 w-5" />
                  Sync Now
                </>
              )}
            </Button>
          </div>
        </div>

        {syncResult && (
          <Alert 
            color={syncResult.success ? 'success' : 'failure'}
            icon={syncResult.success ? FiCheckCircle : FiAlertCircle}
            className="mb-4"
          >
            <span className="font-medium">{syncResult.success ? 'Success!' : 'Error!'}</span>{' '}
            {syncResult.message}
          </Alert>
        )}

        {selectedReport && (
          <div className="mb-4">
            <Card>
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-bold text-gray-900 dark:text-white">
                  {selectedReport.name}
                </h4>
                <Button color="light" size="xs" onClick={() => setSelectedReport(null)}>
                  Close
                </Button>
              </div>
              <div className="h-[600px] w-full bg-gray-50 dark:bg-gray-800 relative">
                <iframe 
                  title={selectedReport.name}
                  src={selectedReport.embed_url}
                  frameBorder="0"
                  style={{ position: 'absolute', top: 0, left: 0, bottom: 0, right: 0, width: '100%', height: '100%' }}
                  allowFullScreen
                />
              </div>
            </Card>
          </div>
        )}

        <Tabs.Group
          aria-label="Integration tabs"
          style="underline"
          onActiveTabChange={(index) => {
            const tabs = ['summary', 'reports', 'dashboards', 'history'];
            setActiveTab(tabs[index]);
            setSelectedReport(null);
          }}
        >
          <Tabs.Item active title="Summary">
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Connection Details</h5>
                  <Table>
                    <Table.Body className="divide-y">
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Workspace ID</Table.Cell>
                        <Table.Cell>{integration.configuration?.workspace_id || 'Not configured'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Tenant ID</Table.Cell>
                        <Table.Cell>{integration.configuration?.tenant_id || 'Not configured'}</Table.Cell>
                      </Table.Row>
                    </Table.Body>
                  </Table>
                </div>
                
                <div>
                  <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Synchronization Stats</h5>
                  <Table>
                    <Table.Body className="divide-y">
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Reports</Table.Cell>
                        <Table.Cell>{integration.stats?.reports_count || '0'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Dashboards</Table.Cell>
                        <Table.Cell>{integration.stats?.dashboards_count || '0'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Last Sync</Table.Cell>
                        <Table.Cell>{formatDate(integration.last_sync_at)}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Last Sync Status</Table.Cell>
                        <Table.Cell>
                          <Badge 
                            color={integration.stats?.last_sync_status === 'success' ? 'success' : 'failure'}
                          >
                            {integration.stats?.last_sync_status || 'Never run'}
                          </Badge>
                        </Table.Cell>
                      </Table.Row>
                    </Table.Body>
                  </Table>
                </div>
              </div>
            </div>
          </Tabs.Item>
          
          <Tabs.Item title="Reports">
            <div className="mb-4">
              <div className="flex gap-2 items-center mb-2">
                <Label htmlFor="report-search" className="sr-only">Search</Label>
                <TextInput
                  id="report-search"
                  type="search"
                  placeholder="Search reports..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full"
                />
              </div>
            </div>
            
            {reportsLoading ? (
              <div className="flex justify-center py-8">
                <Spinner size="xl" />
              </div>
            ) : !reports || reports.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  No reports found.
                </p>
                <Button onClick={handleSync} disabled={syncInProgress}>
                  <FiRefreshCw className="mr-2 h-5 w-5" />
                  Sync Now
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <Table.Head>
                    <Table.HeadCell>Name</Table.HeadCell>
                    <Table.HeadCell>Description</Table.HeadCell>
                    <Table.HeadCell>Modified</Table.HeadCell>
                    <Table.HeadCell>Actions</Table.HeadCell>
                  </Table.Head>
                  <Table.Body className="divide-y">
                    {filteredItems.map((report) => (
                      <Table.Row key={report.id} className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">
                          <div className="flex items-center">
                            <FiBarChart2 className="mr-2 h-5 w-5 text-blue-500" />
                            {report.name}
                          </div>
                        </Table.Cell>
                        <Table.Cell>{report.description || 'No description'}</Table.Cell>
                        <Table.Cell>{formatDate(report.modified_at)}</Table.Cell>
                        <Table.Cell>
                          <div className="flex gap-2">
                            <Button 
                              size="xs" 
                              onClick={() => handleEmbedReport(report)}
                            >
                              <FiEye className="mr-1 h-4 w-4" />
                              View
                            </Button>
                            <Button 
                              size="xs" 
                              color="light"
                              onClick={() => window.open(report.web_url, '_blank')}
                            >
                              <FiExternalLink className="mr-1 h-4 w-4" />
                              Open
                            </Button>
                          </div>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table>
              </div>
            )}
          </Tabs.Item>
          
          <Tabs.Item title="Dashboards">
            <div className="mb-4">
              <div className="flex gap-2 items-center mb-2">
                <Label htmlFor="dashboard-search" className="sr-only">Search</Label>
                <TextInput
                  id="dashboard-search"
                  type="search"
                  placeholder="Search dashboards..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full"
                />
              </div>
            </div>
            
            {dashboardsLoading ? (
              <div className="flex justify-center py-8">
                <Spinner size="xl" />
              </div>
            ) : !dashboards || dashboards.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  No dashboards found.
                </p>
                <Button onClick={handleSync} disabled={syncInProgress}>
                  <FiRefreshCw className="mr-2 h-5 w-5" />
                  Sync Now
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <Table.Head>
                    <Table.HeadCell>Name</Table.HeadCell>
                    <Table.HeadCell>Description</Table.HeadCell>
                    <Table.HeadCell>Tiles</Table.HeadCell>
                    <Table.HeadCell>Modified</Table.HeadCell>
                    <Table.HeadCell>Actions</Table.HeadCell>
                  </Table.Head>
                  <Table.Body className="divide-y">
                    {filteredItems.map((dashboard) => (
                      <Table.Row key={dashboard.id} className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">
                          <div className="flex items-center">
                            <FiPieChart className="mr-2 h-5 w-5 text-purple-500" />
                            {dashboard.name}
                          </div>
                        </Table.Cell>
                        <Table.Cell>{dashboard.description || 'No description'}</Table.Cell>
                        <Table.Cell>{dashboard.tiles_count || 0}</Table.Cell>
                        <Table.Cell>{formatDate(dashboard.modified_at)}</Table.Cell>
                        <Table.Cell>
                          <Button 
                            size="xs" 
                            color="light"
                            onClick={() => window.open(dashboard.web_url, '_blank')}
                          >
                            <FiExternalLink className="mr-1 h-4 w-4" />
                            Open
                          </Button>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table>
              </div>
            )}
          </Tabs.Item>
          
          <Tabs.Item title="Sync History">
            {historyLoading ? (
              <div className="flex justify-center py-8">
                <Spinner size="xl" />
              </div>
            ) : !syncHistory || syncHistory.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  No synchronization history available.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <Table.Head>
                    <Table.HeadCell>Timestamp</Table.HeadCell>
                    <Table.HeadCell>Status</Table.HeadCell>
                    <Table.HeadCell>Reports Synced</Table.HeadCell>
                    <Table.HeadCell>Dashboards Synced</Table.HeadCell>
                    <Table.HeadCell>Details</Table.HeadCell>
                  </Table.Head>
                  <Table.Body className="divide-y">
                    {syncHistory.map((history) => (
                      <Table.Row key={history.id} className="bg-white dark:bg-gray-800">
                        <Table.Cell>{formatDate(history.created_at)}</Table.Cell>
                        <Table.Cell>
                          <Badge 
                            color={history.status === 'success' ? 'success' : 
                                 history.status === 'partial' ? 'warning' : 'failure'}
                          >
                            {history.status}
                          </Badge>
                        </Table.Cell>
                        <Table.Cell>{history.details?.reports_synced || 0}</Table.Cell>
                        <Table.Cell>{history.details?.dashboards_synced || 0}</Table.Cell>
                        <Table.Cell>
                          {history.error_message || 'No issues reported'}
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table>
              </div>
            )}
          </Tabs.Item>
        </Tabs.Group>
      </Card>
    </div>
  );
};

export default PowerBIIntegration;