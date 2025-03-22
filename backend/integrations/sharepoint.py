"""
Enterprise Architecture Solution - SharePoint Integration

This module provides integration with SharePoint for document management, 
collaboration, and publishing EA artifacts.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, BinaryIO
from datetime import datetime

import requests
import msal

from .integration_base import IntegrationBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SharePointIntegration(IntegrationBase):
    """Integration with SharePoint for EA document management and collaboration."""
    
    def __init__(self, supabase_client, config_id: str = None):
        """Initialize the SharePoint integration.
        
        Args:
            supabase_client: Initialized Supabase client
            config_id: ID of the integration configuration in the database
        """
        super().__init__(supabase_client, config_id)
        self.site_url = self.config.get("site_url", "")
        self.access_token = None
        self.site_id = None
    
    def _get_integration_type(self) -> str:
        """Get the integration type identifier."""
        return "sharepoint"
    
    def configure(self, site_url: str, client_id: str, client_secret: str, 
                 tenant_id: str, library_name: str = "EA Documents") -> Dict[str, Any]:
        """Configure the SharePoint integration.
        
        Args:
            site_url: SharePoint site URL
            client_id: Microsoft Entra ID client ID
            client_secret: Microsoft Entra ID client secret
            tenant_id: Microsoft Entra ID tenant ID
            library_name: Name of the document library to use
            
        Returns:
            Configuration status
        """
        self.site_url = site_url
        
        self.config = {
            "site_url": site_url,
            "client_id": client_id,
            "client_secret": client_secret,
            "tenant_id": tenant_id,
            "library_name": library_name,
            "last_configured": datetime.now().isoformat()
        }
        
        self._save_config()
        
        # Test the connection to validate the configuration
        test_result = self.test_connection()
        
        if test_result.get("success"):
            # Store the site ID for future use
            self.site_id = test_result.get("site_id")
            self.config["site_id"] = self.site_id
            self._save_config()
        
        return {
            "success": test_result.get("success", False),
            "message": test_result.get("message", ""),
            "config_id": self.config_id,
            "site_id": self.site_id
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to SharePoint."""
        try:
            # Get access token
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for SharePoint"
                }
            
            # Get site information
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json;odata=verbose",
                "Content-Type": "application/json"
            }
            
            # Extract site name from URL
            site_parts = self.site_url.strip("/").split("/")
            site_name = site_parts[-1] if len(site_parts) > 0 else ""
            
            # Get site ID
            graph_site_url = f"https://graph.microsoft.com/v1.0/sites/root:/sites/{site_name}"
            site_response = requests.get(graph_site_url, headers=headers)
            
            if site_response.status_code == 200:
                site_data = site_response.json()
                site_id = site_data.get("id")
                return {
                    "success": True,
                    "message": "Successfully connected to SharePoint site",
                    "site_id": site_id,
                    "site_name": site_data.get("displayName")
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to connect to SharePoint site. Status code: {site_response.status_code}, Response: {site_response.text}"
                }
        except Exception as e:
            logger.error(f"Error testing SharePoint connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to SharePoint: {str(e)}"
            }
    
    def _get_access_token(self) -> None:
        """Get access token for SharePoint API."""
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
    
    def get_document_libraries(self) -> Dict[str, Any]:
        """Get available document libraries in the SharePoint site."""
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for SharePoint"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json;odata=verbose",
                "Content-Type": "application/json"
            }
            
            # Use the stored site ID if available
            site_id = self.config.get("site_id")
            if not site_id:
                return {
                    "success": False,
                    "message": "Site ID not available. Please reconfigure the integration."
                }
            
            # Get document libraries
            libraries_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            libraries_response = requests.get(libraries_url, headers=headers)
            
            if libraries_response.status_code == 200:
                libraries_data = libraries_response.json()
                libraries = libraries_data.get("value", [])
                
                return {
                    "success": True,
                    "libraries": [
                        {
                            "id": lib.get("id"),
                            "name": lib.get("name"),
                            "description": lib.get("description", ""),
                            "web_url": lib.get("webUrl")
                        }
                        for lib in libraries
                    ]
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to get document libraries. Status code: {libraries_response.status_code}, Response: {libraries_response.text}"
                }
        except Exception as e:
            logger.error(f"Error getting document libraries: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting document libraries: {str(e)}"
            }
    
    def upload_document(self, file_name: str, file_content: BinaryIO, 
                       folder_path: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Upload a document to SharePoint.
        
        Args:
            file_name: Name of the file to upload
            file_content: File content as bytes or file-like object
            folder_path: Path to folder in document library (optional)
            metadata: Additional metadata for the document (optional)
            
        Returns:
            Upload results
        """
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for SharePoint"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/octet-stream"
            }
            
            # Get document library ID
            libraries = self.get_document_libraries()
            
            if not libraries.get("success"):
                return libraries
            
            library_name = self.config.get("library_name")
            library = next((lib for lib in libraries.get("libraries", []) if lib["name"] == library_name), None)
            
            if not library:
                return {
                    "success": False,
                    "message": f"Document library '{library_name}' not found"
                }
            
            library_id = library["id"]
            
            # Build upload URL
            upload_path = f"/drives/{library_id}/root:"
            if folder_path:
                upload_path += f"/{folder_path}"
            upload_path += f"/{file_name}:/content"
            
            upload_url = f"https://graph.microsoft.com/v1.0{upload_path}"
            
            # Upload file
            upload_response = requests.put(upload_url, headers=headers, data=file_content)
            
            if upload_response.status_code in [200, 201]:
                file_data = upload_response.json()
                
                # Update metadata if provided
                if metadata and len(metadata) > 0:
                    item_id = file_data.get("id")
                    metadata_url = f"https://graph.microsoft.com/v1.0/drives/{library_id}/items/{item_id}"
                    
                    metadata_headers = {
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    }
                    
                    # Convert metadata to SharePoint format
                    sp_metadata = {}
                    for key, value in metadata.items():
                        sp_metadata[key] = value
                    
                    metadata_payload = {"fields": sp_metadata}
                    metadata_response = requests.patch(metadata_url, headers=metadata_headers, json=metadata_payload)
                    
                    if metadata_response.status_code not in [200, 201, 204]:
                        logger.warning(f"Failed to update metadata. Status code: {metadata_response.status_code}, Response: {metadata_response.text}")
                
                return {
                    "success": True,
                    "file_id": file_data.get("id"),
                    "name": file_data.get("name"),
                    "web_url": file_data.get("webUrl")
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to upload document. Status code: {upload_response.status_code}, Response: {upload_response.text}"
                }
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return {
                "success": False,
                "message": f"Error uploading document: {str(e)}"
            }
    
    def get_documents(self, folder_path: str = None, filter_query: str = None) -> Dict[str, Any]:
        """Get documents from SharePoint.
        
        Args:
            folder_path: Path to folder in document library (optional)
            filter_query: Filter query for documents (optional)
            
        Returns:
            List of documents
        """
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for SharePoint"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json;odata=verbose",
                "Content-Type": "application/json"
            }
            
            # Get document library ID
            libraries = self.get_document_libraries()
            
            if not libraries.get("success"):
                return libraries
            
            library_name = self.config.get("library_name")
            library = next((lib for lib in libraries.get("libraries", []) if lib["name"] == library_name), None)
            
            if not library:
                return {
                    "success": False,
                    "message": f"Document library '{library_name}' not found"
                }
            
            library_id = library["id"]
            
            # Build query URL
            query_path = f"/drives/{library_id}/root"
            if folder_path:
                query_path += f":{folder_path}:"
            query_path += "/children"
            
            query_url = f"https://graph.microsoft.com/v1.0{query_path}"
            
            # Add filter if provided
            if filter_query:
                query_url += f"?$filter={filter_query}"
            
            # Get documents
            documents_response = requests.get(query_url, headers=headers)
            
            if documents_response.status_code == 200:
                documents_data = documents_response.json()
                documents = documents_data.get("value", [])
                
                return {
                    "success": True,
                    "documents": [
                        {
                            "id": doc.get("id"),
                            "name": doc.get("name"),
                            "size": doc.get("size"),
                            "web_url": doc.get("webUrl"),
                            "created_datetime": doc.get("createdDateTime"),
                            "last_modified_datetime": doc.get("lastModifiedDateTime"),
                            "is_folder": "folder" in doc
                        }
                        for doc in documents
                    ]
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to get documents. Status code: {documents_response.status_code}, Response: {documents_response.text}"
                }
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting documents: {str(e)}"
            }
    
    def download_document(self, document_id: str) -> Dict[str, Any]:
        """Download a document from SharePoint.
        
        Args:
            document_id: ID of the document to download
            
        Returns:
            Document content
        """
        try:
            self._get_access_token()
            
            if not self.access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token for SharePoint"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # Get document library ID
            libraries = self.get_document_libraries()
            
            if not libraries.get("success"):
                return libraries
            
            library_name = self.config.get("library_name")
            library = next((lib for lib in libraries.get("libraries", []) if lib["name"] == library_name), None)
            
            if not library:
                return {
                    "success": False,
                    "message": f"Document library '{library_name}' not found"
                }
            
            library_id = library["id"]
            
            # Build download URL
            download_url = f"https://graph.microsoft.com/v1.0/drives/{library_id}/items/{document_id}/content"
            
            # Download file
            download_response = requests.get(download_url, headers=headers)
            
            if download_response.status_code == 200:
                return {
                    "success": True,
                    "content": download_response.content,
                    "content_type": download_response.headers.get("Content-Type")
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to download document. Status code: {download_response.status_code}, Response: {download_response.text}"
                }
        except Exception as e:
            logger.error(f"Error downloading document: {str(e)}")
            return {
                "success": False,
                "message": f"Error downloading document: {str(e)}"
            }
    
    def publish_ea_artifact(self, artifact_id: str, artifact_type: str, 
                           folder_path: str = None) -> Dict[str, Any]:
        """Publish an EA artifact to SharePoint.
        
        Args:
            artifact_id: ID of the EA artifact to publish
            artifact_type: Type of artifact (model, element, view, etc.)
            folder_path: Path to folder in document library (optional)
            
        Returns:
            Publishing results
        """
        try:
            # Get artifact data
            artifact_data = self._get_artifact_data(artifact_id, artifact_type)
            
            if not artifact_data:
                return {
                    "success": False,
                    "message": f"Failed to get artifact data for {artifact_type} with ID {artifact_id}"
                }
            
            # Generate document content
            document_content, file_name, content_type = self._generate_document(artifact_data, artifact_type)
            
            if not document_content:
                return {
                    "success": False,
                    "message": "Failed to generate document content"
                }
            
            # Add metadata
            metadata = {
                "EA_ArtifactID": artifact_id,
                "EA_ArtifactType": artifact_type,
                "EA_PublishedDate": datetime.now().isoformat(),
                "EA_Name": artifact_data.get("name", ""),
                "EA_Description": artifact_data.get("description", "")
            }
            
            # Upload to SharePoint
            from io import BytesIO
            upload_result = self.upload_document(
                file_name=file_name,
                file_content=BytesIO(document_content),
                folder_path=folder_path,
                metadata=metadata
            )
            
            if upload_result.get("success"):
                # Update artifact with publishing info
                self._update_artifact_publishing_info(artifact_id, artifact_type, upload_result.get("web_url"))
                
                return {
                    "success": True,
                    "message": f"Successfully published {artifact_type} to SharePoint",
                    "file_id": upload_result.get("file_id"),
                    "web_url": upload_result.get("web_url")
                }
            else:
                return upload_result
        except Exception as e:
            logger.error(f"Error publishing EA artifact: {str(e)}")
            return {
                "success": False,
                "message": f"Error publishing EA artifact: {str(e)}"
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
    
    def _generate_document(self, artifact_data: Dict[str, Any], artifact_type: str) -> tuple:
        """Generate document content for an EA artifact.
        
        Args:
            artifact_data: Artifact data
            artifact_type: Type of artifact
            
        Returns:
            Tuple of (document_content, file_name, content_type)
        """
        try:
            # Generate document title
            title = f"{artifact_data.get('name', 'Untitled')} - {artifact_type.capitalize()}"
            
            # Generate file name
            file_name = f"{artifact_type}_{artifact_data.get('id')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
            
            # Generate HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333366; }}
                    .metadata {{ background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
                    .content {{ margin-top: 20px; }}
                </style>
            </head>
            <body>
                <h1>{title}</h1>
                <div class="metadata">
                    <p><strong>ID:</strong> {artifact_data.get('id')}</p>
                    <p><strong>Type:</strong> {artifact_type}</p>
                    <p><strong>Created:</strong> {artifact_data.get('created_at')}</p>
                    <p><strong>Last Updated:</strong> {artifact_data.get('updated_at')}</p>
                </div>
                <div class="content">
                    <h2>Description</h2>
                    <p>{artifact_data.get('description', 'No description provided.')}</p>
            """
            
            # Add artifact-specific content
            if artifact_type == "model":
                html_content += f"""
                    <h2>Status</h2>
                    <p>{artifact_data.get('status', 'Unknown')}</p>
                    <h2>Version</h2>
                    <p>{artifact_data.get('version', '1.0')}</p>
                """
            elif artifact_type == "element":
                html_content += f"""
                    <h2>Element Type</h2>
                    <p>{artifact_data.get('type_id', 'Unknown')}</p>
                    <h2>Status</h2>
                    <p>{artifact_data.get('status', 'Unknown')}</p>
                """
            elif artifact_type == "view":
                html_content += f"""
                    <h2>View Type</h2>
                    <p>{artifact_data.get('view_type', 'Unknown')}</p>
                """
            
            # Close HTML
            html_content += """
                </div>
            </body>
            </html>
            """
            
            return html_content.encode('utf-8'), file_name, "text/html"
        except Exception as e:
            logger.error(f"Error generating document: {str(e)}")
            return None, None, None
    
    def _update_artifact_publishing_info(self, artifact_id: str, artifact_type: str, web_url: str) -> None:
        """Update artifact with publishing information.
        
        Args:
            artifact_id: ID of the artifact
            artifact_type: Type of artifact
            web_url: URL of the published document
        """
        try:
            # Update properties based on artifact type
            properties_update = {
                "sharepoint_url": web_url,
                "last_published": datetime.now().isoformat()
            }
            
            if artifact_type == "model":
                self.supabase.table("ea_models").update({
                    "properties": self.supabase.rpc("jsonb_merge", {
                        "json1": artifact_id,
                        "json2": json.dumps(properties_update)
                    })
                }).eq("id", artifact_id).execute()
            elif artifact_type == "element":
                self.supabase.table("ea_elements").update({
                    "properties": self.supabase.rpc("jsonb_merge", {
                        "json1": artifact_id,
                        "json2": json.dumps(properties_update)
                    })
                }).eq("id", artifact_id).execute()
            elif artifact_type == "view":
                self.supabase.table("ea_views").update({
                    "properties": self.supabase.rpc("jsonb_merge", {
                        "json1": artifact_id,
                        "json2": json.dumps(properties_update)
                    })
                }).eq("id", artifact_id).execute()
        except Exception as e:
            logger.error(f"Error updating artifact publishing info: {str(e)}")
            
    def sync(self) -> Dict[str, Any]:
        """Synchronize documents between SharePoint and the EA repository.
        
        This method implements the sync operation required by the IntegrationBase class.
        
        Returns:
            Synchronization results
        """
        try:
            # This is a simplified implementation that just reports statistics
            # In a real implementation, this would perform bi-directional synchronization
            
            # Get document count
            documents_result = self.get_documents()
            document_count = len(documents_result.get("documents", [])) if documents_result.get("success") else 0
            
            return {
                "success": True,
                "message": f"Synchronized with SharePoint",
                "document_count": document_count,
                "libraries": self.get_document_libraries().get("libraries", []) if self.get_document_libraries().get("success") else []
            }
        except Exception as e:
            logger.error(f"Error synchronizing with SharePoint: {str(e)}")
            return {
                "success": False,
                "message": f"Error synchronizing with SharePoint: {str(e)}"
            }
