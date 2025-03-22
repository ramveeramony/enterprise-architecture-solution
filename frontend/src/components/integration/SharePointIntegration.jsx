import React, { useState, useEffect } from 'react';
import { Card, Button, Table, Badge, Spinner, Alert, Tabs, TextInput, Label } from 'flowbite-react';
import { FiRefreshCw, FiEdit, FiPlus, FiAlertCircle, FiCheckCircle, FiFile, FiFolder, FiExternalLink, FiUpload, FiDownload } from 'react-icons/fi';
import { useQuery } from '@tanstack/react-query';

import IntegrationForm from './IntegrationForm';
import { integrationApi } from '../../services/api';

const SharePointIntegration = ({ integration, onSave }) => {
  const [isConfiguring, setIsConfiguring] = useState(!integration);
  const [activeTab, setActiveTab] = useState('summary');
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [syncResult, setSyncResult] = useState(null);
  const [currentFolder, setCurrentFolder] = useState('/');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);

  // Fetch document library content
  const { 
    data: documents, 
    isLoading: documentsLoading, 
    refetch: refetchDocuments 
  } = useQuery({
    queryKey: ['sharepoint-documents', integration?.id, currentFolder],
    queryFn: () => integration?.id ? integrationApi.getSharePointDocuments(integration.id, currentFolder) : Promise.resolve([]),
    enabled: !!integration?.id && activeTab === 'documents',
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
        message: `Synchronization completed successfully. ${result.stats?.created || 0} documents created, ${result.stats?.updated || 0} documents updated.`
      });
      
      // Refetch data after sync
      if (activeTab === 'history') refetchHistory();
      if (activeTab === 'documents') refetchDocuments();
      
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

  // Handle file download
  const handleDownload = async (file) => {
    if (!file || !integration?.id) return;
    
    try {
      const result = await integrationApi.downloadSharePointFile(integration.id, file.path);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([result]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.name);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Error downloading file:', error);
      setSyncResult({
        success: false,
        message: `Failed to download file: ${error.message}`
      });
    }
  };

  // Handle file upload
  const handleUpload = async (e) => {
    e.preventDefault();
    
    if (!uploadFile || !integration?.id) return;
    
    setSyncInProgress(true);
    setSyncResult(null);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('folder', currentFolder);
      
      await integrationApi.uploadSharePointFile(integration.id, formData);
      
      setSyncResult({
        success: true,
        message: `File ${uploadFile.name} uploaded successfully.`
      });
      
      // Reset upload file and refetch documents
      setUploadFile(null);
      refetchDocuments();
    } catch (error) {
      setSyncResult({
        success: false,
        message: `Failed to upload file: ${error.message}`
      });
    } finally {
      setSyncInProgress(false);
    }
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  // Format file size
  const formatFileSize = (sizeInBytes) => {
    if (!sizeInBytes) return 'N/A';
    
    const KB = 1024;
    const MB = KB * 1024;
    const GB = MB * 1024;
    
    if (sizeInBytes < KB) {
      return `${sizeInBytes} B`;
    } else if (sizeInBytes < MB) {
      return `${(sizeInBytes / KB).toFixed(2)} KB`;
    } else if (sizeInBytes < GB) {
      return `${(sizeInBytes / MB).toFixed(2)} MB`;
    } else {
      return `${(sizeInBytes / GB).toFixed(2)} GB`;
    }
  };

  // Navigate to a folder
  const navigateToFolder = (folderPath) => {
    setCurrentFolder(folderPath);
    setSearchQuery('');
  };

  // Filter documents based on search query
  const filteredDocuments = documents?.filter(item => {
    if (!searchQuery) return true;
    return item.name.toLowerCase().includes(searchQuery.toLowerCase());
  }) || [];

  if (isConfiguring) {
    return (
      <IntegrationForm 
        type="sharepoint" 
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
          <FiFolder className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h5 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            No SharePoint Integration Configured
          </h5>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Connect to SharePoint to manage and integrate your enterprise architecture documents.
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
              {integration.name || 'SharePoint Integration'}
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
                        <Table.Cell className="font-medium">Site URL</Table.Cell>
                        <Table.Cell>
                          <a href={integration.configuration?.site_url} target="_blank" rel="noopener noreferrer" className="flex items-center text-blue-600 hover:underline">
                            {integration.configuration?.site_url || 'Not configured'}
                            <FiExternalLink className="ml-1 h-4 w-4" />
                          </a>
                        </Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Document Library</Table.Cell>
                        <Table.Cell>{integration.configuration?.document_library || 'Not configured'}</Table.Cell>
                      </Table.Row>
                    </Table.Body>
                  </Table>
                </div>
                
                <div>
                  <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Synchronization Stats</h5>
                  <Table>
                    <Table.Body className="divide-y">
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Total Documents</Table.Cell>
                        <Table.Cell>{integration.stats?.total_documents || '0'}</Table.Cell>
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
          
          <Tabs.Item title="Documents">
            <div className="mb-4 flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="flex gap-2 items-center mb-2">
                  <Label htmlFor="document-search" className="sr-only">Search</Label>
                  <TextInput
                    id="document-search"
                    type="search"
                    placeholder="Search documents..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full"
                  />
                  <Button color="gray" onClick={() => navigateToFolder('/')}>
                    Root
                  </Button>
                </div>
                
                <div className="text-sm text-gray-500 mb-2">
                  Current path: {currentFolder}
                </div>
              </div>
              
              <div>
                <form onSubmit={handleUpload} className="flex gap-2">
                  <div>
                    <Label htmlFor="file-upload" className="sr-only">Upload file</Label>
                    <input
                      id="file-upload"
                      type="file"
                      className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none dark:text-gray-400 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400"
                      onChange={(e) => setUploadFile(e.target.files[0])}
                    />
                  </div>
                  <Button type="submit" disabled={!uploadFile || syncInProgress}>
                    <FiUpload className="mr-2 h-5 w-5" />
                    Upload
                  </Button>
                </form>
              </div>
            </div>
            
            {documentsLoading ? (
              <div className="flex justify-center py-8">
                <Spinner size="xl" />
              </div>
            ) : !documents || documents.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  No documents found in this folder.
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
                    <Table.HeadCell>Type</Table.HeadCell>
                    <Table.HeadCell>Size</Table.HeadCell>
                    <Table.HeadCell>Modified</Table.HeadCell>
                    <Table.HeadCell>Actions</Table.HeadCell>
                  </Table.Head>
                  <Table.Body className="divide-y">
                    {filteredDocuments.map((item) => (
                      <Table.Row key={item.id} className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">
                          <div className="flex items-center">
                            {item.is_folder ? (
                              <FiFolder className="mr-2 h-5 w-5 text-yellow-400" />
                            ) : (
                              <FiFile className="mr-2 h-5 w-5 text-blue-500" />
                            )}
                            {item.is_folder ? (
                              <button 
                                className="hover:underline"
                                onClick={() => navigateToFolder(item.path)}
                              >
                                {item.name}
                              </button>
                            ) : (
                              <span>{item.name}</span>
                            )}
                          </div>
                        </Table.Cell>
                        <Table.Cell>{item.is_folder ? 'Folder' : (item.file_type || 'File')}</Table.Cell>
                        <Table.Cell>{item.is_folder ? '-' : formatFileSize(item.size)}</Table.Cell>
                        <Table.Cell>{formatDate(item.modified_at)}</Table.Cell>
                        <Table.Cell>
                          {!item.is_folder && (
                            <div className="flex gap-2">
                              <Button 
                                size="xs" 
                                onClick={() => handleDownload(item)}
                              >
                                <FiDownload className="mr-1 h-4 w-4" />
                                Download
                              </Button>
                              <Button 
                                size="xs" 
                                color="light"
                                onClick={() => window.open(item.web_url, '_blank')}
                              >
                                <FiExternalLink className="mr-1 h-4 w-4" />
                                Open
                              </Button>
                            </div>
                          )}
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

export default SharePointIntegration;