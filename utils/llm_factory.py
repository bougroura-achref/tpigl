"""
LLM Factory - Creates the appropriate LLM client based on configuration.
Supports both Anthropic Claude and Google Gemini as per project requirements.
"""

from __future__ import annotations

import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


def get_llm(
    model_name: Optional[str] = None,
    temperature: float = 0.1,
    timeout: int = 120
) -> Any:
    """
    Factory function to create the appropriate LLM client.
    
    Automatically selects between Anthropic Claude and Google Gemini
    based on the model name and available API keys.
    
    Args:
        model_name: Model to use. If None, uses MODEL_NAME env var.
        temperature: LLM temperature (0-1)
        timeout: Request timeout in seconds
        
    Returns:
        LLM client (ChatAnthropic or ChatGoogleGenerativeAI)
        
    Raises:
        ValueError: If no valid API key is found for the requested model
    """
    # Default model from environment
    if model_name is None:
        model_name = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")
    
    # Detect which provider to use based on model name
    is_gemini = model_name.startswith("gemini") or model_name.startswith("models/gemini")
    is_claude = model_name.startswith("claude")
    
    # Check available API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    # Auto-detect provider if model name doesn't clearly indicate one
    if not is_gemini and not is_claude:
        # Check which API key is available
        if anthropic_key and anthropic_key != "your_anthropic_api_key_here":
            is_claude = True
            model_name = "claude-sonnet-4-20250514"
        elif google_key and google_key != "your_google_api_key_here":
            is_gemini = True
            model_name = "gemini-2.0-flash"
        else:
            raise ValueError(
                "No valid API key found. Please set either ANTHROPIC_API_KEY or GOOGLE_API_KEY in your .env file"
            )
    
    # Create the appropriate LLM client
    if is_gemini:
        if not google_key or google_key == "your_google_api_key_here":
            raise ValueError(
                "GOOGLE_API_KEY not configured. Please set it in your .env file to use Gemini models."
            )
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            logger.info(f"Using Google Gemini: {model_name}")
            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                google_api_key=google_key,
                convert_system_message_to_human=True  # Gemini doesn't have system messages
            )
        except ImportError:
            raise ImportError(
                "langchain-google-genai not installed. Install with: pip install langchain-google-genai"
            )
    
    else:  # Default to Anthropic Claude
        if not anthropic_key or anthropic_key == "your_anthropic_api_key_here":
            raise ValueError(
                "ANTHROPIC_API_KEY not configured. Please set it in your .env file to use Claude models."
            )
        
        try:
            from langchain_anthropic import ChatAnthropic
            
            logger.info(f"Using Anthropic Claude: {model_name}")
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                timeout=timeout
            )
        except ImportError:
            raise ImportError(
                "langchain-anthropic not installed. Install with: pip install langchain-anthropic"
            )


def get_provider_name(model_name: Optional[str] = None) -> str:
    """
    Get the provider name for the given model.
    
    Args:
        model_name: Model name to check
        
    Returns:
        Provider name ("anthropic" or "google")
    """
    if model_name is None:
        model_name = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")
    
    if model_name.startswith("gemini") or model_name.startswith("models/gemini"):
        return "google"
    return "anthropic"
