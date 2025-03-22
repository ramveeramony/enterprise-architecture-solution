"""
Enterprise Architecture Solution - Impact Analysis

This module implements the AI-powered impact analysis capabilities
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

class ImpactAnalysis:
    """Analyze the impact of architecture changes."""
    
    def __init__(self, supabase_client):
        """Initialize the Impact Analysis engine.
        
        Args:
            supabase_client: A configured Supabase client for database operations
        """
        self.supabase = supabase_client
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def analyze_impact(self, element_id: str, change_description: str, 
                     change_type: str, analysis_depth: int = 2) -> Dict[str, Any]:
        """Analyze the impact of a proposed change to an architecture element.
        
        Args:
            element_id: UUID of the element being changed
            change_description: Description of the proposed change
            change_type: Type of change (modify, replace, remove)
            analysis_depth: Depth of impact analysis (1=direct, 2=indirect, 3=comprehensive)
            
        Returns:
            Dict containing the impact analysis results
        """
        try:
            # Get element data
            element_data = self._get_element_data(element_id)
            
            # Get related elements based on analysis depth
            related_elements = self._get_related_elements(element_id, analysis_depth)
            
            # Perform impact analysis using OpenAI
            impact_analysis = self._analyze_with_ai(element_data, related_elements, 
                                                  change_description, change_type)
            
            # Log the analysis
            self._log_analysis(element_id, change_description, change_type, analysis_depth)
            
            return {
                "success": True,
                "impact_analysis": impact_analysis,
                "metadata": {
                    "element_id": element_id,
                    "change_type": change_type,
                    "analysis_depth": analysis_depth,
                    "analyzed_at": datetime.now().isoformat(),
                }
            }
            
        except Exception as e:
            logger.error(f"Error performing impact analysis: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_element_data(self, element_id: str) -> Dict[str, Any]:
        """Get element data from the database.
        
        Args:
            element_id: ID of the element
            
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
        
        # Compile element data
        element_data = {
            "id": element["id"],
            "name": element["name"],
            "description": element["description"],
            "type": element_type["name"],
            "status": element["status"],
            "properties": element["properties"],
            "model": model["name"]
        }
        
        return element_data

    def _get_related_elements(self, element_id: str, depth: int = 2) -> List[Dict[str, Any]]:
        """Get related elements based on analysis depth.
        
        Args:
            element_id: ID of the element
            depth: Depth of relationship analysis
            
        Returns:
            List of related elements with relationship information
        """
        related_elements = []
        
        # Level 1: Direct relationships
        # Get relationships where this element is the source
        source_rels_query = self.supabase.table("ea_relationships").select("*").eq("source_element_id", element_id).execute()
        source_rels = source_rels_query.data if source_rels_query.data else []
        
        # Get relationships where this element is the target
        target_rels_query = self.supabase.table("ea_relationships").select("*").eq("target_element_id", element_id).execute()
        target_rels = target_rels_query.data if target_rels_query.data else []
        
        # Process direct relationships
        level1_element_ids = []
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
                
                related_elements.append({
                    "id": other_element["id"],
                    "name": other_element["name"],
                    "type": element_type["name"],
                    "relationship": rel_type["name"],
                    "direction": "outgoing" if rel["source_element_id"] == element_id else "incoming",
                    "level": 1
                })
                
                level1_element_ids.append(other_id)
        
        # If depth is greater than 1, get indirect relationships
        if depth > 1:
            # For each directly related element, get its relationships
            for related_id in level1_element_ids:
                # Get relationships where this element is the source
                source_rels_query = self.supabase.table("ea_relationships").select("*").eq("source_element_id", related_id).execute()
                source_rels = source_rels_query.data if source_rels_query.data else []
                
                # Get relationships where this element is the target
                target_rels_query = self.supabase.table("ea_relationships").select("*").eq("target_element_id", related_id).execute()
                target_rels = target_rels_query.data if target_rels_query.data else []
                
                # Process level 2 relationships
                for rel in source_rels + target_rels:
                    # Skip relationships with the original element
                    if rel["source_element_id"] == element_id or rel["target_element_id"] == element_id:
                        continue
                    
                    rel_type_query = self.supabase.table("ea_relationship_types").select("*").eq("id", rel["relationship_type_id"]).execute()
                    rel_type = rel_type_query.data[0] if rel_type_query.data else {"name": "Unknown"}
                    
                    # Get the other element in the relationship
                    other_id = rel["target_element_id"] if rel["source_element_id"] == related_id else rel["source_element_id"]
                    other_element_query = self.supabase.table("ea_elements").select("*").eq("id", other_id).execute()
                    
                    if other_element_query.data:
                        other_element = other_element_query.data[0]
                        element_type_query = self.supabase.table("ea_element_types").select("*").eq("id", other_element["type_id"]).execute()
                        element_type = element_type_query.data[0] if element_type_query.data else {"name": "Unknown"}
                        
                        # Check if this is already in our list
                        if not any(e["id"] == other_element["id"] for e in related_elements):
                            related_elements.append({
                                "id": other_element["id"],
                                "name": other_element["name"],
                                "type": element_type["name"],
                                "relationship": f"indirect via {rel_type['name']}",
                                "direction": "secondary",
                                "level": 2
                            })
        
        # If depth is 3, we would continue to get more indirect relationships
        # This could be implemented recursively or iteratively
        # For now, we'll stop at depth 2
        
        return related_elements

    def _analyze_with_ai(self, element_data: Dict[str, Any], 
                        related_elements: List[Dict[str, Any]],
                        change_description: str, change_type: str) -> Dict[str, Any]:
        """Generate impact analysis using OpenAI.
        
        Args:
            element_data: Data about the element being changed
            related_elements: List of related elements
            change_description: Description of the proposed change
            change_type: Type of change (modify, replace, remove)
            
        Returns:
            Dict containing the impact analysis
        """
        # Create a context for the AI
        element_context = {
            "element": element_data,
            "change": {
                "type": change_type,
                "description": change_description
            },
            "related_elements": related_elements
        }
        
        # Create a prompt for the impact analysis
        prompt = f"""
        Please analyze the impact of the following change to an enterprise architecture element:
        
        ELEMENT DETAILS:
        Name: {element_data['name']}
        Type: {element_data['type']}
        Description: {element_data['description']}
        
        PROPOSED CHANGE:
        Type: {change_type}
        Description: {change_description}
        
        RELATED ELEMENTS:
        """
        
        # Add information about related elements
        for rel in related_elements:
            prompt += f"- {rel['name']} ({rel['type']}): {rel['relationship']} relationship, {rel['direction']}, level {rel['level']}\n"
        
        prompt += """
        Please provide a comprehensive impact analysis including:
        1. Direct impacts on related systems, processes, and stakeholders
        2. Potential indirect impacts and cascading effects
        3. Risk assessment (High/Medium/Low) with explanation
        4. Recommended mitigation strategies
        5. Implementation considerations
        """
        
        # Get completion from OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert enterprise architecture analyst specializing in impact analysis. Your job is to assess the potential impacts of architectural changes and provide actionable recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        
        # Extract the analysis
        analysis_text = response.choices[0].message.content
        
        # Now, use a follow-up request to structure the analysis as JSON
        structured_prompt = f"""
        Based on the following impact analysis, please provide a structured JSON response with the following sections:
        1. direct_impacts (array of impact objects with 'area', 'severity', and 'description')
        2. indirect_impacts (array of impact objects with 'area', 'severity', and 'description')
        3. risk_assessment (object with 'overall_risk', 'explanation', and 'factors')
        4. mitigation_strategies (array of strategy objects with 'strategy' and 'description')
        5. implementation_considerations (array of consideration objects with 'area' and 'description')
        
        The analysis is:
        {analysis_text}
        """
        
        # Get structured response
        structured_response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert enterprise architecture analyst specializing in impact analysis. Your task is to structure impact analysis in JSON format."},
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
            structured_analysis = json.loads(json_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, return the unstructured analysis
            structured_analysis = {
                "unstructured_analysis": analysis_text
            }
        
        # Return both the structured analysis and the original text
        return {
            "structured_analysis": structured_analysis,
            "text_analysis": analysis_text,
            "element_context": element_context
        }

    def _log_analysis(self, element_id: str, change_description: str, 
                     change_type: str, analysis_depth: int):
        """Log impact analysis in the database.
        
        Args:
            element_id: ID of the element
            change_description: Description of the change
            change_type: Type of change
            analysis_depth: Depth of analysis
        """
        try:
            # Insert a record into the ai_generated_content table
            self.supabase.table("ai_generated_content").insert({
                "content_type": "analysis",
                "related_element_id": element_id,
                "prompt": f"Analyze impact of {change_type} change: {change_description}",
                "created_by": self.supabase.auth.get_user().user.id,  # This would need to be passed in or retrieved
                "properties": {
                    "change_type": change_type,
                    "analysis_depth": analysis_depth
                }
            }).execute()
        except Exception as e:
            logger.error(f"Error logging impact analysis: {str(e)}")
            # Continue even if logging fails
            pass
