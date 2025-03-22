import React from 'react';
import { Badge, ListGroup } from 'flowbite-react';
import { FiLink2, FiCheckCircle, FiAlertCircle, FiClock } from 'react-icons/fi';

const IntegrationList = ({ integrations, onSelect, activeId }) => {
  // Get status icon based on status
  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <FiCheckCircle className="h-5 w-5 text-green-500" />;
      case 'inactive':
        return <FiClock className="h-5 w-5 text-gray-500" />;
      case 'error':
        return <FiAlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <FiLink2 className="h-5 w-5 text-blue-500" />;
    }
  };

  // Get status color
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

  // Format integration type
  const formatIntegrationType = (type) => {
    switch (type) {
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
        return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ');
    }
  };

  if (!integrations || integrations.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500">
        No integrations configured yet
      </div>
    );
  }

  return (
    <ListGroup className="border-0">
      {integrations.map((integration) => (
        <ListGroup.Item
          key={integration.id}
          active={integration.id === activeId}
          className={`cursor-pointer ${integration.id === activeId ? 'bg-blue-50 dark:bg-blue-900' : ''}`}
          onClick={() => onSelect(integration)}
        >
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center">
              {getStatusIcon(integration.status)}
              <span className="ml-2 font-medium">{integration.name || formatIntegrationType(integration.integration_type)}</span>
            </div>
            <Badge color={getStatusColor(integration.status)} size="sm">
              {integration.status}
            </Badge>
          </div>
          <div className="mt-1 pl-7 text-xs text-gray-500">
            {integration.last_sync_at
              ? `Last synchronized: ${new Date(integration.last_sync_at).toLocaleString()}`
              : 'Never synchronized'}
          </div>
        </ListGroup.Item>
      ))}
    </ListGroup>
  );
};

export default IntegrationList;