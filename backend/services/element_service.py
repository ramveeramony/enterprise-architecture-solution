"""
Enterprise Architecture Solution - Element Service

This module provides services for EA element operations.
"""

import logging
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

from .base_service import BaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElementService(BaseService):
    """Service for EA element operations."""
    
    def __init__(self, supabase_client):
        """Initialize the element service.
        
        Args:
            supabase_client: A configured Supabase client for database operations
        """
        super().__init__(supabase_client, 'ea_elements')
        # Initialize version history table
        self.version_table = 'ea_element_versions'
    
    async def create_element(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new EA element.
        
        Args:
            data: Element data
            user_id: ID of the user creating the element
            
        Returns:
            Created element
        """
        try:
            # Validate required fields
            required_fields = ['name', 'type_id', 'model_id']
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Field '{field}' is required")
            
            # Set default values
            if 'status' not in data or not data['status']:
                data['status'] = 'draft'
            
            # Create element
            element = await self.create(data, user_id)
            
            # Create initial version
            await self._create_version(element, user_id, 'Initial version')
            
            return await self.get_element_with_details(element['id'])
        
        except Exception as e:
            logger.error(f"Error creating element: {str(e)}")
            raise
    
    async def update_element(self, id: str, data: Dict[str, Any], user_id: str, change_description: str = 'Update') -> Dict[str, Any]:
        """Update an EA element.
        
        Args:
            id: Element ID
            data: Updated element data
            user_id: ID of the user updating the element
            change_description: Description of the changes made
            
        Returns:
            Updated element
        """
        try:
            # Get current element
            current_element = await self.get_by_id(id)
            
            if not current_element:
                raise ValueError(f"Element {id} not found")
            
            # Don't allow changing model_id
            if 'model_id' in data and data['model_id'] != current_element['model_id']:
                raise ValueError("Changing the model of an element is not allowed")
            
            # Update element
            updated_element = await self.update(id, data, user_id)
            
            # Create version
            await self._create_version(updated_element, user_id, change_description)
            
            return await self.get_element_with_details(id)
        
        except Exception as e:
            logger.error(f"Error updating element {id}: {str(e)}")
            raise
    
    async def delete_element(self, id: str, user_id: str) -> bool:
        """Delete an EA element.
        
        Args:
            id: Element ID
            user_id: ID of the user deleting the element
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            # Check for related relationships
            source_rels = await self.supabase.table('ea_relationships').select('id').eq('source_element_id', id).execute()
            target_rels = await self.supabase.table('ea_relationships').select('id').eq('target_element_id', id).execute()
            
            relationships = []
            if source_rels.data:
                relationships.extend(source_rels.data)
            if target_rels.data:
                relationships.extend(target_rels.data)
            
            # Delete associated relationships first
            for rel in relationships:
                await self.supabase.table('ea_relationships').delete().eq('id', rel['id']).execute()
            
            # Delete versions
            await self.supabase.table(self.version_table).delete().eq('element_id', id).execute()
            
            # Delete element
            return await self.delete(id)
        
        except Exception as e:
            logger.error(f"Error deleting element {id}: {str(e)}")
            raise
    
    async def get_version_history(self, id: str) -> List[Dict[str, Any]]:
        """Get version history for an element.
        
        Args:
            id: Element ID
            
        Returns:
            List of versions
        """
        try:
            result = self.supabase.table(self.version_table).select('*').eq('element_id', id).order('created_at', desc=True).execute()
            
            return result.data if result.data else []
        
        except Exception as e:
            logger.error(f"Error getting version history for element {id}: {str(e)}")
            raise
    
    async def get_element_with_details(self, id: str) -> Dict[str, Any]:
        """Get an element with detailed information.
        
        Args:
            id: Element ID
            
        Returns:
            Element with details
        """
        try:
            # Get element
            element = await self.get_by_id(id)
            
            if not element:
                raise ValueError(f"Element {id} not found")
            
            # Get element type details
            element_type = await self.supabase.table('ea_element_types').select('*').eq('id', element['type_id']).execute()
            
            if not element_type.data or len(element_type.data) == 0:
                raise ValueError(f"Element type {element['type_id']} not found")
            
            # Get model details
            model = await self.supabase.table('ea_models').select('name, status, lifecycle_state').eq('id', element['model_id']).execute()
            
            if not model.data or len(model.data) == 0:
                raise ValueError(f"Model {element['model_id']} not found")
            
            # Get domain details
            domain = await self.supabase.table('ea_domains').select('name').eq('id', element_type.data[0]['domain_id']).execute()
            
            domain_name = domain.data[0]['name'] if domain.data and len(domain.data) > 0 else "Unknown"
            
            # Get relationships where this element is the source
            source_rels_query = """
            SELECT r.id, r.name, r.description, 
                   rt.name as relationship_type, 
                   e.id as target_id, e.name as target_name, 
                   et.name as target_type
            FROM ea_relationships r
            JOIN ea_relationship_types rt ON r.relationship_type_id = rt.id
            JOIN ea_elements e ON r.target_element_id = e.id
            JOIN ea_element_types et ON e.type_id = et.id
            WHERE r.source_element_id = ?
            """
            source_rels = await self.supabase.rpc('run_sql', {'query': source_rels_query, 'params': [id]}).execute()
            
            # Get relationships where this element is the target
            target_rels_query = """
            SELECT r.id, r.name, r.description,
                   rt.name as relationship_type,
                   e.id as source_id, e.name as source_name,
                   et.name as source_type
            FROM ea_relationships r
            JOIN ea_relationship_types rt ON r.relationship_type_id = rt.id
            JOIN ea_elements e ON r.source_element_id = e.id
            JOIN ea_element_types et ON e.type_id = et.id
            WHERE r.target_element_id = ?
            """
            target_rels = await self.supabase.rpc('run_sql', {'query': target_rels_query, 'params': [id]}).execute()
            
            # Combine all information
            return {
                **element,
                'type': element_type.data[0],
                'model': model.data[0],
                'domain': domain_name,
                'outgoing_relationships': source_rels.data if source_rels.data else [],
                'incoming_relationships': target_rels.data if target_rels.data else []
            }
        
        except Exception as e:
            logger.error(f"Error getting element with details {id}: {str(e)}")
            raise
    
    async def get_elements_by_model(self, model_id: str) -> List[Dict[str, Any]]:
        """Get all elements for a specific model.
        
        Args:
            model_id: Model ID
            
        Returns:
            List of elements with type information
        """
        try:
            # Query with join to get element type information
            query = """
            SELECT e.*, et.name as type_name, et.icon as type_icon, d.name as domain_name
            FROM ea_elements e
            JOIN ea_element_types et ON e.type_id = et.id
            JOIN ea_domains d ON et.domain_id = d.id
            WHERE e.model_id = ?
            """
            
            result = await self.supabase.rpc('run_sql', {'query': query, 'params': [model_id]}).execute()
            
            return result.data if result.data else []
        
        except Exception as e:
            logger.error(f"Error getting elements for model {model_id}: {str(e)}")
            raise
    
    async def get_elements_by_domain(self, model_id: str, domain_id: str) -> List[Dict[str, Any]]:
        """Get elements for a specific model and domain.
        
        Args:
            model_id: Model ID
            domain_id: Domain ID
            
        Returns:
            List of elements with type information
        """
        try:
            # Query with join to get element type information
            query = """
            SELECT e.*, et.name as type_name, et.icon as type_icon
            FROM ea_elements e
            JOIN ea_element_types et ON e.type_id = et.id
            WHERE e.model_id = ? AND et.domain_id = ?
            """
            
            result = await self.supabase.rpc('run_sql', {'query': query, 'params': [model_id, domain_id]}).execute()
            
            return result.data if result.data else []
        
        except Exception as e:
            logger.error(f"Error getting elements for model {model_id} and domain {domain_id}: {str(e)}")
            raise
    
    async def get_elements_by_status(self, model_id: str, status: str) -> List[Dict[str, Any]]:
        """Get elements for a specific model and status.
        
        Args:
            model_id: Model ID
            status: Element status
            
        Returns:
            List of elements with type information
        """
        try:
            # Query with join to get element type information
            query = """
            SELECT e.*, et.name as type_name, et.icon as type_icon, d.name as domain_name
            FROM ea_elements e
            JOIN ea_element_types et ON e.type_id = et.id
            JOIN ea_domains d ON et.domain_id = d.id
            WHERE e.model_id = ? AND e.status = ?
            """
            
            result = await self.supabase.rpc('run_sql', {'query': query, 'params': [model_id, status]}).execute()
            
            return result.data if result.data else []
        
        except Exception as e:
            logger.error(f"Error getting elements for model {model_id} and status {status}: {str(e)}")
            raise
    
    async def search_elements(self, search_term: str, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for elements by name or description.
        
        Args:
            search_term: Search term
            model_id: Optional model ID to restrict search
            
        Returns:
            List of matching elements
        """
        try:
            # Prepare query
            if model_id:
                query = """
                SELECT e.*, et.name as type_name, et.icon as type_icon, m.name as model_name, d.name as domain_name
                FROM ea_elements e
                JOIN ea_element_types et ON e.type_id = et.id
                JOIN ea_models m ON e.model_id = m.id
                JOIN ea_domains d ON et.domain_id = d.id
                WHERE e.model_id = ?
                AND (e.name ILIKE ? OR e.description ILIKE ?)
                """
                search_pattern = f"%{search_term}%"
                result = await self.supabase.rpc('run_sql', {'query': query, 'params': [model_id, search_pattern, search_pattern]}).execute()
            else:
                query = """
                SELECT e.*, et.name as type_name, et.icon as type_icon, m.name as model_name, d.name as domain_name
                FROM ea_elements e
                JOIN ea_element_types et ON e.type_id = et.id
                JOIN ea_models m ON e.model_id = m.id
                JOIN ea_domains d ON et.domain_id = d.id
                WHERE e.name ILIKE ? OR e.description ILIKE ?
                """
                search_pattern = f"%{search_term}%"
                result = await self.supabase.rpc('run_sql', {'query': query, 'params': [search_pattern, search_pattern]}).execute()
            
            return result.data if result.data else []
        
        except Exception as e:
            logger.error(f"Error searching elements: {str(e)}")
            raise
    
    async def _create_version(
        self, 
        element: Dict[str, Any], 
        user_id: str, 
        change_description: str
    ) -> Dict[str, Any]:
        """Create a version record for an element.
        
        Args:
            element: Element data
            user_id: ID of the user creating the version
            change_description: Description of the changes
            
        Returns:
            Created version
        """
        try:
            # Create version
            version_data = {
                'element_id': element['id'],
                'element_data': element,
                'change_description': change_description,
                'created_by': user_id,
                'created_at': datetime.now().isoformat()
            }
            
            result = await self.supabase.table(self.version_table).insert(version_data).execute()
            
            if not result.data:
                raise ValueError(f"Failed to create version for element {element['id']}")
                
            return result.data[0]
        
        except Exception as e:
            logger.error(f"Error creating version for element {element['id']}: {str(e)}")
            raise
    
    async def restore_version(self, element_id: str, version_id: str, user_id: str) -> Dict[str, Any]:
        """Restore an element from a version.
        
        Args:
            element_id: Element ID
            version_id: Version ID
            user_id: ID of the user restoring the version
            
        Returns:
            Restored element
        """
        try:
            # Get version
            version_result = await self.supabase.table(self.version_table).select('*').eq('id', version_id).eq('element_id', element_id).execute()
            
            if not version_result.data or len(version_result.data) == 0:
                raise ValueError(f"Version {version_id} not found for element {element_id}")
                
            version = version_result.data[0]
            
            # Get current element
            current_element = await self.get_by_id(element_id)
            
            if not current_element:
                raise ValueError(f"Element {element_id} not found")
            
            # Create snapshot of current state before restoring
            await self._create_version(
                current_element, 
                user_id, 
                f"Automatic snapshot before restoring version {version_id}"
            )
            
            # Extract data from version
            element_data = version['element_data']
            
            # Ensure ID and model_id remain the same
            element_data['id'] = element_id
            element_data['model_id'] = current_element['model_id']
            
            # Update element
            updated_element = await self.update(element_id, element_data, user_id)
            
            # Create version for restoration
            await self._create_version(
                updated_element, 
                user_id, 
                f"Restored from version {version_id}"
            )
            
            return await self.get_element_with_details(element_id)
        
        except Exception as e:
            logger.error(f"Error restoring version {version_id} for element {element_id}: {str(e)}")
            raise
