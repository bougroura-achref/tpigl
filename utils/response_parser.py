"""
Response Parser - Unified JSON parsing for LLM responses.
Eliminates code duplication across agents.
"""

import json
import re
from typing import Dict, Any, Optional


def parse_llm_json_response(
    response: str,
    fallback: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Universal JSON parser for LLM responses with robust fallback handling.
    
    Handles multiple response formats:
    - JSON wrapped in ```json ... ``` blocks
    - JSON wrapped in ``` ... ``` blocks
    - Raw JSON objects
    - Python code blocks (extracts as fixed_code)
    
    Args:
        response: Raw LLM response string
        fallback: Fallback dictionary if parsing fails
        
    Returns:
        Parsed JSON as dictionary, or fallback if parsing fails
    """
    if not response or not isinstance(response, str):
        return fallback or {"error": "Empty or invalid response"}
    
    response = response.strip()
    
    # Strategy 1: Try ```json ... ``` block
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response, re.IGNORECASE)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass
    
    # Strategy 2: Try generic ``` ... ``` block (might be JSON without language tag)
    code_match = re.search(r'```\s*([\s\S]*?)\s*```', response)
    if code_match:
        content = code_match.group(1).strip()
        # Check if it looks like JSON
        if content.startswith('{') or content.startswith('['):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass
    
    # Strategy 3: Try to find raw JSON object in response
    try:
        # Find the outermost { } pair
        start = response.find('{')
        if start >= 0:
            # Count braces to find matching closing brace
            depth = 0
            end = start
            for i, char in enumerate(response[start:], start):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            
            json_str = response[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    # Strategy 4: Check for Python code block (for Fixer agent)
    python_match = re.search(r'```python\s*([\s\S]*?)\s*```', response, re.IGNORECASE)
    if python_match:
        code = python_match.group(1).strip()
        if code:
            return {
                "fixed_code": code,
                "changes_made": ["Code extracted from Python block"]
            }
    
    # Strategy 5: If response looks like Python code directly
    if 'def ' in response or 'class ' in response or 'import ' in response:
        # Clean up any markdown artifacts
        clean_code = re.sub(r'^```\w*\n?', '', response)
        clean_code = re.sub(r'\n?```$', '', clean_code)
        return {
            "fixed_code": clean_code.strip(),
            "changes_made": ["Code extracted from response"]
        }
    
    # Return fallback
    return fallback or {
        "error": "Failed to parse LLM response",
        "raw_response": response[:500] if len(response) > 500 else response
    }


def extract_code_from_response(response: str) -> Optional[str]:
    """
    Extract Python code from an LLM response.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Extracted Python code or None
    """
    # Try Python code block first
    python_match = re.search(r'```python\s*([\s\S]*?)\s*```', response, re.IGNORECASE)
    if python_match:
        return python_match.group(1).strip()
    
    # Try generic code block
    code_match = re.search(r'```\s*([\s\S]*?)\s*```', response)
    if code_match:
        content = code_match.group(1).strip()
        # Verify it looks like Python
        if 'def ' in content or 'class ' in content or 'import ' in content:
            return content
    
    # Try parsing as JSON and extracting fixed_code
    try:
        parsed = parse_llm_json_response(response)
        if "fixed_code" in parsed:
            return parsed["fixed_code"]
    except Exception:
        pass
    
    return None
