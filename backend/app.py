"""
Enterprise Architecture Solution - Main Backend Application

This module provides the main FastAPI application for the Enterprise Architecture Solution.
"""

import os
import logging
from typing import Dict, List, Optional

from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise EnvironmentError("Supabase URL and key must be set in environment variables")

supabase = create_client(supabase_url, supabase_key)

# API security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Create FastAPI app
app = FastAPI(
    title="Enterprise Architecture Solution API",
    description="API for Enterprise Architecture Solution built on Essential Cloud",
    version="1.0.0",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security dependency
async def get_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is missing",
        )
    
    # In production, validate the API key against stored keys
    # This is a simplified example
    expected_api_key = os.getenv("API_KEY")
    if api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return api_key

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": app.version}

# Import routers
from routers import models, elements, integrations, genai
from services import visualization

# Register routers
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(elements.router, prefix="/api/elements", tags=["elements"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])
app.include_router(genai.router, prefix="/api/genai", tags=["genai"])
app.include_router(visualization.router, prefix="/api/visualizations", tags=["visualizations"])

# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    # Get host and port from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Run the server
    uvicorn.run("app:app", host=host, port=port, reload=True)
