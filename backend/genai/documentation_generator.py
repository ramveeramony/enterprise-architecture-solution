"""
Enterprise Architecture Solution - Documentation Generator

This module implements the GenAI-powered documentation generation capabilities.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from openai import OpenAI
from markdown import Markdown

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentationGenerator:
    """Class for generating documentation from EA artifacts."""
    
    def __init__(self, supabase_client, openai_client=None):
        """Initialize the documentation generator.
        
        Args:
            supabase_client: A configured Supabase client for database operations
            openai_client: Optional pre-configured OpenAI client
        """
        self.supabase = supabase_client
        self.openai = openai_client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def generate_element_documentation(self, element_id: str, 
                                      format: str = "markdown",
                                      style: str = "technical",
                                      include_relationships: bool = True) -> Dict[str, Any]:
        """Generate documentation for an EA element.
        
        Args:
            element_id: UUID of the element to document
            format: Output format (markdown, html, docx)
            style: Documentation style (technical, business, executive)
            include_relationships: Whether to include relationships in the documentation
            
        Returns:
            Dictionary containing the generated documentation and metadata
        """
        try:
            # Fetch the element data from Supabase
            element_query = self.supabase.table("ea_elements").select(
                "*"
            ).eq("id", element_id).execute()
            
            if not element_query.data:
                return {
                    "success": False,
                    "error": f"Element with ID {element_id} not found"
                }
            
            element = element_query.data[0]
            
            # Fetch element type information
            element_type_query = self.supabase.table("ea_element_types").select(
                "*"
            ).eq("id", element["type_id"]).execute()
            
            element_type = element_type_query.data[0] if element_type_query.data else None
            
            # Fetch relationships if requested
            relationships = []
            if include_relationships:
                # Fetch relationships where this element is the source
                source_relationships = self.supabase.table("ea_relationships").select(
                    "id", "name", "description", "relationship_type_id", "target_element_id", "properties"
                ).eq("source_element_id", element_id).execute()
                
                # Fetch relationships where this element is the target
                target_relationships = self.supabase.table("ea_relationships").select(
                    "id", "name", "description", "relationship_type_id", "source_element_id", "properties"
                ).eq("target_element_id", element_id).execute()
                
                # Combine relationships data
                relationships = []
                if source_relationships.data:
                    for rel in source_relationships.data:
                        rel["direction"] = "outgoing"
                        relationships.append(rel)
                
                if target_relationships.data:
                    for rel in target_relationships.data:
                        rel["direction"] = "incoming"
                        relationships.append(rel)
            
            # Prepare context for AI generation
            context = {
                "element": {
                    "id": element["id"],
                    "name": element["name"],
                    "description": element["description"],
                    "type": element_type["name"] if element_type else "Unknown",
                    "properties": element["properties"],
                    "status": element["status"]
                },
                "relationships": relationships,
                "style": style,
                "format": format
            }
            
            # Generate documentation using OpenAI
            documentation = self._generate_with_ai(context)
            
            # Format the documentation based on the requested output format
            formatted_documentation = self._format_documentation(documentation, format)
            
            # Save the generated documentation to the database
            doc_id = self._save_documentation(element_id, "element", formatted_documentation, format, style)
            
            return {
                "success": True,
                "documentation_id": doc_id,
                "content": formatted_documentation,
                "format": format,
                "element_id": element_id,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating documentation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def generate_model_documentation(self, model_id: str,
                                    format: str = "markdown",
                                    style: str = "technical",
                                    include_diagrams: bool = True) -> Dict[str, Any]:
        """Generate documentation for an EA model.
        
        Args:
            model_id: UUID of the model to document
            format: Output format (markdown, html, docx)
            style: Documentation style (technical, business, executive)
            include_diagrams: Whether to include diagrams in the documentation
            
        Returns:
            Dictionary containing the generated documentation and metadata
        """
        try:
            # Fetch the model data from Supabase
            model_query = self.supabase.table("ea_models").select(
                "*"
            ).eq("id", model_id).execute()
            
            if not model_query.data:
                return {
                    "success": False,
                    "error": f"Model with ID {model_id} not found"
                }
            
            model = model_query.data[0]
            
            # Fetch elements in this model
            elements_query = self.supabase.table("ea_elements").select(
                "*"
            ).eq("model_id", model_id).execute()
            
            elements = elements_query.data if elements_query.data else []
            
            # Fetch relationships in this model
            relationships_query = self.supabase.table("ea_relationships").select(
                "*"
            ).eq("model_id", model_id).execute()
            
            relationships = relationships_query.data if relationships_query.data else []
            
            # Fetch views/diagrams if requested
            views = []
            if include_diagrams:
                views_query = self.supabase.table("ea_views").select(
                    "*"
                ).eq("model_id", model_id).execute()
                
                views = views_query.data if views_query.data else []
            
            # Prepare context for AI generation
            context = {
                "model": {
                    "id": model["id"],
                    "name": model["name"],
                    "description": model["description"],
                    "version": model["version"],
                    "lifecycle_state": model["lifecycle_state"],
                    "status": model["status"],
                    "properties": model["properties"]
                },
                "elements": elements,
                "relationships": relationships,
                "views": views,
                "style": style,
                "format": format
            }
            
            # Generate documentation using OpenAI
            documentation = self._generate_model_documentation_with_ai(context)
            
            # Format the documentation based on the requested output format
            formatted_documentation = self._format_documentation(documentation, format)
            
            # Save the generated documentation to the database
            doc_id = self._save_documentation(model_id, "model", formatted_documentation, format, style)
            
            return {
                "success": True,
                "documentation_id": doc_id,
                "content": formatted_documentation,
                "format": format,
                "model_id": model_id,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating model documentation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_with_ai(self, context: Dict[str, Any]) -> str:
        """Generate documentation content using OpenAI.
        
        Args:
            context: Context dictionary with element data
            
        Returns:
            Generated documentation content
        """
        style_descriptions = {
            "technical": "Detailed technical documentation with comprehensive specifications",
            "business": "Business-focused documentation emphasizing value and processes",
            "executive": "High-level executive summary focusing on strategic aspects"
        }
        
        style_description = style_descriptions.get(context["style"], style_descriptions["technical"])
        
        # Create a prompt for OpenAI
        prompt = f"""
        Generate {style_description} for the following enterprise architecture element:
        
        Name: {context['element']['name']}
        Type: {context['element']['type']}
        Description: {context['element']['description']}
        Status: {context['element']['status']}
        
        Additional Properties:
        {json.dumps(context['element']['properties'], indent=2)}
        
        Relationships:
        {json.dumps(context['relationships'], indent=2) if context['relationships'] else 'None'}
        
        The documentation should follow these guidelines:
        - Format: {context['format']}
        - Style: {context['style']}
        - Include a clear title and structured sections
        - For technical style, include detailed specifications and technical dependencies
        - For business style, emphasize business value, processes, and outcomes
        - For executive style, focus on strategic importance and high-level insights
        - Include appropriate headings, lists, and tables as needed
        - Be comprehensive but concise
        
        Generate only the documentation content, formatted appropriately.
        """
        
        # Call OpenAI API
        response = self.openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert Enterprise Architecture documentation specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        
        # Extract and return the generated content
        return response.choices[0].message.content
    
    def _generate_model_documentation_with_ai(self, context: Dict[str, Any]) -> str:
        """Generate model documentation content using OpenAI.
        
        Args:
            context: Context dictionary with model data
            
        Returns:
            Generated documentation content
        """
        style_descriptions = {
            "technical": "Detailed technical documentation with comprehensive specifications",
            "business": "Business-focused documentation emphasizing value and processes",
            "executive": "High-level executive summary focusing on strategic aspects"
        }
        
        style_description = style_descriptions.get(context["style"], style_descriptions["technical"])
        
        # Create a summary of elements by type
        element_types = {}
        for element in context["elements"]:
            element_type = element.get("type_id", "unknown")
            if element_type not in element_types:
                element_types[element_type] = []
            element_types[element_type].append(element["name"])
        
        # Create a prompt for OpenAI
        prompt = f"""
        Generate {style_description} for the following enterprise architecture model:
        
        Name: {context['model']['name']}
        Description: {context['model']['description']}
        Version: {context['model']['version']}
        Lifecycle State: {context['model']['lifecycle_state']}
        Status: {context['model']['status']}
        
        The model contains:
        - {len(context['elements'])} elements
        - {len(context['relationships'])} relationships
        - {len(context['views'])} views/diagrams
        
        The documentation should follow these guidelines:
        - Format: {context['format']}
        - Style: {context['style']}
        - Include a clear title and structured sections
        - Provide an executive summary at the beginning
        - Include sections on purpose, scope, and key components
        - For technical style, include detailed architecture patterns and technical components
        - For business style, emphasize business capabilities and processes
        - For executive style, focus on strategic alignment and business outcomes
        - Include appropriate headings, lists, and tables as needed
        - Be comprehensive but concise
        
        Generate only the documentation content, formatted appropriately.
        """
        
        # Call OpenAI API
        response = self.openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert Enterprise Architecture documentation specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        # Extract and return the generated content
        return response.choices[0].message.content
    
    def _format_documentation(self, content: str, format: str) -> str:
        """Format the documentation based on the requested output format.
        
        Args:
            content: Raw documentation content
            format: Output format (markdown, html, docx)
            
        Returns:
            Formatted documentation content
        """
        if format == "markdown":
            # Already in markdown format
            return content
        
        elif format == "html":
            # Convert markdown to HTML
            md = Markdown()
            return md.convert(content)
        
        elif format == "docx":
            # In a real implementation, we would use a library like python-docx
            # For this example, we'll just return markdown with a note
            return f"# DOCX Format\n\n{content}\n\n_This content would be converted to DOCX format in production._"
        
        else:
            # Default to markdown
            return content
    
    def _save_documentation(self, entity_id: str, entity_type: str, 
                           content: str, format: str, style: str) -> str:
        """Save the generated documentation to the database.
        
        Args:
            entity_id: UUID of the entity (element, model, etc.)
            entity_type: Type of entity (element, model, view, policy)
            content: Documentation content
            format: Output format
            style: Documentation style
            
        Returns:
            UUID of the saved documentation
        """
        try:
            # Check if documentation for this entity already exists
            existing_query = self.supabase.table("ai_generated_content").select(
                "id"
            ).eq("content_type", "documentation").eq(
                f"related_{entity_type}_id", entity_id
            ).execute()
            
            now = datetime.now().isoformat()
            
            if existing_query.data:
                # Update existing documentation
                doc_id = existing_query.data[0]["id"]
                self.supabase.table("ai_generated_content").update({
                    "content": content,
                    "properties": {
                        "format": format,
                        "style": style,
                        "updated_at": now
                    },
                    "updated_at": now
                }).eq("id", doc_id).execute()
                
                return doc_id
            else:
                # Insert new documentation
                result = self.supabase.table("ai_generated_content").insert({
                    "content_type": "documentation",
                    f"related_{entity_type}_id": entity_id,
                    "content": content,
                    "prompt": f"Generate {style} documentation for {entity_type} {entity_id}",
                    "properties": {
                        "format": format,
                        "style": style,
                        "created_at": now
                    },
                    "applied": True,
                    "created_at": now,
                    "updated_at": now
                }).execute()
                
                return result.data[0]["id"] if result.data else None
                
        except Exception as e:
            logger.error(f"Error saving documentation: {str(e)}")
            return None
