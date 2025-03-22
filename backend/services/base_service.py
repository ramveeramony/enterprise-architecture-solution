"""
Enterprise Architecture Solution - Base Service

This module provides a base service class with common database operations.
"""

import logging
from typing import Dict, List, Any, Optional, Type, TypeVar
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Generic type for service results
T = TypeVar('T')

class BaseService:
    """Base service with common database operations."""
    
    def __init__(self, supabase_client, table_name: str):
        """Initialize the base service.
        
        Args:
            supabase_client: A configured Supabase client for database operations
            table_name: Name of the database table
        """
        self.supabase = supabase_client
        self.table_name = table_name
    
    async def get_all(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        limit: int = 100, 
        offset: int = 0,
        order_by: Optional[str] = None,
        order_direction: str = 'asc'
    ) -> List[Dict[str, Any]]:
        """Get all records from the table with optional filtering.
        
        Args:
            filters: Optional dictionary of filters (field: value)
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Field to order by
            order_direction: Direction to order (asc or desc)
            
        Returns:
            List of records
        """
        try:
            query = self.supabase.table(self.table_name).select('*')
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    query = query.eq(field, value)
            
            # Apply ordering if provided
            if order_by:
                query = query.order(order_by, desc=(order_direction.lower() == 'desc'))
            
            # Apply pagination
            query = query.range(offset, offset + limit - 1)
            
            # Execute the query
            result = query.execute()
            
            return result.data if result.data else []
        
        except Exception as e:
            logger.error(f"Error getting records from {self.table_name}: {str(e)}")
            raise
    
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Record or None if not found
        """
        try:
            result = self.supabase.table(self.table_name).select('*').eq('id', id).execute()
            
            if not result.data:
                return None
                
            return result.data[0]
        
        except Exception as e:
            logger.error(f"Error getting record {id} from {self.table_name}: {str(e)}")
            raise
    
    async def create(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new record.
        
        Args:
            data: Record data
            user_id: ID of the user creating the record
            
        Returns:
            Created record
        """
        try:
            # Add metadata
            current_time = datetime.now().isoformat()
            record_data = {
                **data,
                'id': str(uuid.uuid4()) if 'id' not in data else data['id'],
                'created_at': current_time,
                'updated_at': current_time,
                'created_by': user_id,
                'updated_by': user_id
            }
            
            # Insert record
            result = self.supabase.table(self.table_name).insert(record_data).execute()
            
            if not result.data:
                raise ValueError(f"Failed to create record in {self.table_name}")
                
            return result.data[0]
        
        except Exception as e:
            logger.error(f"Error creating record in {self.table_name}: {str(e)}")
            raise
    
    async def update(self, id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update a record.
        
        Args:
            id: Record ID
            data: Updated record data
            user_id: ID of the user updating the record
            
        Returns:
            Updated record
        """
        try:
            # Add metadata
            update_data = {
                **data,
                'updated_at': datetime.now().isoformat(),
                'updated_by': user_id
            }
            
            # Remove fields that shouldn't be updated
            if 'id' in update_data:
                del update_data['id']
            if 'created_at' in update_data:
                del update_data['created_at']
            if 'created_by' in update_data:
                del update_data['created_by']
            
            # Update record
            result = self.supabase.table(self.table_name).update(update_data).eq('id', id).execute()
            
            if not result.data:
                raise ValueError(f"Record {id} not found in {self.table_name}")
                
            return result.data[0]
        
        except Exception as e:
            logger.error(f"Error updating record {id} in {self.table_name}: {str(e)}")
            raise
    
    async def delete(self, id: str) -> bool:
        """Delete a record.
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.supabase.table(self.table_name).delete().eq('id', id).execute()
            
            return len(result.data) > 0
        
        except Exception as e:
            logger.error(f"Error deleting record {id} from {self.table_name}: {str(e)}")
            raise
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering.
        
        Args:
            filters: Optional dictionary of filters (field: value)
            
        Returns:
            Count of records
        """
        try:
            query = self.supabase.table(self.table_name).select('id', count='exact')
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    query = query.eq(field, value)
            
            # Execute the query
            result = query.execute()
            
            return result.count if hasattr(result, 'count') else 0
        
        except Exception as e:
            logger.error(f"Error counting records in {self.table_name}: {str(e)}")
            raise

    async def exists(self, id: str) -> bool:
        """Check if a record exists.
        
        Args:
            id: Record ID
            
        Returns:
            True if exists, False otherwise
        """
        try:
            result = self.supabase.table(self.table_name).select('id').eq('id', id).execute()
            
            return len(result.data) > 0
        
        except Exception as e:
            logger.error(f"Error checking existence of record {id} in {self.table_name}: {str(e)}")
            raise
    
    async def get_version_history(self, id: str) -> List[Dict[str, Any]]:
        """Get version history for a record.
        
        This is a placeholder that should be overridden by services that implement versioning.
        
        Args:
            id: Record ID
            
        Returns:
            List of versions
        """
        raise NotImplementedError("Version history not implemented for this entity")
