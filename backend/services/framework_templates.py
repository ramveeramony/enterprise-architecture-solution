"""
Enterprise Architecture Solution - Framework Templates Module

This module provides comprehensive enterprise architecture framework templates and metamodels
for the Enterprise Architecture Solution. It supports various industry-standard frameworks
like TOGAF, ArchiMate, Zachman, and custom frameworks like WEAF (WA Enterprise Architecture Framework).
"""

import os
import logging
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from pydantic import BaseModel, Field
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Enums
class FrameworkType(str, Enum):
    TOGAF = "togaf"
    ARCHIMATE = "archimate"
    ZACHMAN = "zachman"
    FEAF = "feaf"
    DODAF = "dodaf"
    MODAF = "modaf"
    WEAF = "weaf"  # WA Enterprise Architecture Framework
    CUSTOM = "custom"

class ElementType(str, Enum):
    BUSINESS = "business"
    DATA = "data"
    APPLICATION = "application"
    TECHNOLOGY = "technology"
    STRATEGY = "strategy"
    MOTIVATION = "motivation"
    IMPLEMENTATION = "implementation"
    PHYSICAL = "physical"
    GOVERNANCE = "governance"

class ViewpointType(str, Enum):
    STAKEHOLDER = "stakeholder"
    GOAL_REALIZATION = "goal_realization"
    SERVICE_REALIZATION = "service_realization"
    IMPLEMENTATION_DEPLOYMENT = "implementation_deployment"
    TECHNOLOGY_USAGE = "technology_usage"
    LAYERED = "layered"
    LANDSCAPE = "landscape"
    CAPABILITY = "capability"
    DATA_FLOW = "data_flow"
    INFRASTRUCTURE = "infrastructure"
    CUSTOM = "custom"

# Models
class ElementDefinition(BaseModel):
    name: str = Field(..., description="Name of the element type")
    description: str = Field(..., description="Description of the element type")
    domain: ElementType = Field(..., description="Domain of the element type")
    notation: Dict[str, Any] = Field(default_factory=dict, description="Notation/display properties")
    properties: List[Dict[str, Any]] = Field(default_factory=list, description="Properties of the element type")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="Allowed relationships")
    icon: Optional[str] = None

class ViewpointDefinition(BaseModel):
    name: str = Field(..., description="Name of the viewpoint")
    description: str = Field(..., description="Description of the viewpoint")
    type: ViewpointType = Field(..., description="Type of viewpoint")
    purpose: str = Field(..., description="Purpose of the viewpoint")
    stakeholders: List[str] = Field(default_factory=list, description="Target stakeholders")
    elements: List[str] = Field(default_factory=list, description="Allowed element types")
    notation: Dict[str, Any] = Field(default_factory=dict, description="Notation/display properties")

class FrameworkBase(BaseModel):
    name: str = Field(..., description="Name of the framework")
    description: str = Field(..., description="Description of the framework")
    framework_type: FrameworkType = Field(..., description="Type of framework")
    version: str = Field(..., description="Version of the framework")
    domains: List[Dict[str, Any]] = Field(default_factory=list, description="Domains in the framework")
    elements: List[ElementDefinition] = Field(default_factory=list, description="Element types in the framework")
    viewpoints: List[ViewpointDefinition] = Field(default_factory=list, description="Viewpoints in the framework")
    custom_properties: Dict[str, Any] = Field(default_factory=dict, description="Custom properties")

class FrameworkTemplate(FrameworkBase):
    id: UUID = Field(..., description="Framework template unique identifier")
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: Optional[str] = None
    is_system: bool = Field(default=False, description="Whether this is a system-provided template")

class FrameworkTemplateCreate(FrameworkBase):
    pass

class FrameworkTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    domains: Optional[List[Dict[str, Any]]] = None
    elements: Optional[List[ElementDefinition]] = None
    viewpoints: Optional[List[ViewpointDefinition]] = None
    custom_properties: Optional[Dict[str, Any]] = None

class ModelInstantiationRequest(BaseModel):
    framework_id: UUID = Field(..., description="Framework template ID")
    model_name: str = Field(..., description="Name for the new model")
    model_description: Optional[str] = None
    customize_elements: bool = Field(default=False, description="Whether to customize elements during instantiation")
    customize_viewpoints: bool = Field(default=False, description="Whether to customize viewpoints during instantiation")

class ModelInstantiationResponse(BaseModel):
    success: bool
    message: str
    model_id: Optional[UUID] = None
    warnings: List[str] = Field(default_factory=list)

# Mock database - in a real implementation, this would be replaced with Supabase
mock_framework_templates = {}

# Helper Functions
def get_current_user():
    """
    Get the current authenticated user.
    
    Returns:
        Mock user ID for demonstration purposes
    """
    return "user-123"  # Mock user ID

def generate_uuid():
    """
    Generate a UUID.
    
    Returns:
        A new UUID
    """
    return uuid.uuid4()

def load_system_templates():
    """
    Load system-provided framework templates.
    
    This function loads predefined templates for common EA frameworks.
    In a real implementation, these would be loaded from a database or configuration files.
    """
    # Implementation for loading system templates... (abbreviated for brevity)
    logger.info(f"Loaded {len(mock_framework_templates)} system framework templates")

# Routes
@router.post("/templates", response_model=FrameworkTemplate)
async def create_framework_template(
    template: FrameworkTemplateCreate = Body(...)
):
    """
    Create a new framework template.
    
    Args:
        template: Framework template details
    
    Returns:
        The created framework template
    """
    try:
        # Generate a new UUID for the template
        template_id = generate_uuid()
        
        # Get the current user
        current_user = get_current_user()
        
        # Current timestamp
        now = datetime.now()
        
        # Create the template record
        new_template = {
            "id": template_id,
            **template.dict(),
            "created_at": now,
            "updated_at": now,
            "created_by": current_user,
            "updated_by": None,
            "is_system": False
        }
        
        # Store the template in the mock database
        mock_framework_templates[str(template_id)] = new_template
        
        # Log the creation
        logger.info(f"Created new framework template: {new_template['name']} (ID: {template_id})")
        
        # Return the created template
        return FrameworkTemplate(**new_template)
    except Exception as e:
        logger.error(f"Error creating framework template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating framework template: {str(e)}")

@router.get("/templates", response_model=List[FrameworkTemplate])
async def list_framework_templates(
    framework_type: Optional[FrameworkType] = None,
    include_system: bool = Query(True, description="Whether to include system-provided templates"),
    search: Optional[str] = None
):
    """
    List framework templates with optional filtering.
    
    Args:
        framework_type: Filter by framework type
        include_system: Whether to include system-provided templates
        search: Search term for name or description
    
    Returns:
        List of framework templates matching the criteria
    """
    try:
        # Convert templates dictionary values to a list
        templates = list(mock_framework_templates.values())
        
        # Apply filters
        filtered_templates = templates
        
        # Filter by framework type
        if framework_type:
            filtered_templates = [t for t in filtered_templates if t["framework_type"] == framework_type]
        
        # Filter by system/custom
        if not include_system:
            filtered_templates = [t for t in filtered_templates if not t["is_system"]]
        
        # Filter by search term
        if search:
            search_lower = search.lower()
            filtered_templates = [
                t for t in filtered_templates 
                if search_lower in t["name"].lower() or 
                   (t["description"] and search_lower in t["description"].lower())
            ]
        
        # Convert to Pydantic models
        return [FrameworkTemplate(**template) for template in filtered_templates]
    except Exception as e:
        logger.error(f"Error listing framework templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing framework templates: {str(e)}")

@router.get("/templates/{template_id}", response_model=FrameworkTemplate)
async def get_framework_template(
    template_id: UUID = Path(..., description="Framework template ID")
):
    """
    Get a specific framework template by ID.
    
    Args:
        template_id: Framework template ID
    
    Returns:
        The requested framework template
    """
    try:
        template_id_str = str(template_id)
        
        # Check if the template exists
        if template_id_str not in mock_framework_templates:
            raise HTTPException(status_code=404, detail=f"Framework template {template_id} not found")
        
        # Return the template
        return FrameworkTemplate(**mock_framework_templates[template_id_str])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving framework template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving framework template: {str(e)}")

@router.put("/templates/{template_id}", response_model=FrameworkTemplate)
async def update_framework_template(
    template_id: UUID = Path(..., description="Framework template ID"),
    template_update: FrameworkTemplateUpdate = Body(...)
):
    """
    Update an existing framework template.
    
    Args:
        template_id: Framework template ID
        template_update: Framework template update details
    
    Returns:
        The updated framework template
    """
    try:
        template_id_str = str(template_id)
        
        # Check if the template exists
        if template_id_str not in mock_framework_templates:
            raise HTTPException(status_code=404, detail=f"Framework template {template_id} not found")
        
        # Get the existing template
        existing_template = mock_framework_templates[template_id_str]
        
        # Check if it's a system template
        if existing_template["is_system"]:
            raise HTTPException(status_code=403, detail="Cannot update system-provided templates")
        
        # Get the current user
        current_user = get_current_user()
        
        # Current timestamp
        now = datetime.now()
        
        # Update the template with the new values
        update_data = template_update.dict(exclude_unset=True)
        
        # Update the template
        updated_template = {
            **existing_template,
            **update_data,
            "updated_at": now,
            "updated_by": current_user
        }
        
        # Store the updated template
        mock_framework_templates[template_id_str] = updated_template
        
        # Log the update
        logger.info(f"Updated framework template: {updated_template['name']} (ID: {template_id})")
        
        # Return the updated template
        return FrameworkTemplate(**updated_template)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating framework template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating framework template: {str(e)}")

@router.delete("/templates/{template_id}")
async def delete_framework_template(
    template_id: UUID = Path(..., description="Framework template ID")
):
    """
    Delete a framework template.
    
    Args:
        template_id: Framework template ID
    
    Returns:
        Success message
    """
    try:
        template_id_str = str(template_id)
        
        # Check if the template exists
        if template_id_str not in mock_framework_templates:
            raise HTTPException(status_code=404, detail=f"Framework template {template_id} not found")
        
        # Get the template
        template = mock_framework_templates[template_id_str]
        
        # Check if it's a system template
        if template["is_system"]:
            raise HTTPException(status_code=403, detail="Cannot delete system-provided templates")
        
        # Delete the template
        del mock_framework_templates[template_id_str]
        
        # Log the deletion
        logger.info(f"Deleted framework template: {template['name']} (ID: {template_id})")
        
        return {
            "success": True,
            "message": f"Framework template {template_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting framework template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting framework template: {str(e)}")

@router.post("/models/instantiate", response_model=ModelInstantiationResponse)
async def instantiate_model_from_template(
    request: ModelInstantiationRequest = Body(...)
):
    """
    Create a new EA model based on a framework template.
    
    Args:
        request: Model instantiation request details
    
    Returns:
        Information about the created model
    """
    try:
        template_id_str = str(request.framework_id)
        
        # Check if the template exists
        if template_id_str not in mock_framework_templates:
            raise HTTPException(status_code=404, detail=f"Framework template {request.framework_id} not found")
        
        # Get the template
        template = mock_framework_templates[template_id_str]
        
        # Generate a new UUID for the model
        model_id = generate_uuid()
        
        # Get the current user
        current_user = get_current_user()
        
        # Current timestamp
        now = datetime.now()
        
        # In a real implementation, you would create a new model in the database
        # using the template as a basis, and optionally customize elements and viewpoints
        
        # For this example, we'll simulate creating a model
        logger.info(f"Instantiated model '{request.model_name}' (ID: {model_id}) from template '{template['name']}'")
        
        # Return the model information
        return ModelInstantiationResponse(
            success=True,
            message=f"Successfully created model '{request.model_name}' based on template '{template['name']}'",
            model_id=model_id,
            warnings=[]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error instantiating model from template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error instantiating model from template: {str(e)}")

@router.get("/frameworks/types", response_model=List[Dict[str, str]])
async def list_framework_types():
    """
    List all available framework types.
    
    Returns:
        List of framework types with ID and name
    """
    try:
        types = [
            {"id": ft.value, "name": ft.name.replace("_", " ").title()}
            for ft in FrameworkType
        ]
        
        return types
    except Exception as e:
        logger.error(f"Error listing framework types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing framework types: {str(e)}")

@router.get("/templates/export/{template_id}")
async def export_framework_template(
    template_id: UUID = Path(..., description="Framework template ID")
):
    """
    Export a framework template as JSON.
    
    Args:
        template_id: Framework template ID
    
    Returns:
        JSON representation of the framework template
    """
    try:
        template_id_str = str(template_id)
        
        # Check if the template exists
        if template_id_str not in mock_framework_templates:
            raise HTTPException(status_code=404, detail=f"Framework template {template_id} not found")
        
        # Get the template
        template = mock_framework_templates[template_id_str]
        
        # Convert to FrameworkTemplate model
        framework_template = FrameworkTemplate(**template)
        
        # Return as JSON
        return framework_template.dict(exclude={"id", "created_at", "updated_at", "created_by", "updated_by", "is_system"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting framework template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting framework template: {str(e)}")

@router.post("/templates/import")
async def import_framework_template(
    template_data: Dict[str, Any] = Body(...),
    name: Optional[str] = Query(None, description="Optional name override for the imported template")
):
    """
    Import a framework template from JSON.
    
    Args:
        template_data: Framework template data
        name: Optional name override for the imported template
    
    Returns:
        Information about the imported template
    """
    try:
        # Create a FrameworkTemplateCreate from the data
        if name:
            template_data["name"] = name
            
        template = FrameworkTemplateCreate(**template_data)
        
        # Create the template
        new_template = await create_framework_template(template)
        
        return {
            "success": True,
            "message": f"Successfully imported framework template '{new_template.name}'",
            "template_id": new_template.id
        }
    except Exception as e:
        logger.error(f"Error importing framework template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error importing framework template: {str(e)}")

# Initialize system templates when the module is loaded
load_system_templates()
