"""
Enterprise Architecture Solution - GenAI Engine

This module provides the core GenAI engine for the Enterprise Architecture Solution,
using OpenAI's Agents Python SDK to implement intelligent assistants for EA tasks.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

import openai
from openai.agents import Agent, Step, Tool, run
from openai.types import FunctionDefinition

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenAIEngine:
    """Core GenAI engine for Enterprise Architecture Solution."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        """Initialize the GenAI engine.
        
        Args:
            api_key: OpenAI API key (uses environment variable if not provided)
            model: OpenAI model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key)
        self.agents = {}
    
    def create_assistant(self, name: str, description: str, 
                       tools: List[Tool] = None, steps: List[Step] = None) -> Agent:
        """Create an OpenAI Assistant Agent.
        
        Args:
            name: Name of the assistant
            description: Description of the assistant's purpose
            tools: List of tools the assistant can use
            steps: List of steps the assistant should follow
            
        Returns:
            Agent instance
        """
        # Create default steps if not provided
        if not steps:
            steps = [
                Step(
                    name="understand_request",
                    description="Understand the user's request in the context of Enterprise Architecture"
                ),
                Step(
                    name="gather_context",
                    description="Gather relevant Enterprise Architecture context needed for the task"
                ),
                Step(
                    name="perform_task",
                    description="Perform the requested task using appropriate EA knowledge and tools"
                ),
                Step(
                    name="generate_response",
                    description="Generate a helpful response with the results"
                )
            ]
        
        # Create the agent
        agent = Agent(
            name=name,
            description=description,
            tools=tools or [],
            steps=steps
        )
        
        # Cache the agent for future use
        self.agents[name] = agent
        
        return agent
    
    def get_assistant(self, name: str) -> Optional[Agent]:
        """Get a previously created assistant by name.
        
        Args:
            name: Name of the assistant
            
        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(name)
    
    def run_assistant(self, agent_or_name: Any, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Run an assistant with provided messages.
        
        Args:
            agent_or_name: Agent instance or name of a cached agent
            messages: Conversation messages
            
        Returns:
            Assistant response
        """
        try:
            # Get the agent - either use the provided one or look up by name
            agent = agent_or_name
            if isinstance(agent_or_name, str):
                agent = self.get_assistant(agent_or_name)
                if not agent:
                    raise ValueError(f"No assistant found with name '{agent_or_name}'")
            
            # Run the agent
            result = run(agent, messages)
            
            return {
                "success": True,
                "result": result,
                "messages": messages + [{"role": "assistant", "content": result}]
            }
        except Exception as e:
            logger.error(f"Error running assistant: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "messages": messages
            }
    
    def create_tool(self, name: str, description: str, 
                  function_params: Dict[str, Any], function: callable) -> Tool:
        """Create a tool for assistants to use.
        
        Args:
            name: Name of the tool
            description: Description of the tool's purpose
            function_params: Parameters definition for the function
            function: Callable function to execute
            
        Returns:
            Tool instance
        """
        # Create function definition
        function_def = FunctionDefinition(
            name=name,
            description=description,
            parameters=function_params
        )
        
        # Create and return the tool
        return Tool(
            name=name,
            description=description,
            function=function_def
        )
    
    def simple_completion(self, prompt: str, temperature: float = 0.7, 
                        max_tokens: int = 1000) -> Dict[str, Any]:
        """Generate a simple completion using the OpenAI API.
        
        Args:
            prompt: Text prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Completion result
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "success": True,
                "text": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"Error generating completion: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def structured_generation(self, prompt: str, structure: Dict[str, Any], 
                           temperature: float = 0.7) -> Dict[str, Any]:
        """Generate structured content using function calling.
        
        Args:
            prompt: Text prompt
            structure: JSON schema structure for the output
            temperature: Sampling temperature (0-1)
            
        Returns:
            Structured generation result
        """
        try:
            # Create function definition for structuring output
            function_def = {
                "name": "generate_structured_output",
                "description": "Generate structured output based on the user's input",
                "parameters": structure
            }
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                functions=[function_def],
                function_call={"name": "generate_structured_output"}
            )
            
            # Parse the function call arguments as JSON
            function_call = response.choices[0].message.function_call
            structured_data = json.loads(function_call.arguments)
            
            return {
                "success": True,
                "structured_data": structured_data,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"Error generating structured content: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
