"""
Enterprise Architecture Solution - Impact Analysis

This module implements the GenAI-powered impact analysis capabilities.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImpactAnalysis:
    """Class for analyzing the impact of architecture changes."""
    
    def __init__(self, supabase_client, openai_client=None):
        """Initialize the impact analyzer.
        
        Args:
            supabase_client: A configured Supabase client for database operations
            openai_client: Optional pre-configured OpenAI client
        """
        self.supabase = supabase_client
        self.openai = openai_client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def analyze_element_change(self, element_id: str, 
                              change_description: str,
                              change_type: str = "modify",
                              analysis_depth: int = 2) -> Dict[str, Any]:
        """Analyze the impact of a change to an EA element.
        
        Args:
            element_id: UUID of the element being changed
            change_description: Description of the proposed change
            change_type: Type of change (modify, replace, remove)
            analysis_depth: Depth of impact analysis (1=direct, 2=indirect, 3=comprehensive)
            
        Returns:
            Dictionary containing the impact analysis results
        """
        try:
            # Validate parameters
            valid_change_types = ["modify", "replace", "remove"]
            if change_type not in valid_change_types:
                return {
                    "success": False,
                    "error": f"Invalid change_type: {change_type}. Must be one of {valid_change_types}"
                }
            
            if analysis_depth < 1 or analysis_depth > 3:
                return {
                    "success": False,
                    "error": f"Invalid analysis_depth: {analysis_depth}. Must be between 1 and 3"
                }
            
            # Fetch the element being changed
            element_query = self.supabase.table("ea_elements").select(
                "*"
            ).eq("id", element_id).execute()
            
            if not element_query.data:
                return {
                    "success": False,
                    "error": f"Element with ID {element_id} not found"
                }
            
            element = element_query.data[0]
            
            # Get element type information
            element_type_query = self.supabase.table("ea_element_types").select(
                "*"
            ).eq("id", element["type_id"]).execute()
            
            element_type = element_type_query.data[0] if element_type_query.data else None
            
            # Identify affected elements based on analysis depth
            affected_elements = []
            
            # Level 1: Directly connected elements (through relationships)
            direct_relationships = self._get_element_relationships(element_id)
            direct_elements = self._get_related_elements(direct_relationships)
            affected_elements.extend(direct_elements)
            
            # Level 2: Indirectly connected elements (second-degree relationships)
            if analysis_depth >= 2:
                indirect_elements = []
                for related_element in direct_elements:
                    # Skip self-references
                    if related_element["id"] == element_id:
                        continue
                    
                    # Get relationships for this related element
                    related_relationships = self._get_element_relationships(related_element["id"])
                    related_indirect_elements = self._get_related_elements(related_relationships)
                    
                    # Add unique elements only
                    for indirect_element in related_indirect_elements:
                        if indirect_element["id"] != element_id and not any(e["id"] == indirect_element["id"] for e in affected_elements):
                            indirect_element["impact_level"] = "indirect"
                            indirect_elements.append(indirect_element)
                
                affected_elements.extend(indirect_elements)
            
            # Level 3: Comprehensive analysis (third-degree relationships and domain analysis)
            if analysis_depth >= 3:
                # Get elements in the same domain
                if element_type:
                    domain_id = element_type.get("domain_id")
                    if domain_id:
                        domain_elements_query = self.supabase.table("ea_elements").select(
                            "*"
                        ).eq("domain_id", domain_id).neq("id", element_id).execute()
                        
                        domain_elements = domain_elements_query.data if domain_elements_query.data else []
                        
                        for domain_element in domain_elements:
                            if not any(e["id"] == domain_element["id"] for e in affected_elements):
                                domain_element["impact_level"] = "domain"
                                affected_elements.append(domain_element)
            
            # Prepare context for AI analysis
            context = {
                "element": {
                    "id": element["id"],
                    "name": element["name"],
                    "description": element["description"],
                    "type": element_type["name"] if element_type else "Unknown",
                    "properties": element["properties"]
                },
                "change": {
                    "type": change_type,
                    "description": change_description
                },
                "affected_elements": affected_elements,
                "analysis_depth": analysis_depth
            }
            
            # Generate impact analysis using OpenAI
            analysis_result = self._generate_impact_analysis(context)
            
            # Save the analysis result to the database
            analysis_id = self._save_analysis_result(element_id, change_description, change_type, analysis_result)
            
            return {
                "success": True,
                "analysis_id": analysis_id,
                "element_id": element_id,
                "change_type": change_type,
                "analysis_depth": analysis_depth,
                "affected_elements_count": len(affected_elements),
                "analysis": analysis_result,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing element change: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_element_relationships(self, element_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for an element.
        
        Args:
            element_id: UUID of the element
            
        Returns:
            List of relationship dictionaries
        """
        # Fetch relationships where this element is the source
        source_relationships = self.supabase.table("ea_relationships").select(
            "*"
        ).eq("source_element_id", element_id).execute()
        
        # Fetch relationships where this element is the target
        target_relationships = self.supabase.table("ea_relationships").select(
            "*"
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
        
        return relationships
    
    def _get_related_elements(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get elements related through relationships.
        
        Args:
            relationships: List of relationship dictionaries
            
        Returns:
            List of related element dictionaries
        """
        related_elements = []
        element_ids = set()
        
        for relationship in relationships:
            # Determine the related element ID based on relationship direction
            related_id = None
            if relationship.get("direction") == "outgoing":
                related_id = relationship.get("target_element_id")
            elif relationship.get("direction") == "incoming":
                related_id = relationship.get("source_element_id")
            
            if related_id and related_id not in element_ids:
                element_ids.add(related_id)
                
                # Fetch the related element
                element_query = self.supabase.table("ea_elements").select(
                    "*"
                ).eq("id", related_id).execute()
                
                if element_query.data:
                    element = element_query.data[0]
                    element["impact_level"] = "direct"
                    element["relationship"] = {
                        "id": relationship.get("id"),
                        "type_id": relationship.get("relationship_type_id"),
                        "name": relationship.get("name"),
                        "direction": relationship.get("direction")
                    }
                    related_elements.append(element)
        
        return related_elements
    
    def _generate_impact_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate impact analysis using OpenAI.
        
        Args:
            context: Context dictionary with element and change data
            
        Returns:
            Impact analysis results
        """
        # Create a prompt for OpenAI
        prompt = f"""
        Analyze the impact of the following change to an enterprise architecture element:
        
        Element Information:
        - Name: {context['element']['name']}
        - Type: {context['element']['type']}
        - Description: {context['element']['description']}
        
        Proposed Change:
        - Change Type: {context['change']['type']} (modify, replace, or remove)
        - Change Description: {context['change']['description']}
        
        Analysis Depth: {context['analysis_depth']} (1=direct, 2=indirect, 3=comprehensive)
        
        Affected Elements:
        {json.dumps([{
            "id": e.get("id"),
            "name": e.get("name"),
            "type": e.get("type"),
            "impact_level": e.get("impact_level"),
            "relationship": e.get("relationship")
        } for e in context['affected_elements']], indent=2)}
        
        Please provide a structured impact analysis with the following sections:
        1. Executive Summary: A brief overview of the change and its potential impact
        2. Impact Rating: A 1-5 scale rating (1=minimal, 5=severe) with justification
        3. Affected Elements Analysis: Detailed analysis of how each affected element may be impacted
        4. Risks and Issues: Potential risks and issues resulting from the change
        5. Recommendations: Recommendations for mitigating risks and implementing the change effectively
        
        Format your response as a structured JSON object following this schema:
        {
            "executive_summary": "text",
            "impact_rating": number,
            "impact_justification": "text",
            "affected_elements_analysis": [
                {
                    "element_id": "id",
                    "element_name": "name",
                    "impact_description": "description of impact",
                    "impact_severity": "Low/Medium/High"
                }
            ],
            "risks_and_issues": [
                {
                    "description": "risk description",
                    "severity": "Low/Medium/High",
                    "mitigation": "mitigation approach"
                }
            ],
            "recommendations": [
                "recommendation text"
            ]
        }
        """
        
        # Call OpenAI API
        response = self.openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert Enterprise Architecture impact analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        
        # Extract the generated content
        analysis_text = response.choices[0].message.content
        
        # Parse the JSON response
        try:
            # Clean up the text to ensure it's valid JSON
            json_text = analysis_text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            
            analysis = json.loads(json_text)
            return analysis
        except Exception as e:
            logger.error(f"Error parsing analysis JSON: {str(e)}")
            return {
                "error": "Failed to parse analysis JSON",
                "raw_analysis": analysis_text
            }
    
    def _save_analysis_result(self, element_id: str, change_description: str, 
                             change_type: str, analysis: Dict[str, Any]) -> str:
        """Save the impact analysis result to the database.
        
        Args:
            element_id: UUID of the element being changed
            change_description: Description of the proposed change
            change_type: Type of change
            analysis: Analysis results dictionary
            
        Returns:
            UUID of the saved analysis
        """
        try:
            now = datetime.now().isoformat()
            analysis_id = str(uuid.uuid4())
            
            # Insert new analysis
            result = self.supabase.table("ai_generated_content").insert({
                "id": analysis_id,
                "content_type": "analysis",
                "related_element_id": element_id,
                "content": json.dumps(analysis),
                "prompt": f"Analyze impact of {change_type} change: {change_description}",
                "properties": {
                    "change_type": change_type,
                    "change_description": change_description,
                    "impact_rating": analysis.get("impact_rating"),
                    "created_at": now
                },
                "applied": False,
                "created_at": now,
                "updated_at": now
            }).execute()
            
            return analysis_id
                
        except Exception as e:
            logger.error(f"Error saving impact analysis: {str(e)}")
            return None
