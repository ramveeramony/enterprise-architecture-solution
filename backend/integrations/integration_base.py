"""
Enterprise Architecture Solution - Base Integration Class

This module defines the base class for all integrations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationBase:
    """Base class for all integrations."""
    
    def __init__(self, supabase_client, config_id: str = None):
        """Initialize the integration.
        
        Args:
            supabase_client: Initialized Supabase client
            config_id: ID of the integration configuration in the database
        """
        self.supabase = supabase_client
        self.config_id = config_id
        self.config = {}
        
        if config_id:
            self._load_config()
    
    def _load_config(self):
        """Load integration configuration from the database."""
        try:
            config_query = self.supabase.table("integration_configs").select("*").eq("id", self.config_id).execute()
            
            if config_query.data and len(config_query.data) > 0:
                self.config = config_query.data[0]["configuration"]
            else:
                logger.warning(f"No configuration found for integration ID {self.config_id}")
        except Exception as e:
            logger.error(f"Error loading integration configuration: {str(e)}")
    
    def _save_config(self):
        """Save integration configuration to the database."""
        try:
            if self.config_id:
                # Update existing config
                self.supabase.table("integration_configs").update({
                    "configuration": self.config,
                    "updated_at": datetime.now().isoformat()
                }).eq("id", self.config_id).execute()
            else:
                # Create new config
                result = self.supabase.table("integration_configs").insert({
                    "integration_type": self._get_integration_type(),
                    "configuration": self.config,
                    "status": "active",
                    "created_by": self.supabase.auth.get_user().user.id
                }).execute()
                
                if result.data and len(result.data) > 0:
                    self.config_id = result.data[0]["id"]
        except Exception as e:
            logger.error(f"Error saving integration configuration: {str(e)}")
    
    def _get_integration_type(self) -> str:
        """Get the integration type identifier."""
        raise NotImplementedError("Subclasses must implement _get_integration_type()")
    
    def _log_sync(self, status: str, items_processed: int = 0, items_created: int = 0,
                 items_updated: int = 0, items_failed: int = 0, error_message: str = None,
                 details: Dict[str, Any] = None):
        """Log synchronization activity to the database."""
        try:
            if not self.config_id:
                logger.warning("Cannot log sync: No config_id available")
                return
            
            self.supabase.table("integration_sync_logs").insert({
                "integration_config_id": self.config_id,
                "status": status,
                "items_processed": items_processed,
                "items_created": items_created,
                "items_updated": items_updated,
                "items_failed": items_failed,
                "error_message": error_message,
                "details": details or {}
            }).execute()
        except Exception as e:
            logger.error(f"Error logging sync activity: {str(e)}")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the external system."""
        raise NotImplementedError("Subclasses must implement test_connection()")
    
    def sync(self) -> Dict[str, Any]:
        """Synchronize data between the EA repository and the external system."""
        raise NotImplementedError("Subclasses must implement sync()")
