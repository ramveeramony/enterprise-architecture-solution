"""
Enterprise Architecture Solution - Model Service

This module provides services for EA model operations.
"""

import logging
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

from .base_service import BaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelService(BaseService):
    """Service for EA model operations."""
    
    def __init__(self, supabase_client):
        """Initialize the model service.
        
        Args:
            supabase_client: A configured Supabase client for database operations
        """
        super().__init__(supabase_client, 'ea_models')
        # Initialize version history table
        self.version_table = 'ea_model_versions'
    
    async def create_model(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new EA model.
        
        Args:
            data: Model data
            user_id: ID of the user creating the model
            
        Returns:
            Created model
        """
        try:
            # Validate required fields
            required_fields = ['name']
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Field '{field}' is required")
            
            # Set default values
            if 'status' not in data or not data['status']:
                data['status'] = 'draft'
            
            if 'version' not in data or not data['version']:
                data['version'] = '1.0'
            
            if 'lifecycle_state' not in data or not data['lifecycle_state']:
                data['lifecycle_state'] = 'current'
            
            # Create model
            model = await self.create(data, user_id)
            
            # Create initial version
            await self._create_version(model, user_id, 'Initial version')
            
            return model
        
        except Exception as e:
            logger.error(f"Error creating model: {str(e)}")
            raise
    
    async def update_model(self, id: str, data: Dict[str, Any], user_id: str, change_description: str = 'Update') -> Dict[str, Any]:
        """Update an EA model.
        
        Args:
            id: Model ID
            data: Updated model data
            user_id: ID of the user updating the model
            change_description: Description of the changes made
            
        Returns:
            Updated model
        """
        try:
            # Get current model
            current_model = await self.get_by_id(id)
            
            if not current_model:
                raise ValueError(f"Model {id} not found")
            
            # Update model
            updated_model = await self.update(id, data, user_id)
            
            # Create version
            await self._create_version(updated_model, user_id, change_description)
            
            return updated_model
        
        except Exception as e:
            logger.error(f"Error updating model {id}: {str(e)}")
            raise
    
    async def delete_model(self, id: str, user_id: str) -> bool:
        """Delete an EA model.
        
        Args:
            id: Model ID
            user_id: ID of the user deleting the model
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            # Check for related elements
            elements = await self.supabase.table('ea_elements').select('id').eq('model_id', id).execute()
            
            if elements.data and len(elements.data) > 0:
                raise ValueError(f"Cannot delete model {id} with associated elements")
            
            # Delete versions
            await self.supabase.table(self.version_table).delete().eq('model_id', id).execute()
            
            # Delete model
            return await self.delete(id)
        
        except Exception as e:
            logger.error(f"Error deleting model {id}: {str(e)}")
            raise
    
    async def get_version_history(self, id: str) -> List[Dict[str, Any]]:
        """Get version history for a model.
        
        Args:
            id: Model ID
            
        Returns:
            List of versions
        """
        try:
            result = self.supabase.table(self.version_table).select('*').eq('model_id', id).order('created_at', desc=True).execute()
            
            return result.data if result.data else []
        
        except Exception as e:
            logger.error(f"Error getting version history for model {id}: {str(e)}")
            raise
    
    async def get_model_with_details(self, id: str) -> Dict[str, Any]:
        """Get a model with detailed information.
        
        Args:
            id: Model ID
            
        Returns:
            Model with details
        """
        try:
            # Get model
            model = await self.get_by_id(id)
            
            if not model:
                raise ValueError(f"Model {id} not found")
            
            # Get element counts by type
            element_counts_query = """
            SELECT et.name as type_name, COUNT(*) as count
            FROM ea_elements e
            JOIN ea_element_types et ON e.type_id = et.id
            WHERE e.model_id = ?
            GROUP BY et.name
            """
            element_counts = await self.supabase.rpc('run_sql', {'query': element_counts_query, 'params': [id]}).execute()
            
            # Get relationship counts by type
            relationship_counts_query = """
            SELECT rt.name as type_name, COUNT(*) as count
            FROM ea_relationships r
            JOIN ea_relationship_types rt ON r.relationship_type_id = rt.id
            WHERE r.model_id = ?
            GROUP BY rt.name
            """
            relationship_counts = await self.supabase.rpc('run_sql', {'query': relationship_counts_query, 'params': [id]}).execute()
            
            # Get views
            views = await self.supabase.table('ea_views').select('*').eq('model_id', id).execute()
            
            # Combine all information
            return {
                **model,
                'element_counts': element_counts.data if element_counts.data else [],
                'relationship_counts': relationship_counts.data if relationship_counts.data else [],
                'views': views.data if views.data else []
            }
        
        except Exception as e:
            logger.error(f"Error getting model with details {id}: {str(e)}")
            raise
    
    async def change_lifecycle_state(
        self, 
        id: str, 
        new_state: str, 
        user_id: str,
        change_description: str = 'Changed lifecycle state'
    ) -> Dict[str, Any]:
        """Change the lifecycle state of a model.
        
        Args:
            id: Model ID
            new_state: New lifecycle state (current, target, transitional)
            user_id: ID of the user changing the state
            change_description: Description of the change
            
        Returns:
            Updated model
        """
        try:
            # Validate state
            valid_states = ['current', 'target', 'transitional']
            if new_state not in valid_states:
                raise ValueError(f"Invalid lifecycle state: {new_state}")
            
            # Update model
            updated_model = await self.update(id, {'lifecycle_state': new_state}, user_id)
            
            # Create version
            await self._create_version(updated_model, user_id, change_description)
            
            return updated_model
        
        except Exception as e:
            logger.error(f"Error changing lifecycle state for model {id}: {str(e)}")
            raise
    
    async def create_model_snapshot(self, id: str, user_id: str, description: str) -> Dict[str, Any]:
        """Create a snapshot of a model.
        
        Args:
            id: Model ID
            user_id: ID of the user creating the snapshot
            description: Snapshot description
            
        Returns:
            Created snapshot
        """
        try:
            # Get model
            model = await self.get_by_id(id)
            
            if not model:
                raise ValueError(f"Model {id} not found")
            
            # Create snapshot version
            snapshot = await self._create_version(model, user_id, description, is_snapshot=True)
            
            return snapshot
        
        except Exception as e:
            logger.error(f"Error creating snapshot for model {id}: {str(e)}")
            raise
    
    async def _create_version(
        self, 
        model: Dict[str, Any], 
        user_id: str, 
        change_description: str,
        is_snapshot: bool = False
    ) -> Dict[str, Any]:
        """Create a version record for a model.
        
        Args:
            model: Model data
            user_id: ID of the user creating the version
            change_description: Description of the changes
            is_snapshot: Whether this is a snapshot
            
        Returns:
            Created version
        """
        try:
            # Get elements and relationships for model
            elements = await self.supabase.table('ea_elements').select('*').eq('model_id', model['id']).execute()
            relationships = await self.supabase.table('ea_relationships').select('*').eq('model_id', model['id']).execute()
            views = await self.supabase.table('ea_views').select('*').eq('model_id', model['id']).execute()
            
            # Create version
            version_data = {
                'model_id': model['id'],
                'model_data': model,
                'elements': elements.data if elements.data else [],
                'relationships': relationships.data if relationships.data else [],
                'views': views.data if views.data else [],
                'change_description': change_description,
                'created_by': user_id,
                'created_at': datetime.now().isoformat(),
                'is_snapshot': is_snapshot
            }
            
            result = await self.supabase.table(self.version_table).insert(version_data).execute()
            
            if not result.data:
                raise ValueError(f"Failed to create version for model {model['id']}")
                
            return result.data[0]
        
        except Exception as e:
            logger.error(f"Error creating version for model {model['id']}: {str(e)}")
            raise
    
    async def restore_version(self, model_id: str, version_id: str, user_id: str) -> Dict[str, Any]:
        """Restore a model from a version.
        
        Args:
            model_id: Model ID
            version_id: Version ID
            user_id: ID of the user restoring the version
            
        Returns:
            Restored model
        """
        try:
            # Get version
            version_result = await self.supabase.table(self.version_table).select('*').eq('id', version_id).eq('model_id', model_id).execute()
            
            if not version_result.data or len(version_result.data) == 0:
                raise ValueError(f"Version {version_id} not found for model {model_id}")
                
            version = version_result.data[0]
            
            # Get current model
            current_model = await self.get_by_id(model_id)
            
            if not current_model:
                raise ValueError(f"Model {model_id} not found")
            
            # Create snapshot of current state before restoring
            await self._create_version(
                current_model, 
                user_id, 
                f"Automatic snapshot before restoring version {version_id}",
                is_snapshot=True
            )
            
            # Extract data from version
            model_data = version['model_data']
            elements_data = version['elements']
            relationships_data = version['relationships']
            views_data = version['views']
            
            # Update model
            updated_model = await self.update(model_id, model_data, user_id)
            
            # Delete current elements, relationships, and views
            await self.supabase.table('ea_elements').delete().eq('model_id', model_id).execute()
            await self.supabase.table('ea_relationships').delete().eq('model_id', model_id).execute()
            await self.supabase.table('ea_views').delete().eq('model_id', model_id).execute()
            
            # Restore elements, relationships, and views
            if elements_data and len(elements_data) > 0:
                await self.supabase.table('ea_elements').insert(elements_data).execute()
            
            if relationships_data and len(relationships_data) > 0:
                await self.supabase.table('ea_relationships').insert(relationships_data).execute()
            
            if views_data and len(views_data) > 0:
                await self.supabase.table('ea_views').insert(views_data).execute()
            
            # Create version for restoration
            await self._create_version(
                updated_model, 
                user_id, 
                f"Restored from version {version_id}"
            )
            
            return updated_model
        
        except Exception as e:
            logger.error(f"Error restoring version {version_id} for model {model_id}: {str(e)}")
            raise
