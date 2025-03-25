"""
Enterprise Architecture Solution - IT Asset Management Service

This module provides comprehensive IT asset management capabilities, including:
- Asset tracking with detailed metadata
- Asset relationship management
- Integration with architecture elements
- Maintenance tracking
- Import/export functionality
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models for API request/response
class AssetBase(BaseModel):
    name: str = Field(..., description="Name of the asset")
    description: Optional[str] = Field(None, description="Description of the asset")
    asset_type: str = Field(..., description="Type of the asset (hardware, software, service, etc.)")
    status: str = Field("active", description="Status of the asset (active, retired, planned, etc.)")
    owner: Optional[str] = Field(None, description="Owner of the asset")
    location: Optional[str] = Field(None, description="Physical or logical location of the asset")
    purchase_date: Optional[datetime] = Field(None, description="Date when the asset was purchased")
    end_of_life: Optional[datetime] = Field(None, description="Expected end of life date")
    cost: Optional[float] = Field(None, description="Cost of the asset")
    vendor: Optional[str] = Field(None, description="Vendor or manufacturer of the asset")
    model: Optional[str] = Field(None, description="Model or version of the asset")
    serial_number: Optional[str] = Field(None, description="Serial number of the asset")
    license_key: Optional[str] = Field(None, description="License key for software assets")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties of the asset")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the asset")

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the asset")
    description: Optional[str] = Field(None, description="Description of the asset")
    asset_type: Optional[str] = Field(None, description="Type of the asset (hardware, software, service, etc.)")
    status: Optional[str] = Field(None, description="Status of the asset (active, retired, planned, etc.)")
    owner: Optional[str] = Field(None, description="Owner of the asset")
    location: Optional[str] = Field(None, description="Physical or logical location of the asset")
    purchase_date: Optional[datetime] = Field(None, description="Date when the asset was purchased")
    end_of_life: Optional[datetime] = Field(None, description="Expected end of life date")
    cost: Optional[float] = Field(None, description="Cost of the asset")
    vendor: Optional[str] = Field(None, description="Vendor or manufacturer of the asset")
    model: Optional[str] = Field(None, description="Model or version of the asset")
    serial_number: Optional[str] = Field(None, description="Serial number of the asset")
    license_key: Optional[str] = Field(None, description="License key for software assets")
    properties: Optional[Dict[str, Any]] = Field(None, description="Additional properties of the asset")
    tags: Optional[List[str]] = Field(None, description="Tags associated with the asset")

class Asset(AssetBase):
    id: str = Field(..., description="Unique identifier of the asset")
    created_by: str = Field(..., description="User who created the asset")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    ea_element_id: Optional[str] = Field(None, description="ID of the associated EA element")

class AssetRelationshipBase(BaseModel):
    source_asset_id: str = Field(..., description="ID of the source asset")
    target_asset_id: str = Field(..., description="ID of the target asset")
    relationship_type: str = Field(..., description="Type of relationship (contains, depends_on, connects_to, etc.)")
    description: Optional[str] = Field(None, description="Description of the relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties of the relationship")

    @validator('source_asset_id')
    def source_not_equal_target(cls, v, values):
        if 'target_asset_id' in values and v == values['target_asset_id']:
            raise ValueError('source_asset_id cannot be the same as target_asset_id')
        return v

class AssetRelationshipCreate(AssetRelationshipBase):
    pass

class AssetRelationshipUpdate(BaseModel):
    relationship_type: Optional[str] = Field(None, description="Type of relationship")
    description: Optional[str] = Field(None, description="Description of the relationship")
    properties: Optional[Dict[str, Any]] = Field(None, description="Additional properties of the relationship")

class AssetRelationship(AssetRelationshipBase):
    id: str = Field(..., description="Unique identifier of the relationship")
    created_by: str = Field(..., description="User who created the relationship")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class MaintenanceBase(BaseModel):
    asset_id: str = Field(..., description="ID of the asset")
    maintenance_type: str = Field(..., description="Type of maintenance (repair, upgrade, inspection, etc.)")
    description: str = Field(..., description="Description of the maintenance activity")
    scheduled_date: datetime = Field(..., description="Date when the maintenance is scheduled")
    completed_date: Optional[datetime] = Field(None, description="Date when the maintenance was completed")
    performed_by: Optional[str] = Field(None, description="Person or company who performed the maintenance")
    cost: Optional[float] = Field(None, description="Cost of the maintenance")
    result: Optional[str] = Field(None, description="Result of the maintenance activity")
    notes: Optional[str] = Field(None, description="Additional notes")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceUpdate(BaseModel):
    maintenance_type: Optional[str] = Field(None, description="Type of maintenance")
    description: Optional[str] = Field(None, description="Description of the maintenance activity")
    scheduled_date: Optional[datetime] = Field(None, description="Date when the maintenance is scheduled")
    completed_date: Optional[datetime] = Field(None, description="Date when the maintenance was completed")
    performed_by: Optional[str] = Field(None, description="Person or company who performed the maintenance")
    cost: Optional[float] = Field(None, description="Cost of the maintenance")
    result: Optional[str] = Field(None, description="Result of the maintenance activity")
    notes: Optional[str] = Field(None, description="Additional notes")
    properties: Optional[Dict[str, Any]] = Field(None, description="Additional properties")

class Maintenance(MaintenanceBase):
    id: str = Field(..., description="Unique identifier of the maintenance record")
    created_by: str = Field(..., description="User who created the record")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class AssetImport(BaseModel):
    assets: List[AssetCreate] = Field(..., description="List of assets to import")
    relationships: Optional[List[AssetRelationshipCreate]] = Field(None, description="List of relationships to import")
    create_relationships: bool = Field(True, description="Whether to create relationships between assets")
    update_existing: bool = Field(False, description="Whether to update existing assets")
    
class AssetExport(BaseModel):
    format: str = Field("json", description="Export format (json, csv, excel)")
    include_relationships: bool = Field(True, description="Whether to include relationships")
    include_maintenance: bool = Field(False, description="Whether to include maintenance records")
    filter: Optional[Dict[str, Any]] = Field(None, description="Filter criteria for assets to export")

# API endpoints
@router.post("/assets", response_model=Asset, status_code=status.HTTP_201_CREATED)
async def create_asset(asset: AssetCreate):
    """Create a new asset."""
    try:
        # In a real implementation, this would create a record in the database
        # For demo purposes, we'll return a mock response
        return {
            **asset.dict(),
            "id": "asset-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "created_by": "current-user-id",  # Would get from auth
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "ea_element_id": None
        }
    except Exception as e:
        logger.error(f"Error creating asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating asset"
        )

@router.get("/assets", response_model=List[Asset])
async def get_assets(
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    owner: Optional[str] = Query(None, description="Filter by owner"),
    location: Optional[str] = Query(None, description="Filter by location"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    ea_element_id: Optional[str] = Query(None, description="Filter by associated EA element ID"),
    search: Optional[str] = Query(None, description="Search term for asset name or description")
):
    """Get assets with optional filtering."""
    try:
        # In a real implementation, this would query the database
        # For demo purposes, we'll return mock data
        return [
            {
                "id": "asset-1",
                "name": "Web Server",
                "description": "Production web server",
                "asset_type": "hardware",
                "status": "active",
                "owner": "IT Department",
                "location": "Data Center 1",
                "purchase_date": "2023-01-15T00:00:00Z",
                "end_of_life": "2028-01-15T00:00:00Z",
                "cost": 5000.00,
                "vendor": "Dell",
                "model": "PowerEdge R740",
                "serial_number": "SN12345678",
                "license_key": None,
                "properties": {
                    "cpu": "Intel Xeon Gold 5218",
                    "memory": "64GB",
                    "storage": "2TB SSD"
                },
                "tags": ["critical", "production"],
                "created_by": "user-1",
                "created_at": "2023-01-20T10:30:00Z",
                "updated_at": "2023-05-15T14:45:00Z",
                "ea_element_id": "element-1"
            },
            {
                "id": "asset-2",
                "name": "CRM System",
                "description": "Customer Relationship Management System",
                "asset_type": "software",
                "status": "active",
                "owner": "Sales Department",
                "location": "Cloud",
                "purchase_date": "2022-06-10T00:00:00Z",
                "end_of_life": "2025-06-10T00:00:00Z",
                "cost": 20000.00,
                "vendor": "Salesforce",
                "model": "Enterprise Edition",
                "serial_number": None,
                "license_key": "SF-ENT-12345-67890",
                "properties": {
                    "users": 100,
                    "modules": ["Sales", "Marketing", "Service"]
                },
                "tags": ["business", "critical"],
                "created_by": "user-2",
                "created_at": "2022-06-15T09:00:00Z",
                "updated_at": "2022-06-15T09:00:00Z",
                "ea_element_id": "element-2"
            }
        ]
    except Exception as e:
        logger.error(f"Error getting assets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting assets"
        )

@router.get("/assets/{asset_id}", response_model=Asset)
async def get_asset(asset_id: str = Path(..., description="ID of the asset to get")):
    """Get an asset by ID."""
    try:
        # In a real implementation, this would get the asset from the database
        # For demo purposes, we'll return mock data
        return {
            "id": asset_id,
            "name": "Web Server",
            "description": "Production web server",
            "asset_type": "hardware",
            "status": "active",
            "owner": "IT Department",
            "location": "Data Center 1",
            "purchase_date": "2023-01-15T00:00:00Z",
            "end_of_life": "2028-01-15T00:00:00Z",
            "cost": 5000.00,
            "vendor": "Dell",
            "model": "PowerEdge R740",
            "serial_number": "SN12345678",
            "license_key": None,
            "properties": {
                "cpu": "Intel Xeon Gold 5218",
                "memory": "64GB",
                "storage": "2TB SSD"
            },
            "tags": ["critical", "production"],
            "created_by": "user-1",
            "created_at": "2023-01-20T10:30:00Z",
            "updated_at": "2023-05-15T14:45:00Z",
            "ea_element_id": "element-1"
        }
    except Exception as e:
        logger.error(f"Error getting asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting asset"
        )

@router.put("/assets/{asset_id}", response_model=Asset)
async def update_asset(
    asset_update: AssetUpdate,
    asset_id: str = Path(..., description="ID of the asset to update")
):
    """Update an asset."""
    try:
        # In a real implementation, this would update the asset in the database
        # For demo purposes, we'll return mock data
        return {
            "id": asset_id,
            "name": asset_update.name or "Web Server",
            "description": asset_update.description or "Production web server",
            "asset_type": asset_update.asset_type or "hardware",
            "status": asset_update.status or "active",
            "owner": asset_update.owner or "IT Department",
            "location": asset_update.location or "Data Center 1",
            "purchase_date": asset_update.purchase_date or "2023-01-15T00:00:00Z",
            "end_of_life": asset_update.end_of_life or "2028-01-15T00:00:00Z",
            "cost": asset_update.cost or 5000.00,
            "vendor": asset_update.vendor or "Dell",
            "model": asset_update.model or "PowerEdge R740",
            "serial_number": asset_update.serial_number or "SN12345678",
            "license_key": asset_update.license_key,
            "properties": asset_update.properties or {
                "cpu": "Intel Xeon Gold 5218",
                "memory": "64GB",
                "storage": "2TB SSD"
            },
            "tags": asset_update.tags or ["critical", "production"],
            "created_by": "user-1",
            "created_at": "2023-01-20T10:30:00Z",
            "updated_at": datetime.now().isoformat(),
            "ea_element_id": "element-1"
        }
    except Exception as e:
        logger.error(f"Error updating asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating asset"
        )

@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(asset_id: str = Path(..., description="ID of the asset to delete")):
    """Delete an asset."""
    try:
        # In a real implementation, this would delete the asset from the database
        # For demo purposes, we'll just return a success status
        return None
    except Exception as e:
        logger.error(f"Error deleting asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting asset"
        )

@router.post("/assets/{asset_id}/map-to-element", response_model=Asset)
async def map_asset_to_element(
    asset_id: str = Path(..., description="ID of the asset"),
    element_id: str = Body(..., embed=True, description="ID of the EA element")
):
    """Map an asset to an EA element."""
    try:
        # In a real implementation, this would update the asset in the database
        # For demo purposes, we'll return mock data
        return {
            "id": asset_id,
            "name": "Web Server",
            "description": "Production web server",
            "asset_type": "hardware",
            "status": "active",
            "owner": "IT Department",
            "location": "Data Center 1",
            "purchase_date": "2023-01-15T00:00:00Z",
            "end_of_life": "2028-01-15T00:00:00Z",
            "cost": 5000.00,
            "vendor": "Dell",
            "model": "PowerEdge R740",
            "serial_number": "SN12345678",
            "license_key": None,
            "properties": {
                "cpu": "Intel Xeon Gold 5218",
                "memory": "64GB",
                "storage": "2TB SSD"
            },
            "tags": ["critical", "production"],
            "created_by": "user-1",
            "created_at": "2023-01-20T10:30:00Z",
            "updated_at": datetime.now().isoformat(),
            "ea_element_id": element_id
        }
    except Exception as e:
        logger.error(f"Error mapping asset to element: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error mapping asset to element"
        )

@router.post("/asset-relationships", response_model=AssetRelationship, status_code=status.HTTP_201_CREATED)
async def create_asset_relationship(relationship: AssetRelationshipCreate):
    """Create a new asset relationship."""
    try:
        # In a real implementation, this would create a record in the database
        # For demo purposes, we'll return a mock response
        return {
            **relationship.dict(),
            "id": "rel-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "created_by": "current-user-id",  # Would get from auth
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error creating asset relationship: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating asset relationship"
        )

@router.get("/asset-relationships", response_model=List[AssetRelationship])
async def get_asset_relationships(
    source_asset_id: Optional[str] = Query(None, description="Filter by source asset ID"),
    target_asset_id: Optional[str] = Query(None, description="Filter by target asset ID"),
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type")
):
    """Get asset relationships with optional filtering."""
    try:
        # In a real implementation, this would query the database
        # For demo purposes, we'll return mock data
        return [
            {
                "id": "rel-1",
                "source_asset_id": "asset-1",
                "target_asset_id": "asset-2",
                "relationship_type": "depends_on",
                "description": "Web server depends on database server",
                "properties": {},
                "created_by": "user-1",
                "created_at": "2023-01-20T10:35:00Z",
                "updated_at": "2023-01-20T10:35:00Z"
            },
            {
                "id": "rel-2",
                "source_asset_id": "asset-3",
                "target_asset_id": "asset-1",
                "relationship_type": "connects_to",
                "description": "Load balancer connects to web server",
                "properties": {
                    "protocol": "HTTP",
                    "port": 80
                },
                "created_by": "user-1",
                "created_at": "2023-01-20T10:40:00Z",
                "updated_at": "2023-01-20T10:40:00Z"
            }
        ]
    except Exception as e:
        logger.error(f"Error getting asset relationships: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting asset relationships"
        )

@router.get("/assets/{asset_id}/relationships", response_model=List[AssetRelationship])
async def get_asset_relationships_by_asset(
    asset_id: str = Path(..., description="ID of the asset"),
    direction: str = Query("both", description="Relationship direction (incoming, outgoing, both)")
):
    """Get relationships for a specific asset."""
    try:
        # In a real implementation, this would query the database
        # For demo purposes, we'll return mock data
        return [
            {
                "id": "rel-1",
                "source_asset_id": asset_id,
                "target_asset_id": "asset-2",
                "relationship_type": "depends_on",
                "description": "Web server depends on database server",
                "properties": {},
                "created_by": "user-1",
                "created_at": "2023-01-20T10:35:00Z",
                "updated_at": "2023-01-20T10:35:00Z"
            },
            {
                "id": "rel-2",
                "source_asset_id": "asset-3",
                "target_asset_id": asset_id,
                "relationship_type": "connects_to",
                "description": "Load balancer connects to web server",
                "properties": {
                    "protocol": "HTTP",
                    "port": 80
                },
                "created_by": "user-1",
                "created_at": "2023-01-20T10:40:00Z",
                "updated_at": "2023-01-20T10:40:00Z"
            }
        ]
    except Exception as e:
        logger.error(f"Error getting asset relationships: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting asset relationships"
        )

@router.post("/asset-maintenance", response_model=Maintenance, status_code=status.HTTP_201_CREATED)
async def create_maintenance(maintenance: MaintenanceCreate):
    """Create a new maintenance record."""
    try:
        # In a real implementation, this would create a record in the database
        # For demo purposes, we'll return a mock response
        return {
            **maintenance.dict(),
            "id": "maint-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "created_by": "current-user-id",  # Would get from auth
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error creating maintenance record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating maintenance record"
        )

@router.get("/assets/{asset_id}/maintenance", response_model=List[Maintenance])
async def get_asset_maintenance(
    asset_id: str = Path(..., description="ID of the asset"),
    maintenance_type: Optional[str] = Query(None, description="Filter by maintenance type"),
    from_date: Optional[datetime] = Query(None, description="Filter by scheduled date (from)"),
    to_date: Optional[datetime] = Query(None, description="Filter by scheduled date (to)"),
    completed: Optional[bool] = Query(None, description="Filter by completion status")
):
    """Get maintenance records for a specific asset."""
    try:
        # In a real implementation, this would query the database
        # For demo purposes, we'll return mock data
        return [
            {
                "id": "maint-1",
                "asset_id": asset_id,
                "maintenance_type": "repair",
                "description": "Replace faulty hard drive",
                "scheduled_date": "2023-03-15T09:00:00Z",
                "completed_date": "2023-03-15T11:30:00Z",
                "performed_by": "John Technician",
                "cost": 500.00,
                "result": "Successful replacement",
                "notes": "Drive was showing early signs of failure in monitoring",
                "properties": {},
                "created_by": "user-1",
                "created_at": "2023-03-10T14:00:00Z",
                "updated_at": "2023-03-15T12:00:00Z"
            },
            {
                "id": "maint-2",
                "asset_id": asset_id,
                "maintenance_type": "upgrade",
                "description": "Increase RAM to 128GB",
                "scheduled_date": "2023-06-10T08:00:00Z",
                "completed_date": None,
                "performed_by": None,
                "cost": None,
                "result": None,
                "notes": "Upgrade needed due to increased workload",
                "properties": {},
                "created_by": "user-2",
                "created_at": "2023-05-20T16:30:00Z",
                "updated_at": "2023-05-20T16:30:00Z"
            }
        ]
    except Exception as e:
        logger.error(f"Error getting maintenance records: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting maintenance records"
        )

@router.post("/assets/import", status_code=status.HTTP_200_OK)
async def import_assets(import_data: AssetImport):
    """Import assets and optionally relationships."""
    try:
        # In a real implementation, this would create records in the database
        # For demo purposes, we'll return a mock response
        asset_count = len(import_data.assets)
        relationship_count = len(import_data.relationships) if import_data.relationships else 0
        
        return {
            "success": True,
            "message": f"Successfully imported {asset_count} assets and {relationship_count} relationships",
            "asset_count": asset_count,
            "relationship_count": relationship_count,
            "errors": []
        }
    except Exception as e:
        logger.error(f"Error importing assets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error importing assets"
        )

@router.post("/assets/export", status_code=status.HTTP_200_OK)
async def export_assets(export_config: AssetExport):
    """Export assets to the specified format."""
    try:
        # In a real implementation, this would query the database and format the data
        # For demo purposes, we'll return a mock response
        return {
            "success": True,
            "message": f"Successfully exported assets in {export_config.format} format",
            "download_url": f"/api/assets/export/download?format={export_config.format}&token=mock-token",
            "expires_at": (datetime.now().replace(microsecond=0) + datetime.timedelta(hours=24)).isoformat()
        }
    except Exception as e:
        logger.error(f"Error exporting assets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting assets"
        )

@router.get("/assets/statistics", status_code=status.HTTP_200_OK)
async def get_asset_statistics():
    """Get statistics about assets."""
    try:
        # In a real implementation, this would query the database
        # For demo purposes, we'll return mock data
        return {
            "total_assets": 150,
            "assets_by_type": {
                "hardware": 50,
                "software": 75,
                "service": 15,
                "network": 10
            },
            "assets_by_status": {
                "active": 120,
                "retired": 15,
                "planned": 10,
                "maintenance": 5
            },
            "assets_by_location": {
                "Data Center 1": 40,
                "Data Center 2": 35,
                "Cloud": 45,
                "Office Locations": 30
            },
            "total_cost": 2500000.00,
            "maintenance_stats": {
                "scheduled": 8,
                "completed_this_month": 12,
                "upcoming": 5
            },
            "recently_added": 7,
            "recently_updated": 15
        }
    except Exception as e:
        logger.error(f"Error getting asset statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting asset statistics"
        )
