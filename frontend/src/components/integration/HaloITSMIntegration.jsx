import React, { useState, useEffect } from 'react';
import { Card, Button, Table, Badge, Spinner, Alert, Tabs } from 'flowbite-react';
import { FiRefreshCw, FiEdit, FiPlus, FiAlertCircle, FiCheckCircle, FiServer, FiDatabase, FiHardDrive, FiLink } from 'react-icons/fi';
import { useQuery } from '@tanstack/react-query';

import IntegrationForm from './IntegrationForm';
import { integrationApi } from '../../services/api';

const HaloITSMIntegration = ({ integration, onSave }) => {
  const [isConfiguring, setIsConfiguring] = useState(!integration);
  const [activeTab, setActiveTab] = useState('summary');
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [syncResult, setSyncResult] = useState(null);

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

  // Fetch CMDB items (if integration is configured)
  const { 
    data: cmdbItems, 
    isLoading: cmdbLoading, 
    refetch: refetchCmdb 
  } = useQuery({
    queryKey: ['cmdb-items', integration?.id],
    queryFn: () => integration?.id ? integrationApi.getCmdbItems(integration.id) : Promise.resolve([]),
    enabled: !!integration?.id && activeTab === 'items',
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
        message: `Synchronization completed successfully. ${result.stats?.created || 0} items created, ${result.stats?.updated || 0} items updated.`
      });
      
      // Refetch data after sync
      if (activeTab === 'history') refetchHistory();
      if (activeTab === 'items') refetchCmdb();
      
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

  // Get CI type icon
  const getCITypeIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'server':
        return <FiServer className="h-5 w-5" />;
      case 'database':
        return <FiDatabase className="h-5 w-5" />;
      case 'application':
        return <FiHardDrive className="h-5 w-5" />;
      default:
        return <FiLink className="h-5 w-5" />;
    }
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (isConfiguring) {
    return (
      <IntegrationForm 
        type="halo_itsm" 
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
          <FiLink className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h5 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            No Halo ITSM Integration Configured
          </h5>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Connect to Halo ITSM to synchronize your CMDB data with the Enterprise Architecture repository.
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
              {integration.name || 'Halo ITSM Integration'}
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

        <Tabs.Group
          aria-label="Integration tabs"
          style="underline"
          onActiveTabChange={setActiveTab}
        >
          <Tabs.Item active title="Summary">
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Connection Details</h5>
                  <Table>
                    <Table.Body className="divide-y">
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">API URL</Table.Cell>
                        <Table.Cell>{integration.configuration?.api_url || 'Not configured'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Sync Frequency</Table.Cell>
                        <Table.Cell className="capitalize">{integration.configuration?.sync_frequency || 'Not configured'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Client ID</Table.Cell>
                        <Table.Cell>{integration.configuration?.client_id || 'Not configured'}</Table.Cell>
                      </Table.Row>
                    </Table.Body>
                  </Table>
                </div>
                
                <div>
                  <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Synchronization Stats</h5>
                  <Table>
                    <Table.Body className="divide-y">
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Total Items</Table.Cell>
                        <Table.Cell>{integration.stats?.total_items || '0'}</Table.Cell>
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
          
          <Tabs.Item title="CI Items">
            {cmdbLoading ? (
              <div className="flex justify-center py-8">
                <Spinner size="xl" />
              </div>
            ) : !cmdbItems || cmdbItems.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  No CMDB items have been synchronized yet. 
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
                    <Table.HeadCell>Type</Table.HeadCell>
                    <Table.HeadCell>Name</Table.HeadCell>
                    <Table.HeadCell>ID</Table.HeadCell>
                    <Table.HeadCell>Status</Table.HeadCell>
                    <Table.HeadCell>Last Updated</Table.HeadCell>
                  </Table.Head>
                  <Table.Body className="divide-y">
                    {cmdbItems.map((item) => (
                      <Table.Row key={item.id} className="bg-white dark:bg-gray-800">
                        <Table.Cell className="flex items-center">
                          <span className="mr-2">{getCITypeIcon(item.type)}</span>
                          {item.type}
                        </Table.Cell>
                        <Table.Cell className="font-medium">{item.name}</Table.Cell>
                        <Table.Cell>{item.external_id}</Table.Cell>
                        <Table.Cell>
                          <Badge color={item.status === 'active' ? 'success' : 'gray'}>
                            {item.status}
                          </Badge>
                        </Table.Cell>
                        <Table.Cell>{formatDate(item.updated_at)}</Table.Cell>
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
                    <Table.HeadCell>Created</Table.HeadCell>
                    <Table.HeadCell>Updated</Table.HeadCell>
                    <Table.HeadCell>Failed</Table.HeadCell>
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
                        <Table.Cell>{history.items_created}</Table.Cell>
                        <Table.Cell>{history.items_updated}</Table.Cell>
                        <Table.Cell>{history.items_failed}</Table.Cell>
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

export default HaloITSMIntegration;