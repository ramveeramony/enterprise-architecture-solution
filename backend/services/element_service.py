"""
Enterprise Architecture Solution - Element Service

This module provides services for EA element operations.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElementService:
    """Service for EA element operations."""
    
    def __init__(self, supabase_client):
        """Initialize the Element Service.
        
        Args:
            supabase_client: Configured Supabase client
        """
        self.supabase = supabase_client
    
    async def get_elements(self, model_id: Optional[str] = None, type_id: Optional[str] = None,
                          user_id: str = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get EA elements with optional filtering.
        
        Args:
            model_id: Optional ID of the model to filter by
            type_id: Optional ID of the element type to filter by
            user_id: ID of the requesting user
            filters: Additional filters to apply
            
        Returns:
            List of EA elements
        """
        try:
            query = self.supabase.table("ea_elements") \
                .select("*, type_id(id, name, domain_id, icon), model_id(id, name), created_by(id, email), updated_by(id, email)")
            
            # Apply mandatory filters
            if model_id:
                query = query.eq("model_id", model_id)
                
            if type_id:
                query = query.eq("type_id", type_id)
            
            # Apply additional filters if provided
            if filters:
                if 'name' in filters:
                    query = query.ilike('name', f'%{filters["name"]}%')
                    
                if 'status' in filters:
                    query = query.eq('status', filters['status'])
                    
                if 'external_id' in filters:
                    query = query.eq('external_id', filters['external_id'])
                    
                if 'external_source' in filters:
                    query = query.eq('external_source', filters['external_source'])
                    
                if 'domain_id' in filters:
                    # This requires a join, so we'll fetch all elements and filter in-memory
                    pass  # Handled below
            
            # Execute the query
            response = query.execute()
            
            if not response.data:
                return []
            
            # Apply domain filter if needed
            elements = response.data
            if filters and 'domain_id' in filters:
                domain_id = filters['domain_id']
                elements = [e for e in elements if e['type_id']['domain_id'] == domain_id]
                
            return elements
            
        except Exception as e:
            logger.error(f"Error getting elements: {str(e)}")
            raise
    
    async def get_element_by_id(self, element_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get an EA element by ID.
        
        Args:
            element_id: ID of the element to retrieve
            user_id: ID of the requesting user
            
        Returns:
            EA element if found, None otherwise
        """
        try:
            response = self.supabase.table("ea_elements") \
                .select("*, type_id(id, name, domain_id, icon), model_id(id, name), created_by(id, email), updated_by(id, email)") \
                .eq("id", element_id) \
                .execute()
            
            if not response.data:
                return None
                
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error getting element by ID: {str(e)}")
            raise
    
    async def create_element(self, element_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new EA element.
        
        Args:
            element_data: Element data to create
            user_id: ID of the user creating the element
            
        Returns:
            Created element
        """
        try:
            # Prepare the element data
            new_element = {
                "model_id": element_data["model_id"],
                "type_id": element_data["type_id"],
                "name": element_data["name"],
                "description": element_data.get("description"),
                "status": element_data.get("status", "draft"),
                "external_id": element_data.get("external_id"),
                "external_source": element_data.get("external_source"),
                "properties": element_data.get("properties", {}),
                "position_x": element_data.get("position_x"),
                "position_y": element_data.get("position_y"),
                "created_by": user_id
            }
            
            # Insert the element
            response = self.supabase.table("ea_elements").insert(new_element).execute()
            
            if not response.data:
                raise Exception("Failed to create element")
                
            # Get the created element with full information
            created_element = await self.get_element_by_id(response.data[0]["id"], user_id)
            
            return created_element
            
        except Exception as e:
            logger.error(f"Error creating element: {str(e)}")
            raise
    
    async def update_element(self, element_id: str, element_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing EA element.
        
        Args:
            element_id: ID of the element to update
            element_data: Updated element data
            user_id: ID of the user updating the element
            
        Returns:
            Updated element
        """
        try:
            # Check if the element exists
            existing_element = await self.get_element_by_id(element_id, user_id)
            
            if not existing_element:
                raise Exception(f"Element with ID {element_id} not found")
            
            # Prepare the update data
            update_data = {
                "updated_at": datetime.now().isoformat(),
                "updated_by": user_id
            }
            
            # Add fields to update if they are provided
            updateable_fields = [
                "name", "description", "status", "external_id", 
                "external_source", "properties", "position_x", "position_y"
            ]
            
            for field in updateable_fields:
                if field in element_data:
                    update_data[field] = element_data[field]
            
            # Handle type_id separately (it requires additional validation)
            if "type_id" in element_data:
                # Check if the type exists
                type_response = self.supabase.table("ea_element_types") \
                    .select("id") \
                    .eq("id", element_data["type_id"]) \
                    .execute()
                
                if not type_response.data:
                    raise Exception(f"Element type with ID {element_data['type_id']} not found")
                
                update_data["type_id"] = element_data["type_id"]
            
            # Update the element
            response = self.supabase.table("ea_elements") \
                .update(update_data) \
                .eq("id", element_id) \
                .execute()
            
            if not response.data:
                raise Exception(f"Failed to update element with ID {element_id}")
                
            # Get the updated element with full information
            updated_element = await self.get_element_by_id(element_id, user_id)
            
            return updated_element
            
        except Exception as e:
            logger.error(f"Error updating element: {str(e)}")
            raise
    
    async def delete_element(self, element_id: str, user_id: str) -> bool:
        """Delete an EA element.
        
        Args:
            element_id: ID of the element to delete
            user_id: ID of the user deleting the element
            
        Returns:
            True if deleted successfully
        """
        try:
            # Check if the element exists
            existing_element = await self.get_element_by_id(element_id, user_id)
            
            if not existing_element:
                raise Exception(f"Element with ID {element_id} not found")
            
            # First, check for dependencies
            # Check for relationships where this element is source or target
            relationships_response = self.supabase.table("ea_relationships") \
                .select("id") \
                .or(f"source_element_id.eq.{element_id},target_element_id.eq.{element_id}") \
                .execute()
            
            if relationships_response.data and len(relationships_response.data) > 0:
                # Delete the relationships first
                self.supabase.table("ea_relationships") \
                    .delete() \
                    .or(f"source_element_id.eq.{element_id},target_element_id.eq.{element_id}") \
                    .execute()
            
            # Delete the element
            response = self.supabase.table("ea_elements") \
                .delete() \
                .eq("id", element_id) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting element: {str(e)}")
            raise
    
    async def get_element_relationships(self, element_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for an element.
        
        Args:
            element_id: ID of the element
            user_id: ID of the requesting user
            
        Returns:
            List of relationships
        """
        try:
            # Check if the element exists
            existing_element = await self.get_element_by_id(element_id, user_id)
            
            if not existing_element:
                raise Exception(f"Element with ID {element_id} not found")
            
            # Get relationships where this element is source or target
            response = self.supabase.table("ea_relationships") \
                .select("*, relationship_type_id(id, name, directional), source_element_id(id, name, type_id), target_element_id(id, name, type_id), created_by(id, email), updated_by(id, email)") \
                .or(f"source_element_id.eq.{element_id},target_element_id.eq.{element_id}") \
                .execute()
            
            if not response.data:
                return []
                
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting element relationships: {str(e)}")
            raise
    
    async def get_related_elements(self, element_id: str, user_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Get elements related to the specified element.
        
        Args:
            element_id: ID of the element
            user_id: ID of the requesting user
            depth: Relationship depth (1 = direct relationships only)
            
        Returns:
            List of related elements
        """
        try:
            # Check if the element exists
            existing_element = await self.get_element_by_id(element_id, user_id)
            
            if not existing_element:
                raise Exception(f"Element with ID {element_id} not found")
            
            if depth < 1:
                depth = 1
            
            # Start with the direct relationships
            relationships = await self.get_element_relationships(element_id, user_id)
            
            # Collect related element IDs
            related_element_ids = set()
            for relationship in relationships:
                if relationship["source_element_id"]["id"] == element_id:
                    related_element_ids.add(relationship["target_element_id"]["id"])
                else:
                    related_element_ids.add(relationship["source_element_id"]["id"])
            
            # For depth > 1, iterate to get indirect relationships
            if depth > 1:
                for d in range(1, depth):
                    # Get the next level of relationships
                    next_level_ids = set()
                    for related_id in related_element_ids:
                        indirect_relationships = await self.get_element_relationships(related_id, user_id)
                        for rel in indirect_relationships:
                            if rel["source_element_id"]["id"] == related_id:
                                next_level_ids.add(rel["target_element_id"]["id"])
                            else:
                                next_level_ids.add(rel["source_element_id"]["id"])
                    
                    # Remove the original element and already processed elements
                    next_level_ids.discard(element_id)
                    next_level_ids = next_level_ids - related_element_ids
                    
                    # Add to the set of related elements
                    related_element_ids.update(next_level_ids)
            
            # Get the full details for each related element
            related_elements = []
            for related_id in related_element_ids:
                element = await self.get_element_by_id(related_id, user_id)
                if element:
                    related_elements.append(element)
            
            return related_elements
            
        except Exception as e:
            logger.error(f"Error getting related elements: {str(e)}")
            raise
    
    async def get_element_history(self, element_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get the version history of an element.
        
        Args:
            element_id: ID of the element
            user_id: ID of the requesting user
            
        Returns:
            List of element versions from the audit trail
        """
        try:
            # Check if the element exists
            existing_element = await self.get_element_by_id(element_id, user_id)
            
            if not existing_element:
                raise Exception(f"Element with ID {element_id} not found")
            
            # In a production system, we would query an audit trail table
            # For now, we'll return a simplified history
            response = self.supabase.table("ea_elements") \
                .select("updated_at, updated_by(id, email)") \
                .eq("id", element_id) \
                .execute()
            
            if not response.data or not response.data[0]["updated_at"]:
                # Only the creation event
                return [{
                    "element_id": element_id,
                    "event": "created",
                    "timestamp": existing_element["created_at"],
                    "user": existing_element["created_by"],
                    "data": existing_element
                }]
            
            # Return created and updated events
            return [
                {
                    "element_id": element_id,
                    "event": "created",
                    "timestamp": existing_element["created_at"],
                    "user": existing_element["created_by"],
                    "data": existing_element
                },
                {
                    "element_id": element_id,
                    "event": "updated",
                    "timestamp": existing_element["updated_at"],
                    "user": existing_element["updated_by"],
                    "data": existing_element
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting element history: {str(e)}")
            raise
    
    async def create_relationship(self, source_id: str, target_id: str, relationship_type_id: str, 
                                 relationship_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a relationship between two elements.
        
        Args:
            source_id: ID of the source element
            target_id: ID of the target element
            relationship_type_id: ID of the relationship type
            relationship_data: Additional relationship data
            user_id: ID of the user creating the relationship
            
        Returns:
            Created relationship
        """
        try:
            # Check if the source element exists
            source_element = await self.get_element_by_id(source_id, user_id)
            
            if not source_element:
                raise Exception(f"Source element with ID {source_id} not found")
            
            # Check if the target element exists
            target_element = await self.get_element_by_id(target_id, user_id)
            
            if not target_element:
                raise Exception(f"Target element with ID {target_id} not found")
            
            # Check if the elements are in the same model
            if source_element["model_id"]["id"] != target_element["model_id"]["id"]:
                raise Exception("Source and target elements must be in the same model")
            
            # Check if the relationship type exists
            type_response = self.supabase.table("ea_relationship_types") \
                .select("id") \
                .eq("id", relationship_type_id) \
                .execute()
            
            if not type_response.data:
                raise Exception(f"Relationship type with ID {relationship_type_id} not found")
            
            # Prepare the relationship data
            new_relationship = {
                "model_id": source_element["model_id"]["id"],
                "relationship_type_id": relationship_type_id,
                "source_element_id": source_id,
                "target_element_id": target_id,
                "name": relationship_data.get("name"),
                "description": relationship_data.get("description"),
                "status": relationship_data.get("status", "draft"),
                "properties": relationship_data.get("properties", {}),
                "created_by": user_id
            }
            
            # Insert the relationship
            response = self.supabase.table("ea_relationships").insert(new_relationship).execute()
            
            if not response.data:
                raise Exception("Failed to create relationship")
                
            # Get the created relationship with full information
            relationship_id = response.data[0]["id"]
            created_relationship = self.supabase.table("ea_relationships") \
                .select("*, relationship_type_id(id, name, directional), source_element_id(id, name, type_id), target_element_id(id, name, type_id), created_by(id, email)") \
                .eq("id", relationship_id) \
                .execute()
            
            if not created_relationship.data:
                raise Exception(f"Failed to retrieve created relationship with ID {relationship_id}")
                
            return created_relationship.data[0]
            
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            raise
    
    async def update_relationship(self, relationship_id: str, relationship_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing relationship.
        
        Args:
            relationship_id: ID of the relationship to update
            relationship_data: Updated relationship data
            user_id: ID of the user updating the relationship
            
        Returns:
            Updated relationship
        """
        try:
            # Check if the relationship exists
            relationship_response = self.supabase.table("ea_relationships") \
                .select("id") \
                .eq("id", relationship_id) \
                .execute()
            
            if not relationship_response.data:
                raise Exception(f"Relationship with ID {relationship_id} not found")
            
            # Prepare the update data
            update_data = {
                "updated_at": datetime.now().isoformat(),
                "updated_by": user_id
            }
            
            # Add fields to update if they are provided
            updateable_fields = ["name", "description", "status", "properties"]
            
            for field in updateable_fields:
                if field in relationship_data:
                    update_data[field] = relationship_data[field]
            
            # Update the relationship
            response = self.supabase.table("ea_relationships") \
                .update(update_data) \
                .eq("id", relationship_id) \
                .execute()
            
            if not response.data:
                raise Exception(f"Failed to update relationship with ID {relationship_id}")
                
            # Get the updated relationship with full information
            updated_relationship = self.supabase.table("ea_relationships") \
                .select("*, relationship_type_id(id, name, directional), source_element_id(id, name, type_id), target_element_id(id, name, type_id), created_by(id, email), updated_by(id, email)") \
                .eq("id", relationship_id) \
                .execute()
            
            if not updated_relationship.data:
                raise Exception(f"Failed to retrieve updated relationship with ID {relationship_id}")
                
            return updated_relationship.data[0]
            
        except Exception as e:
            logger.error(f"Error updating relationship: {str(e)}")
            raise
    
    async def delete_relationship(self, relationship_id: str, user_id: str) -> bool:
        """Delete a relationship.
        
        Args:
            relationship_id: ID of the relationship to delete
            user_id: ID of the user deleting the relationship
            
        Returns:
            True if deleted successfully
        """
        try:
            # Check if the relationship exists
            relationship_response = self.supabase.table("ea_relationships") \
                .select("id") \
                .eq("id", relationship_id) \
                .execute()
            
            if not relationship_response.data:
                raise Exception(f"Relationship with ID {relationship_id} not found")
            
            # Delete the relationship
            response = self.supabase.table("ea_relationships") \
                .delete() \
                .eq("id", relationship_id) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting relationship: {str(e)}")
            raise