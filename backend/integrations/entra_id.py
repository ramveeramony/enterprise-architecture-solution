"""
Enterprise Architecture Solution - Microsoft Entra ID Integration

This module provides integration with Microsoft Entra ID for authentication
and user management in the Enterprise Architecture Solution.
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

class EntraIDIntegration(IntegrationBase):
    """Integration with Microsoft Entra ID for authentication and user management."""
    
    def __init__(self, supabase_client, config_id: str = None):
        """Initialize the Entra ID integration.
        
        Args:
            supabase_client: Initialized Supabase client
            config_id: ID of the integration configuration in the database
        """
        super().__init__(supabase_client, config_id)
        self.access_token = None
        self.msal_app = None
    
    def _get_integration_type(self) -> str:
        """Get the integration type identifier."""
        return "entra_id"
    
    def configure(self, tenant_id: str, client_id: str, client_secret: str,
                 redirect_uri: str, scope: List[str] = None,
                 group_mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """Configure the Entra ID integration.
        
        Args:
            tenant_id: Microsoft Entra ID tenant ID
            client_id: Microsoft Entra ID client ID
            client_secret: Microsoft Entra ID client secret
            redirect_uri: Redirect URI for authentication flow
            scope: Optional list of scopes to request
            group_mapping: Optional mapping of Entra ID group IDs to EA roles
            
        Returns:
            Configuration status
        """
        self.config = {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "scope": scope or ["openid", "profile", "email", "User.Read", "Directory.Read.All"],
            "group_mapping": group_mapping or {},
            "last_configured": datetime.now().isoformat()
        }
        
        self._save_config()
        
        # Initialize MSAL app
        self._initialize_msal_app()
        
        # Test the connection to validate the configuration
        test_result = self.test_connection()
        
        return {
            "success": test_result.get("success", False),
            "message": test_result.get("message", ""),
            "config_id": self.config_id
        }
    
    def _initialize_msal_app(self) -> None:
        """Initialize the MSAL application."""
        try:
            self.msal_app = msal.ConfidentialClientApplication(
                client_id=self.config.get("client_id"),
                client_credential=self.config.get("client_secret"),
                authority=f"https://login.microsoftonline.com/{self.config.get('tenant_id')}"
            )
        except Exception as e:
            logger.error(f"Error initializing MSAL app: {str(e)}")
            self.msal_app = None
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Microsoft Entra ID."""
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
            
            # Test access to Microsoft Graph API
            me_url = "https://graph.microsoft.com/v1.0/me"
            me_response = requests.get(me_url, headers=headers)
            
            if me_response.status_code == 200:
                return {
                    "success": True,
                    "message": "Successfully connected to Microsoft Entra ID"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to connect to Microsoft Entra ID. Status code: {me_response.status_code}, Response: {me_response.text}"
                }
        except Exception as e:
            logger.error(f"Error testing Entra ID connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to Microsoft Entra ID: {str(e)}"
            }
    
    def _get_access_token(self) -> None:
        """Get access token for Microsoft Graph API."""
        try:
            if not self.msal_app:
                self._initialize_msal_app()
            
            # Get token using client credentials flow
            token_result = self.msal_app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            
            if "access_token" in token_result:
                self.access_token = token_result["access_token"]
            else:
                logger.error(f"Failed to obtain access token: {token_result.get('error_description')}")
                self.access_token = None
        except Exception as e:
            logger.error(f"Error obtaining access token: {str(e)}")
            self.access_token = None
    
    def get_login_url(self, state: str = None) -> Dict[str, Any]:
        """Get the login URL for redirecting users to Microsoft Entra ID login.
        
        Args:
            state: Optional state parameter for OAuth flow
            
        Returns:
            Login URL information
        """
        try:
            if not self.msal_app:
                self._initialize_msal_app()
            
            auth_params = {
                "response_type": "code",
                "redirect_uri": self.config.get("redirect_uri"),
                "scope": " ".join(self.config.get("scope", []))
            }
            
            if state:
                auth_params["state"] = state
            
            auth_url = self.msal_app.get_authorization_request_url(
                scopes=self.config.get("scope", []),
                redirect_uri=self.config.get("redirect_uri"),
                state=state
            )
            
            return {
                "success": True,
                "login_url": auth_url
            }
        except Exception as e:
            logger.error(f"Error generating login URL: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating login URL: {str(e)}"
            }
    
    def handle_auth_callback(self, code: str) -> Dict[str, Any]:
        """Handle the authentication callback from Microsoft Entra ID.
        
        Args:
            code: Authorization code from the callback
            
        Returns:
            Authentication result with user information
        """
        try:
            if not self.msal_app:
                self._initialize_msal_app()
            
            # Acquire token by authorization code
            token_result = self.msal_app.acquire_token_by_authorization_code(
                code=code,
                scopes=self.config.get("scope", []),
                redirect_uri=self.config.get("redirect_uri")
            )
            
            if "access_token" not in token_result:
                return {
                    "success": False,
                    "message": f"Failed to obtain access token: {token_result.get('error_description')}"
                }
            
            # Get user information
            user_info = self._get_user_info(token_result["access_token"])
            
            if not user_info:
                return {
                    "success": False,
                    "message": "Failed to obtain user information"
                }
            
            # Process user information
            user_data = {
                "id": user_info.get("id"),
                "email": user_info.get("userPrincipalName"),
                "name": user_info.get("displayName"),
                "first_name": user_info.get("givenName"),
                "last_name": user_info.get("surname"),
                "avatar_url": None
            }
            
            # Get user groups and assign role based on group mapping
            user_groups = self._get_user_groups(token_result["access_token"], user_info.get("id"))
            user_role = self._determine_user_role(user_groups)
            
            user_data["role"] = user_role
            
            # Create or update user in Supabase
            supabase_user = self._sync_user_to_supabase(user_data)
            
            if not supabase_user:
                return {
                    "success": False,
                    "message": "Failed to sync user to Supabase"
                }
            
            return {
                "success": True,
                "user": user_data,
                "token": token_result["access_token"],
                "refresh_token": token_result.get("refresh_token"),
                "expires_in": token_result.get("expires_in")
            }
        except Exception as e:
            logger.error(f"Error handling auth callback: {str(e)}")
            return {
                "success": False,
                "message": f"Error handling auth callback: {str(e)}"
            }
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token information
        """
        try:
            if not self.msal_app:
                self._initialize_msal_app()
            
            # Acquire token by refresh token
            token_result = self.msal_app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=self.config.get("scope", [])
            )
            
            if "access_token" not in token_result:
                return {
                    "success": False,
                    "message": f"Failed to refresh token: {token_result.get('error_description')}"
                }
            
            return {
                "success": True,
                "token": token_result["access_token"],
                "refresh_token": token_result.get("refresh_token"),
                "expires_in": token_result.get("expires_in")
            }
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return {
                "success": False,
                "message": f"Error refreshing token: {str(e)}"
            }
    
    def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Microsoft Graph API.
        
        Args:
            access_token: Access token
            
        Returns:
            User information
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            me_url = "https://graph.microsoft.com/v1.0/me"
            me_response = requests.get(me_url, headers=headers)
            
            if me_response.status_code == 200:
                return me_response.json()
            else:
                logger.error(f"Failed to get user information. Status code: {me_response.status_code}, Response: {me_response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting user information: {str(e)}")
            return None
    
    def _get_user_groups(self, access_token: str, user_id: str) -> List[Dict[str, Any]]:
        """Get user groups from Microsoft Graph API.
        
        Args:
            access_token: Access token
            user_id: User ID
            
        Returns:
            List of user groups
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            groups_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/memberOf"
            groups_response = requests.get(groups_url, headers=headers)
            
            if groups_response.status_code == 200:
                return groups_response.json().get("value", [])
            else:
                logger.error(f"Failed to get user groups. Status code: {groups_response.status_code}, Response: {groups_response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting user groups: {str(e)}")
            return []
    
    def _determine_user_role(self, user_groups: List[Dict[str, Any]]) -> str:
        """Determine user role based on group membership.
        
        Args:
            user_groups: List of user groups
            
        Returns:
            User role
        """
        group_mapping = self.config.get("group_mapping", {})
        
        # Default role
        default_role = "viewer"
        
        # Check if user is in any mapped groups
        for group in user_groups:
            group_id = group.get("id")
            if group_id in group_mapping:
                return group_mapping[group_id]
        
        return default_role
    
    def _sync_user_to_supabase(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Sync user to Supabase.
        
        Args:
            user_data: User data
            
        Returns:
            Synced user data
        """
        try:
            # Check if user exists
            user_query = self.supabase.table("users").select("*").eq("email", user_data["email"]).execute()
            
            if user_query.data and len(user_query.data) > 0:
                # Update existing user
                user_id = user_query.data[0]["id"]
                
                update_data = {
                    "name": user_data["name"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "role": user_data["role"],
                    "last_login": datetime.now().isoformat(),
                    "external_id": user_data["id"],
                    "avatar_url": user_data["avatar_url"]
                }
                
                update_result = self.supabase.table("users").update(update_data).eq("id", user_id).execute()
                
                if update_result.data and len(update_result.data) > 0:
                    return update_result.data[0]
                else:
                    logger.error("Failed to update user in Supabase")
                    return None
            else:
                # Create new user
                create_data = {
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "role": user_data["role"],
                    "last_login": datetime.now().isoformat(),
                    "external_id": user_data["id"],
                    "avatar_url": user_data["avatar_url"],
                    "auth_provider": "entra_id"
                }
                
                create_result = self.supabase.table("users").insert(create_data).execute()
                
                if create_result.data and len(create_result.data) > 0:
                    return create_result.data[0]
                else:
                    logger.error("Failed to create user in Supabase")
                    return None
        except Exception as e:
            logger.error(f"Error syncing user to Supabase: {str(e)}")
            return None
    
    def get_users(self, limit: int = 50, filter_query: str = None) -> Dict[str, Any]:
        """Get users from Microsoft Entra ID.
        
        Args:
            limit: Maximum number of users to retrieve
            filter_query: Optional filter query
            
        Returns:
            List of users
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
            
            # Build URL
            users_url = f"https://graph.microsoft.com/v1.0/users?$top={limit}"
            
            if filter_query:
                users_url += f"&$filter={filter_query}"
            
            users_response = requests.get(users_url, headers=headers)
            
            if users_response.status_code == 200:
                users_data = users_response.json()
                users = users_data.get("value", [])
                
                return {
                    "success": True,
                    "users": [
                        {
                            "id": user.get("id"),
                            "email": user.get("userPrincipalName"),
                            "name": user.get("displayName"),
                            "first_name": user.get("givenName"),
                            "last_name": user.get("surname"),
                            "job_title": user.get("jobTitle"),
                            "department": user.get("department"),
                            "phone": user.get("mobilePhone")
                        }
                        for user in users
                    ]
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to get users. Status code: {users_response.status_code}, Response: {users_response.text}"
                }
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting users: {str(e)}"
            }
    
    def get_groups(self, limit: int = 50, filter_query: str = None) -> Dict[str, Any]:
        """Get groups from Microsoft Entra ID.
        
        Args:
            limit: Maximum number of groups to retrieve
            filter_query: Optional filter query
            
        Returns:
            List of groups
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
            
            # Build URL
            groups_url = f"https://graph.microsoft.com/v1.0/groups?$top={limit}"
            
            if filter_query:
                groups_url += f"&$filter={filter_query}"
            
            groups_response = requests.get(groups_url, headers=headers)
            
            if groups_response.status_code == 200:
                groups_data = groups_response.json()
                groups = groups_data.get("value", [])
                
                return {
                    "success": True,
                    "groups": [
                        {
                            "id": group.get("id"),
                            "name": group.get("displayName"),
                            "description": group.get("description"),
                            "email": group.get("mail"),
                            "security_enabled": group.get("securityEnabled"),
                            "mail_enabled": group.get("mailEnabled")
                        }
                        for group in groups
                    ]
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to get groups. Status code: {groups_response.status_code}, Response: {groups_response.text}"
                }
        except Exception as e:
            logger.error(f"Error getting groups: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting groups: {str(e)}"
            }
    
    def update_group_mapping(self, group_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Update the group mapping configuration.
        
        Args:
            group_mapping: Mapping of Entra ID group IDs to EA roles
            
        Returns:
            Update result
        """
        try:
            self.config["group_mapping"] = group_mapping
            self._save_config()
            
            return {
                "success": True,
                "message": "Group mapping updated successfully"
            }
        except Exception as e:
            logger.error(f"Error updating group mapping: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating group mapping: {str(e)}"
            }
    
    def sync_users(self, filter_query: str = None) -> Dict[str, Any]:
        """Sync users from Microsoft Entra ID to Supabase.
        
        Args:
            filter_query: Optional filter query
            
        Returns:
            Sync results
        """
        try:
            # Get users from Entra ID
            users_result = self.get_users(limit=999, filter_query=filter_query)
            
            if not users_result.get("success"):
                return users_result
            
            users = users_result.get("users", [])
            
            # Get user groups for role determination
            users_with_roles = []
            for user in users:
                user_groups = self._get_user_groups(self.access_token, user["id"])
                user_role = self._determine_user_role(user_groups)
                user["role"] = user_role
                users_with_roles.append(user)
            
            # Sync users to Supabase
            sync_results = []
            for user in users_with_roles:
                user_data = {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "first_name": user["first_name"],
                    "last_name": user["last_name"],
                    "role": user["role"],
                    "avatar_url": None
                }
                
                sync_result = self._sync_user_to_supabase(user_data)
                
                if sync_result:
                    sync_results.append({
                        "id": user["id"],
                        "email": user["email"],
                        "name": user["name"],
                        "role": user["role"],
                        "status": "success"
                    })
                else:
                    sync_results.append({
                        "id": user["id"],
                        "email": user["email"],
                        "name": user["name"],
                        "status": "failed"
                    })
            
            return {
                "success": True,
                "message": f"Synced {len(sync_results)} users",
                "results": sync_results
            }
        except Exception as e:
            logger.error(f"Error syncing users: {str(e)}")
            return {
                "success": False,
                "message": f"Error syncing users: {str(e)}"
            }
            
    def sync(self) -> Dict[str, Any]:
        """Synchronize users from Microsoft Entra ID.
        
        This method implements the sync operation required by the IntegrationBase class.
        
        Returns:
            Synchronization results
        """
        return self.sync_users()
