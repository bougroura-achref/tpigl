"""
Analysis Tools - Pylint integration for code quality analysis
"""

import subprocess
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from io import StringIO


def run_pylint(file_path: str, additional_args: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run pylint on a file and return the results.
    
    Args:
        file_path: Path to the Python file to analyze
        additional_args: Optional additional pylint arguments
        
    Returns:
        dict: Pylint results including score and messages
    """
    path = Path(file_path)
    
    if not path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "score": 0.0,
            "messages": []
        }
    
    # Build pylint command - use sys.executable to ensure correct Python
    # First run: get score with text format
    score_cmd = [
        sys.executable, "-m", "pylint",
        str(path),
        "--reports=y"
    ]
    
    # Second run: get detailed messages with JSON format
    json_cmd = [
        sys.executable, "-m", "pylint",
        str(path),
        "--output-format=json"
    ]
    
    if additional_args:
        score_cmd.extend(additional_args)
        json_cmd.extend(additional_args)
    
    try:
        # Run for score (text format includes score in output)
        score_result = subprocess.run(
            score_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Extract score from text output (could be in stdout or stderr)
        score = extract_pylint_score(score_result.stdout + score_result.stderr)
        
        # Run for JSON messages
        json_result = subprocess.run(
            json_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Parse JSON output
        messages = []
        if json_result.stdout:
            try:
                messages = json.loads(json_result.stdout)
            except json.JSONDecodeError:
                # Try to extract messages from non-JSON output
                messages = []
        
        return {
            "success": True,
            "score": score,
            "messages": messages,
            "raw_output": json_result.stdout,
            "raw_error": score_result.stdout + score_result.stderr,
            "return_code": json_result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Pylint timed out",
            "score": 0.0,
            "messages": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "score": 0.0,
            "messages": []
        }


def extract_pylint_score(stderr_output: str) -> float:
    """
    Extract the pylint score from stderr output.
    
    Args:
        stderr_output: The stderr output from pylint
        
    Returns:
        float: The pylint score (0.0 to 10.0)
    """
    # Pattern to match "Your code has been rated at X.XX/10"
    pattern = r"Your code has been rated at (-?\d+\.?\d*)/10"
    match = re.search(pattern, stderr_output)
    
    if match:
        return float(match.group(1))
    
    return 0.0


def get_pylint_score(file_path: str) -> float:
    """
    Get just the pylint score for a file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        float: The pylint score
    """
    result = run_pylint(file_path)
    return result.get("score", 0.0)


def get_pylint_messages(file_path: str) -> List[Dict[str, Any]]:
    """
    Get pylint messages for a file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        List[dict]: List of pylint messages
    """
    result = run_pylint(file_path)
    return result.get("messages", [])


def analyze_code_quality(directory: str) -> Dict[str, Any]:
    """
    Analyze code quality for all Python files in a directory.
    
    Args:
        directory: Directory containing Python files
        
    Returns:
        dict: Aggregate analysis results
    """
    from .file_tools import list_python_files
    
    dir_path = Path(directory)
    python_files = list_python_files(directory)
    
    if not python_files:
        return {
            "success": True,
            "total_files": 0,
            "average_score": 0.0,
            "files": [],
            "summary": {
                "errors": 0,
                "warnings": 0,
                "conventions": 0,
                "refactors": 0
            }
        }
    
    file_results = []
    total_score = 0.0
    summary = {
        "errors": 0,
        "warnings": 0,
        "conventions": 0,
        "refactors": 0
    }
    
    for file_path in python_files:
        result = run_pylint(file_path)
        
        file_results.append({
            "path": file_path,
            "score": result.get("score", 0.0),
            "message_count": len(result.get("messages", []))
        })
        
        total_score += result.get("score", 0.0)
        
        # Count message types
        for msg in result.get("messages", []):
            msg_type = msg.get("type", "").lower()
            if msg_type == "error":
                summary["errors"] += 1
            elif msg_type == "warning":
                summary["warnings"] += 1
            elif msg_type == "convention":
                summary["conventions"] += 1
            elif msg_type == "refactor":
                summary["refactors"] += 1
    
    average_score = total_score / len(python_files) if python_files else 0.0
    
    return {
        "success": True,
        "total_files": len(python_files),
        "average_score": round(average_score, 2),
        "files": file_results,
        "summary": summary
    }


def format_pylint_report(messages: List[Dict[str, Any]]) -> str:
    """
    Format pylint messages into a readable report.
    
    Args:
        messages: List of pylint message dictionaries
        
    Returns:
        str: Formatted report string
    """
    if not messages:
        return "No issues found."
    
    lines = ["Pylint Analysis Report", "=" * 50]
    
    # Group by type
    grouped = {}
    for msg in messages:
        msg_type = msg.get("type", "unknown")
        if msg_type not in grouped:
            grouped[msg_type] = []
        grouped[msg_type].append(msg)
    
    # Output by priority
    priority_order = ["error", "warning", "convention", "refactor", "info"]
    
    for msg_type in priority_order:
        if msg_type in grouped:
            lines.append(f"\n{msg_type.upper()}S ({len(grouped[msg_type])})")
            lines.append("-" * 30)
            
            for msg in grouped[msg_type]:
                line = msg.get("line", "?")
                symbol = msg.get("symbol", "unknown")
                message = msg.get("message", "")
                lines.append(f"  Line {line}: [{symbol}] {message}")
    
    return "\n".join(lines)
