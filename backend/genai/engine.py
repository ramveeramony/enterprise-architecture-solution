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
logger = logging.