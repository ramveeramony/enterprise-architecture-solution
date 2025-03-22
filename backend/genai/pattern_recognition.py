"""
Enterprise Architecture Solution - Pattern Recognition

This module implements the AI-powered pattern recognition capabilities
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

class PatternRecognition:
    """Recognize architecture patterns and suggest improvements."""
    
    def __init__(self, supabase_client):
        """Initialize the Pattern Recognition engine.
        
        Args:
            supabase_client: A configured Supabase client for database operations
        """
        self.supabase = supabase_client
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def recognize_patterns(self, model_id: str, element_ids: Optional[List[str]] = None,
                         domain_filter: Optional[str] = None, 
                         pattern_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Recognize patterns in architecture elements.
        
        Args:
            model_id: UUID of the model to analyze
            element_ids: Optional list of specific element IDs to analyze
            domain_filter: Optional domain to filter by
            pattern_types: Optional list of pattern types to look for
            
        Returns:
            Dict containing the recognized patterns
        """
        try:
            # Get model data
            model_data = self._get_model_data(model_id)
            
            # Get elements to analyze
            elements = self._get_elements_to_analyze(model_id, element_ids, domain_filter)
            
            if not elements:
                return {
                    "success": False,
                    "error": "No elements found for analysis"
                }
            
            # Set default pattern types if not specified
            if not pattern_types:
                pattern_types = ["best_practice", "anti_pattern", "optimization", "security", "integration"]
                
            # Perform pattern recognition using OpenAI
            patterns = self._recognize_with_ai(model_data, elements, pattern_types)
            
            # Log the pattern recognition
            self._log_recognition(model_id, element_ids, domain_filter, pattern_types)
            
            return {
                "success": True,
                "patterns": patterns,
                "metadata": {
                    "model_id": model_id,
                    "elements_analyzed": len(elements),
                    "domain_filter": domain_filter,
                    "pattern_types": pattern_types,
                    "analyzed_at": datetime.now().isoformat(),
                }
            }
            
        except Exception as e:
            logger.error(f"Error performing pattern recognition: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_model_data(self, model_id: str) -> Dict[str, Any]:
        """Get model data from the database.
        
        Args:
            model_id: ID of the model
            
        Returns:
            Model data dictionary
        """
        # Query the model table
        model_query = self.supabase.table("ea_models").select("*").eq("id", model_id).execute()
        
        if not model_query.data:
            raise ValueError(f"Model with ID {model_id} not found")
            
        model = model_query.data[0]
        
        # Compile model data
        model_data = {
            "id": model["id"],
            "name": model["name"],
            "description": model["description"],
            "status": model["status"],
            "lifecycle_state": model["lifecycle_state"],
            "properties": model["properties"]
        }
        
        return model_data

    def _get_elements_to_analyze(self, model_id: str, element_ids: Optional[List[str]] = None,
                               domain_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get elements to analyze based on filters.
        
        Args:
            model_id: ID of the model
            element_ids: Optional list of specific element IDs
            domain_filter: Optional domain to filter by
            
        Returns:
            List of elements to analyze
        """
        elements = []
        
        # Build the query
        query = self.supabase.table("ea_elements").select("*").eq("model_id", model_id)
        
        # Apply element ID filter if provided
        if element_ids:
            query = query.in_("id", element_ids)
            
        # Execute the query
        elements_query = query.execute()
        element_items = elements_query.data if elements_query.data else []
        
        # Process each element
        for element in element_items:
            # Get element type
            element_type_query = self.supabase.table("ea_element_types").select("*").eq("id", element["type_id"]).execute()
            element_type = element_type_query.data[0] if element_type_query.data else {"name": "Unknown", "domain_id": None}
            
            # Apply domain filter if provided
            if domain_filter:
                # Get domain for this element type
                domain_query = self.supabase.table("ea_domains").select("*").eq("id", element_type["domain_id"]).execute()
                domain = domain_query.data[0] if domain_query.data else {"name": "Unknown"}
                
                # Skip if domain doesn't match
                if domain["name"].lower() != domain_filter.lower():
                    continue
            
            # Get relationships for this element
            relationships = self._get_element_relationships(element["id"])
            
            elements.append({
                "id": element["id"],
                "name": element["name"],
                "description": element["description"],
                "type": element_type["name"],
                "status": element["status"],
                "properties": element["properties"],
                "relationships": relationships
            })
        
        return elements

    def _get_element_relationships(self, element_id: str) -> List[Dict[str, Any]]:
        """Get relationships for an element.
        
        Args:
            element_id: ID of the element
            
        Returns:
            List of relationships
        """
        relationships = []
        
        # Get relationships where this element is the source
        source_rels_query = self.supabase.table("ea_relationships").select("*").eq("source_element_id", element_id).execute()
        source_rels = source_rels_query.data if source_rels_query.data else []
        
        # Get relationships where this element is the target
        target_rels_query = self.supabase.table("ea_relationships").select("*").eq("target_element_id", element_id).execute()
        target_rels = target_rels_query.data if target_rels_query.data else []
        
        # Process relationships
        for rel in source_rels + target_rels:
            rel_type_query = self.supabase.table("ea_relationship_types").select("*").eq("id", rel["relationship_type_id"]).execute()
            rel_type = rel_type_query.data[0] if rel_type_query.data else {"name": "Unknown"}
            
            # Get the other element in the relationship
            other_id = rel["target_element_id"] if rel["source_element_id"] == element_id else rel["source_element_id"]
            other_element_query = self.supabase.table("ea_elements").select("*").eq("id", other_id).execute()
            
            if other_element_query.data:
                other_element = other_element_query.data[0]
                element_type_query = self.supabase.table("ea_element_types").select("*").eq("id", other_element["type_id"]).execute()
                element_type = element_type_query.data[0] if element_type_query.data else {"name": "Unknown"}
                
                relationships.append({
                    "id": rel["id"],
                    "type": rel_type["name"],
                    "direction": "outgoing" if rel["source_element_id"] == element_id else "incoming",
                    "element": {
                        "id": other_element["id"],
                        "name": other_element["name"],
                        "type": element_type["name"]
                    }
                })
        
        return relationships

    def _recognize_with_ai(self, model_data: Dict[str, Any], 
                          elements: List[Dict[str, Any]],
                          pattern_types: List[str]) -> Dict[str, Any]:
        """Recognize patterns using OpenAI.
        
        Args:
            model_data: Data about the model
            elements: List of elements to analyze
            pattern_types: Types of patterns to look for
            
        Returns:
            Dict containing the recognized patterns
        """
        # Create a context for the AI
        analysis_context = {
            "model": model_data,
            "elements": elements,
            "pattern_types": pattern_types
        }
        
        # Create a prompt for pattern recognition
        prompt = f"""
        Please analyze the following enterprise architecture model and elements for patterns:
        
        MODEL DETAILS:
        Name: {model_data['name']}
        Description: {model_data['description']}
        Lifecycle State: {model_data['lifecycle_state']}
        
        ELEMENTS TO ANALYZE:
        """
        
        # Add information about elements
        for element in elements:
            prompt += f"\n- {element['name']} ({element['type']})\n"
            prompt += f"  Description: {element['description']}\n"
            prompt += "  Relationships:\n"
            
            for rel in element['relationships']:
                prompt += f"    - {rel['direction']} {rel['type']} with {rel['element']['name']} ({rel['element']['type']})\n"
        
        prompt += f"""
        Please identify the following types of patterns:
        {', '.join(pattern_types)}
        
        For each pattern identified, provide:
        1. Pattern name and type
        2. Elements involved
        3. Description of the pattern
        4. Whether it's a positive pattern (best practice) or negative pattern (anti-pattern)
        5. Recommendations for improvement or optimization
        """
        
        # Get completion from OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert enterprise architect specializing in pattern recognition. Your job is to identify architectural patterns, evaluate them against best practices, and suggest improvements."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        # Extract the pattern analysis
        pattern_text = response.choices[0].message.content
        
        # Now, use a follow-up request to structure the patterns as JSON
        structured_prompt = f"""
        Based on the following pattern analysis, please provide a structured JSON response with the following format:
        
        {{
          "patterns": [
            {{
              "name": "Pattern name",
              "type": "One of: best_practice, anti_pattern, optimization, security, integration",
              "elements": ["Element1", "Element2"],
              "description": "Pattern description",
              "is_positive": true or false,
              "recommendations": ["Recommendation 1", "Recommendation 2"]
            }}
          ]
        }}
        
        The pattern analysis is:
        {pattern_text}
        """
        
        # Get structured response
        structured_response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert enterprise architect specializing in pattern recognition. Your task is to structure pattern analysis in JSON format."},
                {"role": "user", "content": structured_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # Extract the JSON structure
        json_text = structured_response.choices[0].message.content
        
        # Clean up the JSON string by removing markdown code blocks if present
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()
        
        try:
            # Parse the JSON
            structured_patterns = json.loads(json_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, return the unstructured analysis
            structured_patterns = {
                "patterns": [
                    {
                        "name": "Unstructured Analysis",
                        "type": "unknown",
                        "description": pattern_text,
                        "is_positive": False,
                        "recommendations": ["Please review the unstructured analysis"]
                    }
                ]
            }
        
        # Return both the structured patterns and the original text
        return {
            "structured_patterns": structured_patterns,
            "text_analysis": pattern_text
        }

    def _log_recognition(self, model_id: str, element_ids: Optional[List[str]],
                        domain_filter: Optional[str], pattern_types: Optional[List[str]]):
        """Log pattern recognition in the database.
        
        Args:
            model_id: ID of the model
            element_ids: Optional list of element IDs
            domain_filter: Optional domain filter
            pattern_types: Optional pattern types
        """
        try:
            # Insert a record into the ai_generated_content table
            self.supabase.table("ai_generated_content").insert({
                "content_type": "pattern",
                "related_model_id": model_id,
                "prompt": f"Recognize patterns in model {model_id}",
                "created_by": self.supabase.auth.get_user().user.id,  # This would need to be passed in or retrieved
                "properties": {
                    "element_ids": element_ids,
                    "domain_filter": domain_filter,
                    "pattern_types": pattern_types
                }
            }).execute()
        except Exception as e:
            logger.error(f"Error logging pattern recognition: {str(e)}")
            # Continue even if logging fails
            pass
