"""
Enterprise Architecture Solution - Repository Service

This module provides core repository services for the EA solution.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RepositoryService:
    """Service for managing EA repository entities."""
    
    def __init__(self, supabase_client):
        """Initialize the Repository Service.
        
        Args:
            supabase_client: A configured Supabase client for database operations
        """
        self.supabase = supabase_client
    
    # ========== Model Management ==========
    
    def get_models(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all EA models with optional filtering.
        
        Args:
            filters: Optional dictionary of filter conditions
            
        Returns:
            List of model dictionaries
        """
        try:
            query = self.supabase.table("ea_models").select("*")
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if key == "status":
                        query = query.eq(key, value)
                    elif key == "name":
                        query = query.ilike(key, f"%{value}%")
                    elif key == "created_by":
                        query = query.eq(key, value)
                    elif key == "lifecycle_state":
                        query = query.eq(key, value)
            
            # Execute the query
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            raise
    
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get an EA model by ID.
        
        Args:
            model_id: UUID of the model
            
        Returns:
            Model dictionary or None if not found
        """
        try:
            result = self.supabase.table("ea_models").select("*").eq("id", model_id).single().execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting model: {str(e)}")
            raise
    
    def create_model(self, user_id: str, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new EA model.
        
        Args:
            user_id: UUID of the creating user
            model_data: Dictionary containing model data
            
        Returns:
            Created model dictionary
        """
        try:
            # Set creation metadata
            model_data["created_by"] = user_id
            model_data["created_at"] = datetime.now().isoformat()
            
            # Set default status if not provided
            if "status" not in model_data:
                model_data["status"] = "draft"
            
            # Create the model
            result = self.supabase.table("ea_models").insert(model_data).execute()
            
            # Return the created model
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error creating model: {str(e)}")
            raise
    
    def update_model(self, model_id: str, user_id: str, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing EA model.
        
        Args:
            model_id: UUID of the model
            user_id: UUID of the updating user
            model_data: Dictionary containing updated model data
            
        Returns:
            Updated model dictionary
        """
        try:
            # Set update metadata
            model_data["updated_by"] = user_id
            model_data["updated_at"] = datetime.now().isoformat()
            
            # Update the model
            result = self.supabase.table("ea_models").update(model_data).eq("id", model_id).execute()
            
            # Return the updated model
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error updating model: {str(e)}")
            raise
    
    def delete_model(self, model_id: str) -> bool:
        """Delete an EA model.
        
        Args:
            model_id: UUID of the model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, delete all elements in the model (which will cascade to relationships)
            elements = self.supabase.table("ea_elements").select("id").eq("model_id", model_id).execute().data
            for element in elements:
                self.delete_element(element["id"])
            
            # Delete all views in the model
            self.supabase.table("ea_views").delete().eq("model_id", model_id).execute()
            
            # Delete the model
            result = self.supabase.table("ea_models").delete().eq("id", model_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error deleting model: {str(e)}")
            raise
    
    def create_model_version(self, model_id: str, user_id: str, new_version: str) -> Dict[str, Any]:
        """Create a new version of an existing model.
        
        Args:
            model_id: UUID of the original model
            user_id: UUID of the creating user
            new_version: Version identifier for the new model
            
        Returns:
            Newly created model version
        """
        try:
            # Get the original model
            original_model = self.get_model(model_id)
            if not original_model:
                raise ValueError(f"Model with ID {model_id} not found")
            
            # Create a new model based on the original
            new_model = {
                "name": original_model["name"],
                "description": original_model["description"],
                "status": "draft",
                "version": new_version,
                "lifecycle_state": original_model["lifecycle_state"],
                "properties": original_model["properties"],
                "created_by": user_id
            }
            
            # Create the new model
            new_model_result = self.create_model(user_id, new_model)
            new_model_id = new_model_result["id"]
            
            # Copy all elements to the new model
            self._copy_model_elements(model_id, new_model_id, user_id)
            
            # Copy all views to the new model
            self._copy_model_views(model_id, new_model_id, user_id)
            
            return new_model_result
            
        except Exception as e:
            logger.error(f"Error creating model version: {str(e)}")
            raise
    
    def _copy_model_elements(self, source_model_id: str, target_model_id: str, user_id: str) -> None:
        """Copy all elements from one model to another.
        
        Args:
            source_model_id: UUID of the source model
            target_model_id: UUID of the target model
            user_id: UUID of the creating user
        """
        try:
            # Get all elements from the source model
            elements = self.get_elements({"model_id": source_model_id})
            
            # Create element ID mapping for relationship copy
            id_mapping = {}
            
            # Copy each element to the new model
            for element in elements:
                old_id = element["id"]
                
                # Create new element data
                new_element = {
                    "model_id": target_model_id,
                    "type_id": element["type_id"],
                    "name": element["name"],
                    "description": element["description"],
                    "external_id": element["external_id"],
                    "external_source": element["external_source"],
                    "properties": element["properties"],
                    "position_x": element.get("position_x"),
                    "position_y": element.get("position_y"),
                    "status": element["status"],
                    "created_by": user_id
                }
                
                # Create the new element
                new_element_result = self.create_element(user_id, new_element)
                
                # Add to ID mapping
                id_mapping[old_id] = new_element_result["id"]
            
            # Copy relationships using the ID mapping
            relationships = self.supabase.table("ea_relationships").select("*").eq("model_id", source_model_id).execute().data
            
            for rel in relationships:
                # Skip if either source or target isn't in the mapping (shouldn't happen)
                if rel["source_element_id"] not in id_mapping or rel["target_element_id"] not in id_mapping:
                    continue
                
                # Create new relationship
                new_rel = {
                    "model_id": target_model_id,
                    "relationship_type_id": rel["relationship_type_id"],
                    "source_element_id": id_mapping[rel["source_element_id"]],
                    "target_element_id": id_mapping[rel["target_element_id"]],
                    "name": rel["name"],
                    "description": rel["description"],
                    "properties": rel["properties"],
                    "status": rel["status"],
                    "created_by": user_id
                }
                
                # Create the relationship
                self.create_relationship(user_id, new_rel)
                
        except Exception as e:
            logger.error(f"Error copying model elements: {str(e)}")
            raise
    
    def _copy_model_views(self, source_model_id: str, target_model_id: str, user_id: str) -> None:
        """Copy all views from one model to another.
        
        Args:
            source_model_id: UUID of the source model
            target_model_id: UUID of the target model
            user_id: UUID of the creating user
        """
        try:
            # Get all views from the source model
            views = self.supabase.table("ea_views").select("*").eq("model_id", source_model_id).execute().data
            
            # Copy each view to the new model
            for view in views:
                # Create new view data
                new_view = {
                    "model_id": target_model_id,
                    "name": view["name"],
                    "description": view["description"],
                    "view_type": view["view_type"],
                    "configuration": view["configuration"],
                    "created_by": user_id
                }
                
                # Create the new view
                self.supabase.table("ea_views").insert(new_view).execute()
                
        except Exception as e:
            logger.error(f"Error copying model views: {str(e)}")
            raise
    
    # ========== Element Management ==========
    
    def get_elements(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all EA elements with optional filtering.
        
        Args:
            filters: Optional dictionary of filter conditions
            
        Returns:
            List of element dictionaries
        """
        try:
            query = self.supabase.table("ea_elements").select("*, ea_element_types(name, domain_id)")
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if key == "model_id":
                        query = query.eq(key, value)
                    elif key == "type_id":
                        query = query.eq(key, value)
                    elif key == "name":
                        query = query.ilike(key, f"%{value}%")
                    elif key == "status":
                        query = query.eq(key, value)
            
            # Execute the query
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting elements: {str(e)}")
            raise
    
    def get_element(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Get an EA element by ID.
        
        Args:
            element_id: UUID of the element
            
        Returns:
            Element dictionary or None if not found
        """
        try:
            result = self.supabase.table("ea_elements").select("*, ea_element_types(name, domain_id)").eq("id", element_id).single().execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting element: {str(e)}")
            raise
    
    def create_element(self, user_id: str, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new EA element.
        
        Args:
            user_id: UUID of the creating user
            element_data: Dictionary containing element data
            
        Returns:
            Created element dictionary
        """
        try:
            # Set creation metadata
            element_data["created_by"] = user_id
            element_data["created_at"] = datetime.now().isoformat()
            
            # Set default status if not provided
            if "status" not in element_data:
                element_data["status"] = "draft"
            
            # Create the element
            result = self.supabase.table("ea_elements").insert(element_data).execute()
            
            # Return the created element
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error creating element: {str(e)}")
            raise
    
    def update_element(self, element_id: str, user_id: str, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing EA element.
        
        Args:
            element_id: UUID of the element
            user_id: UUID of the updating user
            element_data: Dictionary containing updated element data
            
        Returns:
            Updated element dictionary
        """
        try:
            # Set update metadata
            element_data["updated_by"] = user_id
            element_data["updated_at"] = datetime.now().isoformat()
            
            # Update the element
            result = self.supabase.table("ea_elements").update(element_data).eq("id", element_id).execute()
            
            # Return the updated element
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error updating element: {str(e)}")
            raise
    
    def delete_element(self, element_id: str) -> bool:
        """Delete an EA element.
        
        Args:
            element_id: UUID of the element
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, delete all relationships involving this element
            self.supabase.table("ea_relationships").delete().eq("source_element_id", element_id).execute()
            self.supabase.table("ea_relationships").delete().eq("target_element_id", element_id).execute()
            
            # Delete the element
            result = self.supabase.table("ea_elements").delete().eq("id", element_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error deleting element: {str(e)}")
            raise
    
    # ========== Relationship Management ==========
    
    def get_relationships(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all EA relationships with optional filtering.
        
        Args:
            filters: Optional dictionary of filter conditions
            
        Returns:
            List of relationship dictionaries
        """
        try:
            query = self.supabase.table("ea_relationships").select("""
                *,
                source:source_element_id(id, name, type_id),
                target:target_element_id(id, name, type_id),
                relationship_type:relationship_type_id(id, name)
            """)
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if key == "model_id":
                        query = query.eq(key, value)
                    elif key == "relationship_type_id":
                        query = query.eq(key, value)
                    elif key == "source_element_id":
                        query = query.eq(key, value)
                    elif key == "target_element_id":
                        query = query.eq(key, value)
            
            # Execute the query
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting relationships: {str(e)}")
            raise
    
    def get_relationship(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """Get an EA relationship by ID.
        
        Args:
            relationship_id: UUID of the relationship
            
        Returns:
            Relationship dictionary or None if not found
        """
        try:
            result = self.supabase.table("ea_relationships").select("""
                *,
                source:source_element_id(id, name, type_id),
                target:target_element_id(id, name, type_id),
                relationship_type:relationship_type_id(id, name)
            """).eq("id", relationship_id).single().execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting relationship: {str(e)}")
            raise
    
    def create_relationship(self, user_id: str, relationship_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new EA relationship.
        
        Args:
            user_id: UUID of the creating user
            relationship_data: Dictionary containing relationship data
            
        Returns:
            Created relationship dictionary
        """
        try:
            # Set creation metadata
            relationship_data["created_by"] = user_id
            relationship_data["created_at"] = datetime.now().isoformat()
            
            # Set default status if not provided
            if "status" not in relationship_data:
                relationship_data["status"] = "draft"
            
            # Create the relationship
            result = self.supabase.table("ea_relationships").insert(relationship_data).execute()
            
            # Return the created relationship
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            raise
    
    def update_relationship(self, relationship_id: str, user_id: str, relationship_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing EA relationship.
        
        Args:
            relationship_id: UUID of the relationship
            user_id: UUID of the updating user
            relationship_data: Dictionary containing updated relationship data
            
        Returns:
            Updated relationship dictionary
        """
        try:
            # Set update metadata
            relationship_data["updated_by"] = user_id
            relationship_data["updated_at"] = datetime.now().isoformat()
            
            # Update the relationship
            result = self.supabase.table("ea_relationships").update(relationship_data).eq("id", relationship_id).execute()
            
            # Return the updated relationship
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error updating relationship: {str(e)}")
            raise
    
    def delete_relationship(self, relationship_id: str) -> bool:
        """Delete an EA relationship.
        
        Args:
            relationship_id: UUID of the relationship
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the relationship
            result = self.supabase.table("ea_relationships").delete().eq("id", relationship_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error deleting relationship: {str(e)}")
            raise
    
    # ========== View Management ==========
    
    def get_views(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all EA views with optional filtering.
        
        Args:
            filters: Optional dictionary of filter conditions
            
        Returns:
            List of view dictionaries
        """
        try:
            query = self.supabase.table("ea_views").select("*")
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if key == "model_id":
                        query = query.eq(key, value)
                    elif key == "view_type":
                        query = query.eq(key, value)
                    elif key == "name":
                        query = query.ilike(key, f"%{value}%")
            
            # Execute the query
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting views: {str(e)}")
            raise
    
    def get_view(self, view_id: str) -> Optional[Dict[str, Any]]:
        """Get an EA view by ID.
        
        Args:
            view_id: UUID of the view
            
        Returns:
            View dictionary or None if not found
        """
        try:
            result = self.supabase.table("ea_views").select("*").eq("id", view_id).single().execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting view: {str(e)}")
            raise
    
    def create_view(self, user_id: str, view_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new EA view.
        
        Args:
            user_id: UUID of the creating user
            view_data: Dictionary containing view data
            
        Returns:
            Created view dictionary
        """
        try:
            # Set creation metadata
            view_data["created_by"] = user_id
            view_data["created_at"] = datetime.now().isoformat()
            
            # Create the view
            result = self.supabase.table("ea_views").insert(view_data).execute()
            
            # Return the created view
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error creating view: {str(e)}")
            raise
    
    def update_view(self, view_id: str, user_id: str, view_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing EA view.
        
        Args:
            view_id: UUID of the view
            user_id: UUID of the updating user
            view_data: Dictionary containing updated view data
            
        Returns:
            Updated view dictionary
        """
        try:
            # Set update metadata
            view_data["updated_by"] = user_id
            view_data["updated_at"] = datetime.now().isoformat()
            
            # Update the view
            result = self.supabase.table("ea_views").update(view_data).eq("id", view_id).execute()
            
            # Return the updated view
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error updating view: {str(e)}")
            raise
    
    def delete_view(self, view_id: str) -> bool:
        """Delete an EA view.
        
        Args:
            view_id: UUID of the view
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the view
            result = self.supabase.table("ea_views").delete().eq("id", view_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error deleting view: {str(e)}")
            raise
    
    # ========== Metamodel Management ==========
    
    def get_domains(self) -> List[Dict[str, Any]]:
        """Get all EA domains.
        
        Returns:
            List of domain dictionaries
        """
        try:
            result = self.supabase.table("ea_domains").select("*").execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting domains: {str(e)}")
            raise
    
    def get_element_types(self, domain_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all EA element types, optionally filtered by domain.
        
        Args:
            domain_id: Optional UUID of the domain to filter by
            
        Returns:
            List of element type dictionaries
        """
        try:
            query = self.supabase.table("ea_element_types").select("*, ea_domains(name)")
            
            if domain_id:
                query = query.eq("domain_id", domain_id)
            
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting element types: {str(e)}")
            raise
    
    def get_relationship_types(self) -> List[Dict[str, Any]]:
        """Get all EA relationship types.
        
        Returns:
            List of relationship type dictionaries
        """
        try:
            result = self.supabase.table("ea_relationship_types").select("*").execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting relationship types: {str(e)}")
            raise
