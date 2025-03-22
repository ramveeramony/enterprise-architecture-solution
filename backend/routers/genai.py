"""
Enterprise Architecture Solution - GenAI API Router

This module defines the FastAPI router for GenAI features.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Security, status
from pydantic import BaseModel

# Import the GenAI service
from ..genai import GenAIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models for request validation
class DocumentationRequest(BaseModel):
    content_type: str
    content_id: str
    format: str = "markdown"
    include_diagrams: bool = True
    include_relationships: bool = True
    style: str = "technical"

class ImpactAnalysisRequest(BaseModel):
    element_id: str
    change_description: str
    change_type: str
    analysis_depth: int = 2

class PatternRecognitionRequest(BaseModel):
    model_id: str
    element_ids: Optional[List[str]] = None
    domain_filter: Optional[str] = None
    pattern_types: Optional[List[str]] = None

class AssistantMessage(BaseModel):
    role: str
    content: str

class AssistantRequest(BaseModel):
    messages: List[AssistantMessage]

# Dependency to get GenAI service
def get_genai_service():
    # This would normally be initialized with a Supabase client
    # from a dependency injection system
    from supabase import create_client
    import os
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration is missing"
        )
    
    supabase = create_client(supabase_url, supabase_key)
    return GenAIService(supabase)

# Route for documentation generation
@router.post("/documentation", tags=["documentation"])
async def generate_documentation(
    request: DocumentationRequest,
    genai_service: GenAIService = Depends(get_genai_service)
):
    """
    Generate documentation for an EA artifact.
    
    Parameters:
    - content_type: Type of content (element, model, view, policy)
    - content_id: UUID of the content
    - format: Output format (markdown, html, docx)
    - include_diagrams: Whether to include diagrams
    - include_relationships: Whether to include relationships
    - style: Style of documentation (technical, business, executive)
    
    Returns:
    - Generated documentation and metadata
    """
    try:
        result = genai_service.generate_documentation(
            request.content_type,
            request.content_id,
            request.format,
            request.include_diagrams,
            request.include_relationships,
            request.style
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to generate documentation")
            )
            
        return result
    except Exception as e:
        logger.error(f"Error generating documentation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Route for impact analysis
@router.post("/impact-analysis", tags=["impact"])
async def analyze_impact(
    request: ImpactAnalysisRequest,
    genai_service: GenAIService = Depends(get_genai_service)
):
    """
    Analyze the impact of a proposed change to an architecture element.
    
    Parameters:
    - element_id: UUID of the element being changed
    - change_description: Description of the proposed change
    - change_type: Type of change (modify, replace, remove)
    - analysis_depth: Depth of impact analysis (1=direct, 2=indirect, 3=comprehensive)
    
    Returns:
    - Impact analysis results
    """
    try:
        result = genai_service.analyze_impact(
            request.element_id,
            request.change_description,
            request.change_type,
            request.analysis_depth
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to analyze impact")
            )
            
        return result
    except Exception as e:
        logger.error(f"Error analyzing impact: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Route for pattern recognition
@router.post("/pattern-recognition", tags=["patterns"])
async def recognize_patterns(
    request: PatternRecognitionRequest,
    genai_service: GenAIService = Depends(get_genai_service)
):
    """
    Recognize patterns in architecture elements.
    
    Parameters:
    - model_id: UUID of the model to analyze
    - element_ids: Optional list of specific element IDs to analyze
    - domain_filter: Optional domain to filter by
    - pattern_types: Optional list of pattern types to look for
    
    Returns:
    - Recognized patterns
    """
    try:
        result = genai_service.recognize_patterns(
            request.model_id,
            request.element_ids,
            request.domain_filter,
            request.pattern_types
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to recognize patterns")
            )
            
        return result
    except Exception as e:
        logger.error(f"Error recognizing patterns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Route for EA Assistant
@router.post("/assistant", tags=["assistant"])
async def run_assistant(
    request: AssistantRequest,
    genai_service: GenAIService = Depends(get_genai_service)
):
    """
    Run the EA Assistant with the given conversation.
    
    Parameters:
    - messages: List of conversation messages with role and content
    
    Returns:
    - Assistant's response
    """
    try:
        # Convert Pydantic models to dicts
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        result = genai_service.run_assistant(messages)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to run assistant")
            )
            
        return result
    except Exception as e:
        logger.error(f"Error running assistant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
