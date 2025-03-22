import React, { useState } from 'react';
import { Card, Button, Table, Badge, Spinner, Alert, Tabs, TextInput, Label, Avatar } from 'flowbite-react';
import { FiRefreshCw, FiEdit, FiPlus, FiAlertCircle, FiCheckCircle, FiUser, FiUsers, FiUserPlus, FiSearch } from 'react-icons/fi';
import { useQuery } from '@tanstack/react-query';

import IntegrationForm from './IntegrationForm';
import { integrationApi } from '../../services/api';

const EntraIDIntegration = ({ integration, onSave }) => {
  const [isConfiguring, setIsConfiguring] = useState(!integration);
  const [activeTab, setActiveTab] = useState('summary');
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [syncResult, setSyncResult] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);

  // Fetch users from Entra ID
  const { 
    data: users, 
    isLoading: usersLoading, 
    refetch: refetchUsers 
  } = useQuery({
    queryKey: ['entra-users', integration?.id],
    queryFn: () => integration?.id ? integrationApi.getEntraIDUsers(integration.id) : Promise.resolve([]),
    enabled: !!integration?.id && activeTab === 'users',
  });

  // Fetch groups from Entra ID
  const { 
    data: groups, 
    isLoading: groupsLoading, 
    refetch: refetchGroups 
  } = useQuery({
    queryKey: ['entra-groups', integration?.id],
    queryFn: () => integration?.id ? integrationApi.getEntraIDGroups(integration.id) : Promise.resolve([]),
    enabled: !!integration?.id && activeTab === 'groups',
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
        message: `Synchronization completed successfully. ${result.stats?.users_synced || 0} users and ${result.stats?.groups_synced || 0} groups synchronized.`
      });
      
      // Refetch data after sync
      if (activeTab === 'history') refetchHistory();
      if (activeTab === 'users') refetchUsers();
      if (activeTab === 'groups') refetchGroups();
      
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

  // Handle role assignment
  const handleRoleAssignment = async (userId, role) => {
    if (!integration?.id || !userId) return;
    
    try {
      await integrationApi.assignUserRole(integration.id, userId, role);
      refetchUsers();
    } catch (error) {
      setSyncResult({
        success: false,
        message: `Failed to assign role: ${error.message}`
      });
    }
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  // Filter users or groups based on search query
  const filterItems = (items) => {
    if (!items) return [];
    if (!searchQuery) return items;
    
    return items.filter(item => {
      const lowerCaseSearch = searchQuery.toLowerCase();
      return (
        (item.displayName && item.displayName.toLowerCase().includes(lowerCaseSearch)) ||
        (item.givenName && item.givenName.toLowerCase().includes(lowerCaseSearch)) ||
        (item.surname && item.surname.toLowerCase().includes(lowerCaseSearch)) ||
        (item.mail && item.mail.toLowerCase().includes(lowerCaseSearch)) ||
        (item.userPrincipalName && item.userPrincipalName.toLowerCase().includes(lowerCaseSearch)) ||
        (item.description && item.description.toLowerCase().includes(lowerCaseSearch))
      );
    });
  };

  // Filtered items based on active tab
  const filteredItems = activeTab === 'users' 
    ? filterItems(users) 
    : activeTab === 'groups' 
      ? filterItems(groups) 
      : [];

  if (isConfiguring) {
    return (
      <IntegrationForm 
        type="entra_id" 
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
          <FiUser className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h5 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            No Microsoft Entra ID Integration Configured
          </h5>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Connect to Microsoft Entra ID to synchronize users and enable single sign-on.
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
              {integration.name || 'Microsoft Entra ID Integration'}
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

        {selectedUser && (
          <div className="mb-4">
            <Card>
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-bold text-gray-900 dark:text-white">
                  User Details: {selectedUser.displayName}
                </h4>
                <Button color="light" size="xs" onClick={() => setSelectedUser(null)}>
                  Close
                </Button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex flex-col items-center">
                  <Avatar 
                    size="xl"
                    img={selectedUser.profilePhoto || null}
                    rounded
                    alt={selectedUser.displayName}
                    className="mb-3"
                  >
                    {!selectedUser.profilePhoto && selectedUser.displayName?.charAt(0).toUpperCase()}
                  </Avatar>
                  <h5 className="text-lg font-semibold mb-1">{selectedUser.displayName}</h5>
                  <p className="text-gray-500 mb-3">{selectedUser.jobTitle || 'No job title'}</p>
                  
                  <div className="w-full mt-4">
                    <h6 className="font-medium mb-2">Role Assignment</h6>
                    <div className="flex gap-2">
                      <Button 
                        size="sm" 
                        color={selectedUser.role === 'admin' ? 'dark' : 'light'} 
                        onClick={() => handleRoleAssignment(selectedUser.id, 'admin')}
                      >
                        Admin
                      </Button>
                      <Button 
                        size="sm" 
                        color={selectedUser.role === 'editor' ? 'dark' : 'light'}
                        onClick={() => handleRoleAssignment(selectedUser.id, 'editor')}
                      >
                        Editor
                      </Button>
                      <Button 
                        size="sm" 
                        color={selectedUser.role === 'viewer' ? 'dark' : 'light'}
                        onClick={() => handleRoleAssignment(selectedUser.id, 'viewer')}
                      >
                        Viewer
                      </Button>
                    </div>
                  </div>
                </div>
                
                <div>
                  <Table>
                    <Table.Body className="divide-y">
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Email</Table.Cell>
                        <Table.Cell>{selectedUser.mail || selectedUser.userPrincipalName || 'N/A'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Username</Table.Cell>
                        <Table.Cell>{selectedUser.userPrincipalName || 'N/A'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Department</Table.Cell>
                        <Table.Cell>{selectedUser.department || 'N/A'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Office</Table.Cell>
                        <Table.Cell>{selectedUser.officeLocation || 'N/A'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Phone</Table.Cell>
                        <Table.Cell>{selectedUser.businessPhones?.[0] || 'N/A'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Account Created</Table.Cell>
                        <Table.Cell>{formatDate(selectedUser.createdDateTime)}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Last Sign In</Table.Cell>
                        <Table.Cell>{formatDate(selectedUser.signInActivity?.lastSignInDateTime) || 'N/A'}</Table.Cell>
                      </Table.Row>
                    </Table.Body>
                  </Table>
                </div>
              </div>
            </Card>
          </div>
        )}

        <Tabs.Group
          aria-label="Integration tabs"
          style="underline"
          onActiveTabChange={(index) => {
            const tabs = ['summary', 'users', 'groups', 'history'];
            setActiveTab(tabs[index]);
            setSelectedUser(null);
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
                        <Table.Cell className="font-medium">Tenant ID</Table.Cell>
                        <Table.Cell>{integration.configuration?.tenant_id || 'Not configured'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Client ID</Table.Cell>
                        <Table.Cell>{integration.configuration?.client_id || 'Not configured'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Sync Users</Table.Cell>
                        <Table.Cell>{integration.configuration?.sync_users ? 'Yes' : 'No'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Sync Groups</Table.Cell>
                        <Table.Cell>{integration.configuration?.sync_groups ? 'Yes' : 'No'}</Table.Cell>
                      </Table.Row>
                    </Table.Body>
                  </Table>
                </div>
                
                <div>
                  <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Synchronization Stats</h5>
                  <Table>
                    <Table.Body className="divide-y">
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Users</Table.Cell>
                        <Table.Cell>{integration.stats?.users_count || '0'}</Table.Cell>
                      </Table.Row>
                      <Table.Row className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">Groups</Table.Cell>
                        <Table.Cell>{integration.stats?.groups_count || '0'}</Table.Cell>
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
          
          <Tabs.Item title="Users">
            <div className="mb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div className="flex-1">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                    <FiSearch className="w-5 h-5 text-gray-500" />
                  </div>
                  <TextInput
                    id="user-search"
                    type="search"
                    placeholder="Search users by name or email..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 w-full"
                  />
                </div>
              </div>
              
              <div>
                <Button color="light">
                  <FiUserPlus className="mr-2 h-5 w-5" />
                  Import Users
                </Button>
              </div>
            </div>
            
            {usersLoading ? (
              <div className="flex justify-center py-8">
                <Spinner size="xl" />
              </div>
            ) : !users || users.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  No users found.
                </p>
                <Button onClick={handleSync} disabled={syncInProgress}>
                  <FiRefreshCw className="mr-2 h-5 w-5" />
                  Sync Users
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <Table.Head>
                    <Table.HeadCell>User</Table.HeadCell>
                    <Table.HeadCell>Email</Table.HeadCell>
                    <Table.HeadCell>Role</Table.HeadCell>
                    <Table.HeadCell>Department</Table.HeadCell>
                    <Table.HeadCell>Status</Table.HeadCell>
                    <Table.HeadCell>Actions</Table.HeadCell>
                  </Table.Head>
                  <Table.Body className="divide-y">
                    {filteredItems.map((user) => (
                      <Table.Row key={user.id} className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">
                          <div className="flex items-center">
                            <Avatar size="sm" img={user.profilePhoto || null} rounded className="mr-3">
                              {!user.profilePhoto && user.displayName?.charAt(0).toUpperCase()}
                            </Avatar>
                            <div>
                              <div className="font-medium">{user.displayName}</div>
                              <div className="text-xs text-gray-500">{user.jobTitle || 'No title'}</div>
                            </div>
                          </div>
                        </Table.Cell>
                        <Table.Cell>{user.mail || user.userPrincipalName}</Table.Cell>
                        <Table.Cell>
                          <Badge
                            color={
                              user.role === 'admin' ? 'red' :
                              user.role === 'editor' ? 'blue' :
                              'gray'
                            }
                          >
                            {user.role || 'Not assigned'}
                          </Badge>
                        </Table.Cell>
                        <Table.Cell>{user.department || 'N/A'}</Table.Cell>
                        <Table.Cell>
                          <Badge 
                            color={user.accountEnabled ? 'success' : 'gray'}
                          >
                            {user.accountEnabled ? 'Active' : 'Disabled'}
                          </Badge>
                        </Table.Cell>
                        <Table.Cell>
                          <Button 
                            size="xs" 
                            onClick={() => setSelectedUser(user)}
                          >
                            View Details
                          </Button>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table>
              </div>
            )}
          </Tabs.Item>
          
          <Tabs.Item title="Groups">
            <div className="mb-4">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <FiSearch className="w-5 h-5 text-gray-500" />
                </div>
                <TextInput
                  id="group-search"
                  type="search"
                  placeholder="Search groups..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-full"
                />
              </div>
            </div>
            
            {groupsLoading ? (
              <div className="flex justify-center py-8">
                <Spinner size="xl" />
              </div>
            ) : !groups || groups.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  No groups found.
                </p>
                <Button onClick={handleSync} disabled={syncInProgress}>
                  <FiRefreshCw className="mr-2 h-5 w-5" />
                  Sync Groups
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <Table.Head>
                    <Table.HeadCell>Name</Table.HeadCell>
                    <Table.HeadCell>Description</Table.HeadCell>
                    <Table.HeadCell>Members</Table.HeadCell>
                    <Table.HeadCell>Type</Table.HeadCell>
                    <Table.HeadCell>Created</Table.HeadCell>
                  </Table.Head>
                  <Table.Body className="divide-y">
                    {filteredItems.map((group) => (
                      <Table.Row key={group.id} className="bg-white dark:bg-gray-800">
                        <Table.Cell className="font-medium">
                          <div className="flex items-center">
                            <FiUsers className="mr-2 h-5 w-5 text-blue-500" />
                            {group.displayName}
                          </div>
                        </Table.Cell>
                        <Table.Cell>{group.description || 'No description'}</Table.Cell>
                        <Table.Cell>{group.members?.length || 0}</Table.Cell>
                        <Table.Cell>
                          <Badge 
                            color={
                              group.securityEnabled ? 'blue' :
                              group.mailEnabled ? 'purple' :
                              'gray'
                            }
                          >
                            {group.securityEnabled ? 'Security' : 
                             group.mailEnabled ? 'Mail' : 
                             'Distribution'}
                          </Badge>
                        </Table.Cell>
                        <Table.Cell>{formatDate(group.createdDateTime)}</Table.Cell>
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
                    <Table.HeadCell>Users Synced</Table.HeadCell>
                    <Table.HeadCell>Groups Synced</Table.HeadCell>
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
                        <Table.Cell>{history.details?.users_synced || 0}</Table.Cell>
                        <Table.Cell>{history.details?.groups_synced || 0}</Table.Cell>
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

export default EntraIDIntegration;