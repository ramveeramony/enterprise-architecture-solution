"""
Enterprise Architecture Solution - Model Service

This module provides services for EA model operations.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelService:
    """Service for EA model operations."""
    
    def __init__(self, supabase_client):
        """Initialize the Model Service.
        
        Args:
            supabase_client: Configured Supabase client
        """
        self.supabase = supabase_client
    
    async def get_models(self, user_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all EA models with optional filtering.
        
        Args:
            user_id: ID of the requesting user
            filters: Optional filters to apply
            
        Returns:
            List of EA models
        """
        try:
            query = self.supabase.table("ea_models").select("*, created_by(id, email), updated_by(id, email)")
            
            # Apply filters if provided
            if filters:
                if 'name' in filters:
                    query = query.ilike('name', f'%{filters["name"]}%')
                    
                if 'status' in filters:
                    query = query.eq('status', filters['status'])
                    
                if 'lifecycle_state' in filters:
                    query = query.eq('lifecycle_state', filters['lifecycle_state'])
            
            # Execute the query
            response = query.execute()
            
            if not response.data:
                return []
                
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            raise
    
    async def get_model_by_id(self, model_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get an EA model by ID.
        
        Args:
            model_id: ID of the model to retrieve
            user_id: ID of the requesting user
            
        Returns:
            EA model if found, None otherwise
        """
        try:
            response = self.supabase.table("ea_models") \
                .select("*, created_by(id, email), updated_by(id, email)") \
                .eq("id", model_id) \
                .execute()
            
            if not response.data:
                return None
                
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error getting model by ID: {str(e)}")
            raise
    
    async def create_model(self, model_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new EA model.
        
        Args:
            model_data: Model data to create
            user_id: ID of the user creating the model
            
        Returns:
            Created model
        """
        try:
            # Prepare the model data
            new_model = {
                "name": model_data["name"],
                "description": model_data.get("description"),
                "status": model_data.get("status", "draft"),
                "version": model_data.get("version", "1.0"),
                "lifecycle_state": model_data.get("lifecycle_state", "current"),
                "properties": model_data.get("properties", {}),
                "created_by": user_id
            }
            
            # Insert the model
            response = self.supabase.table("ea_models").insert(new_model).execute()
            
            if not response.data:
                raise Exception("Failed to create model")
                
            # Get the created model with user information
            created_model = await self.get_model_by_id(response.data[0]["id"], user_id)
            
            return created_model
            
        except Exception as e:
            logger.error(f"Error creating model: {str(e)}")
            raise
    
    async def update_model(self, model_id: str, model_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing EA model.
        
        Args:
            model_id: ID of the model to update
            model_data: Updated model data
            user_id: ID of the user updating the model
            
        Returns:
            Updated model
        """
        try:
            # Check if the model exists
            existing_model = await self.get_model_by_id(model_id, user_id)
            
            if not existing_model:
                raise Exception(f"Model with ID {model_id} not found")
            
            # Prepare the update data
            update_data = {
                "updated_at": datetime.now().isoformat(),
                "updated_by": user_id
            }
            
            # Add fields to update if they are provided
            if "name" in model_data:
                update_data["name"] = model_data["name"]
                
            if "description" in model_data:
                update_data["description"] = model_data["description"]
                
            if "status" in model_data:
                update_data["status"] = model_data["status"]
                
            if "version" in model_data:
                update_data["version"] = model_data["version"]
                
            if "lifecycle_state" in model_data:
                update_data["lifecycle_state"] = model_data["lifecycle_state"]
                
            if "properties" in model_data:
                update_data["properties"] = model_data["properties"]
            
            # Update the model
            response = self.supabase.table("ea_models") \
                .update(update_data) \
                .eq("id", model_id) \
                .execute()
            
            if not response.data:
                raise Exception(f"Failed to update model with ID {model_id}")
                
            # Get the updated model with user information
            updated_model = await self.get_model_by_id(model_id, user_id)
            
            return updated_model
            
        except Exception as e:
            logger.error(f"Error updating model: {str(e)}")
            raise
    
    async def delete_model(self, model_id: str, user_id: str) -> bool:
        """Delete an EA model.
        
        Args:
            model_id: ID of the model to delete
            user_id: ID of the user deleting the model
            
        Returns:
            True if deleted successfully
        """
        try:
            # Check if the model exists
            existing_model = await self.get_model_by_id(model_id, user_id)
            
            if not existing_model:
                raise Exception(f"Model with ID {model_id} not found")
            
            # First, check for dependencies
            # Check for elements
            elements_response = self.supabase.table("ea_elements") \
                .select("id") \
                .eq("model_id", model_id) \
                .execute()
            
            if elements_response.data and len(elements_response.data) > 0:
                raise Exception(f"Cannot delete model with ID {model_id} because it has associated elements")
            
            # Check for views
            views_response = self.supabase.table("ea_views") \
                .select("id") \
                .eq("model_id", model_id) \
                .execute()
            
            if views_response.data and len(views_response.data) > 0:
                raise Exception(f"Cannot delete model with ID {model_id} because it has associated views")
            
            # Delete the model
            response = self.supabase.table("ea_models") \
                .delete() \
                .eq("id", model_id) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting model: {str(e)}")
            raise
    
    async def clone_model(self, model_id: str, new_name: str, user_id: str) -> Dict[str, Any]:
        """Clone an existing EA model.
        
        Args:
            model_id: ID of the model to clone
            new_name: Name for the cloned model
            user_id: ID of the user cloning the model
            
        Returns:
            Cloned model
        """
        try:
            # Get the model to clone
            source_model = await self.get_model_by_id(model_id, user_id)
            
            if not source_model:
                raise Exception(f"Model with ID {model_id} not found")
            
            # Create a new model based on the source
            new_model = {
                "name": new_name,
                "description": source_model["description"],
                "status": "draft",  # Always start as draft
                "version": f"{source_model['version']}-clone",
                "lifecycle_state": source_model["lifecycle_state"],
                "properties": source_model["properties"],
                "created_by": user_id
            }
            
            # Insert the cloned model
            response = self.supabase.table("ea_models").insert(new_model).execute()
            
            if not response.data:
                raise Exception("Failed to clone model")
                
            cloned_model_id = response.data[0]["id"]
            
            # Get the elements from the source model
            elements_response = self.supabase.table("ea_elements") \
                .select("*") \
                .eq("model_id", model_id) \
                .execute()
            
            if elements_response.data:
                # Map of old element IDs to new element IDs
                element_id_map = {}
                
                # Clone each element
                for element in elements_response.data:
                    # Create a new element based on the source
                    new_element = {
                        "model_id": cloned_model_id,
                        "type_id": element["type_id"],
                        "name": element["name"],
                        "description": element["description"],
                        "status": "draft",  # Always start as draft
                        "external_id": element["external_id"],
                        "external_source": element["external_source"],
                        "properties": element["properties"],
                        "position_x": element["position_x"],
                        "position_y": element["position_y"],
                        "created_by": user_id
                    }
                    
                    # Insert the cloned element
                    new_element_response = self.supabase.table("ea_elements").insert(new_element).execute()
                    
                    if new_element_response.data:
                        # Add to the ID map
                        element_id_map[element["id"]] = new_element_response.data[0]["id"]
                
                # Get the relationships from the source model
                relationships_response = self.supabase.table("ea_relationships") \
                    .select("*") \
                    .eq("model_id", model_id) \
                    .execute()
                
                if relationships_response.data:
                    # Clone each relationship
                    for relationship in relationships_response.data:
                        # Only clone relationships where both elements were cloned
                        if relationship["source_element_id"] in element_id_map and relationship["target_element_id"] in element_id_map:
                            # Create a new relationship based on the source
                            new_relationship = {
                                "model_id": cloned_model_id,
                                "relationship_type_id": relationship["relationship_type_id"],
                                "source_element_id": element_id_map[relationship["source_element_id"]],
                                "target_element_id": element_id_map[relationship["target_element_id"]],
                                "name": relationship["name"],
                                "description": relationship["description"],
                                "status": "draft",  # Always start as draft
                                "properties": relationship["properties"],
                                "created_by": user_id
                            }
                            
                            # Insert the cloned relationship
                            self.supabase.table("ea_relationships").insert(new_relationship).execute()
            
            # Get the views from the source model
            views_response = self.supabase.table("ea_views") \
                .select("*") \
                .eq("model_id", model_id) \
                .execute()
            
            if views_response.data:
                # Clone each view
                for view in views_response.data:
                    # Create a new view based on the source
                    new_view = {
                        "model_id": cloned_model_id,
                        "name": view["name"],
                        "description": view["description"],
                        "view_type": view["view_type"],
                        "configuration": view["configuration"],
                        "created_by": user_id
                    }
                    
                    # Insert the cloned view
                    self.supabase.table("ea_views").insert(new_view).execute()
            
            # Get the cloned model with user information
            cloned_model = await self.get_model_by_id(cloned_model_id, user_id)
            
            return cloned_model
            
        except Exception as e:
            logger.error(f"Error cloning model: {str(e)}")
            raise
    
    async def get_model_version_history(self, model_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get the version history of an EA model.
        
        Args:
            model_id: ID of the model
            user_id: ID of the requesting user
            
        Returns:
            List of model versions
        """
        try:
            # Get the current model
            current_model = await self.get_model_by_id(model_id, user_id)
            
            if not current_model:
                raise Exception(f"Model with ID {model_id} not found")
            
            # Get the base name (without version)
            base_name = current_model["name"].split(" v")[0]
            
            # Find all models with the same base name
            response = self.supabase.table("ea_models") \
                .select("*, created_by(id, email), updated_by(id, email)") \
                .ilike("name", f"{base_name}%") \
                .order("created_at", {"ascending": False}) \
                .execute()
            
            if not response.data:
                # At minimum, return the current model as a version
                return [current_model]
                
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting model version history: {str(e)}")
            raise
    
    async def create_model_version(self, model_id: str, version: str, user_id: str) -> Dict[str, Any]:
        """Create a new version of an EA model.
        
        Args:
            model_id: ID of the model to version
            version: Version number/string
            user_id: ID of the user creating the version
            
        Returns:
            New model version
        """
        try:
            # Get the model to version
            source_model = await self.get_model_by_id(model_id, user_id)
            
            if not source_model:
                raise Exception(f"Model with ID {model_id} not found")
            
            # Create a name for the new version
            base_name = source_model["name"].split(" v")[0]
            new_name = f"{base_name} v{version}"
            
            # Clone the model with the new name and version
            new_model = {
                "name": new_name,
                "description": source_model["description"],
                "status": "draft",  # Always start as draft
                "version": version,
                "lifecycle_state": source_model["lifecycle_state"],
                "properties": source_model["properties"],
                "created_by": user_id
            }
            
            # Insert the new version
            response = self.supabase.table("ea_models").insert(new_model).execute()
            
            if not response.data:
                raise Exception("Failed to create model version")
                
            # Now clone all the elements, relationships, and views (reusing the clone logic)
            new_model_id = response.data[0]["id"]
            cloned_model = await self.clone_model(model_id, new_name, user_id)
            
            # Update the version information
            update_response = self.supabase.table("ea_models") \
                .update({"version": version}) \
                .eq("id", new_model_id) \
                .execute()
            
            # Get the new version with user information
            new_version = await self.get_model_by_id(new_model_id, user_id)
            
            return new_version
            
        except Exception as e:
            logger.error(f"Error creating model version: {str(e)}")
            raise
