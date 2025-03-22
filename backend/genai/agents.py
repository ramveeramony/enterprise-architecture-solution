"""
Enterprise Architecture GenAI Module

This module implements GenAI capabilities for the Enterprise Architecture Solution using
OpenAI's Agents Python SDK. It provides multiple specialized agents for different EA tasks.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# OpenAI imports
from openai import OpenAI
from openai.agents import Agent, Step, Tool, run
from openai.types import FunctionDefinition

# Pydantic for schema validation
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Base Schema Models for EA Artifacts
class ElementBase(BaseModel):
    """Base schema for EA elements."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    domain: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class RelationshipBase(BaseModel):
    """Base schema for EA relationships."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class ViewBase(BaseModel):
    """Base schema for EA views."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    type: str
    element_ids: List[str] = Field(default_factory=list)
    relationship_ids: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)


# Agent Tools
class ElementTool(Tool):
    """Tool for working with EA elements."""
    
    def __init__(self, supabase_client):
        """Initialize the Element Tool."""
        self.supabase = supabase_client
        super().__init__(
            name="element_tool",
            description="Create, update, and retrieve enterprise architecture elements",
            function=FunctionDefinition(
                name="manage_ea_element",
                description="Perform operations on EA elements",
                parameters={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["create", "update", "get", "recommend", "analyze"],
                            "description": "The action to perform"
                        },
                        "element_id": {
                            "type": "string",
                            "description": "UUID of the element (for update/get operations)"
                        },
                        "domain": {
                            "type": "string",
                            "enum": ["business", "data", "application", "technology", "performance"],
                            "description": "The architecture domain"
                        },
                        "element_type": {
                            "type": "string",
                            "description": "Type of element (e.g., 'process', 'service', 'database')"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the element"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the element"
                        },
                        "properties": {
                            "type": "object",
                            "description": "Additional properties for the element"
                        }
                    },
                    "required": ["action"]
                }
            )
        )
    
    def execute(self, action: str, element_id: Optional[str] = None, 
                domain: Optional[str] = None, element_type: Optional[str] = None,
                name: Optional[str] = None, description: Optional[str] = None,
                properties: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute the Element Tool."""
        try:
            if action == "create":
                return self._create_element(domain, element_type, name, description, properties)
            elif action == "update":
                return self._update_element(element_id, name, description, properties)
            elif action == "get":
                return self._get_element(element_id)
            elif action == "recommend":
                return self._recommend_element(domain, element_type, name, description)
            elif action == "analyze":
                return self._analyze_element(element_id)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error(f"Error in Element Tool: {str(e)}")
            return {"error": str(e)}
    
    def _create_element(self, domain: str, element_type: str, name: str, 
                       description: str, properties: Dict) -> Dict[str, Any]:
        """Create a new EA element."""
        try:
            # Prepare element data
            element_data = {
                "domain": domain,
                "type": element_type,
                "name": name,
                "description": description,
                "properties": properties or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Insert into Supabase
            result = self.supabase.table("ea_elements").insert(element_data).execute()
            
            if result.data and len(result.data) > 0:
                return {
                    "success": True,
                    "element": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to create element"
                }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _update_element(self, element_id: str, name: Optional[str] = None, 
                       description: Optional[str] = None, 
                       properties: Optional[Dict] = None) -> Dict[str, Any]:
        """Update an existing EA element."""
        try:
            # Prepare update data
            update_data = {
                "updated_at": datetime.now().isoformat()
            }
            
            if name:
                update_data["name"] = name
            
            if description:
                update_data["description"] = description
                
            if properties:
                # Get current properties and update them
                current = self.supabase.table("ea_elements").select("properties").eq("id", element_id).execute()
                if current.data and len(current.data) > 0:
                    current_props = current.data[0].get("properties", {})
                    # Merge properties
                    merged_props = {**current_props, **properties}
                    update_data["properties"] = merged_props
            
            # Update in Supabase
            result = self.supabase.table("ea_elements").update(update_data).eq("id", element_id).execute()
            
            if result.data and len(result.data) > 0:
                return {
                    "success": True,
                    "element": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to update element or element not found"
                }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _get_element(self, element_id: str) -> Dict[str, Any]:
        """Get an EA element by ID."""
        try:
            result = self.supabase.table("ea_elements").select("*").eq("id", element_id).execute()
            
            if result.data and len(result.data) > 0:
                return {
                    "success": True,
                    "element": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "message": "Element not found"
                }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _recommend_element(self, domain: str, element_type: str, 
                          name: str, description: str) -> Dict[str, Any]:
        """Recommend improvements to an EA element."""
        try:
            # Create context for the AI
            context = {
                "domain": domain,
                "element_type": element_type,
                "name": name,
                "description": description,
            }
            
            # Call OpenAI for recommendations
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an Enterprise Architecture expert advisor. Your task is to provide recommendations to improve architecture elements based on best practices."},
                    {"role": "user", "content": f"Please provide recommendations to improve this enterprise architecture element: {json.dumps(context)}"}
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            recommendation = response.choices[0].message.content
            
            # Log the recommendation activity
            self._log_ai_activity("recommendation", name, recommendation)
            
            return {
                "success": True,
                "recommendation": recommendation
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _analyze_element(self, element_id: str) -> Dict[str, Any]:
        """Analyze an EA element and provide insights."""
        try:
            # Get the element
            element_result = self.supabase.table("ea_elements").select("*").eq("id", element_id).execute()
            
            if not element_result.data or len(element_result.data) == 0:
                return {
                    "success": False,
                    "message": "Element not found"
                }
            
            element = element_result.data[0]
            
            # Get related elements (relationships)
            relationships_result = self.supabase.table("ea_relationships").select("*").or_(
                f"source_element_id.eq.{element_id},target_element_id.eq.{element_id}"
            ).execute()
            
            related_elements = []
            if relationships_result.data:
                for relationship in relationships_result.data:
                    other_id = relationship["source_element_id"] if relationship["target_element_id"] == element_id else relationship["target_element_id"]
                    other_element = self.supabase.table("ea_elements").select("*").eq("id", other_id).execute()
                    if other_element.data and len(other_element.data) > 0:
                        related_elements.append({
                            "element": other_element.data[0],
                            "relationship": relationship
                        })
            
            # Create context for the AI
            context = {
                "element": element,
                "related_elements": related_elements
            }
            
            # Call OpenAI for analysis
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an Enterprise Architecture analyst. Your task is to analyze architecture elements and their relationships, identifying strengths, weaknesses, and providing insights."},
                    {"role": "user", "content": f"Please analyze this enterprise architecture element and its relationships: {json.dumps(context)}"}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content
            
            # Log the analysis activity
            self._log_ai_activity("analysis", element["name"], analysis)
            
            return {
                "success": True,
                "element": element,
                "related_elements": [r["element"] for r in related_elements],
                "analysis": analysis
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _log_ai_activity(self, activity_type: str, element_name: str, content: str):
        """Log AI activity for auditing."""
        try:
            activity_data = {
                "activity_type": activity_type,
                "element_name": element_name,
                "content": content,
                "created_at": datetime.now().isoformat()
            }
            
            self.supabase.table("ai_activity_logs").insert(activity_data).execute()
        except Exception as e:
            logger.error(f"Error logging AI activity: {str(e)}")


class DocumentationTool(Tool):
    """Tool for generating documentation from EA models and elements."""
    
    def __init__(self, supabase_client):
        """Initialize the Documentation Tool."""
        self.supabase = supabase_client
        super().__init__(
            name="documentation_tool",
            description="Generate documentation from enterprise architecture models and elements",
            function=FunctionDefinition(
                name="generate_documentation",
                description="Generate documentation from EA artifacts",
                parameters={
                    "type": "object",
                    "properties": {
                        "artifact_type": {
                            "type": "string",
                            "enum": ["element", "model", "view", "domain"],
                            "description": "Type of artifact to document"
                        },
                        "artifact_id": {
                            "type": "string",
                            "description": "ID of the artifact to document"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["markdown", "html", "docx"],
                            "description": "Output format for the documentation"
                        },
                        "audience": {
                            "type": "string",
                            "enum": ["technical", "business", "executive"],
                            "description": "Target audience for the documentation"
                        },
                        "include_diagrams": {
                            "type": "boolean",
                            "description": "Whether to include diagrams"
                        },
                        "include_related": {
                            "type": "boolean",
                            "description": "Whether to include related artifacts"
                        }
                    },
                    "required": ["artifact_type", "artifact_id", "format"]
                }
            )
        )
    
    def execute(self, artifact_type: str, artifact_id: str, format: str,
               audience: str = "technical", include_diagrams: bool = True,
               include_related: bool = True) -> Dict[str, Any]:
        """Execute the Documentation Tool."""
        try:
            # Gather the artifact data
            artifact_data = self._gather_artifact_data(artifact_type, artifact_id, include_related)
            
            if not artifact_data.get("success", False):
                return artifact_data
            
            # Generate the documentation
            documentation = self._generate_documentation(
                artifact_type, artifact_data, format, audience, include_diagrams
            )
            
            # Save the generated documentation
            saved_doc = self._save_documentation(
                artifact_type, artifact_id, format, audience, documentation
            )
            
            return {
                "success": True,
                "documentation": documentation,
                "document_id": saved_doc.get("document_id")
            }
        except Exception as e:
            logger.error(f"Error in Documentation Tool: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _gather_artifact_data(self, artifact_type: str, artifact_id: str, 
                             include_related: bool) -> Dict[str, Any]:
        """Gather data about the artifact and related artifacts."""
        try:
            if artifact_type == "element":
                return self._gather_element_data(artifact_id, include_related)
            elif artifact_type == "model":
                return self._gather_model_data(artifact_id, include_related)
            elif artifact_type == "view":
                return self._gather_view_data(artifact_id, include_related)
            elif artifact_type == "domain":
                return self._gather_domain_data(artifact_id, include_related)
            else:
                return {"success": False, "message": f"Unknown artifact type: {artifact_type}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _gather_element_data(self, element_id: str, include_related: bool) -> Dict[str, Any]:
        """Gather data about an element and its relationships."""
        # Implementation details...
        return {"success": True, "element": {}, "relationships": []}
    
    def _gather_model_data(self, model_id: str, include_related: bool) -> Dict[str, Any]:
        """Gather data about a model and its elements."""
        # Implementation details...
        return {"success": True, "model": {}, "elements": [], "relationships": []}
    
    def _gather_view_data(self, view_id: str, include_related: bool) -> Dict[str, Any]:
        """Gather data about a view and its elements."""
        # Implementation details...
        return {"success": True, "view": {}, "elements": [], "relationships": []}
    
    def _gather_domain_data(self, domain_id: str, include_related: bool) -> Dict[str, Any]:
        """Gather data about a domain and its elements."""
        # Implementation details...
        return {"success": True, "domain": {}, "elements": []}
    
    def _generate_documentation(self, artifact_type: str, artifact_data: Dict[str, Any],
                               format: str, audience: str, 
                               include_diagrams: bool) -> str:
        """Generate documentation for the artifact."""
        try:
            # Create prompt based on the artifact type and audience
            system_prompt = "You are an Enterprise Architecture documentation specialist. "
            
            if audience == "technical":
                system_prompt += "Create detailed technical documentation suitable for IT architects and developers."
            elif audience == "business":
                system_prompt += "Create business-focused documentation that explains concepts in business terms."
            elif audience == "executive":
                system_prompt += "Create executive-level documentation focusing on strategic impacts and high-level insights."
            
            # Add format-specific instructions
            if format == "markdown":
                system_prompt += " Format the documentation in Markdown."
            elif format == "html":
                system_prompt += " Format the documentation in HTML."
            elif format == "docx":
                system_prompt += " Format the documentation as if it would be exported to MS Word."
            
            # Create user prompt with artifact data
            user_prompt = f"Generate {audience}-focused documentation for this {artifact_type}:\n\n"
            user_prompt += json.dumps(artifact_data)
            
            # Call OpenAI for documentation generation
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=4000
            )
            
            documentation = response.choices[0].message.content
            
            # Log the documentation generation activity
            self._log_ai_activity("documentation", artifact_type, artifact_id, documentation)
            
            return documentation
        except Exception as e:
            logger.error(f"Error generating documentation: {str(e)}")
            raise
    
    def _save_documentation(self, artifact_type: str, artifact_id: str, 
                           format: str, audience: str, documentation: str) -> Dict[str, Any]:
        """Save the generated documentation."""
        try:
            doc_data = {
                "artifact_type": artifact_type,
                "artifact_id": artifact_id,
                "format": format,
                "audience": audience,
                "content": documentation,
                "created_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("ea_documentation").insert(doc_data).execute()
            
            if result.data and len(result.data) > 0:
                return {
                    "success": True,
                    "document_id": result.data[0]["id"]
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to save documentation"
                }
        except Exception as e:
            logger.error(f"Error saving documentation: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _log_ai_activity(self, activity_type: str, artifact_type: str, 
                        artifact_id: str, content: str):
        """Log AI activity for auditing."""
        try:
            activity_data = {
                "activity_type": activity_type,
                "artifact_type": artifact_type,
                "artifact_id": artifact_id,
                "content_length": len(content),
                "created_at": datetime.now().isoformat()
            }
            
            self.supabase.table("ai_activity_logs").insert(activity_data).execute()
        except Exception as e:
            logger.error(f"Error logging AI activity: {str(e)}")


class ImpactAnalysisTool(Tool):
    """Tool for analyzing the impact of architecture changes."""
    
    def __init__(self, supabase_client):
        """Initialize the Impact Analysis Tool."""
        self.supabase = supabase_client
        super().__init__(
            name="impact_analysis_tool",
            description="Analyze the impact of changes to architecture elements",
            function=FunctionDefinition(
                name="analyze_impact",
                description="Analyze the impact of changes to architecture elements",
                parameters={
                    "type": "object",
                    "properties": {
                        "element_id": {
                            "type": "string",
                            "description": "ID of the element being changed"
                        },
                        "change_type": {
                            "type": "string",
                            "enum": ["add", "modify", "replace", "remove"],
                            "description": "Type of change being made"
                        },
                        "change_description": {
                            "type": "string",
                            "description": "Description of the proposed change"
                        },
                        "analysis_depth": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 3,
                            "description": "Analysis depth (1=direct, 2=indirect, 3=comprehensive)"
                        }
                    },
                    "required": ["element_id", "change_type", "change_description"]
                }
            )
        )
    
    def execute(self, element_id: str, change_type: str, change_description: str,
               analysis_depth: int = 2) -> Dict[str, Any]:
        """Execute the Impact Analysis Tool."""
        try:
            # Gather the element data
            element_data = self._gather_element_data(element_id, analysis_depth)
            
            if not element_data.get("success", False):
                return element_data
            
            # Perform impact analysis
            analysis = self._perform_impact_analysis(
                element_data, change_type, change_description, analysis_depth
            )
            
            # Save the analysis results
            saved_analysis = self._save_impact_analysis(
                element_id, change_type, change_description, analysis
            )
            
            return {
                "success": True,
                "impact_analysis": analysis,
                "analysis_id": saved_analysis.get("analysis_id")
            }
        except Exception as e:
            logger.error(f"Error in Impact Analysis Tool: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _gather_element_data(self, element_id: str, depth: int) -> Dict[str, Any]:
        """Gather data about an element and its dependencies."""
        try:
            # Get the element
            element_result = self.supabase.table("ea_elements").select("*").eq("id", element_id).execute()
            
            if not element_result.data or len(element_result.data) == 0:
                return {
                    "success": False,
                    "message": "Element not found"
                }
            
            element = element_result.data[0]
            
            # Get direct relationships
            direct_relationships = self._get_element_relationships(element_id)
            
            # Get indirect relationships if depth > 1
            indirect_relationships = []
            if depth > 1:
                for relation in direct_relationships:
                    other_id = relation["source_element_id"] if relation["target_element_id"] == element_id else relation["target_element_id"]
                    indirect_rels = self._get_element_relationships(other_id)
                    # Filter out relationships back to the original element
                    indirect_relationships.extend([
                        r for r in indirect_rels 
                        if r["source_element_id"] != element_id and r["target_element_id"] != element_id
                    ])
            
            # Get all affected elements
            affected_elements = {}
            
            # Add directly connected elements
            for relation in direct_relationships:
                other_id = relation["source_element_id"] if relation["target_element_id"] == element_id else relation["target_element_id"]
                if other_id not in affected_elements:
                    element_data = self.supabase.table("ea_elements").select("*").eq("id", other_id).execute()
                    if element_data.data and len(element_data.data) > 0:
                        affected_elements[other_id] = {
                            "element": element_data.data[0],
                            "relationship": relation,
                            "impact_level": "direct"
                        }
            
            # Add indirectly connected elements if depth > 1
            if depth > 1:
                for relation in indirect_relationships:
                    source_id = relation["source_element_id"]
                    target_id = relation["target_element_id"]
                    
                    for other_id in [source_id, target_id]:
                        if other_id not in affected_elements and other_id != element_id:
                            element_data = self.supabase.table("ea_elements").select("*").eq("id", other_id).execute()
                            if element_data.data and len(element_data.data) > 0:
                                affected_elements[other_id] = {
                                    "element": element_data.data[0],
                                    "relationship": relation,
                                    "impact_level": "indirect"
                                }
            
            return {
                "success": True,
                "element": element,
                "direct_relationships": direct_relationships,
                "indirect_relationships": indirect_relationships,
                "affected_elements": list(affected_elements.values())
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _get_element_relationships(self, element_id: str) -> List[Dict[str, Any]]:
        """Get relationships for an element."""
        try:
            relationships_result = self.supabase.table("ea_relationships").select("*").or_(
                f"source_element_id.eq.{element_id},target_element_id.eq.{element_id}"
            ).execute()
            
            if relationships_result.data:
                return relationships_result.data
            return []
        except Exception as e:
            logger.error(f"Error getting element relationships: {str(e)}")
            return []
    
    def _perform_impact_analysis(self, element_data: Dict[str, Any], change_type: str,
                                change_description: str, depth: int) -> Dict[str, Any]:
        """Perform impact analysis on the changes."""
        try:
            # Create context for the AI
            context = {
                "element": element_data["element"],
                "change_type": change_type,
                "change_description": change_description,
                "direct_relationships": element_data["direct_relationships"],
                "affected_elements": element_data["affected_elements"],
                "analysis_depth": depth
            }
            
            # Call OpenAI for impact analysis
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an Enterprise Architecture impact analyst. Your task is to analyze the impact of proposed changes on connected architecture elements."},
                    {"role": "user", "content": f"Analyze the impact of this change to an EA element: {json.dumps(context)}"}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse out key sections from the analysis
            sections = self._parse_analysis_sections(analysis_text)
            
            # Calculate risk scores for each affected element
            risk_scores = self._calculate_risk_scores(
                element_data["affected_elements"], 
                change_type,
                sections
            )
            
            return {
                "analysis_text": analysis_text,
                "sections": sections,
                "risk_scores": risk_scores,
                "affected_elements": len(element_data["affected_elements"]),
                "risk_level": self._determine_overall_risk(risk_scores)
            }
        except Exception as e:
            logger.error(f"Error performing impact analysis: {str(e)}")
            raise
    
    def _parse_analysis_sections(self, analysis_text: str) -> Dict[str, str]:
        """Parse key sections from the analysis text."""
        # Simple section parsing - this could be enhanced with more sophisticated parsing
        sections = {}
        current_section = "summary"
        current_content = []
        
        for line in analysis_text.split('\n'):
            line = line.strip()
            if line.endswith(':') and len(line) < 50:  # Likely a section header
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                    current_content = []
                current_section = line[:-1].lower().replace(' ', '_')
            else:
                current_content.append(line)
        
        # Add the last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _calculate_risk_scores(self, affected_elements: List[Dict[str, Any]],
                              change_type: str, analysis_sections: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Calculate risk scores for affected elements."""
        risk_scores = {}
        
        # Define risk multipliers based on change type
        risk_multipliers = {
            "add": 0.7,
            "modify": 1.0,
            "replace": 1.2,
            "remove": 1.5
        }
        
        multiplier = risk_multipliers.get(change_type, 1.0)
        
        for affected in affected_elements:
            element = affected["element"]
            impact_level = affected["impact_level"]
            
            # Base risk based on impact level
            base_risk = 0.8 if impact_level == "direct" else 0.4
            
            # Calculate final risk score
            final_risk = base_risk * multiplier
            
            # Limit to range 0-1
            final_risk = min(max(final_risk, 0), 1)
            
            # Convert to qualitative risk level
            risk_level = "high" if final_risk > 0.7 else "medium" if final_risk > 0.3 else "low"
            
            risk_scores[element["id"]] = {
                "element_name": element["name"],
                "impact_level": impact_level,
                "risk_score": round(final_risk, 2),
                "risk_level": risk_level
            }
        
        return risk_scores
    
    def _determine_overall_risk(self, risk_scores: Dict[str, Dict[str, Any]]) -> str:
        """Determine the overall risk level based on individual risk scores."""
        if not risk_scores:
            return "unknown"
        
        high_count = sum(1 for score in risk_scores.values() if score["risk_level"] == "high")
        medium_count = sum(1 for score in risk_scores.values() if score["risk_level"] == "medium")
        
        if high_count > 2 or high_count > len(risk_scores) / 3:
            return "high"
        elif medium_count > len(risk_scores) / 2 or high_count > 0:
            return "medium"
        else:
            return "low"
    
    def _save_impact_analysis(self, element_id: str, change_type: str,
                             change_description: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Save the impact analysis results."""
        try:
            analysis_data = {
                "element_id": element_id,
                "change_type": change_type,
                "change_description": change_description,
                "analysis_result": analysis,
                "risk_level": analysis["risk_level"],
                "created_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("ea_impact_analyses").insert(analysis_data).execute()
            
            if result.data and len(result.data) > 0:
                return {
                    "success": True,
                    "analysis_id": result.data[0]["id"]
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to save impact analysis"
                }
        except Exception as e:
            logger.error(f"Error saving impact analysis: {str(e)}")
            return {"success": False, "message": str(e)}


class PatternRecognitionTool(Tool):
    """Tool for recognizing and suggesting architecture patterns."""
    
    def __init__(self, supabase_client):
        """Initialize the Pattern Recognition Tool."""
        self.supabase = supabase_client
        super().__init__(
            name="pattern_recognition_tool",
            description="Recognize architecture patterns and suggest improvements",
            function=FunctionDefinition(
                name="recognize_patterns",
                description="Identify architecture patterns and suggest improvements",
                parameters={
                    "type": "object",
                    "properties": {
                        "model_id": {
                            "type": "string",
                            "description": "ID of the EA model to analyze"
                        },
                        "domain": {
                            "type": "string",
                            "enum": ["business", "data", "application", "technology", "performance", "all"],
                            "description": "Domain to focus analysis on"
                        },
                        "pattern_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["best_practice", "anti_pattern", "optimization", "security", "integration"]
                            },
                            "description": "Types of patterns to identify"
                        },
                        "element_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific element IDs to analyze (optional)"
                        }
                    },
                    "required": ["model_id"]
                }
            )
        )
    
    def execute(self, model_id: str, domain: str = "all",
               pattern_types: Optional[List[str]] = None,
               element_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute the Pattern Recognition Tool."""
        try:
            # Set defaults
            if pattern_types is None:
                pattern_types = ["best_practice", "anti_pattern", "optimization"]
            
            # Gather architecture data
            model_data = self._gather_model_data(model_id, domain, element_ids)
            
            if not model_data.get("success", False):
                return model_data
            
            # Recognize patterns
            patterns = self._recognize_patterns(model_data, pattern_types)
            
            # Save the results
            saved_result = self._save_pattern_recognition(model_id, domain, pattern_types, patterns)
            
            return {
                "success": True,
                "patterns": patterns,
                "result_id": saved_result.get("result_id")
            }
        except Exception as e:
            logger.error(f"Error in Pattern Recognition Tool: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _gather_model_data(self, model_id: str, domain: str, 
                          element_ids: Optional[List[str]]) -> Dict[str, Any]:
        """Gather data about the model elements."""
        try:
            # Get the model
            model_result = self.supabase.table("ea_models").select("*").eq("id", model_id).execute()
            
            if not model_result.data or len(model_result.data) == 0:
                return {
                    "success": False,
                    "message": "Model not found"
                }
            
            model = model_result.data[0]
            
            # Get elements
            elements_query = self.supabase.table("ea_elements").select("*").eq("model_id", model_id)
            
            # Filter by domain if specified
            if domain != "all":
                elements_query = elements_query.eq("domain", domain)
            
            # Filter by specific element IDs if provided
            if element_ids:
                elements_query = elements_query.in_("id", element_ids)
            
            elements_result = elements_query.execute()
            elements = elements_result.data or []
            
            # Get relationships
            relationships = []
            if elements:
                element_ids_list = [e["id"] for e in elements]
                relationships_result = self.supabase.table("ea_relationships").select("*").or_(
                    f"source_element_id.in.({','.join(element_ids_list)}),target_element_id.in.({','.join(element_ids_list)})"
                ).execute()
                relationships = relationships_result.data or []
            
            return {
                "success": True,
                "model": model,
                "elements": elements,
                "relationships": relationships
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _recognize_patterns(self, model_data: Dict[str, Any], 
                           pattern_types: List[str]) -> Dict[str, Any]:
        """Recognize architecture patterns in the model data."""
        try:
            # Create context for the AI
            context = {
                "model": model_data["model"],
                "elements": model_data["elements"],
                "relationships": model_data["relationships"],
                "pattern_types": pattern_types
            }
            
            # Call OpenAI for pattern recognition
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an Enterprise Architecture pattern specialist. Your task is to identify architecture patterns, anti-patterns, and optimization opportunities in enterprise architecture models."},
                    {"role": "user", "content": f"Identify architecture patterns in this EA model: {json.dumps(context)}"}
                ],
                temperature=0.5,
                max_tokens=2500
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse patterns from the analysis
            parsed_patterns = self._parse_patterns(analysis_text, pattern_types)
            
            return {
                "analysis_text": analysis_text,
                "patterns": parsed_patterns,
                "pattern_count": sum(len(patterns) for patterns in parsed_patterns.values())
            }
        except Exception as e:
            logger.error(f"Error recognizing patterns: {str(e)}")
            raise
    
    def _parse_patterns(self, analysis_text: str, 
                       pattern_types: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Parse architecture patterns from the analysis text."""
        patterns = {pattern_type: [] for pattern_type in pattern_types}
        
        # Call OpenAI again to structure the results
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a parser that extracts structured information about architecture patterns from text. Extract and structure the information into a JSON format with pattern name, description, affected elements, and recommendations."},
                {"role": "user", "content": f"Parse the following architecture pattern analysis into structured data for pattern types {', '.join(pattern_types)}:\n\n{analysis_text}"}
            ],
            temperature=0.2,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        try:
            # Try to parse the structured JSON response
            parsed_data = json.loads(response.choices[0].message.content)
            
            # Check if the response has the expected structure
            if isinstance(parsed_data, dict):
                for pattern_type in pattern_types:
                    if pattern_type in parsed_data and isinstance(parsed_data[pattern_type], list):
                        patterns[pattern_type] = parsed_data[pattern_type]
        except json.JSONDecodeError:
            # Fallback to simple parsing if structured parsing fails
            logger.warning("JSON parsing failed, falling back to simple parsing")
            
            current_type = None
            current_pattern = {}
            
            for line in analysis_text.split('\n'):
                line = line.strip()
                
                # Check for pattern type headers
                for pattern_type in pattern_types:
                    if line.lower().startswith(f"{pattern_type.replace('_', ' ')}:") or line.lower() == pattern_type.replace('_', ' '):
                        current_type = pattern_type
                        break
                
                # If line is a pattern name (usually short, ends with colon)
                if current_type and line.endswith(':') and 3 < len(line) < 50 and not any(p.lower() in line.lower() for p in ["summary", "conclusion", "overview"]):
                    # Save previous pattern if it exists
                    if current_pattern and "name" in current_pattern:
                        patterns[current_type].append(current_pattern)
                    
                    # Start new pattern
                    current_pattern = {"name": line[:-1], "description": ""}
                
                # Add content to current pattern
                elif current_type and current_pattern and "name" in current_pattern:
                    if "description" not in current_pattern:
                        current_pattern["description"] = line
                    else:
                        current_pattern["description"] += "\n" + line
            
            # Add the last pattern
            if current_type and current_pattern and "name" in current_pattern:
                patterns[current_type].append(current_pattern)
        
        return patterns
    
    def _save_pattern_recognition(self, model_id: str, domain: str,
                                 pattern_types: List[str], 
                                 patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Save the pattern recognition results."""
        try:
            result_data = {
                "model_id": model_id,
                "domain": domain,
                "pattern_types": pattern_types,
                "patterns": patterns,
                "created_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("ea_pattern_recognition").insert(result_data).execute()
            
            if result.data and len(result.data) > 0:
                return {
                    "success": True,
                    "result_id": result.data[0]["id"]
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to save pattern recognition results"
                }
        except Exception as e:
            logger.error(f"Error saving pattern recognition results: {str(e)}")
            return {"success": False, "message": str(e)}


# Agent for Enterprise Architecture Guidance
class EnterpriseArchitectureAgent:
    """Master agent for Enterprise Architecture guidance."""
    
    def __init__(self, supabase_client):
        """Initialize the Enterprise Architecture Agent."""
        self.supabase = supabase_client
        
        # Initialize tools
        self.element_tool = ElementTool(supabase_client)
        self.documentation_tool = DocumentationTool(supabase_client)
        self.impact_analysis_tool = ImpactAnalysisTool(supabase_client)
        self.pattern_recognition_tool = PatternRecognitionTool(supabase_client)
        
        # Define the agent
        self.agent = Agent(
            name="Enterprise Architecture Guide",
            description="An expert in enterprise architecture that helps with modeling, analysis, and documentation",
            tools=[self.element_tool, self.documentation_tool, self.impact_analysis_tool, self.pattern_recognition_tool],
            steps=[
                Step(
                    name="understand_request",
                    description="Understand the user's enterprise architecture request"
                ),
                Step(
                    name="gather_context",
                    description="Gather relevant architecture context from the repository"
                ),
                Step(
                    name="generate_insights",
                    description="Generate architecture insights based on the context"
                ),
                Step(
                    name="create_response",
                    description="Create a comprehensive response with architecture recommendations"
                )
            ]
        )
    
    def process_request(self, query: str) -> Dict[str, Any]:
        """Process a user request about enterprise architecture."""
        try:
            # Run the agent
            response = run(self.agent, [{"role": "user", "content": query}])
            
            # Log the interaction
            self._log_interaction(query, response)
            
            return {
                "success": True,
                "response": response,
                "final_output": response.final_output
            }
        except Exception as e:
            logger.error(f"Error processing EA request: {str(e)}")
            return {
                "success": False,
                "message": f"Error processing request: {str(e)}"
            }
    
    def _log_interaction(self, query: str, response: Any):
        """Log the interaction with the EA agent."""
        try:
            log_data = {
                "query": query,
                "response_summary": response.final_output[:500] if hasattr(response, 'final_output') else str(response)[:500],
                "created_at": datetime.now().isoformat()
            }
            
            self.supabase.table("ea_agent_interactions").insert(log_data).execute()
        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")


# Helper function to initialize the Enterprise Architecture GenAI system
def initialize_ea_genai(supabase_url: str, supabase_key: str, openai_api_key: str):
    """Initialize the Enterprise Architecture GenAI system."""
    # Set up OpenAI API key
    os.environ["OPENAI_API_KEY"] = openai_api_key
    
    # Initialize Supabase client
    from supabase import create_client
    supabase = create_client(supabase_url, supabase_key)
    
    # Create the EA Agent
    ea_agent = EnterpriseArchitectureAgent(supabase)
    
    return ea_agent


# Example usage
if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get configuration from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Initialize the EA GenAI system
    ea_agent = initialize_ea_genai(supabase_url, supabase_key, openai_api_key)
    
    # Process a sample request
    response = ea_agent.process_request(
        "Can you analyze our current data architecture and suggest improvements?"
    )
    
    print(response["final_output"])
