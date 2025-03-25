"""
Enterprise Architecture Solution - Repository Service

This module provides the core repository operations for EA artifacts.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RepositoryService:
    """Core service for EA repository operations."""
    
    def __init__(self, supabase_client):
        """Initialize the repository service.
        
        Args:
            supabase_client: Initialized Supabase client
        """
        self.supabase = supabase_client
    
    # ==================== MODEL OPERATIONS ====================
    
    async def get_models(self, 
                         filters: Optional[Dict[str, Any]] = None, 
                         include_elements: bool = False) -> List[Dict[str, Any]]:
        """Get EA models with optional filtering.
        
        Args:
            filters: Optional filters to apply
            include_elements: Whether to include elements in the response
            
        Returns:
            List of EA models
        """
        try:
            # Start query
            query = self.supabase.table("ea_models").select("*")
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if isinstance(value, list):
                        query = query.in_(field, value)
                    else:
                        query = query.eq(field, value)
            
            # Execute query
            result = await query.execute()
            
            models = result.data
            
            # If models with elements are requested
            if include_elements and models:
                for model in models:
                    elements_result = await self.supabase.table("ea_elements") \
                        .select("*") \
                        .eq("model_id", model["id"]) \
                        .execute()
                    model["elements"] = elements_result.data
            
            return models
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            raise
    
    async def get_model_by_id(self, model_id: str, include_elements: bool = False) -> Dict[str, Any]:
        """Get a specific EA model by ID.
        
        Args:
            model_id: ID of the model to retrieve
            include_elements: Whether to include elements in the response
            
        Returns:
            EA model data
        """
        try:
            # Get model
            result = await self.supabase.table("ea_models") \
                .select("*") \
                .eq("id", model_id) \
                .single() \
                .execute()
            
            model = result.data
            
            if not model:
                raise ValueError(f"Model with ID {model_id} not found")
            
            # Include elements if requested
            if include_elements:
                elements_result = await self.supabase.table("ea_elements") \
                    .select("*") \
                    .eq("model_id", model_id) \
                    .execute()
                model["elements"] = elements_result.data
            
            return model
        except Exception as e:
            logger.error(f"Error getting model {model_id}: {str(e)}")
            raise
    
    async def create_model(self, 
                           name: str, 
                           description: Optional[str] = None,
                           status: str = "draft",
                           version: str = "1.0",
                           lifecycle_state: str = "current",
                           properties: Optional[Dict[str, Any]] = None,
                           user_id: str = None) -> Dict[str, Any]:
        """Create a new EA model.
        
        Args:
            name: Model name
            description: Model description
            status: Model status (draft, review, approved, archived)
            version: Model version
            lifecycle_state: Lifecycle state (current, target, transitional)
            properties: Additional properties
            user_id: ID of the user creating the model
            
        Returns:
            Created model data
        """
        try:
            # Prepare model data
            model_data = {
                "id": str(uuid.uuid4()),
                "name": name,
                "description": description,
                "status": status,
                "version": version,
                "lifecycle_state": lifecycle_state,
                "properties": properties or {},
                "created_by": user_id,
                "created_at": datetime.now().isoformat()
            }
            
            # Create model
            result = await self.supabase.table("ea_models") \
                .insert(model_data) \
                .execute()
            
            return result.data[0] if result.data else model_data
        except Exception as e:
            logger.error(f"Error creating model: {str(e)}")
            raise
    
    async def update_model(self, 
                           model_id: str, 
                           updates: Dict[str, Any],
                           user_id: str = None) -> Dict[str, Any]:
        """Update an existing EA model.
        
        Args:
            model_id: ID of the model to update
            updates: Fields to update
            user_id: ID of the user updating the model
            
        Returns:
            Updated model data
        """
        try:
            # Add audit fields
            updates["updated_by"] = user_id
            updates["updated_at"] = datetime.now().isoformat()
            
            # Update model
            result = await self.supabase.table("ea_models") \
                .update(updates) \
                .eq("id", model_id) \
                .execute()
            
            if not result.data:
                raise ValueError(f"Model with ID {model_id} not found")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error updating model {model_id}: {str(e)}")
            raise
    
    async def delete_model(self, model_id: str, cascade: bool = False) -> bool:
        """Delete an EA model.
        
        Args:
            model_id: ID of the model to delete
            cascade: Whether to delete related elements
            
        Returns:
            True if successful
        """
        try:
            # If cascade deletion is requested, delete related elements first
            if cascade:
                # Delete relationships involving elements in this model
                elements_result = await self.supabase.table("ea_elements") \
                    .select("id") \
                    .eq("model_id", model_id) \
                    .execute()
                
                element_ids = [elem["id"] for elem in elements_result.data]
                
                if element_ids:
                    # Delete relationships where these elements are source or target
                    await self.supabase.table("ea_relationships") \
                        .delete() \
                        .in_("source_element_id", element_ids) \
                        .execute()
                    
                    await self.supabase.table("ea_relationships") \
                        .delete() \
                        .in_("target_element_id", element_ids) \
                        .execute()
                
                # Delete elements in this model
                await self.supabase.table("ea_elements") \
                    .delete() \
                    .eq("model_id", model_id) \
                    .execute()
                
                # Delete views in this model
                await self.supabase.table("ea_views") \
                    .delete() \
                    .eq("model_id", model_id) \
                    .execute()
            
            # Delete the model
            result = await self.supabase.table("ea_models") \
                .delete() \
                .eq("id", model_id) \
                .execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deleting model {model_id}: {str(e)}")
            raise
    
    # ==================== ELEMENT OPERATIONS ====================
    
    async def get_elements(self, 
                          filters: Optional[Dict[str, Any]] = None, 
                          include_relationships: bool = False) -> List[Dict[str, Any]]:
        """Get EA elements with optional filtering.
        
        Args:
            filters: Optional filters to apply
            include_relationships: Whether to include relationships in the response
            
        Returns:
            List of EA elements
        """
        try:
            # Start query
            query = self.supabase.table("ea_elements").select("*")
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if isinstance(value, list):
                        query = query.in_(field, value)
                    else:
                        query = query.eq(field, value)
            
            # Execute query
            result = await query.execute()
            
            elements = result.data
            
            # Include relationships if requested
            if include_relationships and elements:
                for element in elements:
                    element["relationships"] = await self._get_element_relationships(element["id"])
            
            return elements
        except Exception as e:
            logger.error(f"Error getting elements: {str(e)}")
            raise
    
    async def get_element_by_id(self, element_id: str, include_relationships: bool = False) -> Dict[str, Any]:
        """Get a specific EA element by ID.
        
        Args:
            element_id: ID of the element to retrieve
            include_relationships: Whether to include relationships in the response
            
        Returns:
            EA element data
        """
        try:
            # Get element
            result = await self.supabase.table("ea_elements") \
                .select("*") \
                .eq("id", element_id) \
                .single() \
                .execute()
            
            element = result.data
            
            if not element:
                raise ValueError(f"Element with ID {element_id} not found")
            
            # Get element type details
            type_result = await self.supabase.table("ea_element_types") \
                .select("*") \
                .eq("id", element["type_id"]) \
                .single() \
                .execute()
            
            element["type"] = type_result.data
            
            # Include relationships if requested
            if include_relationships:
                element["relationships"] = await self._get_element_relationships(element_id)
            
            return element
        except Exception as e:
            logger.error(f"Error getting element {element_id}: {str(e)}")
            raise
    
    async def create_element(self, 
                            model_id: str,
                            type_id: str,
                            name: str,
                            description: Optional[str] = None,
                            status: str = "draft",
                            position: Optional[Dict[str, float]] = None,
                            properties: Optional[Dict[str, Any]] = None,
                            external_id: Optional[str] = None,
                            external_source: Optional[str] = None,
                            user_id: str = None) -> Dict[str, Any]:
        """Create a new EA element.
        
        Args:
            model_id: ID of the model this element belongs to
            type_id: ID of the element type
            name: Element name
            description: Element description
            status: Element status (draft, review, approved, archived)
            position: X,Y position coordinates
            properties: Additional properties
            external_id: External system ID (for synchronization)
            external_source: External system source
            user_id: ID of the user creating the element
            
        Returns:
            Created element data
        """
        try:
            # Prepare element data
            element_data = {
                "id": str(uuid.uuid4()),
                "model_id": model_id,
                "type_id": type_id,
                "name": name,
                "description": description,
                "status": status,
                "position_x": position.get("x") if position else None,
                "position_y": position.get("y") if position else None,
                "properties": properties or {},
                "external_id": external_id,
                "external_source": external_source,
                "created_by": user_id,
                "created_at": datetime.now().isoformat()
            }
            
            # Create element
            result = await self.supabase.table("ea_elements") \
                .insert(element_data) \
                .execute()
            
            return result.data[0] if result.data else element_data
        except Exception as e:
            logger.error(f"Error creating element: {str(e)}")
            raise
    
    async def update_element(self, 
                            element_id: str, 
                            updates: Dict[str, Any],
                            user_id: str = None) -> Dict[str, Any]:
        """Update an existing EA element.
        
        Args:
            element_id: ID of the element to update
            updates: Fields to update
            user_id: ID of the user updating the element
            
        Returns:
            Updated element data
        """
        try:
            # Handle position updates
            if "position" in updates:
                position = updates.pop("position")
                if position:
                    updates["position_x"] = position.get("x")
                    updates["position_y"] = position.get("y")
            
            # Add audit fields
            updates["updated_by"] = user_id
            updates["updated_at"] = datetime.now().isoformat()
            
            # Update element
            result = await self.supabase.table("ea_elements") \
                .update(updates) \
                .eq("id", element_id) \
                .execute()
            
            if not result.data:
                raise ValueError(f"Element with ID {element_id} not found")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error updating element {element_id}: {str(e)}")
            raise
    
    async def delete_element(self, element_id: str, cascade: bool = True) -> bool:
        """Delete an EA element.
        
        Args:
            element_id: ID of the element to delete
            cascade: Whether to delete related relationships
            
        Returns:
            True if successful
        """
        try:
            # If cascade deletion is requested, delete relationships first
            if cascade:
                # Delete relationships where this element is source or target
                await self.supabase.table("ea_relationships") \
                    .delete() \
                    .eq("source_element_id", element_id) \
                    .execute()
                
                await self.supabase.table("ea_relationships") \
                    .delete() \
                    .eq("target_element_id", element_id) \
                    .execute()
            
            # Delete the element
            result = await self.supabase.table("ea_elements") \
                .delete() \
                .eq("id", element_id) \
                .execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deleting element {element_id}: {str(e)}")
            raise
    
    # ==================== RELATIONSHIP OPERATIONS ====================
    
    async def _get_element_relationships(self, element_id: str) -> List[Dict[str, Any]]:
        """Get relationships for a specific element.
        
        Args:
            element_id: ID of the element
            
        Returns:
            List of relationships
        """
        try:
            # Get relationships where this element is the source
            source_rels_result = await self.supabase.table("ea_relationships") \
                .select("*") \
                .eq("source_element_id", element_id) \
                .execute()
            
            # Get relationships where this element is the target
            target_rels_result = await self.supabase.table("ea_relationships") \
                .select("*") \
                .eq("target_element_id", element_id) \
                .execute()
            
            relationships = []
            
            # Process source relationships
            for rel in source_rels_result.data:
                # Get relationship type
                rel_type_result = await self.supabase.table("ea_relationship_types") \
                    .select("*") \
                    .eq("id", rel["relationship_type_id"]) \
                    .single() \
                    .execute()
                
                # Get target element
                target_elem_result = await self.supabase.table("ea_elements") \
                    .select("id, name, type_id") \
                    .eq("id", rel["target_element_id"]) \
                    .single() \
                    .execute()
                
                if target_elem_result.data:
                    # Get target element type
                    target_type_result = await self.supabase.table("ea_element_types") \
                        .select("name") \
                        .eq("id", target_elem_result.data["type_id"]) \
                        .single() \
                        .execute()
                    
                    # Compile relationship data
                    relationships.append({
                        "id": rel["id"],
                        "type": rel_type_result.data["name"] if rel_type_result.data else "Unknown",
                        "direction": "outgoing",
                        "element": {
                            "id": target_elem_result.data["id"],
                            "name": target_elem_result.data["name"],
                            "type": target_type_result.data["name"] if target_type_result.data else "Unknown"
                        }
                    })
            
            # Process target relationships
            for rel in target_rels_result.data:
                # Get relationship type
                rel_type_result = await self.supabase.table("ea_relationship_types") \
                    .select("*") \
                    .eq("id", rel["relationship_type_id"]) \
                    .single() \
                    .execute()
                
                # Get source element
                source_elem_result = await self.supabase.table("ea_elements") \
                    .select("id, name, type_id") \
                    .eq("id", rel["source_element_id"]) \
                    .single() \
                    .execute()
                
                if source_elem_result.data:
                    # Get source element type
                    source_type_result = await self.supabase.table("ea_element_types") \
                        .select("name") \
                        .eq("id", source_elem_result.data["type_id"]) \
                        .single() \
                        .execute()
                    
                    # Compile relationship data
                    relationships.append({
                        "id": rel["id"],
                        "type": rel_type_result.data["name"] if rel_type_result.data else "Unknown",
                        "direction": "incoming",
                        "element": {
                            "id": source_elem_result.data["id"],
                            "name": source_elem_result.data["name"],
                            "type": source_type_result.data["name"] if source_type_result.data else "Unknown"
                        }
                    })
            
            return relationships
        except Exception as e:
            logger.error(f"Error getting relationships for element {element_id}: {str(e)}")
            raise
    
    async def get_relationships(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get EA relationships with optional filtering.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of EA relationships
        """
        try:
            # Start query
            query = self.supabase.table("ea_relationships").select("*")
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if isinstance(value, list):
                        query = query.in_(field, value)
                    else:
                        query = query.eq(field, value)
            
            # Execute query
            result = await query.execute()
            
            relationships = result.data
            
            # Enrich relationship data
            for rel in relationships:
                # Get relationship type
                rel_type_result = await self.supabase.table("ea_relationship_types") \
                    .select("name") \
                    .eq("id", rel["relationship_type_id"]) \
                    .single() \
                    .execute()
                
                rel["type"] = rel_type_result.data["name"] if rel_type_result.data else "Unknown"
                
                # Get source element
                source_elem_result = await self.supabase.table("ea_elements") \
                    .select("name") \
                    .eq("id", rel["source_element_id"]) \
                    .single() \
                    .execute()
                
                rel["source_name"] = source_elem_result.data["name"] if source_elem_result.data else "Unknown"
                
                # Get target element
                target_elem_result = await self.supabase.table("ea_elements") \
                    .select("name") \
                    .eq("id", rel["target_element_id"]) \
                    .single() \
                    .execute()
                
                rel["target_name"] = target_elem_result.data["name"] if target_elem_result.data else "Unknown"
            
            return relationships
        except Exception as e:
            logger.error(f"Error getting relationships: {str(e)}")
            raise
    
    async def create_relationship(self, 
                                 model_id: str,
                                 relationship_type_id: str,
                                 source_element_id: str,
                                 target_element_id: str,
                                 name: Optional[str] = None,
                                 description: Optional[str] = None,
                                 status: str = "draft",
                                 properties: Optional[Dict[str, Any]] = None,
                                 user_id: str = None) -> Dict[str, Any]:
        """Create a new EA relationship.
        
        Args:
            model_id: ID of the model this relationship belongs to
            relationship_type_id: ID of the relationship type
            source_element_id: ID of the source element
            target_element_id: ID of the target element
            name: Relationship name
            description: Relationship description
            status: Relationship status (draft, review, approved, archived)
            properties: Additional properties
            user_id: ID of the user creating the relationship
            
        Returns:
            Created relationship data
        """
        try:
            # Prepare relationship data
            relationship_data = {
                "id": str(uuid.uuid4()),
                "model_id": model_id,
                "relationship_type_id": relationship_type_id,
                "source_element_id": source_element_id,
                "target_element_id": target_element_id,
                "name": name,
                "description": description,
                "status": status,
                "properties": properties or {},
                "created_by": user_id,
                "created_at": datetime.now().isoformat()
            }
            
            # Create relationship
            result = await self.supabase.table("ea_relationships") \
                .insert(relationship_data) \
                .execute()
            
            return result.data[0] if result.data else relationship_data
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            raise
    
    async def update_relationship(self, 
                                 relationship_id: str, 
                                 updates: Dict[str, Any],
                                 user_id: str = None) -> Dict[str, Any]:
        """Update an existing EA relationship.
        
        Args:
            relationship_id: ID of the relationship to update
            updates: Fields to update
            user_id: ID of the user updating the relationship
            
        Returns:
            Updated relationship data
        """
        try:
            # Add audit fields
            updates["updated_by"] = user_id
            updates["updated_at"] = datetime.now().isoformat()
            
            # Update relationship
            result = await self.supabase.table("ea_relationships") \
                .update(updates) \
                .eq("id", relationship_id) \
                .execute()
            
            if not result.data:
                raise ValueError(f"Relationship with ID {relationship_id} not found")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error updating relationship {relationship_id}: {str(e)}")
            raise
    
    async def delete_relationship(self, relationship_id: str) -> bool:
        """Delete an EA relationship.
        
        Args:
            relationship_id: ID of the relationship to delete
            
        Returns:
            True if successful
        """
        try:
            # Delete the relationship
            result = await self.supabase.table("ea_relationships") \
                .delete() \
                .eq("id", relationship_id) \
                .execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deleting relationship {relationship_id}: {str(e)}")
            raise
    
    # ==================== VIEW OPERATIONS ====================
    
    async def get_views(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get EA views with optional filtering.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of EA views
        """
        try:
            # Start query
            query = self.supabase.table("ea_views").select("*")
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if isinstance(value, list):
                        query = query.in_(field, value)
                    else:
                        query = query.eq(field, value)
            
            # Execute query
            result = await query.execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error getting views: {str(e)}")
            raise
    
    async def get_view_by_id(self, view_id: str) -> Dict[str, Any]:
        """Get a specific EA view by ID.
        
        Args:
            view_id: ID of the view to retrieve
            
        Returns:
            EA view data
        """
        try:
            # Get view
            result = await self.supabase.table("ea_views") \
                .select("*") \
                .eq("id", view_id) \
                .single() \
                .execute()
            
            if not result.data:
                raise ValueError(f"View with ID {view_id} not found")
            
            return result.data
        except Exception as e:
            logger.error(f"Error getting view {view_id}: {str(e)}")
            raise
    
    async def create_view(self, 
                         model_id: str,
                         name: str,
                         view_type: str,
                         description: Optional[str] = None,
                         configuration: Optional[Dict[str, Any]] = None,
                         user_id: str = None) -> Dict[str, Any]:
        """Create a new EA view.
        
        Args:
            model_id: ID of the model this view belongs to
            name: View name
            view_type: Type of view (diagram, matrix, heatmap, roadmap, list)
            description: View description
            configuration: View configuration
            user_id: ID of the user creating the view
            
        Returns:
            Created view data
        """
        try:
            # Validate view type
            valid_types = ["diagram", "matrix", "heatmap", "roadmap", "list"]
            if view_type not in valid_types:
                raise ValueError(f"Invalid view type. Must be one of: {', '.join(valid_types)}")
            
            # Prepare view data
            view_data = {
                "id": str(uuid.uuid4()),
                "model_id": model_id,
                "name": name,
                "view_type": view_type,
                "description": description,
                "configuration": configuration or {},
                "created_by": user_id,
                "created_at": datetime.now().isoformat()
            }
            
            # Create view
            result = await self.supabase.table("ea_views") \
                .insert(view_data) \
                .execute()
            
            return result.data[0] if result.data else view_data
        except Exception as e:
            logger.error(f"Error creating view: {str(e)}")
            raise
    
    async def update_view(self, 
                         view_id: str, 
                         updates: Dict[str, Any],
                         user_id: str = None) -> Dict[str, Any]:
        """Update an existing EA view.
        
        Args:
            view_id: ID of the view to update
            updates: Fields to update
            user_id: ID of the user updating the view
            
        Returns:
            Updated view data
        """
        try:
            # Validate view type if provided
            if "view_type" in updates:
                valid_types = ["diagram", "matrix", "heatmap", "roadmap", "list"]
                if updates["view_type"] not in valid_types:
                    raise ValueError(f"Invalid view type. Must be one of: {', '.join(valid_types)}")
            
            # Add audit fields
            updates["updated_by"] = user_id
            updates["updated_at"] = datetime.now().isoformat()
            
            # Update view
            result = await self.supabase.table("ea_views") \
                .update(updates) \
                .eq("id", view_id) \
                .execute()
            
            if not result.data:
                raise ValueError(f"View with ID {view_id} not found")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error updating view {view_id}: {str(e)}")
            raise
    
    async def delete_view(self, view_id: str) -> bool:
        """Delete an EA view.
        
        Args:
            view_id: ID of the view to delete
            
        Returns:
            True if successful
        """
        try:
            # Delete the view
            result = await self.supabase.table("ea_views") \
                .delete() \
                .eq("id", view_id) \
                .execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deleting view {view_id}: {str(e)}")
            raise
    
    # ==================== METAMODEL OPERATIONS ====================
    
    async def get_domains(self) -> List[Dict[str, Any]]:
        """Get all EA domains.
        
        Returns:
            List of EA domains
        """
        try:
            result = await self.supabase.table("ea_domains") \
                .select("*") \
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error getting domains: {str(e)}")
            raise
    
    async def get_element_types(self, domain_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get element types, optionally filtered by domain.
        
        Args:
            domain_id: Optional domain ID to filter by
            
        Returns:
            List of element types
        """
        try:
            query = self.supabase.table("ea_element_types").select("*")
            
            if domain_id:
                query = query.eq("domain_id", domain_id)
            
            result = await query.execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error getting element types: {str(e)}")
            raise
    
    async def get_relationship_types(self, 
                                   source_domain_id: Optional[str] = None,
                                   target_domain_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get relationship types, optionally filtered by domain.
        
        Args:
            source_domain_id: Optional source domain ID to filter by
            target_domain_id: Optional target domain ID to filter by
            
        Returns:
            List of relationship types
        """
        try:
            query = self.supabase.table("ea_relationship_types").select("*")
            
            if source_domain_id:
                query = query.eq("source_domain_id", source_domain_id)
            
            if target_domain_id:
                query = query.eq("target_domain_id", target_domain_id)
            
            result = await query.execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error getting relationship types: {str(e)}")
            raise
    
    # ==================== VERSIONING OPERATIONS ====================
    
    async def create_version(self, 
                           model_id: str, 
                           version: str, 
                           description: Optional[str] = None,
                           user_id: str = None) -> Dict[str, Any]:
        """Create a new version of an EA model.
        
        Args:
            model_id: ID of the model to version
            version: Version string
            description: Version description
            user_id: ID of the user creating the version
            
        Returns:
            New version model data
        """
        try:
            # Get the original model
            original_model = await self.get_model_by_id(model_id, include_elements=True)
            
            # Create new model as a version
            new_model_data = {
                "name": original_model["name"],
                "description": description or f"Version {version} of {original_model['name']}",
                "status": "draft",
                "version": version,
                "lifecycle_state": original_model["lifecycle_state"],
                "properties": {
                    **original_model["properties"],
                    "versioned_from": model_id,
                    "version_description": description
                },
                "user_id": user_id
            }
            
            # Create the new model
            new_model = await self.create_model(**new_model_data)
            
            # If original has elements, clone them to the new model
            if "elements" in original_model and original_model["elements"]:
                # Create mapping from old IDs to new IDs
                id_mapping = {}
                
                # Clone elements
                for element in original_model["elements"]:
                    new_element_data = {
                        "model_id": new_model["id"],
                        "type_id": element["type_id"],
                        "name": element["name"],
                        "description": element["description"],
                        "status": element["status"],
                        "position": {
                            "x": element["position_x"] if "position_x" in element else None,
                            "y": element["position_y"] if "position_y" in element else None
                        },
                        "properties": {
                            **element["properties"],
                            "versioned_from": element["id"]
                        },
                        "external_id": element["external_id"],
                        "external_source": element["external_source"],
                        "user_id": user_id
                    }
                    
                    # Create the new element
                    new_element = await self.create_element(**new_element_data)
                    
                    # Add to mapping
                    id_mapping[element["id"]] = new_element["id"]
                
                # Get relationships for the original model
                relationships = await self.get_relationships({"model_id": model_id})
                
                # Clone relationships
                for rel in relationships:
                    # Only clone if both source and target were cloned
                    if rel["source_element_id"] in id_mapping and rel["target_element_id"] in id_mapping:
                        new_relationship_data = {
                            "model_id": new_model["id"],
                            "relationship_type_id": rel["relationship_type_id"],
                            "source_element_id": id_mapping[rel["source_element_id"]],
                            "target_element_id": id_mapping[rel["target_element_id"]],
                            "name": rel["name"],
                            "description": rel["description"],
                            "status": rel["status"],
                            "properties": {
                                **rel["properties"],
                                "versioned_from": rel["id"]
                            },
                            "user_id": user_id
                        }
                        
                        # Create the new relationship
                        await self.create_relationship(**new_relationship_data)
                
                # Clone views
                views = await self.get_views({"model_id": model_id})
                
                for view in views:
                    # Update configuration to use new element IDs
                    config = view["configuration"]
                    if "elements" in config:
                        # Replace element IDs in the configuration
                        new_elements = []
                        for elem_id in config["elements"]:
                            if elem_id in id_mapping:
                                new_elements.append(id_mapping[elem_id])
                        
                        config["elements"] = new_elements
                    
                    new_view_data = {
                        "model_id": new_model["id"],
                        "name": view["name"],
                        "view_type": view["view_type"],
                        "description": view["description"],
                        "configuration": config,
                        "user_id": user_id
                    }
                    
                    # Create the new view
                    await self.create_view(**new_view_data)
            
            return new_model
        except Exception as e:
            logger.error(f"Error creating version of model {model_id}: {str(e)}")
            raise
    
    # ==================== SEARCH OPERATIONS ====================
    
    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Search for EA artifacts.
        
        Args:
            query: Search query string
            filters: Optional filters to apply
            
        Returns:
            Search results by category
        """
        try:
            results = {
                "models": [],
                "elements": [],
                "relationships": [],
                "views": []
            }
            
            # Search models
            model_query = self.supabase.table("ea_models") \
                .select("*") \
                .or(f"name.ilike.%{query}%,description.ilike.%{query}%")
            
            if filters and "model_filters" in filters:
                for field, value in filters["model_filters"].items():
                    if isinstance(value, list):
                        model_query = model_query.in_(field, value)
                    else:
                        model_query = model_query.eq(field, value)
            
            model_result = await model_query.execute()
            results["models"] = model_result.data
            
            # Search elements
            element_query = self.supabase.table("ea_elements") \
                .select("*") \
                .or(f"name.ilike.%{query}%,description.ilike.%{query}%")
            
            if filters and "element_filters" in filters:
                for field, value in filters["element_filters"].items():
                    if isinstance(value, list):
                        element_query = element_query.in_(field, value)
                    else:
                        element_query = element_query.eq(field, value)
            
            element_result = await element_query.execute()
            results["elements"] = element_result.data
            
            # Search relationships
            relationship_query = self.supabase.table("ea_relationships") \
                .select("*") \
                .or(f"name.ilike.%{query}%,description.ilike.%{query}%")
            
            if filters and "relationship_filters" in filters:
                for field, value in filters["relationship_filters"].items():
                    if isinstance(value, list):
                        relationship_query = relationship_query.in_(field, value)
                    else:
                        relationship_query = relationship_query.eq(field, value)
            
            relationship_result = await relationship_query.execute()
            results["relationships"] = relationship_result.data
            
            # Search views
            view_query = self.supabase.table("ea_views") \
                .select("*") \
                .or(f"name.ilike.%{query}%,description.ilike.%{query}%")
            
            if filters and "view_filters" in filters:
                for field, value in filters["view_filters"].items():
                    if isinstance(value, list):
                        view_query = view_query.in_(field, value)
                    else:
                        view_query = view_query.eq(field, value)
            
            view_result = await view_query.execute()
            results["views"] = view_result.data
            
            return results
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            raise
    
    # ==================== STATISTICS OPERATIONS ====================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics.
        
        Returns:
            Repository statistics
        """
        try:
            # Get counts
            models_count = await self.supabase.table("ea_models").select("count", count="exact").execute()
            elements_count = await self.supabase.table("ea_elements").select("count", count="exact").execute()
            relationships_count = await self.supabase.table("ea_relationships").select("count", count="exact").execute()
            views_count = await self.supabase.table("ea_views").select("count", count="exact").execute()
            domains_count = await self.supabase.table("ea_domains").select("count", count="exact").execute()
            element_types_count = await self.supabase.table("ea_element_types").select("count", count="exact").execute()
            relationship_types_count = await self.supabase.table("ea_relationship_types").select("count", count="exact").execute()
            
            # Get counts by status
            models_by_status = {}
            elements_by_status = {}
            relationships_by_status = {}
            
            for status in ["draft", "review", "approved", "archived"]:
                # Count models by status
                models_status_count = await self.supabase.table("ea_models") \
                    .select("count", count="exact") \
                    .eq("status", status) \
                    .execute()
                
                models_by_status[status] = models_status_count.count if hasattr(models_status_count, "count") else 0
                
                # Count elements by status
                elements_status_count = await self.supabase.table("ea_elements") \
                    .select("count", count="exact") \
                    .eq("status", status) \
                    .execute()
                
                elements_by_status[status] = elements_status_count.count if hasattr(elements_status_count, "count") else 0
                
                # Count relationships by status
                relationships_status_count = await self.supabase.table("ea_relationships") \
                    .select("count", count="exact") \
                    .eq("status", status) \
                    .execute()
                
                relationships_by_status[status] = relationships_status_count.count if hasattr(relationships_status_count, "count") else 0
            
            # Get counts by lifecycle state
            models_by_lifecycle = {}
            
            for state in ["current", "target", "transitional"]:
                # Count models by lifecycle state
                models_lifecycle_count = await self.supabase.table("ea_models") \
                    .select("count", count="exact") \
                    .eq("lifecycle_state", state) \
                    .execute()
                
                models_by_lifecycle[state] = models_lifecycle_count.count if hasattr(models_lifecycle_count, "count") else 0
            
            # Get counts by domain
            elements_by_domain = {}
            domains = await self.get_domains()
            
            for domain in domains:
                # Get element types in this domain
                element_types = await self.get_element_types(domain["id"])
                element_type_ids = [et["id"] for et in element_types]
                
                if element_type_ids:
                    # Count elements by domain (via element types)
                    elements_domain_count = await self.supabase.table("ea_elements") \
                        .select("count", count="exact") \
                        .in_("type_id", element_type_ids) \
                        .execute()
                    
                    elements_by_domain[domain["name"]] = elements_domain_count.count if hasattr(elements_domain_count, "count") else 0
                else:
                    elements_by_domain[domain["name"]] = 0
            
            # Get counts by view type
            views_by_type = {}
            
            for view_type in ["diagram", "matrix", "heatmap", "roadmap", "list"]:
                # Count views by type
                views_type_count = await self.supabase.table("ea_views") \
                    .select("count", count="exact") \
                    .eq("view_type", view_type) \
                    .execute()
                
                views_by_type[view_type] = views_type_count.count if hasattr(views_type_count, "count") else 0
            
            # Compile statistics
            return {
                "counts": {
                    "models": models_count.count if hasattr(models_count, "count") else 0,
                    "elements": elements_count.count if hasattr(elements_count, "count") else 0,
                    "relationships": relationships_count.count if hasattr(relationships_count, "count") else 0,
                    "views": views_count.count if hasattr(views_count, "count") else 0,
                    "domains": domains_count.count if hasattr(domains_count, "count") else 0,
                    "element_types": element_types_count.count if hasattr(element_types_count, "count") else 0,
                    "relationship_types": relationship_types_count.count if hasattr(relationship_types_count, "count") else 0
                },
                "status": {
                    "models": models_by_status,
                    "elements": elements_by_status,
                    "relationships": relationships_by_status
                },
                "lifecycle": {
                    "models": models_by_lifecycle
                },
                "domains": {
                    "elements": elements_by_domain
                },
                "view_types": views_by_type
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            raise
