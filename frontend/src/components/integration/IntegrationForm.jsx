import React, { useState, useEffect } from 'react';
import { Card, Button, Label, TextInput, Select, Alert, Checkbox } from 'flowbite-react';
import { FiAlertCircle, FiCheckCircle, FiSave, FiX } from 'react-icons/fi';

import { integrationApi } from '../../services/api';

const IntegrationForm = ({ type, integration, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    status: 'inactive',
    configuration: {},
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Initialize form data based on integration type and provided integration
  useEffect(() => {
    if (integration) {
      setFormData({
        name: integration.name || '',
        status: integration.status || 'inactive',
        configuration: integration.configuration || {},
      });
    } else {
      // Default configurations based on type
      let defaultConfig = {};

      switch (type) {
        case 'halo_itsm':
          defaultConfig = {
            api_url: '',
            api_key: '',
            client_id: '',
            sync_frequency: 'daily',
            sync_ci_types: ['server', 'application', 'database', 'network'],
          };
          break;
        case 'entra_id':
          defaultConfig = {
            tenant_id: '',
            client_id: '',
            client_secret: '',
            sync_users: true,
            sync_groups: true,
          };
          break;
        case 'sharepoint':
          defaultConfig = {
            site_url: '',
            client_id: '',
            client_secret: '',
            document_library: 'Documents',
          };
          break;
        case 'power_bi':
          defaultConfig = {
            workspace_id: '',
            client_id: '',
            client_secret: '',
            tenant_id: '',
          };
          break;
        case 'servicenow':
          defaultConfig = {
            instance_url: '',
            username: '',
            password: '',
            sync_tables: ['cmdb_ci', 'cmdb_ci_service', 'cmdb_ci_appl'],
          };
          break;
        case 'jira':
          defaultConfig = {
            site_url: '',
            username: '',
            api_token: '',
            project_key: '',
          };
          break;
        default:
          defaultConfig = {};
      }

      setFormData({
        name: getTypeName(type),
        status: 'inactive',
        configuration: defaultConfig,
      });
    }
  }, [type, integration]);

  // Get display name for integration type
  const getTypeName = (integrationType) => {
    switch (integrationType) {
      case 'halo_itsm':
        return 'Halo ITSM';
      case 'entra_id':
        return 'Microsoft Entra ID';
      case 'sharepoint':
        return 'SharePoint';
      case 'power_bi':
        return 'Power BI';
      case 'servicenow':
        return 'ServiceNow';
      case 'jira':
        return 'Jira';
      default:
        return integrationType.charAt(0).toUpperCase() + integrationType.slice(1).replace('_', ' ');
    }
  };

  // Handle form field changes
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    if (name.includes('.')) {
      // Handle nested configuration properties
      const [parent, child] = name.split('.');
      setFormData({
        ...formData,
        [parent]: {
          ...formData[parent],
          [child]: type === 'checkbox' ? checked : value,
        },
      });
    } else {
      // Handle top-level properties
      setFormData({
        ...formData,
        [name]: type === 'checkbox' ? checked : value,
      });
    }

    // Clear messages when form changes
    setError('');
    setSuccess('');
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const payload = {
        name: formData.name,
        status: formData.status,
        integration_type: type,
        configuration: formData.configuration,
      };

      let result;
      if (integration?.id) {
        // Update existing integration
        result = await integrationApi.updateIntegration(integration.id, payload);
      } else {
        // Create new integration
        result = await integrationApi.createIntegration(payload);
      }

      setSuccess('Integration successfully saved');
      setTimeout(() => {
        if (onSave) onSave(result);
      }, 1500);
    } catch (err) {
      console.error('Error saving integration:', err);
      setError(err.response?.data?.message || 'Failed to save integration');
    } finally {
      setLoading(false);
    }
  };

  // Test the integration
  const handleTest = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const result = await integrationApi.testIntegration({
        integration_type: type,
        configuration: formData.configuration,
      });

      if (result.success) {
        setSuccess('Connection test successful');
      } else {
        setError(result.message || 'Connection test failed');
      }
    } catch (err) {
      console.error('Error testing integration:', err);
      setError(err.response?.data?.message || 'Failed to test integration');
    } finally {
      setLoading(false);
    }
  };

  // Render configuration fields based on integration type
  const renderConfigurationFields = () => {
    switch (type) {
      case 'halo_itsm':
        return (
          <>
            <div className="mb-4">
              <Label htmlFor="configuration.api_url" value="API URL" />
              <TextInput
                id="configuration.api_url"
                name="configuration.api_url"
                value={formData.configuration.api_url || ''}
                onChange={handleChange}
                placeholder="https://your-instance.haloitsm.com/api"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.api_key" value="API Key" />
              <TextInput
                id="configuration.api_key"
                name="configuration.api_key"
                type="password"
                value={formData.configuration.api_key || ''}
                onChange={handleChange}
                placeholder="Your Halo ITSM API Key"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.client_id" value="Client ID" />
              <TextInput
                id="configuration.client_id"
                name="configuration.client_id"
                value={formData.configuration.client_id || ''}
                onChange={handleChange}
                placeholder="Your Halo ITSM Client ID"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.sync_frequency" value="Synchronization Frequency" />
              <Select
                id="configuration.sync_frequency"
                name="configuration.sync_frequency"
                value={formData.configuration.sync_frequency || 'daily'}
                onChange={handleChange}
                required
              >
                <option value="hourly">Hourly</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="manual">Manual Only</option>
              </Select>
            </div>
          </>
        );
      
      case 'entra_id':
        return (
          <>
            <div className="mb-4">
              <Label htmlFor="configuration.tenant_id" value="Tenant ID" />
              <TextInput
                id="configuration.tenant_id"
                name="configuration.tenant_id"
                value={formData.configuration.tenant_id || ''}
                onChange={handleChange}
                placeholder="Your Microsoft Entra ID Tenant ID"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.client_id" value="Client ID" />
              <TextInput
                id="configuration.client_id"
                name="configuration.client_id"
                value={formData.configuration.client_id || ''}
                onChange={handleChange}
                placeholder="Application (client) ID"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.client_secret" value="Client Secret" />
              <TextInput
                id="configuration.client_secret"
                name="configuration.client_secret"
                type="password"
                value={formData.configuration.client_secret || ''}
                onChange={handleChange}
                placeholder="Application client secret"
                required
              />
            </div>
            <div className="flex items-center gap-2 mb-4">
              <Checkbox
                id="configuration.sync_users"
                name="configuration.sync_users"
                checked={formData.configuration.sync_users || false}
                onChange={handleChange}
              />
              <Label htmlFor="configuration.sync_users">Synchronize Users</Label>
            </div>
            <div className="flex items-center gap-2 mb-4">
              <Checkbox
                id="configuration.sync_groups"
                name="configuration.sync_groups"
                checked={formData.configuration.sync_groups || false}
                onChange={handleChange}
              />
              <Label htmlFor="configuration.sync_groups">Synchronize Groups</Label>
            </div>
          </>
        );
        
      case 'sharepoint':
        return (
          <>
            <div className="mb-4">
              <Label htmlFor="configuration.site_url" value="SharePoint Site URL" />
              <TextInput
                id="configuration.site_url"
                name="configuration.site_url"
                value={formData.configuration.site_url || ''}
                onChange={handleChange}
                placeholder="https://yourcompany.sharepoint.com/sites/architecture"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.client_id" value="Client ID" />
              <TextInput
                id="configuration.client_id"
                name="configuration.client_id"
                value={formData.configuration.client_id || ''}
                onChange={handleChange}
                placeholder="Application (client) ID"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.client_secret" value="Client Secret" />
              <TextInput
                id="configuration.client_secret"
                name="configuration.client_secret"
                type="password"
                value={formData.configuration.client_secret || ''}
                onChange={handleChange}
                placeholder="Application client secret"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.document_library" value="Document Library" />
              <TextInput
                id="configuration.document_library"
                name="configuration.document_library"
                value={formData.configuration.document_library || ''}
                onChange={handleChange}
                placeholder="Documents"
                required
              />
            </div>
          </>
        );
      
      case 'power_bi':
        return (
          <>
            <div className="mb-4">
              <Label htmlFor="configuration.workspace_id" value="Workspace ID" />
              <TextInput
                id="configuration.workspace_id"
                name="configuration.workspace_id"
                value={formData.configuration.workspace_id || ''}
                onChange={handleChange}
                placeholder="Power BI Workspace ID"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.tenant_id" value="Tenant ID" />
              <TextInput
                id="configuration.tenant_id"
                name="configuration.tenant_id"
                value={formData.configuration.tenant_id || ''}
                onChange={handleChange}
                placeholder="Your Microsoft Tenant ID"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.client_id" value="Client ID" />
              <TextInput
                id="configuration.client_id"
                name="configuration.client_id"
                value={formData.configuration.client_id || ''}
                onChange={handleChange}
                placeholder="Application (client) ID"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.client_secret" value="Client Secret" />
              <TextInput
                id="configuration.client_secret"
                name="configuration.client_secret"
                type="password"
                value={formData.configuration.client_secret || ''}
                onChange={handleChange}
                placeholder="Application client secret"
                required
              />
            </div>
          </>
        );
      
      case 'servicenow':
        return (
          <>
            <div className="mb-4">
              <Label htmlFor="configuration.instance_url" value="Instance URL" />
              <TextInput
                id="configuration.instance_url"
                name="configuration.instance_url"
                value={formData.configuration.instance_url || ''}
                onChange={handleChange}
                placeholder="https://your-instance.service-now.com"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.username" value="Username" />
              <TextInput
                id="configuration.username"
                name="configuration.username"
                value={formData.configuration.username || ''}
                onChange={handleChange}
                placeholder="ServiceNow username"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.password" value="Password" />
              <TextInput
                id="configuration.password"
                name="configuration.password"
                type="password"
                value={formData.configuration.password || ''}
                onChange={handleChange}
                placeholder="ServiceNow password"
                required
              />
            </div>
          </>
        );
      
      case 'jira':
        return (
          <>
            <div className="mb-4">
              <Label htmlFor="configuration.site_url" value="Jira Site URL" />
              <TextInput
                id="configuration.site_url"
                name="configuration.site_url"
                value={formData.configuration.site_url || ''}
                onChange={handleChange}
                placeholder="https://your-company.atlassian.net"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.username" value="Email Address" />
              <TextInput
                id="configuration.username"
                name="configuration.username"
                value={formData.configuration.username || ''}
                onChange={handleChange}
                placeholder="Your Jira account email"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.api_token" value="API Token" />
              <TextInput
                id="configuration.api_token"
                name="configuration.api_token"
                type="password"
                value={formData.configuration.api_token || ''}
                onChange={handleChange}
                placeholder="Your Jira API token"
                required
              />
            </div>
            <div className="mb-4">
              <Label htmlFor="configuration.project_key" value="Project Key" />
              <TextInput
                id="configuration.project_key"
                name="configuration.project_key"
                value={formData.configuration.project_key || ''}
                onChange={handleChange}
                placeholder="PROJ"
                required
              />
            </div>
          </>
        );
        
      default:
        return (
          <div className="mb-4">
            <Label htmlFor="configuration" value="Configuration JSON" />
            <textarea
              id="configuration"
              name="configuration"
              className="block w-full p-2.5 text-sm text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
              value={JSON.stringify(formData.configuration, null, 2)}
              onChange={(e) => {
                try {
                  const config = JSON.parse(e.target.value);
                  setFormData({
                    ...formData,
                    configuration: config,
                  });
                } catch (err) {
                  // Do nothing on invalid JSON
                }
              }}
              rows="10"
            />
          </div>
        );
    }
  };

  return (
    <Card>
      <h5 className="text-xl font-bold leading-none text-gray-900 dark:text-white mb-4">
        {integration ? 'Edit Integration' : 'New Integration'}: {getTypeName(type)}
      </h5>

      {error && (
        <Alert color="failure" icon={FiAlertCircle} className="mb-4">
          {error}
        </Alert>
      )}

      {success && (
        <Alert color="success" icon={FiCheckCircle} className="mb-4">
          {success}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <Label htmlFor="name" value="Name" />
          <TextInput
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Integration name"
            required
          />
        </div>

        <div className="mb-4">
          <Label htmlFor="status" value="Status" />
          <Select
            id="status"
            name="status"
            value={formData.status}
            onChange={handleChange}
            required
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </Select>
        </div>

        <h6 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 mt-6">
          Configuration
        </h6>

        {renderConfigurationFields()}

        <div className="flex justify-end space-x-3 mt-6">
          <Button color="gray" onClick={onCancel} disabled={loading}>
            <FiX className="mr-2 h-5 w-5" />
            Cancel
          </Button>
          <Button color="light" onClick={handleTest} disabled={loading}>
            Test Connection
          </Button>
          <Button type="submit" disabled={loading}>
            <FiSave className="mr-2 h-5 w-5" />
            {loading ? 'Saving...' : 'Save Integration'}
          </Button>
        </div>
      </form>
    </Card>
  );
};

export default IntegrationForm;