"""
Enterprise Architecture Solution - Metadata Service

This module provides services for EA metamodel operations.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetadataService:
    """Service for EA metamodel operations."""
    
    def __init__(self, supabase_client):
        """Initialize the Metadata Service.
        
        Args:
            supabase_client: Configured Supabase client
        """
        self.supabase = supabase_client
    
    async def get_domains(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all EA domains.
        
        Args:
            user_id: ID of the requesting user
            
        Returns:
            List of EA domains
        """
        try:
            response = self.supabase.table("ea_domains") \
                .select("*") \
                .order("name") \
                .execute()
            
            if not response.data:
                return []
                
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting domains: {str(e)}")
            raise
    
    async def get_domain_by_id(self, domain_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get an EA domain by ID.
        
        Args:
            domain_id: ID of the domain to retrieve
            user_id: ID of the requesting user
            
        Returns:
            EA domain if found, None otherwise
        """
        try:
            response = self.supabase.table("ea_domains") \
                .select("*") \
                .eq("id", domain_id) \
                .execute()
            
            if not response.data:
                return None
                
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error getting domain by ID: {str(e)}")
            raise
    
    async def create_domain(self, domain_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new EA domain.
        
        Args:
            domain_data: Domain data to create
            user_id: ID of the user creating the domain
            
        Returns:
            Created domain
        """
        try:
            # Check if a domain with the same name already exists
            existing_domain = self.supabase.table("ea_domains") \
                .select("id") \
                .eq("name", domain_data["name"]) \
                .execute()
            
            if existing_domain.data:
                raise Exception(f"Domain with name '{domain_data['name']}' already exists")
            
            # Prepare the domain data
            new_domain = {
                "name": domain_data["name"],
                "description": domain_data.get("description")
            }
            
            # Insert the domain
            response = self.supabase.table("ea_domains").insert(new_domain).execute()
            
            if not response.data:
                raise Exception("Failed to create domain")
                
            # Get the created domain
            created_domain = await self.get_domain_by_id(response.data[0]["id"], user_id)
            
            return created_domain
            
        except Exception as e:
            logger.error(f"Error creating domain: {str(e)}")
            raise
    
    async def update_domain(self, domain_id: str, domain_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing EA domain.
        
        Args:
            domain_id: ID of the domain to update
            domain_data: Updated domain data
            user_id: ID of the user updating the domain
            
        Returns:
            Updated domain
        """
        try:
            # Check if the domain exists
            existing_domain = await self.get_domain_by_id(domain_id, user_id)
            
            if not existing_domain:
                raise Exception(f"Domain with ID {domain_id} not found")
            
            # Check if the name is being changed and if it conflicts
            if "name" in domain_data and domain_data["name"] != existing_domain["name"]:
                name_check = self.supabase.table("ea_domains") \
                    .select("id") \
                    .eq("name", domain_data["name"]) \
                    .execute()
                
                if name_check.data:
                    raise Exception(f"Domain with name '{domain_data['name']}' already exists")
            
            # Prepare the update data
            update_data = {
                "updated_at": datetime.now().isoformat()
            }
            
            # Add fields to update if they are provided
            if "name" in domain_data:
                update_data["name"] = domain_data["name"]
                
            if "description" in domain_data:
                update_data["description"] = domain_data["description"]
            
            # Update the domain
            response = self.supabase.table("ea_domains") \
                .update(update_data) \
                .eq("id", domain_id) \
                .execute()
            
            if not response.data:
                raise Exception(f"Failed to update domain with ID {domain_id}")
                
            # Get the updated domain
            updated_domain = await self.get_domain_by_id(domain_id, user_id)
            
            return updated_domain
            
        except Exception as e:
            logger.error(f"Error updating domain: {str(e)}")
            raise
    
    async def delete_domain(self, domain_id: str, user_id: str) -> bool:
        """Delete an EA domain.
        
        Args:
            domain_id: ID of the domain to delete
            user_id: ID of the user deleting the domain
            
        Returns:
            True if deleted successfully
        """
        try:
            # Check if the domain exists
            existing_domain = await self.get_domain_by_id(domain_id, user_id)
            
            if not existing_domain:
                raise Exception(f"Domain with ID {domain_id} not found")
            
            # Check for dependencies
            # 1. Check for element types in this domain
            element_types_response = self.supabase.table("ea_element_types") \
                .select("id") \
                .eq("domain_id", domain_id) \
                .execute()
            
            if element_types_response.data and len(element_types_response.data) > 0:
                raise Exception(f"Cannot delete domain with ID {domain_id} because it has associated element types")
            
            # 2. Check for relationship types with this domain as source or target
            relationship_types_response = self.supabase.table("ea_relationship_types") \
                .select("id") \
                .or(f"source_domain_id.eq.{domain_id},target_domain_id.eq.{domain_id}") \
                .execute()
            
            if relationship_types_response.data and len(relationship_types_response.data) > 0:
                raise Exception(f"Cannot delete domain with ID {domain_id} because it has associated relationship types")
            
            # Delete the domain
            response = self.supabase.table("ea_domains") \
                .delete() \
                .eq("id", domain_id) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting domain: {str(e)}")
            raise
    
    async def get_element_types(self, domain_id: Optional[str] = None, user_id: str = None) -> List[Dict[str, Any]]:
        """Get EA element types with optional domain filtering.
        
        Args:
            domain_id: Optional ID of the domain to filter by
            user_id: ID of the requesting user
            
        Returns:
            List of EA element types
        """
        try:
            query = self.supabase.table("ea_element_types") \
                .select("*, domain_id(id, name)")
            
            if domain_id:
                query = query.eq("domain_id", domain_id)
            
            response = query.order("name").execute()
            
            if not response.data:
                return []
                
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting element types: {str(e)}")
            raise
    
    async def get_element_type_by_id(self, type_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get an EA element type by ID.
        
        Args:
            type_id: ID of the element type to retrieve
            user_id: ID of the requesting user
            
        Returns:
            EA element type if found, None otherwise
        """
        try:
            response = self.supabase.table("ea_element_types") \
                .select("*, domain_id(id, name)") \
                .eq("id", type_id) \
                .execute()
            
            if not response.data:
                return None
                
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error getting element type by ID: {str(e)}")
            raise
    
    async def create_element_type(self, type_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new EA element type.
        
        Args:
            type_data: Element type data to create
            user_id: ID of the user creating the element type
            
        Returns:
            Created element type
        """
        try:
            # Check if the domain exists
            domain_response = self.supabase.table("ea_domains") \
                .select("id") \
                .eq("id", type_data["domain_id"]) \
                .execute()
            
            if not domain_response.data:
                raise Exception(f"Domain with ID {type_data['domain_id']} not found")
            
            # Check if an element type with the same name already exists in this domain
            existing_type = self.supabase.table("ea_element_types") \
                .select("id") \
                .eq("domain_id", type_data["domain_id"]) \
                .eq("name", type_data["name"]) \
                .execute()
            
            if existing_type.data:
                raise Exception(f"Element type with name '{type_data['name']}' already exists in this domain")
            
            # Prepare the element type data
            new_type = {
                "domain_id": type_data["domain_id"],
                "name": type_data["name"],
                "icon": type_data.get("icon"),
                "description": type_data.get("description"),
                "properties": type_data.get("properties", {})
            }
            
            # Insert the element type
            response = self.supabase.table("ea_element_types").insert(new_type).execute()
            
            if not response.data:
                raise Exception("Failed to create element type")
                
            # Get the created element type
            created_type = await self.get_element_type_by_id(response.data[0]["id"], user_id)
            
            return created_type
            
        except Exception as e:
            logger.error(f"Error creating element type: {str(e)}")
            raise
    
    async def update_element_type(self, type_id: str, type_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing EA element type.
        
        Args:
            type_id: ID of the element type to update
            type_data: Updated element type data
            user_id: ID of the user updating the element type
            
        Returns:
            Updated element type
        """
        try:
            # Check if the element type exists
            existing_type = await self.get_element_type_by_id(type_id, user_id)
            
            if not existing_type:
                raise Exception(f"Element type with ID {type_id} not found")
            
            # Prepare the update data
            update_data = {
                "updated_at": datetime.now().isoformat()
            }
            
            # Handle domain_id (requires validation)
            if "domain_id" in type_data and type_data["domain_id"] != existing_type["domain_id"]["id"]:
                # Check if the domain exists
                domain_response = self.supabase.table("ea_domains") \
                    .select("id") \
                    .eq("id", type_data["domain_id"]) \
                    .execute()
                
                if not domain_response.data:
                    raise Exception(f"Domain with ID {type_data['domain_id']} not found")
                
                update_data["domain_id"] = type_data["domain_id"]
            
            # Check if the name is being changed and if it conflicts
            if "name" in type_data and type_data["name"] != existing_type["name"]:
                domain_id = type_data.get("domain_id", existing_type["domain_id"]["id"])
                name_check = self.supabase.table("ea_element_types") \
                    .select("id") \
                    .eq("domain_id", domain_id) \
                    .eq("name", type_data["name"]) \
                    .execute()
                
                if name_check.data:
                    raise Exception(f"Element type with name '{type_data['name']}' already exists in this domain")
                
                update_data["name"] = type_data["name"]
            
            # Add other fields to update if they are provided
            if "icon" in type_data:
                update_data["icon"] = type_data["icon"]
                
            if "description" in type_data:
                update_data["description"] = type_data["description"]
                
            if "properties" in type_data:
                update_data["properties"] = type_data["properties"]
            
            # Update the element type
            response = self.supabase.table("ea_element_types") \
                .update(update_data) \
                .eq("id", type_id) \
                .execute()
            
            if not response.data:
                raise Exception(f"Failed to update element type with ID {type_id}")
                
            # Get the updated element type
            updated_type = await self.get_element_type_by_id(type_id, user_id)
            
            return updated_type
            
        except Exception as e:
            logger.error(f"Error updating element type: {str(e)}")
            raise
    
    async def delete_element_type(self, type_id: str, user_id: str) -> bool:
        """Delete an EA element type.
        
        Args:
            type_id: ID of the element type to delete
            user_id: ID of the user deleting the element type
            
        Returns:
            True if deleted successfully
        """
        try:
            # Check if the element type exists
            existing_type = await self.get_element_type_by_id(type_id, user_id)
            
            if not existing_type:
                raise Exception(f"Element type with ID {type_id} not found")
            
            # Check for dependencies
            # Check for elements of this type
            elements_response = self.supabase.table("ea_elements") \
                .select("id") \
                .eq("type_id", type_id) \
                .execute()
            
            if elements_response.data and len(elements_response.data) > 0:
                raise Exception(f"Cannot delete element type with ID {type_id} because it has associated elements")
            
            # Delete the element type
            response = self.supabase.table("ea_element_types") \
                .delete() \
                .eq("id", type_id) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting element type: {str(e)}")
            raise
    
    async def get_relationship_types(self, source_domain_id: Optional[str] = None, 
                                   target_domain_id: Optional[str] = None, 
                                   user_id: str = None) -> List[Dict[str, Any]]:
        """Get EA relationship types with optional domain filtering.
        
        Args:
            source_domain_id: Optional ID of the source domain to filter by
            target_domain_id: Optional ID of the target domain to filter by
            user_id: ID of the requesting user
            
        Returns:
            List of EA relationship types
        """
        try:
            query = self.supabase.table("ea_relationship_types") \
                .select("*, source_domain_id(id, name), target_domain_id(id, name)")
            
            if source_domain_id:
                query = query.eq("source_domain_id", source_domain_id)
            
            if target_domain_id:
                query = query.eq("target_domain_id", target_domain_id)
            
            response = query.order("name").execute()
            
            if not response.data:
                return []
                
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting relationship types: {str(e)}")
            raise
    
    async def get_relationship_type_by_id(self, type_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get an EA relationship type by ID.
        
        Args:
            type_id: ID of the relationship type to retrieve
            user_id: ID of the requesting user
            
        Returns:
            EA relationship type if found, None otherwise
        """
        try:
            response = self.supabase.table("ea_relationship_types") \
                .select("*, source_domain_id(id, name), target_domain_id(id, name)") \
                .eq("id", type_id) \
                .execute()
            
            if not response.data:
                return None
                
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error getting relationship type by ID: {str(e)}")
            raise
    
    async def create_relationship_type(self, type_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new EA relationship type.
        
        Args:
            type_data: Relationship type data to create
            user_id: ID of the user creating the relationship type
            
        Returns:
            Created relationship type
        """
        try:
            # Check if the domains exist
            if type_data.get("source_domain_id"):
                source_domain_response = self.supabase.table("ea_domains") \
                    .select("id") \
                    .eq("id", type_data["source_domain_id"]) \
                    .execute()
                
                if not source_domain_response.data:
                    raise Exception(f"Source domain with ID {type_data['source_domain_id']} not found")
            
            if type_data.get("target_domain_id"):
                target_domain_response = self.supabase.table("ea_domains") \
                    .select("id") \
                    .eq("id", type_data["target_domain_id"]) \
                    .execute()
                
                if not target_domain_response.data:
                    raise Exception(f"Target domain with ID {type_data['target_domain_id']} not found")
            
            # Check if a relationship type with the same name already exists
            existing_type = self.supabase.table("ea_relationship_types") \
                .select("id") \
                .eq("name", type_data["name"]) \
                .execute()
            
            if existing_type.data:
                raise Exception(f"Relationship type with name '{type_data['name']}' already exists")
            
            # Prepare the relationship type data
            new_type = {
                "name": type_data["name"],
                "source_domain_id": type_data.get("source_domain_id"),
                "target_domain_id": type_data.get("target_domain_id"),
                "directional": type_data.get("directional", True),
                "icon": type_data.get("icon"),
                "description": type_data.get("description"),
                "properties": type_data.get("properties", {})
            }
            
            # Insert the relationship type
            response = self.supabase.table("ea_relationship_types").insert(new_type).execute()
            
            if not response.data:
                raise Exception("Failed to create relationship type")
                
            # Get the created relationship type
            created_type = await self.get_relationship_type_by_id(response.data[0]["id"], user_id)
            
            return created_type
            
        except Exception as e:
            logger.error(f"Error creating relationship type: {str(e)}")
            raise
    
    async def update_relationship_type(self, type_id: str, type_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing EA relationship type.
        
        Args:
            type_id: ID of the relationship type to update
            type_data: Updated relationship type data
            user_id: ID of the user updating the relationship type
            
        Returns:
            Updated relationship type
        """
        try:
            # Check if the relationship type exists
            existing_type = await self.get_relationship_type_by_id(type_id, user_id)
            
            if not existing_type:
                raise Exception(f"Relationship type with ID {type_id} not found")
            
            # Prepare the update data
            update_data = {
                "updated_at": datetime.now().isoformat()
            }
            
            # Handle domain IDs (requires validation)
            if "source_domain_id" in type_data:
                if type_data["source_domain_id"]:
                    # Check if the domain exists
                    source_domain_response = self.supabase.table("ea_domains") \
                        .select("id") \
                        .eq("id", type_data["source_domain_id"]) \
                        .execute()
                    
                    if not source_domain_response.data:
                        raise Exception(f"Source domain with ID {type_data['source_domain_id']} not found")
                
                update_data["source_domain_id"] = type_data["source_domain_id"]
            
            if "target_domain_id" in type_data:
                if type_data["target_domain_id"]:
                    # Check if the domain exists
                    target_domain_response = self.supabase.table("ea_domains") \
                        .select("id") \
                        .eq("id", type_data["target_domain_id"]) \
                        .execute()
                    
                    if not target_domain_response.data:
                        raise Exception(f"Target domain with ID {type_data['target_domain_id']} not found")
                
                update_data["target_domain_id"] = type_data["target_domain_id"]
            
            # Check if the name is being changed and if it conflicts
            if "name" in type_data and type_data["name"] != existing_type["name"]:
                name_check = self.supabase.table("ea_relationship_types") \
                    .select("id") \
                    .eq("name", type_data["name"]) \
                    .execute()
                
                if name_check.data:
                    raise Exception(f"Relationship type with name '{type_data['name']}' already exists")
                
                update_data["name"] = type_data["name"]
            
            # Add other fields to update if they are provided
            if "directional" in type_data:
                update_data["directional"] = type_data["directional"]
                
            if "icon" in type_data:
                update_data["icon"] = type_data["icon"]
                
            if "description" in type_data:
                update_data["description"] = type_data["description"]
                
            if "properties" in type_data:
                update_data["properties"] = type_data["properties"]
            
            # Update the relationship type
            response = self.supabase.table("ea_relationship_types") \
                .update(update_data) \
                .eq("id", type_id) \
                .execute()
            
            if not response.data:
                raise Exception(f"Failed to update relationship type with ID {type_id}")
                
            # Get the updated relationship type
            updated_type = await self.get_relationship_type_by_id(type_id, user_id)
            
            return updated_type
            
        except Exception as e:
            logger.error(f"Error updating relationship type: {str(e)}")
            raise
    
    async def delete_relationship_type(self, type_id: str, user_id: str) -> bool:
        """Delete an EA relationship type.
        
        Args:
            type_id: ID of the relationship type to delete
            user_id: ID of the user deleting the relationship type
            
        Returns:
            True if deleted successfully
        """
        try:
            # Check if the relationship type exists
            existing_type = await self.get_relationship_type_by_id(type_id, user_id)
            
            if not existing_type:
                raise Exception(f"Relationship type with ID {type_id} not found")
            
            # Check for dependencies
            # Check for relationships of this type
            relationships_response = self.supabase.table("ea_relationships") \
                .select("id") \
                .eq("relationship_type_id", type_id) \
                .execute()
            
            if relationships_response.data and len(relationships_response.data) > 0:
                raise Exception(f"Cannot delete relationship type with ID {type_id} because it has associated relationships")
            
            # Delete the relationship type
            response = self.supabase.table("ea_relationship_types") \
                .delete() \
                .eq("id", type_id) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting relationship type: {str(e)}")
            raise