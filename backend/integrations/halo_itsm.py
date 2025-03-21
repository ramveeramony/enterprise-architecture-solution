"""
Enterprise Architecture Solution - Halo ITSM Integration

This module handles integration with Halo ITSM for CMDB synchronization.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from .integration_base import IntegrationBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HaloITSMIntegration(IntegrationBase):
    """Integration with Halo ITSM CMDB."""
    
    def __init__(self, supabase_client, config_id: str = None):
        """Initialize the Halo ITSM integration.
        
        Args:
            supabase_client: Initialized Supabase client
            config_id: ID of the integration configuration in the database
        """
        super().__init__(supabase_client, config_id)
        self.api_url = self.config.get("api_url", "")
        self.api_key = self.config.get("api_key", "")
        self.client_id = self.config.get("client_id", "")
    
    def _get_integration_type(self) -> str:
        """Get the integration type identifier."""
        return "halo_itsm"
    
    def configure(self, api_url: str, api_key: str, client_id: str) -> Dict[str, Any]:
        """Configure the Halo ITSM integration.
        
        Args:
            api_url: Halo ITSM API URL
            api_key: Halo ITSM API key
            client_id: Halo ITSM client ID
            
        Returns:
            Configuration status
        """
        self.api_url = api_url
        self.api_key = api_key
        self.client_id = client_id
        
        self.config = {
            "api_url": api_url,
            "api_key": api_key,
            "client_id": client_id,
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
        """Test the connection to Halo ITSM."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Call the Halo ITSM API to verify credentials
            test_url = f"{self.api_url}/api/cmdb/items?limit=1"
            response = requests.get(test_url, headers=headers)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Successfully connected to Halo ITSM"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to connect to Halo ITSM. Status code: {response.status_code}, Response: {response.text}"
                }
        except Exception as e:
            logger.error(f"Error testing Halo ITSM connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to Halo ITSM: {str(e)}"
            }
    
    def sync(self) -> Dict[str, Any]:
        """Synchronize CMDB items from Halo ITSM with the EA repository."""
        if not self.api_url or not self.api_key or not self.client_id:
            return {
                "success": False,
                "message": "Halo ITSM integration not fully configured"
            }
        
        try:
            # Track sync metrics
            items_processed = 0
            items_created = 0
            items_updated = 0
            items_failed = 0
            sync_details = {}
            
            # Get CMDB items from Halo ITSM
            cmdb_items = self._get_cmdb_items()
            items_processed = len(cmdb_items)
            
            if not cmdb_items:
                self._log_sync("failed", items_processed, items_created, items_updated, 
                              items_failed, "No CMDB items retrieved from Halo ITSM")
                return {
                    "success": False,
                    "message": "No CMDB items retrieved from Halo ITSM"
                }
            
            # Get the model ID for Halo ITSM integration
            model_id = self._get_or_create_integration_model()
            
            # Process each CMDB item
            for item in cmdb_items:
                try:
                    # Map the CMDB item to an EA element
                    element_data = self._map_cmdb_item_to_element(item, model_id)
                    
                    # Check if the element already exists
                    external_id = f"halo-{item['id']}"
                    existing_element = self._find_existing_element(external_id)
                    
                    if existing_element:
                        # Update existing element
                        self._update_element(existing_element["id"], element_data)
                        items_updated += 1
                    else:
                        # Create new element
                        self._create_element(element_data)
                        items_created += 1
                except Exception as e:
                    logger.error(f"Error processing CMDB item {item.get('id', 'unknown')}: {str(e)}")
                    items_failed += 1
                    sync_details[f"item_{item.get('id', 'unknown')}"] = str(e)
            
            # Update last sync timestamp in config
            self.config["last_sync"] = datetime.now().isoformat()
            self._save_config()
            
            # Log the sync activity
            sync_status = "success" if items_failed == 0 else "partial" if items_created + items_updated > 0 else "failed"
            self._log_sync(sync_status, items_processed, items_created, items_updated, items_failed, 
                          None if sync_status != "failed" else "Some items failed to process", sync_details)
            
            return {
                "success": sync_status != "failed",
                "message": f"Processed {items_processed} items: {items_created} created, {items_updated} updated, {items_failed} failed",
                "details": {
                    "items_processed": items_processed,
                    "items_created": items_created,
                    "items_updated": items_updated,
                    "items_failed": items_failed
                }
            }
            
        except Exception as e:
            logger.error(f"Error syncing with Halo ITSM: {str(e)}")
            self._log_sync("failed", 0, 0, 0, 0, str(e))
            return {
                "success": False,
                "message": f"Error syncing with Halo ITSM: {str(e)}"
            }
    
    def _get_cmdb_items(self) -> List[Dict[str, Any]]:
        """Get CMDB items from Halo ITSM."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Get all CMDB items, handling pagination
        all_items = []
        page = 1
        limit = 100  # Items per page
        
        while True:
            url = f"{self.api_url}/api/cmdb/items?page={page}&limit={limit}"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Error fetching CMDB items, status code: {response.status_code}, response: {response.text}")
                break
            
            data = response.json()
            items = data.get("data", [])
            all_items.extend(items)
            
            # Check if we've reached the last page
            if len(items) < limit:
                break
            
            page += 1
        
        return all_items
    
    def _get_or_create_integration_model(self) -> str:
        """Get or create an EA model for the Halo ITSM integration."""
        # Implementation details...
        pass
    
    def _map_cmdb_item_to_element(self, cmdb_item: Dict[str, Any], model_id: str) -> Dict[str, Any]:
        """Map a CMDB item to an EA element."""
        # Implementation details...
        pass
    
    def _find_existing_element(self, external_id: str) -> Optional[Dict[str, Any]]:
        """Find an existing element by external ID."""
        # Implementation details...
        pass
    
    def _create_element(self, element_data: Dict[str, Any]) -> str:
        """Create a new EA element."""
        # Implementation details...
        pass
    
    def _update_element(self, element_id: str, element_data: Dict[str, Any]) -> None:
        """Update an existing EA element."""
        # Implementation details...
        pass
