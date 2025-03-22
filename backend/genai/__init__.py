"""
Enterprise Architecture Solution - GenAI Package

This package provides AI-powered features for the Enterprise Architecture Solution.
"""

import logging
from typing import Dict, Any, Optional

from .agents import initialize_ea_assistant
from .documentation_generator import DocumentationGenerator
from .impact_analysis import ImpactAnalysis
from .pattern_recognition import PatternRecognition

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenAIService:
    """Service for accessing all GenAI features."""
    
    def __init__(self, supabase_client):
        """Initialize the GenAI service.
        
        Args:
            supabase_client: A configured Supabase client for database operations
        """
        self.supabase = supabase_client
        self.documentation_generator = DocumentationGenerator(supabase_client)
        self.impact_analysis = ImpactAnalysis(supabase_client)
        self.pattern_recognition = PatternRecognition(supabase_client)
        self.ea_assistant = initialize_ea_assistant(supabase_client)
        
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
        return self.documentation_generator.generate_documentation(
            content_type, content_id, format, include_diagrams, include_relationships, style
        )
        
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
        return self.impact_analysis.analyze_impact(
            element_id, change_description, change_type, analysis_depth
        )
        
    def recognize_patterns(self, model_id: str, element_ids: Optional[list] = None,
                         domain_filter: Optional[str] = None, 
                         pattern_types: Optional[list] = None) -> Dict[str, Any]:
        """Recognize patterns in architecture elements.
        
        Args:
            model_id: UUID of the model to analyze
            element_ids: Optional list of specific element IDs to analyze
            domain_filter: Optional domain to filter by
            pattern_types: Optional list of pattern types to look for
            
        Returns:
            Dict containing the recognized patterns
        """
        return self.pattern_recognition.recognize_patterns(
            model_id, element_ids, domain_filter, pattern_types
        )
        
    def run_assistant(self, messages: list) -> Dict[str, Any]:
        """Run the EA Assistant with the given conversation.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Dict containing the assistant's response
        """
        from openai.agents import run
        
        try:
            result = run(self.ea_assistant, messages)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error running EA Assistant: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
