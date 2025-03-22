"""
Enterprise Architecture Solution - Integration Manager

This module manages all integrations in the Enterprise Architecture Solution.
It provides a unified interface for accessing and managing different integrations.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Type

from .integration_base import IntegrationBase
from .halo_itsm import HaloITSMIntegration
from .sharepoint import SharePointIntegration
from .entra_id import EntraIDIntegration
from .microsoft_teams import TeamsIntegration
from .power_bi import PowerBIIntegration
from .visio import VisioIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationManager:
    """Manages all integrations in the EA Solution."""
    
    # Map of integration types to their implementation classes
    INTEGRATION_TYPES = {
        "halo_itsm": HaloITSMIntegration,
        "sharepoint": SharePointIntegration,
        "entra_id": EntraIDIntegration,
        "microsoft_teams": TeamsIntegration,
        "power_bi": PowerBIIntegration,
        "microsoft_visio": VisioIntegration
    }
    
    def __init__(self, supabase_client):
        """Initialize the integration manager.
        
        Args:
            supabase_client: Initialized Supabase client
        """
        self.supabase = supabase_client
        self.integrations = {}
    
    def get_integration(self, integration_type: str, config_id: str = None) -> Optional[IntegrationBase]:
        """Get an integration instance.
        
        Args:
            integration_type: Type of integration
            config_id: Optional ID of the integration configuration
            
        Returns:
            Integration instance
        """
        try:
            # Check if integration type is supported
            if integration_type not in self.INTEGRATION_TYPES:
                logger.error(f"Unsupported integration type: {integration_type}")
                return None
            
            # Generate key for caching
            cache_key = f"{integration_type}_{config_id}"
            
            # Check if integration instance exists in cache
            if cache_key in self.integrations:
                return self.integrations[cache_key]
            
            # Create new integration instance
            integration_class = self.INTEGRATION_TYPES[integration_type]
            integration = integration_class(self.supabase, config_id)
            
            # Cache integration instance
            self.integrations[cache_key] = integration
            
            return integration
        except Exception as e:
            logger.error(f"Error getting integration: {str(e)}")
            return None
    
    def get_available_integrations(self) -> List[Dict[str, Any]]:
        """Get list of available integration types.
        
        Returns:
            List of available integrations with their descriptions
        """
        return [
            {
                "type": "halo_itsm",
                "name": "Halo ITSM",
                "description": "Integration with Halo ITSM for CMDB synchronization"
            },
            {
                "type": "sharepoint",
                "name": "SharePoint",
                "description": "Integration with SharePoint for document management"
            },
            {
                "type": "entra_id",
                "name": "Microsoft Entra ID",
                "description": "Integration with Microsoft Entra ID for authentication"
            },
            {
                "type": "microsoft_teams",
                "name": "Microsoft Teams",
                "description": "Integration with Microsoft Teams for collaboration"
            },
            {
                "type": "power_bi",
                "name": "Power BI",
                "description": "Integration with Power BI for advanced visualization"
            },
            {
                "type": "microsoft_visio",
                "name": "Microsoft Visio",
                "description": "Integration with Microsoft Visio for diagram creation and import"
            }
        ]
    
    def get_configured_integrations(self) -> List[Dict[str, Any]]:
        """Get list of configured integrations.
        
        Returns:
            List of configured integrations
        """
        try:
            # Query configured integrations from the database
            config_query = self.supabase.table("integration_configs").select("*").execute()
            
            if not config_query.data:
                return []
            
            configs = config_query.data
            result = []
            
            # Get details for each configured integration
            for config in configs:
                integration_type = config.get("integration_type")
                
                if integration_type in self.INTEGRATION_TYPES:
                    # Get integration instance
                    integration = self.get_integration(integration_type, config.get("id"))
                    
                    # Test connection
                    status = "inactive"
                    if integration:
                        test_result = integration.test_connection()
                        status = "active" if test_result.get("success", False) else "error"
                    
                    # Get integration details
                    integration_details = next(
                        (i for i in self.get_available_integrations() if i["type"] == integration_type),
                        {"name": integration_type, "description": ""}
                    )
                    
                    result.append({
                        "id": config.get("id"),
                        "type": integration_type,
                        "name": integration_details["name"],
                        "description": integration_details["description"],
                        "status": status,
                        "last_sync": config.get("last_sync_at"),
                        "created_at": config.get("created_at"),
                        "updated_at": config.get("updated_at")
                    })
            
            return result
        except Exception as e:
            logger.error(f"Error getting configured integrations: {str(e)}")
            return []
    
    def configure_integration(self, integration_type: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Configure an integration.
        
        Args:
            integration_type: Type of integration
            config_data: Configuration data
            
        Returns:
            Configuration result
        """
        try:
            # Check if integration type is supported
            if integration_type not in self.INTEGRATION_TYPES:
                return {
                    "success": False,
                    "message": f"Unsupported integration type: {integration_type}"
                }
            
            # Get integration instance
            integration = self.get_integration(integration_type)
            
            if not integration:
                return {
                    "success": False,
                    "message": f"Failed to create integration instance for {integration_type}"
                }
            
            # Configure integration
            result = integration.configure(**config_data)
            
            # Update cache if configuration was successful
            if result.get("success") and result.get("config_id"):
                cache_key = f"{integration_type}_{result.get('config_id')}"
                self.integrations[cache_key] = integration
            
            return result
        except Exception as e:
            logger.error(f"Error configuring integration: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring integration: {str(e)}"
            }
    
    def delete_integration(self, integration_id: str) -> Dict[str, Any]:
        """Delete an integration configuration.
        
        Args:
            integration_id: ID of the integration configuration
            
        Returns:
            Deletion result
        """
        try:
            # Query integration info
            integration_query = self.supabase.table("integration_configs").select("*").eq("id", integration_id).execute()
            
            if not integration_query.data or len(integration_query.data) == 0:
                return {
                    "success": False,
                    "message": f"Integration configuration not found: {integration_id}"
                }
            
            integration_type = integration_query.data[0].get("integration_type")
            
            # Delete integration configuration
            delete_result = self.supabase.table("integration_configs").delete().eq("id", integration_id).execute()
            
            # Remove from cache
            cache_key = f"{integration_type}_{integration_id}"
            if cache_key in self.integrations:
                del self.integrations[cache_key]
            
            return {
                "success": True,
                "message": f"Integration configuration deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting integration: {str(e)}")
            return {
                "success": False,
                "message": f"Error deleting integration: {str(e)}"
            }
    
    def sync_integration(self, integration_id: str) -> Dict[str, Any]:
        """Synchronize an integration.
        
        Args:
            integration_id: ID of the integration configuration
            
        Returns:
            Synchronization result
        """
        try:
            # Query integration info
            integration_query = self.supabase.table("integration_configs").select("*").eq("id", integration_id).execute()
            
            if not integration_query.data or len(integration_query.data) == 0:
                return {
                    "success": False,
                    "message": f"Integration configuration not found: {integration_id}"
                }
            
            integration_type = integration_query.data[0].get("integration_type")
            
            # Get integration instance
            integration = self.get_integration(integration_type, integration_id)
            
            if not integration:
                return {
                    "success": False,
                    "message": f"Failed to create integration instance for {integration_type}"
                }
            
            # Synchronize integration
            result = integration.sync()
            
            # Update last sync timestamp
            if result.get("success"):
                self.supabase.table("integration_configs").update({
                    "last_sync_at": "now()",
                    "status": "active"
                }).eq("id", integration_id).execute()
            else:
                self.supabase.table("integration_configs").update({
                    "status": "error"
                }).eq("id", integration_id).execute()
            
            return result
        except Exception as e:
            logger.error(f"Error synchronizing integration: {str(e)}")
            return {
                "success": False,
                "message": f"Error synchronizing integration: {str(e)}"
            }
    
    def get_sync_logs(self, integration_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get synchronization logs for an integration.
        
        Args:
            integration_id: ID of the integration configuration
            limit: Maximum number of logs to retrieve
            
        Returns:
            Synchronization logs
        """
        try:
            # Query sync logs
            logs_query = self.supabase.table("integration_sync_logs").select("*").eq("integration_config_id", integration_id).order("created_at", desc=True).limit(limit).execute()
            
            if not logs_query.data:
                return {
                    "success": True,
                    "logs": []
                }
            
            return {
                "success": True,
                "logs": logs_query.data
            }
        except Exception as e:
            logger.error(f"Error getting sync logs: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting sync logs: {str(e)}"
            }
