"""
Enterprise Architecture Solution - Microsoft Teams Integration

This module provides integration with Microsoft Teams for collaboration,
notifications, and team communication related to EA activities.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests
import msal

from .integration_base import IntegrationBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeamsIntegration(IntegrationBase):
    """Integration with Microsoft Teams for EA collaboration."""
    
    def __init__(self, supabase_client, config_id: str = None):
        """Initialize the Teams integration.
        
        Args:
            supabase_client: Initialized Supabase client
            config_id: ID of the integration configuration in the database
        """
        super().__init__(supabase_client, config_id)
        self.access_token = None
    
    def _get_integration_type(self) -> str:
        """Get the integration type identifier."""
        return "microsoft_teams"
    
    def configure(self, client_id: str, client_secret: str, tenant_id: str,
                 team_id: str = None, channel_id: str = None, webhook_url: str = None) -> Dict[str, Any]:
        """Configure the Teams integration.
        
        Args:
            client_id: Microsoft Entra ID client ID
            client_secret: Microsoft Entra ID client secret
            tenant_id: Microsoft Entra ID tenant ID
            team_id: Optional Teams team ID for direct API integration
            channel_id: Optional Teams channel ID for direct API integration
            webhook_url: Optional webhook URL for incoming webhook integration
            
        Returns:
            Configuration status
        """
        self.config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "tenant_id": tenant_id,
            "team_id": team_id,
            "channel_id": channel_id,
            "webhook_url": webhook_url,
            "last_configured": datetime.now().isoformat()
        }
        
        self._save_config()
        
        # Test the connection to validate the configuration
        test_result = self.test_connection()
        
        return {
            "success": test_result.get("success", False),
            "message": test_result.get("message", ""),
            "config_id": self.config_id
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Microsoft Teams."""
        try:
            # Check if webhook URL is configured
            webhook_url = self.config.get("webhook_url")
            if webhook_url:
                # Test webhook
                test_payload = {
                    "type": "message",
                    "text": "Test connection from Enterprise Architecture Solution"
                }
                
                webhook_response = requests.post(webhook_url, json=test_payload)
                
                if webhook_response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Successfully connected to Microsoft Teams via webhook",
                        "connection_type": "webhook"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to connect to Microsoft Teams webhook. Status code: {webhook_response.status_code}, Response: {webhook_response.text}",
                        "connection_type": "webhook"
                    }
            else:
                # Test Graph API
                self._get_access_token()
                
                if not self.access_token:
                    return {
                        "success": False,
                        "message": "Failed to obtain access token for Microsoft Graph API",
                        "connection_type": "graph_api"
                    }
                
                # Check if team and channel IDs are configured
                team_id = self.config.get("team_id")
                channel_id = self.config.get("channel_id")
                
                if not team_id or not channel_id:
                    return {
                        "success": False,
                        "message": "Team ID and Channel ID must be configured for Graph API integration",
                        "connection_type": "graph_api"
                    }
                
                # Test access to team/channel
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                channel_url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}"
                channel_response = requests.get(channel_url, headers=headers)
                
                if channel_response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Successfully connected to Microsoft Teams via Graph API",
                        "connection_type": "graph_api",
                        "channel_name": channel_response.json().get("displayName")
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to connect to Microsoft Teams channel. Status code: {channel_response.status_code}, Response: {channel_response.text}",
                        "connection_type": "graph_api"
                    }
        except Exception as e:
            logger.error(f"Error testing Teams connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to Microsoft Teams: {str(e)}"
            }
    
    def _get_access_token(self) -> None:
        """Get access token for Microsoft Graph API."""
        try:
            # Initialize MSAL app
            app = msal.ConfidentialClientApplication(
                client_id=self.config.get("client_id"),
                client_credential=self.config.get("client_secret"),
                authority=f"https://login.microsoftonline.com/{self.config.get('tenant_id')}"
            )
            
            # Get token using client credentials flow
            token_result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            
            if "access_token" in token_result:
                self.access_token = token_result["access_token"]
            else:
                logger.error(f"Failed to obtain access token: {token_result.get('error_description')}")
                self.access_token = None
        except Exception as e:
            logger.error(f"Error obtaining access token: {str(e)}")
            self.access_token = None
    
    def send_message(self, message_text: str, title: str = None, 
                    color: str = None, images: List[Dict[str, str]] = None,
                    buttons: List[Dict[str, str]] = None, 
                    sections: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a message to Microsoft Teams.
        
        Args:
            message_text: Text content of the message
            title: Optional title for the message
            color: Optional color for the message card
            images: Optional list of images to include in the message
            buttons: Optional list of action buttons
            sections: Optional list of additional sections
            
        Returns:
            Message sending results
        """
        try:
            # Check if webhook URL is configured
            webhook_url = self.config.get("webhook_url")
            
            if webhook_url:
                # Send via webhook
                return self._send_via_webhook(message_text, title, color, images, buttons, sections)
            else:
                # Send via Graph API
                return self._send_via_graph_api(message_text, title)
        except Exception as e:
            logger.error(f"Error sending Teams message: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending Teams message: {str(e)}"
            }
    
    def _send_via_webhook(self, message_text: str, title: str = None, 
                         color: str = None, images: List[Dict[str, str]] = None,
                         buttons: List[Dict[str, Any]] = None, 
                         sections: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a message via Teams webhook.
        
        Args:
            message_text: Text content of the message
            title: Optional title for the message
            color: Optional color for the message card
            images: Optional list of images to include in the message
            buttons: Optional list of action buttons
            sections: Optional list of additional sections
            
        Returns:
            Message sending results
        """
        try:
            webhook_url = self.config.get("webhook_url")
            
            # Create adaptive card
            card = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "type": "AdaptiveCard",
                            "body": [],
                            "actions": [],
                            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                            "version": "1.2"
                        }
                    }
                ]
            }
            
            # Add title if provided
            if title:
                card["attachments"][0]["content"]["body"].append({
                    "type": "TextBlock",
                    "size": "Medium",
                    "weight": "Bolder",
                    "text": title,
                    "wrap": True
                })
            
            # Add message text
            card["attachments"][0]["content"]["body"].append({
                "type": "TextBlock",
                "text": message_text,
                "wrap": True
            })
            
            # Add images if provided
            if images and len(images) > 0:
                for image in images:
                    card["attachments"][0]["content"]["body"].append({
                        "type": "Image",
                        "url": image.get("url"),
                        "altText": image.get("alt_text", "Image"),
                        "size": image.get("size", "Medium")
                    })
            
            # Add buttons if provided
            if buttons and len(buttons) > 0:
                for button in buttons:
                    card["attachments"][0]["content"]["actions"].append({
                        "type": "Action.OpenUrl",
                        "title": button.get("title"),
                        "url": button.get("url")
                    })
            
            # Add sections if provided
            if sections and len(sections) > 0:
                for section in sections:
                    section_card = {
                        "type": "Container",
                        "items": []
                    }
                    
                    # Add section title
                    if section.get("title"):
                        section_card["items"].append({
                            "type": "TextBlock",
                            "size": "Medium",
                            "weight": "Bolder",
                            "text": section.get("title"),
                            "wrap": True
                        })
                    
                    # Add section text
                    if section.get("text"):
                        section_card["items"].append({
                            "type": "TextBlock",
                            "text": section.get("text"),
                            "wrap": True
                        })
                    
                    # Add section facts
                    if section.get("facts") and len(section.get("facts")) > 0:
                        facts_card = {
                            "type": "FactSet",
                            "facts": []
                        }
                        
                        for fact in section.get("facts"):
                            facts_card["facts"].append({
                                "title": fact.get("title"),
                                "value": fact.get("value")
                            })
                        
                        section_card["items"].append(facts_card)
                    
                    card["attachments"][0]["content"]["body"].append(section_card)
            
            # Set card color if provided
            if color:
                card["attachments"][0]["content"]["style"] = color
            
            # Send message
            response = requests.post(webhook_url, json=card)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Message sent successfully via webhook"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to send message via webhook. Status code: {response.status_code}, Response: {response.text}"
                }
        except Exception as e:
            logger.error(f"Error sending message via webhook: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending message via webhook: {str(e)}"
            }
    
    def _send_via_graph_api(self, message_text: str, title: str = None) -> Dict[str, Any]:
        """Send a message via Microsoft Graph API.
        
        Args:
            message_text: Text content of the message
            title: Optional title for the message
            
        Returns:
            Message sending results
        """
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for Microsoft Graph API"
                }
            
            team_id = self.config.get("team_id")
            channel_id = self.config.get("channel_id")
            
            if not team_id or not channel_id:
                return {
                    "success": False,
                    "message": "Team ID and Channel ID must be configured for Graph API integration"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Prepare message content
            message_content = message_text
            if title:
                message_content = f"# {title}\n\n{message_text}"
            
            # Create message payload
            message_payload = {
                "body": {
                    "content": message_content,
                    "contentType": "text"
                }
            }
            
            # Send message
            message_url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages"
            response = requests.post(message_url, headers=headers, json=message_payload)
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "message": "Message sent successfully via Graph API",
                    "message_id": response.json().get("id")
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to send message via Graph API. Status code: {response.status_code}, Response: {response.text}"
                }
        except Exception as e:
            logger.error(f"Error sending message via Graph API: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending message via Graph API: {str(e)}"
            }
    
    def create_ea_notification(self, artifact_type: str, artifact_id: str, 
                             action_type: str, user_id: str = None,
                             additional_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a notification for an EA artifact in Teams.
        
        Args:
            artifact_type: Type of the artifact (model, element, view, etc.)
            artifact_id: ID of the artifact
            action_type: Type of action (created, updated, approved, etc.)
            user_id: Optional ID of the user who performed the action
            additional_info: Optional additional information
            
        Returns:
            Notification results
        """
        try:
            # Get artifact data
            artifact_data = self._get_artifact_data(artifact_id, artifact_type)
            
            if not artifact_data:
                return {
                    "success": False,
                    "message": f"Failed to get artifact data for {artifact_type} with ID {artifact_id}"
                }
            
            # Get user data if provided
            user_info = "someone"
            if user_id:
                user_data = self._get_user_data(user_id)
                if user_data:
                    user_info = user_data.get("full_name", "someone")
            
            # Create notification title
            title = f"EA {artifact_type.capitalize()} {action_type.capitalize()}"
            
            # Create notification message
            message_text = f"{user_info} has {action_type} the {artifact_type} **{artifact_data.get('name', 'Untitled')}**."
            
            # Add description if available
            if artifact_data.get('description'):
                description = artifact_data.get('description')
                if len(description) > 100:
                    description = description[:97] + "..."
                message_text += f"\n\nDescription: {description}"
            
            # Create sections with additional information
            sections = []
            
            # Add artifact information section
            artifact_facts = [
                {"title": "ID", "value": artifact_id},
                {"title": "Type", "value": artifact_type.capitalize()},
                {"title": "Created", "value": artifact_data.get('created_at')}
            ]
            
            if artifact_data.get('status'):
                artifact_facts.append({"title": "Status", "value": artifact_data.get('status')})
            
            if artifact_type == "model" and artifact_data.get('version'):
                artifact_facts.append({"title": "Version", "value": artifact_data.get('version')})
            
            sections.append({
                "title": "Artifact Information",
                "facts": artifact_facts
            })
            
            # Add additional information if provided
            if additional_info and len(additional_info) > 0:
                additional_facts = []
                
                for key, value in additional_info.items():
                    # Skip internal fields
                    if not key.startswith("_"):
                        additional_facts.append({
                            "title": key.replace("_", " ").capitalize(),
                            "value": str(value)
                        })
                
                if len(additional_facts) > 0:
                    sections.append({
                        "title": "Additional Information",
                        "facts": additional_facts
                    })
            
            # Create buttons if applicable
            buttons = []
            
            # Add view button if web URL is available
            web_url = None
            if artifact_data.get('properties') and artifact_data.get('properties').get('web_url'):
                web_url = artifact_data.get('properties').get('web_url')
                buttons.append({
                    "title": f"View {artifact_type.capitalize()}",
                    "url": web_url
                })
            
            # Add SharePoint button if SharePoint URL is available
            sharepoint_url = None
            if artifact_data.get('properties') and artifact_data.get('properties').get('sharepoint_url'):
                sharepoint_url = artifact_data.get('properties').get('sharepoint_url')
                buttons.append({
                    "title": "View in SharePoint",
                    "url": sharepoint_url
                })
            
            # Send notification
            notification_result = self.send_message(
                message_text=message_text,
                title=title,
                color="accent",
                buttons=buttons,
                sections=sections
            )
            
            return notification_result
        except Exception as e:
            logger.error(f"Error creating EA notification: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating EA notification: {str(e)}"
            }
    
    def _get_artifact_data(self, artifact_id: str, artifact_type: str) -> Dict[str, Any]:
        """Get artifact data from the EA repository.
        
        Args:
            artifact_id: ID of the artifact
            artifact_type: Type of artifact
            
        Returns:
            Artifact data
        """
        try:
            # Query the EA repository based on artifact type
            if artifact_type == "model":
                data = self.supabase.table("ea_models").select("*").eq("id", artifact_id).execute()
            elif artifact_type == "element":
                data = self.supabase.table("ea_elements").select("*").eq("id", artifact_id).execute()
            elif artifact_type == "view":
                data = self.supabase.table("ea_views").select("*").eq("id", artifact_id).execute()
            else:
                logger.error(f"Unsupported artifact type: {artifact_type}")
                return None
            
            if data.data and len(data.data) > 0:
                return data.data[0]
            else:
                logger.error(f"No data found for {artifact_type} with ID {artifact_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting artifact data: {str(e)}")
            return None
    
    def _get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Get user data from the EA repository.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User data
        """
        try:
            data = self.supabase.table("users").select("*").eq("id", user_id).execute()
            
            if data.data and len(data.data) > 0:
                return data.data[0]
            else:
                logger.error(f"No data found for user with ID {user_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            return None
            
    def sync(self) -> Dict[str, Any]:
        """Synchronize teams and channels from Microsoft Teams.
        
        This method implements the sync operation required by the IntegrationBase class.
        
        Returns:
            Synchronization results
        """
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for Microsoft Graph API"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Get teams
            teams_url = "https://graph.microsoft.com/v1.0/me/joinedTeams"
            teams_response = requests.get(teams_url, headers=headers)
            
            if teams_response.status_code != 200:
                return {
                    "success": False,
                    "message": f"Failed to get teams. Status code: {teams_response.status_code}, Response: {teams_response.text}"
                }
            
            teams = teams_response.json().get("value", [])
            
            # Get channels for each team
            teams_with_channels = []
            
            for team in teams:
                team_id = team.get("id")
                channels_url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels"
                channels_response = requests.get(channels_url, headers=headers)
                
                if channels_response.status_code == 200:
                    channels = channels_response.json().get("value", [])
                    teams_with_channels.append({
                        "team_id": team_id,
                        "team_name": team.get("displayName"),
                        "channels": [
                            {
                                "channel_id": channel.get("id"),
                                "channel_name": channel.get("displayName")
                            }
                            for channel in channels
                        ]
                    })
            
            return {
                "success": True,
                "message": f"Synchronized {len(teams)} teams from Microsoft Teams",
                "teams": teams_with_channels
            }
        except Exception as e:
            logger.error(f"Error synchronizing with Microsoft Teams: {str(e)}")
            return {
                "success": False,
                "message": f"Error synchronizing with Microsoft Teams: {str(e)}"
            }
