"""
Enterprise Architecture Solution - Microsoft Teams Integration

This module provides integration with Microsoft Teams for the Enterprise Architecture Solution.
It enables notifications, collaboration, and interactive features between the EA platform and Teams.
"""

import os
import json
import logging
import uuid
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Body, BackgroundTasks
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Models for API requests/responses
class TeamsChannelConfig(BaseModel):
    webhook_url: str = Field(..., description="Microsoft Teams webhook URL")
    channel_name: str = Field(..., description="Name of the Teams channel")
    display_name: str = Field(..., description="Display name for the integration")
    description: Optional[str] = None
    notification_types: List[str] = Field(
        default=["model_updates", "governance_changes", "element_updates"],
        description="Types of notifications to send to this channel"
    )

class TeamsChannelResponse(BaseModel):
    success: bool
    message: str
    config_id: Optional[str] = None

class NotificationTemplate(BaseModel):
    template_type: str = Field(..., description="Type of notification template")
    template_name: str = Field(..., description="Name of the template")
    template_content: Dict[str, Any] = Field(..., description="Adaptive card template content")
    description: Optional[str] = None

class NotificationTemplateResponse(BaseModel):
    success: bool
    message: str
    template_id: Optional[str] = None

class NotificationRequest(BaseModel):
    channel_config_ids: List[str] = Field(..., description="IDs of channel configurations to send to")
    template_id: str = Field(..., description="ID of the template to use")
    context_data: Dict[str, Any] = Field(..., description="Data to populate the template")
    immediate: bool = Field(default=True, description="Whether to send immediately or queue for later")

class NotificationResponse(BaseModel):
    success: bool
    message: str
    notification_ids: List[str] = []

# Helper functions
async def send_teams_notification(webhook_url: str, adaptive_card: Dict[str, Any]):
    """
    Send a notification to a Microsoft Teams channel using a webhook.
    
    Args:
        webhook_url: Teams webhook URL
        adaptive_card: Adaptive card content
    
    Returns:
        Response status
    """
    async with httpx.AsyncClient() as client:
        try:
            # Format the payload according to Teams webhook requirements
            payload = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": adaptive_card
                    }
                ]
            }
            
            response = await client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return {"success": True, "status_code": response.status_code}
            else:
                logger.error(f"Error sending Teams notification: {response.text}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
        except Exception as e:
            logger.error(f"Exception sending Teams notification: {str(e)}")
            return {"success": False, "error": str(e)}

def get_default_templates() -> List[Dict[str, Any]]:
    """
    Get default notification templates for common EA events.
    
    Returns:
        List of default templates
    """
    return [
        {
            "id": "model_update",
            "template_type": "model_updates",
            "template_name": "Model Update Notification",
            "description": "Notification when an EA model is updated",
            "template_content": {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "Container",
                        "items": [
                            {
                                "type": "TextBlock",
                                "size": "large",
                                "weight": "bolder",
                                "text": "EA Model Updated"
                            },
                            {
                                "type": "TextBlock",
                                "spacing": "small",
                                "text": "Model: ${modelName}",
                                "isSubtle": True
                            },
                            {
                                "type": "TextBlock",
                                "text": "Updated by: ${updatedBy}",
                                "spacing": "small"
                            },
                            {
                                "type": "TextBlock",
                                "text": "Changes: ${changeDescription}",
                                "wrap": True
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "View Model",
                        "url": "${modelUrl}"
                    }
                ]
            }
        },
        {
            "id": "element_created",
            "template_type": "element_updates",
            "template_name": "Element Created Notification",
            "description": "Notification when a new EA element is created",
            "template_content": {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "Container",
                        "items": [
                            {
                                "type": "TextBlock",
                                "size": "large",
                                "weight": "bolder",
                                "text": "New EA Element Created"
                            },
                            {
                                "type": "TextBlock",
                                "spacing": "small",
                                "text": "Element: ${elementName}",
                                "isSubtle": True
                            },
                            {
                                "type": "TextBlock",
                                "text": "Type: ${elementType}",
                                "spacing": "small"
                            },
                            {
                                "type": "TextBlock",
                                "text": "Created by: ${createdBy}",
                                "spacing": "small"
                            },
                            {
                                "type": "TextBlock",
                                "text": "Description: ${elementDescription}",
                                "wrap": True
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "View Element",
                        "url": "${elementUrl}"
                    }
                ]
            }
        }
    ]

async def process_notification_queue(notification_queue):
    """
    Background process to handle the notification queue.
    
    Args:
        notification_queue: Queue of notifications to process
    """
    while True:
        try:
            # Get a notification from the queue
            notification = await notification_queue.get()
            
            # Process the notification
            webhook_url = notification.get("webhook_url")
            adaptive_card = notification.get("adaptive_card")
            
            if webhook_url and adaptive_card:
                await send_teams_notification(webhook_url, adaptive_card)
            
            # Mark the task as done
            notification_queue.task_done()
            
        except Exception as e:
            logger.error(f"Error processing notification queue: {str(e)}")
        
        # Sleep briefly to prevent high CPU usage
        await asyncio.sleep(0.1)

# Notification queue
notification_queue = asyncio.Queue()

# Start the background task for processing notifications
@router.on_startup
async def startup_notification_processor():
    asyncio.create_task(process_notification_queue(notification_queue))

# Routes
@router.post("/channels", response_model=TeamsChannelResponse)
async def create_teams_channel_config(
    config: TeamsChannelConfig = Body(...)
):
    """
    Create a new Teams channel configuration for notifications.
    
    Args:
        config: Channel configuration details
    
    Returns:
        Information about the created channel configuration
    """
    try:
        # In a real implementation, you would store the configuration in the database
        config_id = str(uuid.uuid4())
        
        # Test the webhook URL to ensure it's valid
        test_result = await send_teams_notification(
            config.webhook_url,
            {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "size": "medium",
                        "weight": "bolder",
                        "text": "Enterprise Architecture Solution - Teams Integration Test"
                    },
                    {
                        "type": "TextBlock",
                        "text": "This is a test notification to verify the webhook configuration.",
                        "wrap": True
                    }
                ]
            }
        )
        
        if not test_result.get("success", False):
            return TeamsChannelResponse(
                success=False,
                message=f"Failed to send test notification to the webhook URL: {test_result.get('error', 'Unknown error')}"
            )
        
        # Simulate storing the configuration
        logger.info(f"Created new Teams channel configuration: {config.display_name}")
        
        return TeamsChannelResponse(
            success=True,
            message=f"Successfully created Teams channel configuration '{config.display_name}'",
            config_id=config_id
        )
    except Exception as e:
        logger.error(f"Error creating Teams channel configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating Teams channel configuration: {str(e)}")

@router.get("/channels")
async def list_teams_channel_configs():
    """
    List all configured Teams channels.
    
    Returns:
        List of channel configurations
    """
    try:
        # In a real implementation, you would fetch configurations from the database
        
        # Simulate a list of configurations
        configs = [
            {
                "id": str(uuid.uuid4()),
                "display_name": "EA Updates Channel",
                "channel_name": "EA Updates",
                "notification_types": ["model_updates", "element_updates"],
                "created_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "display_name": "Governance Notifications",
                "channel_name": "EA Governance",
                "notification_types": ["governance_changes"],
                "created_at": datetime.now().isoformat()
            }
        ]
        
        return {"success": True, "channels": configs}
    except Exception as e:
        logger.error(f"Error listing Teams channel configurations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing Teams channel configurations: {str(e)}")

@router.post("/templates", response_model=NotificationTemplateResponse)
async def create_notification_template(
    template: NotificationTemplate = Body(...)
):
    """
    Create a new notification template.
    
    Args:
        template: Notification template details
    
    Returns:
        Information about the created template
    """
    try:
        # In a real implementation, you would store the template in the database
        template_id = str(uuid.uuid4())
        
        # Validate that the template content is a valid adaptive card
        # (In a real implementation, perform more thorough validation)
        if "type" not in template.template_content or template.template_content["type"] != "AdaptiveCard":
            return NotificationTemplateResponse(
                success=False,
                message="Invalid adaptive card template. The root element must have type 'AdaptiveCard'."
            )
        
        # Simulate storing the template
        logger.info(f"Created new notification template: {template.template_name}")
        
        return NotificationTemplateResponse(
            success=True,
            message=f"Successfully created notification template '{template.template_name}'",
            template_id=template_id
        )
    except Exception as e:
        logger.error(f"Error creating notification template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating notification template: {str(e)}")

@router.get("/templates")
async def list_notification_templates():
    """
    List all notification templates.
    
    Returns:
        List of notification templates
    """
    try:
        # In a real implementation, you would fetch templates from the database
        
        # Return default templates
        templates = get_default_templates()
        
        return {"success": True, "templates": templates}
    except Exception as e:
        logger.error(f"Error listing notification templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing notification templates: {str(e)}")

@router.post("/notify", response_model=NotificationResponse)
async def send_notification(
    request: NotificationRequest = Body(...),
    background_tasks: BackgroundTasks = None
):
    """
    Send a notification to one or more Teams channels.
    
    Args:
        request: Notification request details
        background_tasks: FastAPI background tasks
    
    Returns:
        Information about the sent notifications
    """
    try:
        # In a real implementation, you would:
        # 1. Fetch the channel configurations for the specified IDs
        # 2. Fetch the template for the specified template ID
        # 3. Apply the context data to the template
        # 4. Send the notification to each channel
        
        # For this example, we'll simulate successful processing
        notification_ids = []
        
        # Simulate finding the template
        template = get_default_templates()[0]  # Just use the first default template
        
        # Simulate finding channel configurations
        channel_configs = [
            {
                "id": channel_id,
                "webhook_url": "https://example.webhook.office.com/webhookb2/..."  # Placeholder
            }
            for channel_id in request.channel_config_ids
        ]
        
        # Process the notifications
        for channel_config in channel_configs:
            # Apply context data to the template
            # (In a real implementation, use a proper template engine)
            adaptive_card = template["template_content"]
            
            # Create a notification entry
            notification_id = str(uuid.uuid4())
            notification_ids.append(notification_id)
            
            # Prepare the notification
            notification = {
                "id": notification_id,
                "webhook_url": channel_config["webhook_url"],
                "adaptive_card": adaptive_card,
                "context_data": request.context_data,
                "created_at": datetime.now().isoformat()
            }
            
            # Send immediately or queue for later
            if request.immediate:
                # Use background tasks to avoid blocking the API response
                if background_tasks:
                    background_tasks.add_task(
                        send_teams_notification,
                        channel_config["webhook_url"],
                        adaptive_card
                    )
                else:
                    # Add to queue for processing by the background task
                    await notification_queue.put(notification)
            else:
                # Add to queue for processing by the background task
                await notification_queue.put(notification)
        
        return NotificationResponse(
            success=True,
            message=f"Successfully processed {len(notification_ids)} notifications",
            notification_ids=notification_ids
        )
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending notification: {str(e)}")

@router.post("/webhook", status_code=200)
async def teams_webhook_handler(request: Request):
    """
    Handle incoming webhook requests from Microsoft Teams.
    
    Args:
        request: The incoming request
    
    Returns:
        Acknowledgment response
    """
    try:
        # Parse the webhook payload
        payload = await request.json()
        
        # In a real implementation, you would validate the payload and process it based on the type of event
        # For example, handle different types of interactions with adaptive cards
        
        logger.info(f"Received Teams webhook request: {json.dumps(payload)[:100]}...")
        
        # Process the webhook based on the type of activity
        if "type" in payload:
            if payload["type"] == "message":
                # Handle incoming message
                pass
            elif payload["type"] == "invoke":
                # Handle card actions
                pass
        
        # Acknowledge receipt of the webhook
        return {"success": True, "message": "Webhook processed successfully"}
    except Exception as e:
        logger.error(f"Error handling Teams webhook: {str(e)}")
        # Always return 200 to acknowledge receipt, even if processing fails
        return {"success": False, "message": f"Error processing webhook: {str(e)}"}

@router.get("/status")
async def get_teams_integration_status():
    """
    Get the status of the Teams integration.
    
    Returns:
        Integration status information
    """
    try:
        # In a real implementation, you would check the status of the integration
        # For example, check if the background task is running, connection to Teams, etc.
        
        return {
            "success": True,
            "status": "healthy",
            "queue_size": notification_queue.qsize(),
            "channels_configured": 2,  # Placeholder
            "templates_configured": len(get_default_templates()),
            "last_notification_sent": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting Teams integration status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting Teams integration status: {str(e)}")
