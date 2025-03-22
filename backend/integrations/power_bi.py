"""
Enterprise Architecture Solution - Power BI Integration

This module provides integration with Power BI for advanced visualization and reporting
capabilities for EA artifacts and analytics.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

import requests
import msal

from .integration_base import IntegrationBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PowerBIIntegration(IntegrationBase):
    """Integration with Power BI for EA visualization and reporting."""
    
    def __init__(self, supabase_client, config_id: str = None):
        """Initialize the Power BI integration.
        
        Args:
            supabase_client: Initialized Supabase client
            config_id: ID of the integration configuration in the database
        """
        super().__init__(supabase_client, config_id)
        self.access_token = None
    
    def _get_integration_type(self) -> str:
        """Get the integration type identifier."""
        return "power_bi"
    
    def configure(self, client_id: str, client_secret: str, tenant_id: str,
                 workspace_id: str = None) -> Dict[str, Any]:
        """Configure the Power BI integration.
        
        Args:
            client_id: Microsoft Entra ID client ID
            client_secret: Microsoft Entra ID client secret
            tenant_id: Microsoft Entra ID tenant ID
            workspace_id: Optional Power BI workspace ID
            
        Returns:
            Configuration status
        """
        self.config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
            "last_configured": datetime.now().isoformat()
        }
        
        self._save_config()
        
        # Test the connection to validate the configuration
        test_result = self.test_connection()
        
        return {
            "success": test_result.get("success", False),
            "message": test_result.get("message", ""),
            "config_id": self.config_id
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Power BI."""
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for Power BI API"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Test access to Power BI
            workspace_id = self.config.get("workspace_id")
            
            if workspace_id:
                # Test specific workspace
                workspace_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
                workspace_response = requests.get(workspace_url, headers=headers)
                
                if workspace_response.status_code == 200:
                    workspace_data = workspace_response.json()
                    return {
                        "success": True,
                        "message": "Successfully connected to Power BI workspace",
                        "workspace_name": workspace_data.get("name")
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to connect to Power BI workspace. Status code: {workspace_response.status_code}, Response: {workspace_response.text}"
                    }
            else:
                # Test general access
                workspaces_url = "https://api.powerbi.com/v1.0/myorg/groups"
                workspaces_response = requests.get(workspaces_url, headers=headers)
                
                if workspaces_response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Successfully connected to Power BI API",
                        "workspaces_count": len(workspaces_response.json().get("value", []))
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to connect to Power BI API. Status code: {workspaces_response.status_code}, Response: {workspaces_response.text}"
                    }
        except Exception as e:
            logger.error(f"Error testing Power BI connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to Power BI: {str(e)}"
            }
    
    def _get_access_token(self) -> None:
        """Get access token for Power BI API."""
        try:
            # Initialize MSAL app
            app = msal.ConfidentialClientApplication(
                client_id=self.config.get("client_id"),
                client_credential=self.config.get("client_secret"),
                authority=f"https://login.microsoftonline.com/{self.config.get('tenant_id')}"
            )
            
            # Get token using client credentials flow
            scopes = ["https://analysis.windows.net/powerbi/api/.default"]
            token_result = app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in token_result:
                self.access_token = token_result["access_token"]
            else:
                logger.error(f"Failed to obtain access token: {token_result.get('error_description')}")
                self.access_token = None
        except Exception as e:
            logger.error(f"Error obtaining access token: {str(e)}")
            self.access_token = None
    
    def get_workspaces(self) -> Dict[str, Any]:
        """Get available Power BI workspaces.
        
        Returns:
            List of workspaces
        """
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for Power BI API"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Get workspaces
            workspaces_url = "https://api.powerbi.com/v1.0/myorg/groups"
            workspaces_response = requests.get(workspaces_url, headers=headers)
            
            if workspaces_response.status_code == 200:
                workspaces_data = workspaces_response.json()
                workspaces = workspaces_data.get("value", [])
                
                return {
                    "success": True,
                    "workspaces": [
                        {
                            "id": workspace.get("id"),
                            "name": workspace.get("name"),
                            "type": workspace.get("type"),
                            "state": workspace.get("state")
                        }
                        for workspace in workspaces
                    ]
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to get Power BI workspaces. Status code: {workspaces_response.status_code}, Response: {workspaces_response.text}"
                }
        except Exception as e:
            logger.error(f"Error getting Power BI workspaces: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting Power BI workspaces: {str(e)}"
            }
    
    def get_reports(self, workspace_id: str = None) -> Dict[str, Any]:
        """Get reports from a Power BI workspace.
        
        Args:
            workspace_id: Optional workspace ID (uses configured workspace if not provided)
            
        Returns:
            List of reports
        """
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for Power BI API"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Use provided workspace ID or fall back to configured one
            workspace_id = workspace_id or self.config.get("workspace_id")
            
            if not workspace_id:
                return {
                    "success": False,
                    "message": "Workspace ID not provided and not configured"
                }
            
            # Get reports
            reports_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
            reports_response = requests.get(reports_url, headers=headers)
            
            if reports_response.status_code == 200:
                reports_data = reports_response.json()
                reports = reports_data.get("value", [])
                
                return {
                    "success": True,
                    "reports": [
                        {
                            "id": report.get("id"),
                            "name": report.get("name"),
                            "web_url": report.get("webUrl"),
                            "embed_url": report.get("embedUrl"),
                            "dataset_id": report.get("datasetId")
                        }
                        for report in reports
                    ]
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to get Power BI reports. Status code: {reports_response.status_code}, Response: {reports_response.text}"
                }
        except Exception as e:
            logger.error(f"Error getting Power BI reports: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting Power BI reports: {str(e)}"
            }
    
    def get_dashboards(self, workspace_id: str = None) -> Dict[str, Any]:
        """Get dashboards from a Power BI workspace.
        
        Args:
            workspace_id: Optional workspace ID (uses configured workspace if not provided)
            
        Returns:
            List of dashboards
        """
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for Power BI API"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Use provided workspace ID or fall back to configured one
            workspace_id = workspace_id or self.config.get("workspace_id")
            
            if not workspace_id:
                return {
                    "success": False,
                    "message": "Workspace ID not provided and not configured"
                }
            
            # Get dashboards
            dashboards_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/dashboards"
            dashboards_response = requests.get(dashboards_url, headers=headers)
            
            if dashboards_response.status_code == 200:
                dashboards_data = dashboards_response.json()
                dashboards = dashboards_data.get("value", [])
                
                return {
                    "success": True,
                    "dashboards": [
                        {
                            "id": dashboard.get("id"),
                            "name": dashboard.get("displayName"),
                            "web_url": dashboard.get("webUrl"),
                            "embed_url": dashboard.get("embedUrl")
                        }
                        for dashboard in dashboards
                    ]
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to get Power BI dashboards. Status code: {dashboards_response.status_code}, Response: {dashboards_response.text}"
                }
        except Exception as e:
            logger.error(f"Error getting Power BI dashboards: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting Power BI dashboards: {str(e)}"
            }
    
    def get_datasets(self, workspace_id: str = None) -> Dict[str, Any]:
        """Get datasets from a Power BI workspace.
        
        Args:
            workspace_id: Optional workspace ID (uses configured workspace if not provided)
            
        Returns:
            List of datasets
        """
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for Power BI API"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Use provided workspace ID or fall back to configured one
            workspace_id = workspace_id or self.config.get("workspace_id")
            
            if not workspace_id:
                return {
                    "success": False,
                    "message": "Workspace ID not provided and not configured"
                }
            
            # Get datasets
            datasets_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
            datasets_response = requests.get(datasets_url, headers=headers)
            
            if datasets_response.status_code == 200:
                datasets_data = datasets_response.json()
                datasets = datasets_data.get("value", [])
                
                return {
                    "success": True,
                    "datasets": [
                        {
                            "id": dataset.get("id"),
                            "name": dataset.get("name"),
                            "configured_by": dataset.get("configuredBy"),
                            "is_refreshable": dataset.get("isRefreshable")
                        }
                        for dataset in datasets
                    ]
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to get Power BI datasets. Status code: {datasets_response.status_code}, Response: {datasets_response.text}"
                }
        except Exception as e:
            logger.error(f"Error getting Power BI datasets: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting Power BI datasets: {str(e)}"
            }
    
    def get_embed_token(self, report_id: str, dataset_id: str = None, 
                       workspace_id: str = None) -> Dict[str, Any]:
        """Generate an embed token for a Power BI report.
        
        Args:
            report_id: ID of the report to embed
            dataset_id: Optional dataset ID (can be obtained from report)
            workspace_id: Optional workspace ID (uses configured workspace if not provided)
            
        Returns:
            Embed token information
        """
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for Power BI API"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Use provided workspace ID or fall back to configured one
            workspace_id = workspace_id or self.config.get("workspace_id")
            
            if not workspace_id:
                return {
                    "success": False,
                    "message": "Workspace ID not provided and not configured"
                }
            
            # If dataset ID is not provided, get it from the report
            if not dataset_id:
                report_info = self._get_report_info(report_id, workspace_id)
                if not report_info:
                    return {
                        "success": False,
                        "message": f"Failed to get dataset ID for report {report_id}"
                    }
                dataset_id = report_info.get("datasetId")
            
            # Generate embed token
            token_url = "https://api.powerbi.com/v1.0/myorg/GenerateToken"
            token_payload = {
                "datasets": [{"id": dataset_id}],
                "reports": [{"id": report_id}]
            }
            
            token_response = requests.post(token_url, headers=headers, json=token_payload)
            
            if token_response.status_code == 200:
                token_data = token_response.json()
                
                return {
                    "success": True,
                    "token": token_data.get("token"),
                    "token_id": token_data.get("tokenId"),
                    "expiration": token_data.get("expiration")
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to generate embed token. Status code: {token_response.status_code}, Response: {token_response.text}"
                }
        except Exception as e:
            logger.error(f"Error generating Power BI embed token: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating Power BI embed token: {str(e)}"
            }
    
    def _get_report_info(self, report_id: str, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Get report information.
        
        Args:
            report_id: ID of the report
            workspace_id: ID of the workspace
            
        Returns:
            Report information
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            report_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
            report_response = requests.get(report_url, headers=headers)
            
            if report_response.status_code == 200:
                return report_response.json()
            else:
                logger.error(f"Failed to get report info. Status code: {report_response.status_code}, Response: {report_response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting report info: {str(e)}")
            return None
    
    def export_ea_data_to_dataset(self, dataset_name: str, workspace_id: str = None,
                                tables: Dict[str, List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Export EA data to a Power BI dataset.
        
        Args:
            dataset_name: Name of the dataset to create or update
            workspace_id: Optional workspace ID (uses configured workspace if not provided)
            tables: Dictionary of table names to lists of records
            
        Returns:
            Export results
        """
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for Power BI API"
                }
            
            # Use provided workspace ID or fall back to configured one
            workspace_id = workspace_id or self.config.get("workspace_id")
            
            if not workspace_id:
                return {
                    "success": False,
                    "message": "Workspace ID not provided and not configured"
                }
            
            # If no tables are provided, fetch EA data
            if not tables:
                tables = self._get_ea_data()
            
            # Create or get dataset
            dataset_id = self._get_or_create_dataset(dataset_name, workspace_id, tables)
            
            if not dataset_id:
                return {
                    "success": False,
                    "message": "Failed to create or get dataset"
                }
            
            # Push data to dataset
            results = {}
            
            for table_name, records in tables.items():
                push_result = self._push_data_to_table(dataset_id, workspace_id, table_name, records)
                results[table_name] = push_result
            
            # Check if any table failed
            failed_tables = [table_name for table_name, result in results.items() if not result.get("success")]
            
            if failed_tables:
                return {
                    "success": False,
                    "message": f"Failed to push data to tables: {', '.join(failed_tables)}",
                    "results": results
                }
            else:
                return {
                    "success": True,
                    "message": f"Successfully exported EA data to dataset {dataset_name}",
                    "dataset_id": dataset_id,
                    "results": results
                }
        except Exception as e:
            logger.error(f"Error exporting EA data to Power BI: {str(e)}")
            return {
                "success": False,
                "message": f"Error exporting EA data to Power BI: {str(e)}"
            }
    
    def _get_ea_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get EA data from the repository.
        
        Returns:
            Dictionary of table names to lists of records
        """
        try:
            tables = {}
            
            # Get models
            models_query = self.supabase.table("ea_models").select("*").execute()
            if models_query.data:
                tables["Models"] = models_query.data
            
            # Get elements
            elements_query = self.supabase.table("ea_elements").select("*").execute()
            if elements_query.data:
                tables["Elements"] = elements_query.data
            
            # Get relationships
            relationships_query = self.supabase.table("ea_relationships").select("*").execute()
            if relationships_query.data:
                tables["Relationships"] = relationships_query.data
            
            # Get views
            views_query = self.supabase.table("ea_views").select("*").execute()
            if views_query.data:
                tables["Views"] = views_query.data
            
            return tables
        except Exception as e:
            logger.error(f"Error getting EA data: {str(e)}")
            return {}
    
    def _get_or_create_dataset(self, dataset_name: str, workspace_id: str,
                           tables: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
        """Get or create a Power BI dataset.
        
        Args:
            dataset_name: Name of the dataset
            workspace_id: ID of the workspace
            tables: Dictionary of table names to lists of records
            
        Returns:
            Dataset ID
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Check if dataset exists
            datasets_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
            datasets_response = requests.get(datasets_url, headers=headers)
            
            if datasets_response.status_code == 200:
                datasets = datasets_response.json().get("value", [])
                matching_dataset = next((dataset for dataset in datasets if dataset.get("name") == dataset_name), None)
                
                if matching_dataset:
                    return matching_dataset.get("id")
            
            # Create dataset if it doesn't exist
            create_dataset_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
            
            # Build the dataset schema
            tables_schema = []
            for table_name, records in tables.items():
                if records and len(records) > 0:
                    columns = []
                    
                    # Get the first record to determine column types
                    first_record = records[0]
                    
                    for column_name, value in first_record.items():
                        # Skip nested objects and arrays
                        if isinstance(value, dict) or isinstance(value, list):
                            continue
                        
                        # Determine column type
                        column_type = "string"
                        if isinstance(value, bool):
                            column_type = "boolean"
                        elif isinstance(value, int):
                            column_type = "int64"
                        elif isinstance(value, float):
                            column_type = "double"
                        elif isinstance(value, str) and re.match(r'\d{4}-\d{2}-\d{2}', value):
                            column_type = "datetime"
                        
                        # Add column to schema
                        columns.append({
                            "name": column_name,
                            "dataType": column_type
                        })
                    
                    # Add table to schema
                    tables_schema.append({
                        "name": self._sanitize_name(table_name),
                        "columns": columns
                    })
            
            # Create dataset payload
            create_dataset_payload = {
                "name": dataset_name,
                "tables": tables_schema
            }
            
            create_dataset_response = requests.post(create_dataset_url, headers=headers, json=create_dataset_payload)
            
            if create_dataset_response.status_code in [200, 201, 202]:
                return create_dataset_response.json().get("id")
            else:
                logger.error(f"Failed to create dataset. Status code: {create_dataset_response.status_code}, Response: {create_dataset_response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating dataset: {str(e)}")
            return None
    
    def _push_data_to_table(self, dataset_id: str, workspace_id: str,
                          table_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Push data to a Power BI dataset table.
        
        Args:
            dataset_id: ID of the dataset
            workspace_id: ID of the workspace
            table_name: Name of the table
            records: List of records to push
            
        Returns:
            Push results
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Sanitize table name
            sanitized_table_name = self._sanitize_name(table_name)
            
            # Prepare rows
            rows = []
            for record in records:
                row = {}
                
                for column_name, value in record.items():
                    # Skip nested objects and arrays
                    if isinstance(value, dict) or isinstance(value, list):
                        continue
                    
                    row[column_name] = value
                
                rows.append(row)
            
            # Push data
            push_data_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/tables/{sanitized_table_name}/rows"
            push_data_payload = {
                "rows": rows
            }
            
            push_data_response = requests.post(push_data_url, headers=headers, json=push_data_payload)
            
            if push_data_response.status_code in [200, 201, 202]:
                return {
                    "success": True,
                    "message": f"Successfully pushed {len(rows)} rows to table {table_name}"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to push data to table {table_name}. Status code: {push_data_response.status_code}, Response: {push_data_response.text}"
                }
        except Exception as e:
            logger.error(f"Error pushing data to table: {str(e)}")
            return {
                "success": False,
                "message": f"Error pushing data to table: {str(e)}"
            }
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use in Power BI.
        
        Args:
            name: Name to sanitize
            
        Returns:
            Sanitized name
        """
        # Replace spaces and special characters
        sanitized = re.sub(r'[^a-zA-Z0-9]', '_', name)
        
        # Ensure it starts with a letter
        if not sanitized[0].isalpha():
            sanitized = 'T_' + sanitized
        
        return sanitized
        
    def sync(self) -> Dict[str, Any]:
        """Synchronize EA data with Power BI.
        
        This method implements the sync operation required by the IntegrationBase class.
        
        Returns:
            Synchronization results
        """
        try:
            # Use configured workspace
            workspace_id = self.config.get("workspace_id")
            
            if not workspace_id:
                return {
                    "success": False,
                    "message": "Workspace ID not configured"
                }
            
            # Export EA data to dataset
            dataset_name = "EA_Data"
            export_result = self.export_ea_data_to_dataset(dataset_name, workspace_id)
            
            if not export_result.get("success"):
                return export_result
            
            # Get available reports
            reports_result = self.get_reports(workspace_id)
            
            return {
                "success": True,
                "message": f"Successfully synchronized EA data with Power BI",
                "dataset_id": export_result.get("dataset_id"),
                "reports": reports_result.get("reports", []) if reports_result.get("success") else []
            }
        except Exception as e:
            logger.error(f"Error synchronizing with Power BI: {str(e)}")
            return {
                "success": False,
                "message": f"Error synchronizing with Power BI: {str(e)}"
            }
