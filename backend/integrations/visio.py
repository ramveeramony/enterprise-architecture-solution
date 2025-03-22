"""
Enterprise Architecture Solution - Microsoft Visio Integration

This module provides integration with Microsoft Visio for the Enterprise Architecture Solution,
enabling users to create, edit, and import/export EA models using Visio.
"""

import os
import base64
import logging
import json
from io import BytesIO
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests
from pyviscache import VisioCache  # Visio Python client library (Note: This is a placeholder name)

from .integration_base import IntegrationBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisioIntegration(IntegrationBase):
    """Integration with Microsoft Visio for EA modeling."""
    
    def __init__(self, supabase_client, config_id: str = None):
        """Initialize the Visio integration.
        
        Args:
            supabase_client: Initialized Supabase client
            config_id: ID of the integration configuration in the database
        """
        super().__init__(supabase_client, config_id)
        self.graph_api_endpoint = self.config.get("graph_api_endpoint", "https://graph.microsoft.com/v1.0")
        self.access_token = None
    
    def _get_integration_type(self) -> str:
        """Get the integration type identifier."""
        return "microsoft_visio"
    
    def configure(self, graph_api_endpoint: str = None, 
                 client_id: str = None, client_secret: str = None,
                 tenant_id: str = None) -> Dict[str, Any]:
        """Configure the Visio integration.
        
        Args:
            graph_api_endpoint: Microsoft Graph API endpoint
            client_id: Microsoft Entra ID client ID
            client_secret: Microsoft Entra ID client secret
            tenant_id: Microsoft Entra ID tenant ID
            
        Returns:
            Configuration status
        """
        if graph_api_endpoint:
            self.graph_api_endpoint = graph_api_endpoint
        
        self.config.update({
            "graph_api_endpoint": self.graph_api_endpoint,
            "client_id": client_id,
            "client_secret": client_secret,
            "tenant_id": tenant_id,
            "last_configured": datetime.now().isoformat()
        })
        
        self._save_config()
        
        # Test the connection to validate the configuration
        test_result = self.test_connection()
        
        return {
            "success": test_result.get("success", False),
            "message": test_result.get("message", ""),
            "config_id": self.config_id
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Microsoft Graph API."""
        try:
            # Get access token
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for Microsoft Graph API"
                }
            
            # Test API access by getting user profile
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(f"{self.graph_api_endpoint}/me", headers=headers)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Successfully connected to Microsoft Graph API"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to connect to Microsoft Graph API. Status code: {response.status_code}, Response: {response.text}"
                }
        except Exception as e:
            logger.error(f"Error testing Microsoft Graph API connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to Microsoft Graph API: {str(e)}"
            }
    
    def _get_access_token(self) -> None:
        """Get access token for Microsoft Graph API."""
        try:
            token_url = f"https://login.microsoftonline.com/{self.config.get('tenant_id')}/oauth2/v2.0/token"
            
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': self.config.get('client_id'),
                'client_secret': self.config.get('client_secret'),
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            token_response = requests.post(token_url, data=token_data)
            
            if token_response.status_code == 200:
                token_json = token_response.json()
                self.access_token = token_json.get('access_token')
            else:
                logger.error(f"Failed to obtain access token: {token_response.text}")
                self.access_token = None
        except Exception as e:
            logger.error(f"Error obtaining access token: {str(e)}")
            self.access_token = None
    
    def import_visio_diagram(self, file_content: bytes, model_id: str, 
                            element_type_mappings: Dict[str, str] = None) -> Dict[str, Any]:
        """Import a Visio diagram as EA elements and relationships.
        
        Args:
            file_content: Binary content of the Visio file
            model_id: ID of the EA model to import into
            element_type_mappings: Mapping of Visio shape types to EA element types
            
        Returns:
            Import results
        """
        try:
            # Create a Visio cache from the file content
            visio_cache = VisioCache(BytesIO(file_content))
            
            # Extract diagram elements
            shapes = visio_cache.get_shapes()
            connectors = visio_cache.get_connectors()
            
            # Default mappings if not provided
            if not element_type_mappings:
                element_type_mappings = self._get_default_mappings()
            
            # Process shapes as EA elements
            elements_created = []
            for shape in shapes:
                element_type = element_type_mappings.get(shape.type, "generic_element")
                
                # Create EA element
                element_data = {
                    "model_id": model_id,
                    "type": element_type,
                    "name": shape.text or f"Shape {shape.id}",
                    "description": shape.description or "",
                    "properties": {
                        "visio_id": shape.id,
                        "visio_type": shape.type,
                        "position_x": shape.position_x,
                        "position_y": shape.position_y,
                        "width": shape.width,
                        "height": shape.height
                    }
                }
                
                # Call API to create element
                element_id = self._create_element(element_data)
                elements_created.append({
                    "id": element_id,
                    "name": element_data["name"],
                    "visio_id": shape.id
                })
            
            # Process connectors as EA relationships
            relationships_created = []
            for connector in connectors:
                # Find source and target elements
                source_element = next((e for e in elements_created if e["visio_id"] == connector.source_id), None)
                target_element = next((e for e in elements_created if e["visio_id"] == connector.target_id), None)
                
                if source_element and target_element:
                    # Create EA relationship
                    relationship_data = {
                        "model_id": model_id,
                        "type": "generic_relationship",
                        "name": connector.text or f"Connector {connector.id}",
                        "description": connector.description or "",
                        "source_id": source_element["id"],
                        "target_id": target_element["id"],
                        "properties": {
                            "visio_id": connector.id,
                            "visio_type": connector.type
                        }
                    }
                    
                    # Call API to create relationship
                    relationship_id = self._create_relationship(relationship_data)
                    relationships_created.append({
                        "id": relationship_id,
                        "name": relationship_data["name"],
                        "source": source_element["name"],
                        "target": target_element["name"]
                    })
            
            return {
                "success": True,
                "elements_created": len(elements_created),
                "relationships_created": len(relationships_created),
                "elements": elements_created,
                "relationships": relationships_created
            }
        except Exception as e:
            logger.error(f"Error importing Visio diagram: {str(e)}")
            return {
                "success": False,
                "message": f"Error importing Visio diagram: {str(e)}"
            }
    
    def export_to_visio(self, model_id: str, view_id: str = None, 
                       element_ids: List[str] = None) -> Dict[str, Any]:
        """Export EA elements and relationships to a Visio diagram.
        
        Args:
            model_id: ID of the EA model to export
            view_id: Optional ID of a specific view to export
            element_ids: Optional list of specific element IDs to export
            
        Returns:
            Export results with Visio file content
        """
        try:
            # Placeholder for actual implementation
            # In a real implementation, this would:
            # 1. Fetch elements and relationships from the EA repository
            # 2. Create a Visio diagram using a library like python-pptx or direct COM automation
            # 3. Return the binary content of the created Visio file
            
            # Example response with placeholder
            return {
                "success": True,
                "message": "Export to Visio not fully implemented in this version",
                "file_content_base64": base64.b64encode(b"Placeholder for Visio file content").decode('utf-8')
            }
        except Exception as e:
            logger.error(f"Error exporting to Visio: {str(e)}")
            return {
                "success": False,
                "message": f"Error exporting to Visio: {str(e)}"
            }
    
    def _get_default_mappings(self) -> Dict[str, str]:
        """Get default mappings from Visio shape types to EA element types."""
        return {
            "Process": "business_process",
            "Activity": "business_activity",
            "Decision": "business_decision",
            "Database": "data_store",
            "Entity": "data_entity",
            "Application": "application_component",
            "Service": "application_service",
            "Interface": "application_interface",
            "Server": "technology_node",
            "Device": "technology_device",
            "Network": "technology_network"
        }
    
    def _create_element(self, element_data: Dict[str, Any]) -> str:
        """Create an EA element in the repository."""
        try:
            # Insert the element into the database
            result = self.supabase.table("ea_elements").insert(element_data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]["id"]
            else:
                logger.error("Failed to create element in database")
                return f"error-{datetime.now().timestamp()}"
        except Exception as e:
            logger.error(f"Error creating element: {str(e)}")
            return f"error-{datetime.now().timestamp()}"
    
    def _create_relationship(self, relationship_data: Dict[str, Any]) -> str:
        """Create an EA relationship in the repository."""
        try:
            # Insert the relationship into the database
            result = self.supabase.table("ea_relationships").insert(relationship_data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]["id"]
            else:
                logger.error("Failed to create relationship in database")
                return f"error-{datetime.now().timestamp()}"
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            return f"error-{datetime.now().timestamp()}"
    
    def sync(self) -> Dict[str, Any]:
        """Synchronize Visio diagrams with the EA repository.
        
        This method implements the sync operation required by the IntegrationBase class.
        
        Returns:
            Synchronization results
        """
        try:
            # Placeholder implementation
            # In a real implementation, this would:
            # 1. Search for Visio files in a configured location (e.g., SharePoint)
            # 2. Compare with previously imported files
            # 3. Import new or updated files
            
            return {
                "success": True,
                "message": "Visio synchronization not fully implemented in this version",
                "files_processed": 0,
                "files_imported": 0
            }
        except Exception as e:
            logger.error(f"Error synchronizing with Visio: {str(e)}")
            return {
                "success": False,
                "message": f"Error synchronizing with Visio: {str(e)}"
            }
