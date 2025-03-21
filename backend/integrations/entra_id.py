"""
Enterprise Architecture Solution - Microsoft Entra ID Integration

This module provides integration with Microsoft Entra ID for authentication, 
user management, and role-based access control.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import msal
import requests
from fastapi import HTTPException, status

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
        self.tenant_id = self.config.get("tenant_id", "")
        self.client_id = self.config.get("client_id", "")
        self.client_secret = self.config.get("client_secret", "")
        self.redirect_uri = self.config.get("redirect_uri", "")
        self.scopes = self.config.get("scopes", ["User.Read", "Directory.Read.All"])
        self.role_mappings = self.config.get("role_mappings", {})
        
        # Initialize MSAL app
        self.msal_app = None
        if self.tenant_id and self.client_id and self.client_secret:
            self._init_msal_app()
    
    def _get_integration_type(self) -> str:
        """Get the integration type identifier."""
        return "entra_id"
    
    def _init_msal_app(self):
        """Initialize the MSAL application."""
        try:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            self.msal_app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=authority
            )
            logger.info(f"MSAL application initialized for tenant {self.tenant_id}")
        except Exception as e:
            logger.error(f"Error initializing MSAL application: {str(e)}")
            self.msal_app = None
    
    def configure(self, tenant_id: str, client_id: str, client_secret: str, 
                 redirect_uri: str, scopes: List[str] = None, 
                 role_mappings: Dict[str, str] = None) -> Dict[str, Any]:
        """Configure the Entra ID integration.
        
        Args:
            tenant_id: Microsoft Entra ID tenant ID
            client_id: Application (client) ID
            client_secret: Application client secret
            redirect_uri: Redirect URI for authentication flow
            scopes: List of API permission scopes
            role_mappings: Mapping of Entra ID groups to application roles
            
        Returns:
            Configuration status
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or ["User.Read", "Directory.Read.All"]
        self.role_mappings = role_mappings or {}
        
        self.config = {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "scopes": self.scopes,
            "role_mappings": self.role_mappings,
            "last_configured": datetime.now().isoformat()
        }
        
        self._save_config()
        self._init_msal_app()
        
        # Test the connection to validate the configuration
        test_result = self.test_connection()
        
        return {
            "success": test_result.get("success", False),
            "message": test_result.get("message", ""),
            "config_id": self.config_id
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Microsoft Entra ID."""
        if not self.msal_app:
            return {
                "success": False,
                "message": "MSAL application not initialized."
            }
        
        try:
            # Attempt to acquire a token for the Microsoft Graph API
            result = self.msal_app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            
            if "access_token" in result:
                # Verify the token works by making a simple Graph API call
                headers = {
                    "Authorization": f"Bearer {result['access_token']}",
                    "Content-Type": "application/json"
                }
                
                response = requests.get(
                    "https://graph.microsoft.com/v1.0/organization",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Successfully connected to Microsoft Entra ID"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Connected to Entra ID but Graph API call failed. Status code: {response.status_code}, Response: {response.text}"
                    }
            else:
                error = result.get("error", "")
                error_description = result.get("error_description", "")
                return {
                    "success": False,
                    "message": f"Failed to acquire token. Error: {error}, Description: {error_description}"
                }
        except Exception as e:
            logger.error(f"Error testing Entra ID connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to Entra ID: {str(e)}"
            }
    
    def get_authorization_url(self, state: str = None) -> str:
        """Get the authorization URL for initiating the OAuth flow.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL
        """
        if not self.msal_app:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Entra ID integration not configured"
            )
        
        auth_params = {
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "response_mode": "query"
        }
        
        if state:
            auth_params["state"] = state
        
        return self.msal_app.get_authorization_request_url(
            scopes=self.scopes,
            **auth_params
        )
    
    def get_token_from_code(self, code: str) -> Dict[str, Any]:
        """Get access and refresh tokens from authorization code.
        
        Args:
            code: Authorization code from the OAuth flow
            
        Returns:
            Dictionary containing tokens and user information
        """
        if not self.msal_app:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Entra ID integration not configured"
            )
        
        try:
            result = self.msal_app.acquire_token_by_authorization_code(
                code=code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            if "access_token" in result:
                # Get user information
                user_info = self._get_user_info(result["access_token"])
                
                # Map user to roles
                roles = self._map_user_to_roles(result["access_token"], user_info.get("id"))
                
                # Combine token and user information
                token_info = {
                    "access_token": result["access_token"],
                    "refresh_token": result.get("refresh_token", ""),
                    "id_token": result.get("id_token", ""),
                    "expires_in": result.get("expires_in", 3600),
                    "expires_at": (datetime.now() + timedelta(seconds=result.get("expires_in", 3600))).isoformat(),
                    "user": user_info,
                    "roles": roles
                }
                
                return token_info
            else:
                error = result.get("error", "")
                error_description = result.get("error_description", "")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to acquire token. Error: {error}, Description: {error_description}"
                )
        except Exception as e:
            logger.error(f"Error getting token from code: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting token: {str(e)}"
            )
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token using a refresh token.
        
        Args:
            refresh_token: Refresh token from a previous authentication
            
        Returns:
            Dictionary containing new tokens
        """
        if not self.msal_app:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Entra ID integration not configured"
            )
        
        try:
            result = self.msal_app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=self.scopes
            )
            
            if "access_token" in result:
                # Get user information
                user_info = self._get_user_info(result["access_token"])
                
                # Map user to roles
                roles = self._map_user_to_roles(result["access_token"], user_info.get("id"))
                
                # Combine token and user information
                token_info = {
                    "access_token": result["access_token"],
                    "refresh_token": result.get("refresh_token", refresh_token),
                    "id_token": result.get("id_token", ""),
                    "expires_in": result.get("expires_in", 3600),
                    "expires_at": (datetime.now() + timedelta(seconds=result.get("expires_in", 3600))).isoformat(),
                    "user": user_info,
                    "roles": roles
                }
                
                return token_info
            else:
                error = result.get("error", "")
                error_description = result.get("error_description", "")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to refresh token. Error: {error}, Description: {error_description}"
                )
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error refreshing token: {str(e)}"
            )
    
    def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft Graph API.
        
        Args:
            access_token: Access token for Microsoft Graph API
            
        Returns:
            User information dictionary
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "id": user_data.get("id", ""),
                    "displayName": user_data.get("displayName", ""),
                    "givenName": user_data.get("givenName", ""),
                    "surname": user_data.get("surname", ""),
                    "email": user_data.get("mail", user_data.get("userPrincipalName", "")),
                    "jobTitle": user_data.get("jobTitle", ""),
                    "department": user_data.get("department", ""),
                    "officeLocation": user_data.get("officeLocation", "")
                }
            else:
                logger.error(f"Error getting user info. Status code: {response.status_code}, Response: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return {}
    
    def _map_user_to_roles(self, access_token: str, user_id: str) -> List[str]:
        """Map user to application roles based on group memberships.
        
        Args:
            access_token: Access token for Microsoft Graph API
            user_id: User ID to check group memberships for
            
        Returns:
            List of application roles
        """
        if not self.role_mappings:
            return ["viewer"]  # Default role
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Get user's group memberships
            response = requests.get(
                f"https://graph.microsoft.com/v1.0/users/{user_id}/memberOf",
                headers=headers
            )
            
            if response.status_code == 200:
                groups_data = response.json().get("value", [])
                group_ids = [group.get("id") for group in groups_data if group.get("@odata.type") == "#microsoft.graph.group"]
                
                # Map group IDs to roles
                roles = set()
                for group_id in group_ids:
                    if group_id in self.role_mappings:
                        roles.add(self.role_mappings[group_id])
                
                # Add default role if no mappings found
                if not roles:
                    roles.add("viewer")
                
                return list(roles)
            else:
                logger.error(f"Error getting group memberships. Status code: {response.status_code}, Response: {response.text}")
                return ["viewer"]  # Default role
        except Exception as e:
            logger.error(f"Error mapping user to roles: {str(e)}")
            return ["viewer"]  # Default role
    
    def sync(self) -> Dict[str, Any]:
        """Synchronize user information from Entra ID to the application.
        
        This method synchronizes user information and group memberships from
        Microsoft Entra ID to the application's user database.
        
        Returns:
            Synchronization status
        """
        if not self.msal_app:
            return {
                "success": False,
                "message": "Entra ID integration not configured"
            }
        
        try:
            # Track sync metrics
            users_processed = 0
            users_created = 0
            users_updated = 0
            users_failed = 0
            sync_details = {}
            
            # Get an access token for Microsoft Graph API
            result = self.msal_app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            
            if "access_token" not in result:
                error = result.get("error", "")
                error_description = result.get("error_description", "")
                self._log_sync("failed", 0, 0, 0, 0, f"Failed to acquire token. Error: {error}, Description: {error_description}")
                return {
                    "success": False,
                    "message": f"Failed to acquire token. Error: {error}, Description: {error_description}"
                }
            
            access_token = result["access_token"]
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Get users from Entra ID
            users = self._get_all_users(headers)
            users_processed = len(users)
            
            if not users:
                self._log_sync("failed", users_processed, users_created, users_updated, 
                              users_failed, "No users retrieved from Entra ID")
                return {
                    "success": False,
                    "message": "No users retrieved from Entra ID"
                }
            
            # Process each user
            for user in users:
                try:
                    # Map the user data to application user format
                    user_data = {
                        "external_id": user.get("id", ""),
                        "email": user.get("mail", user.get("userPrincipalName", "")),
                        "full_name": user.get("displayName", ""),
                        "given_name": user.get("givenName", ""),
                        "surname": user.get("surname", ""),
                        "job_title": user.get("jobTitle", ""),
                        "department": user.get("department", ""),
                        "office_location": user.get("officeLocation", ""),
                        "external_source": "entra_id",
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    # Get user's group memberships for role mapping
                    user_id = user.get("id", "")
                    if user_id:
                        groups_response = requests.get(
                            f"https://graph.microsoft.com/v1.0/users/{user_id}/memberOf",
                            headers=headers
                        )
                        
                        if groups_response.status_code == 200:
                            groups_data = groups_response.json().get("value", [])
                            group_ids = [group.get("id") for group in groups_data if group.get("@odata.type") == "#microsoft.graph.group"]
                            
                            # Map group IDs to roles
                            roles = set()
                            for group_id in group_ids:
                                if group_id in self.role_mappings:
                                    roles.add(self.role_mappings[group_id])
                            
                            # Add default role if no mappings found
                            if not roles:
                                roles.add("viewer")
                            
                            user_data["roles"] = list(roles)
                    
                    # Check if the user already exists in the application
                    existing_user = self._find_existing_user(user_data["email"])
                    
                    if existing_user:
                        # Update existing user
                        self._update_user(existing_user["id"], user_data)
                        users_updated += 1
                    else:
                        # Create new user
                        self._create_user(user_data)
                        users_created += 1
                except Exception as e:
                    logger.error(f"Error processing user {user.get('id', 'unknown')}: {str(e)}")
                    users_failed += 1
                    sync_details[f"user_{user.get('id', 'unknown')}"] = str(e)
            
            # Update last sync timestamp in config
            self.config["last_sync"] = datetime.now().isoformat()
            self._save_config()
            
            # Log the sync activity
            sync_status = "success" if users_failed == 0 else "partial" if users_created + users_updated > 0 else "failed"
            self._log_sync(sync_status, users_processed, users_created, users_updated, users_failed, 
                          None if sync_status != "failed" else "Some users failed to process", sync_details)
            
            return {
                "success": sync_status != "failed",
                "message": f"Processed {users_processed} users: {users_created} created, {users_updated} updated, {users_failed} failed",
                "details": {
                    "users_processed": users_processed,
                    "users_created": users_created,
                    "users_updated": users_updated,
                    "users_failed": users_failed
                }
            }
            
        except Exception as e:
            logger.error(f"Error syncing with Entra ID: {str(e)}")
            self._log_sync("failed", 0, 0, 0, 0, str(e))
            return {
                "success": False,
                "message": f"Error syncing with Entra ID: {str(e)}"
            }
    
    def _get_all_users(self, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Get all users from Microsoft Entra ID.
        
        Args:
            headers: HTTP headers for Microsoft Graph API
            
        Returns:
            List of user dictionaries
        """
        all_users = []
        next_link = "https://graph.microsoft.com/v1.0/users?$select=id,displayName,givenName,surname,mail,userPrincipalName,jobTitle,department,officeLocation"
        
        while next_link:
            try:
                response = requests.get(next_link, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"Error fetching users, status code: {response.status_code}, response: {response.text}")
                    break
                
                data = response.json()
                users = data.get("value", [])
                all_users.extend(users)
                
                # Check if there are more pages
                next_link = data.get("@odata.nextLink")
                
            except Exception as e:
                logger.error(f"Error fetching users: {str(e)}")
                break
        
        return all_users
    
    def _find_existing_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Find an existing user by email.
        
        Args:
            email: User email to search for
            
        Returns:
            User dictionary or None if not found
        """
        try:
            # Query the users table for a user with matching email
            query = self.supabase.table("users").select("*").eq("email", email).execute()
            
            if query.data and len(query.data) > 0:
                return query.data[0]
            
            return None
        except Exception as e:
            logger.error(f"Error finding user: {str(e)}")
            return None
    
    def _create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user in the application.
        
        Args:
            user_data: User data to create
            
        Returns:
            ID of the created user
        """
        try:
            # Add creation timestamp
            user_data["created_at"] = datetime.now().isoformat()
            
            # Insert the user into the database
            result = self.supabase.table("users").insert(user_data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]["id"]
            
            return ""
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    def _update_user(self, user_id: str, user_data: Dict[str, Any]) -> None:
        """Update an existing user in the application.
        
        Args:
            user_id: ID of the user to update
            user_data: Updated user data
        """
        try:
            # Update the user in the database
            self.supabase.table("users").update(user_data).eq("id", user_id).execute()
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise
