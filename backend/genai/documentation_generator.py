"""
Enterprise Architecture Solution - Documentation Generator

This module implements the AI-powered documentation generation capabilities
for the Enterprise Architecture Solution using OpenAI's GPT models.
"""

import os
import logging
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentationGenerator:
    """Generate documentation from EA models and elements."""
    
    def __init__(self, supabase_client):
        """Initialize the Documentation Generator.
        
        Args:
            supabase_client: A configured Supabase client for database operations
        """
        self.supabase = supabase_client
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def generate_documentation(self, content_type: str, content_id: str, 
                              format: str = "markdown", include_diagrams: bool = True,
                              include_relationships: bool = True, 
                              style: str = "technical") -> Dict[str, Any]:
        """Generate documentation for EA artifacts.
        
        Args:
            content_type: Type of content (element, model, view, policy)
            content_id: UUID of the content
            format: Output format (markdown, html, docx)
            include_diagrams: Whether to include diagrams
            include_relationships: Whether to include relationships
            style: Style of documentation (technical, business, executive)
            
        Returns:
            Dict containing the generated documentation and metadata
        """
        try:
            # Get content data based on type
            if content_type == "element":
                content_data = self._get_element_data(content_id, include_relationships)
            elif content_type == "model":
                content_data = self._get_model_data(content_id, include_diagrams, include_relationships)
            elif content_type == "view":
                content_data = self._get_view_data(content_id)
            elif content_type == "policy":
                content_data = self._get_policy_data(content_id)
            else:
                return {"success": False, "error": f"Unsupported content type: {content_type}"}
                
            # Generate documentation using OpenAI
            documentation = self._generate_with_ai(content_data, content_type, format, style)
            
            # Format according to requested output type
            formatted_doc = self._format_documentation(documentation, format)
            
            # Log the documentation generation
            self._log_generation(content_type, content_id, format, style)
            
            return {
                "success": True,
                "documentation": formatted_doc,
                "metadata": {
                    "content_type": content_type,
                    "content_id": content_id,
                    "format": format,
                    "style": style,
                    "generated_at": datetime.now().isoformat(),
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating documentation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_element_data(self, element_id: str, include_relationships: bool) -> Dict[str, Any]:
        """Get element data from the database.
        
        Args:
            element_id: ID of the element
            include_relationships: Whether to include related elements
            
        Returns:
            Element data dictionary
        """
        # Query the element table
        element_query = self.supabase.table("ea_elements").select("*").eq("id", element_id).execute()
        
        if not element_query.data:
            raise ValueError(f"Element with ID {element_id} not found")
            
        element = element_query.data[0]
        
        # Get element type information
        element_type_query = self.supabase.table("ea_element_types").select("*").eq("id", element["type_id"]).execute()
        element_type = element_type_query.data[0] if element_type_query.data else {"name": "Unknown"}
        
        # Get model information
        model_query = self.supabase.table("ea_models").select("*").eq("id", element["model_id"]).execute()
        model = model_query.data[0] if model_query.data else {"name": "Unknown"}
        
        # If we need relationships, get them
        relationships = []
        if include_relationships:
            # Get relationships where this element is the source
            source_rels_query = self.supabase.table("ea_relationships").select("*").eq("source_element_id", element_id).execute()
            source_rels = source_rels_query.data if source_rels_query.data else []
            
            # Get relationships where this element is the target
            target_rels_query = self.supabase.table("ea_relationships").select("*").eq("target_element_id", element_id).execute()
            target_rels = target_rels_query.data if target_rels_query.data else []
            
            # Combine and process relationships
            for rel in source_rels + target_rels:
                rel_type_query = self.supabase.table("ea_relationship_types").select("*").eq("id", rel["relationship_type_id"]).execute()
                rel_type = rel_type_query.data[0] if rel_type_query.data else {"name": "Unknown"}
                
                # Get the other element in the relationship
                other_id = rel["target_element_id"] if rel["source_element_id"] == element_id else rel["source_element_id"]
                other_element_query = self.supabase.table("ea_elements").select("*").eq("id", other_id).execute()
                other_element = other_element_query.data[0] if other_element_query.data else {"name": "Unknown"}
                
                relationships.append({
                    "relationship_type": rel_type["name"],
                    "element_name": other_element["name"],
                    "element_type": "Unknown",  # We could get this if needed
                    "direction": "outgoing" if rel["source_element_id"] == element_id else "incoming"
                })
        
        # Compile all data
        element_data = {
            "element": {
                "id": element["id"],
                "name": element["name"],
                "description": element["description"],
                "type": element_type["name"],
                "status": element["status"],
                "properties": element["properties"],
                "model": model["name"],
                "relationships": relationships
            }
        }
        
        return element_data

    def _get_model_data(self, model_id: str, include_diagrams: bool, include_relationships: bool) -> Dict[str, Any]:
        """Get model data from the database.
        
        Args:
            model_id: ID of the model
            include_diagrams: Whether to include diagrams
            include_relationships: Whether to include relationships
            
        Returns:
            Model data dictionary
        """
        # Implementation for getting model data
        # This would be similar to _get_element_data but for models
        # For now, return a placeholder
        return {"model": {"id": model_id, "name": "Model Name"}}

    def _get_view_data(self, view_id: str) -> Dict[str, Any]:
        """Get view data from the database.
        
        Args:
            view_id: ID of the view
            
        Returns:
            View data dictionary
        """
        # Implementation for getting view data
        # This would be similar to the other methods but for views
        # For now, return a placeholder
        return {"view": {"id": view_id, "name": "View Name"}}

    def _get_policy_data(self, policy_id: str) -> Dict[str, Any]:
        """Get policy data from the database.
        
        Args:
            policy_id: ID of the policy
            
        Returns:
            Policy data dictionary
        """
        # Implementation for getting policy data
        # This would be similar to the other methods but for policies
        # For now, return a placeholder
        return {"policy": {"id": policy_id, "name": "Policy Name"}}

    def _generate_with_ai(self, content_data: Dict[str, Any], content_type: str, 
                         format: str, style: str) -> str:
        """Generate documentation using OpenAI.
        
        Args:
            content_data: Content data to document
            content_type: Type of content
            format: Output format
            style: Documentation style
            
        Returns:
            Generated documentation as string
        """
        # Create a prompt based on content type and style
        if content_type == "element":
            element = content_data["element"]
            
            # Build a prompt based on element type and style
            if style == "technical":
                prompt = f"""
                Please create a technical documentation for the {element['type']} '{element['name']}'. 
                
                Description: {element.get('description', 'No description provided')}
                
                Include the following sections:
                1. Overview
                2. Technical Details
                3. Relationships and Dependencies
                4. Implementation Considerations
                """
            elif style == "business":
                prompt = f"""
                Please create a business-focused documentation for the {element['type']} '{element['name']}'. 
                
                Description: {element.get('description', 'No description provided')}
                
                Include the following sections:
                1. Business Purpose
                2. Value Proposition
                3. Stakeholders
                4. Business Processes Supported
                """
            elif style == "executive":
                prompt = f"""
                Please create an executive summary for the {element['type']} '{element['name']}'. 
                
                Description: {element.get('description', 'No description provided')}
                
                Include the following sections:
                1. Strategic Value
                2. Key Benefits
                3. Investment and ROI
                4. Key Recommendations
                """
            else:
                prompt = f"""
                Please create documentation for the {element['type']} '{element['name']}'. 
                
                Description: {element.get('description', 'No description provided')}
                """
            
            # Add relationship information if available
            if element.get('relationships'):
                prompt += "\n\nRelationships:\n"
                for rel in element['relationships']:
                    prompt += f"- {rel['direction'].capitalize()} {rel['relationship_type']} with {rel['element_name']}\n"
        elif content_type == "model":
            model = content_data["model"]
            prompt = f"Create documentation for the model '{model['name']}'"
        elif content_type == "view":
            view = content_data["view"]
            prompt = f"Create documentation for the view '{view['name']}'"
        elif content_type == "policy":
            policy = content_data["policy"]
            prompt = f"Create documentation for the policy '{policy['name']}'"
        else:
            prompt = f"Create documentation for this content: {json.dumps(content_data)}"
            
        # Add format-specific instructions
        if format == "markdown":
            prompt += "\n\nPlease format the documentation in Markdown."
        elif format == "html":
            prompt += "\n\nPlease format the documentation in HTML."
        
        # Get completion from OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert enterprise architecture documentation writer. Your job is to create clear, well-structured documentation based on the provided information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Extract and return the documentation
        return response.choices[0].message.content

    def _format_documentation(self, documentation: str, format: str) -> str:
        """Format documentation according to the requested output format.
        
        Args:
            documentation: Raw documentation content
            format: Output format (markdown, html, docx)
            
        Returns:
            Formatted documentation
        """
        if format == "markdown":
            # Already in markdown format from OpenAI
            return documentation
        elif format == "html":
            # If it's already HTML, return as is
            if documentation.strip().startswith("<"):
                return documentation
            
            # Otherwise, convert markdown to HTML (simple implementation)
            # In a real implementation, you would use a proper markdown to HTML converter
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>EA Documentation</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #2c3e50; }}
                    h2 {{ color: #3498db; }}
                    h3 {{ color: #2980b9; }}
                    pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
                    code {{ background-color: #f5f5f5; padding: 2px 5px; border-radius: 3px; }}
                </style>
            </head>
            <body>
                {documentation.replace('\n', '<br>')}
            </body>
            </html>
            """
            return html
        elif format == "docx":
            # For docx, we would normally use a library like python-docx
            # Here we'll just return a placeholder message
            return "DOCX format not implemented in this version"
        else:
            return documentation

    def _log_generation(self, content_type: str, content_id: str, format: str, style: str):
        """Log documentation generation in the database.
        
        Args:
            content_type: Type of content
            content_id: ID of the content
            format: Output format
            style: Documentation style
        """
        try:
            # Insert a record into the ai_generated_content table
            self.supabase.table("ai_generated_content").insert({
                "content_type": "documentation",
                "prompt": f"Generate {style} documentation in {format} format for {content_type} {content_id}",
                "created_by": self.supabase.auth.get_user().user.id,  # This would need to be passed in or retrieved
                "properties": {
                    "documentation_type": content_type,
                    "related_id": content_id,
                    "format": format,
                    "style": style
                }
            }).execute()
        except Exception as e:
            logger.error(f"Error logging documentation generation: {str(e)}")
            # Continue even if logging fails
            pass
