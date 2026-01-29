"""
Auditor Agent - Analyzes code and produces refactoring plans.
Improvements:
- Shared JSON parsing utility
- LLM retry logic with exponential backoff
- File content caching to avoid redundant API calls
- Proper logging instead of print statements
"""

import hashlib
import logging
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage

from prompts.auditor_prompt import AUDITOR_SYSTEM_PROMPT, AUDITOR_ANALYSIS_PROMPT
from tools.file_tools import read_file, list_python_files
from tools.analysis_tools import run_pylint, format_pylint_report
from utils.response_parser import parse_llm_json_response
from utils.retry_handler import retry_llm_call
from utils.llm_factory import get_llm
from config import get_config

logger = logging.getLogger(__name__)


class AuditorAgent:
    """
    The Auditor Agent reads code, runs static analysis, and produces refactoring plans.
    """
    
    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.1,
        verbose: bool = False
    ):
        """
        Initialize the Auditor Agent.
        
        Args:
            model_name: LLM model to use
            temperature: LLM temperature (lower = more deterministic)
            verbose: Enable verbose output
        """
        config = get_config()
        self.model_name = model_name or config.llm.model_name
        self.temperature = temperature
        self.verbose = verbose
        self.cache_enabled = config.agents.auditor_cache_enabled
        
        self.llm = get_llm(
            model_name=self.model_name,
            temperature=self.temperature,
            timeout=config.llm.timeout
        )
        
        self.system_prompt = AUDITOR_SYSTEM_PROMPT
        
        # Cache for file analyses (hash -> analysis result)
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def _get_file_hash(self, content: str) -> str:
        """Generate hash of file content for caching."""
        return hashlib.md5(content.encode()).hexdigest()
    
    @retry_llm_call(max_attempts=3, initial_delay=2.0)
    def _call_llm(self, messages: List) -> str:
        """Call LLM with retry logic."""
        response = self.llm.invoke(messages)
        return response.content
    
    def analyze_file(self, file_path: str, sandbox_dir: str) -> Dict[str, Any]:
        """
        Analyze a single Python file.
        
        Args:
            file_path: Path to the Python file
            sandbox_dir: Sandbox directory for security validation
            
        Returns:
            dict: Analysis results with refactoring plan
        """
        if self.verbose:
            logger.info(f"Auditor analyzing: {file_path}")
        
        try:
            # Read file content
            code_content = read_file(file_path, sandbox_dir)
            
            # Check cache
            content_hash = self._get_file_hash(code_content)
            cache_key = f"{file_path}:{content_hash}"
            
            if self.cache_enabled and cache_key in self._cache:
                if self.verbose:
                    logger.info(f"Using cached analysis for: {file_path}")
                return self._cache[cache_key]
            
            # Run pylint analysis
            pylint_result = run_pylint(file_path)
            pylint_score = pylint_result.get("score", 0.0)
            pylint_messages = format_pylint_report(pylint_result.get("messages", []))
            
            # Prepare prompt
            analysis_prompt = AUDITOR_ANALYSIS_PROMPT.format(
                file_path=file_path,
                code_content=code_content,
                pylint_score=pylint_score,
                pylint_messages=pylint_messages
            )
            
            # Call LLM with retry
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=analysis_prompt)
            ]
            
            response_content = self._call_llm(messages)
            
            # Parse response using shared utility
            analysis = parse_llm_json_response(
                response_content,
                fallback={
                    "summary": "Analysis completed but response parsing failed",
                    "issues": [],
                    "refactoring_plan": []
                }
            )
            
            # Add metadata
            analysis["file_path"] = file_path
            analysis["original_pylint_score"] = pylint_score
            analysis["pylint_messages"] = pylint_result.get("messages", [])
            
            result = {
                "success": True,
                "analysis": analysis
            }
            
            # Cache the result
            if self.cache_enabled:
                self._cache[cache_key] = result
            
            if self.verbose:
                logger.info(f"Analysis complete. Score: {pylint_score}/10, Issues: {len(analysis.get('issues', []))}")
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {file_path}: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def analyze_directory(self, directory: str) -> Dict[str, Any]:
        """
        Analyze all Python files in a directory.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            dict: Comprehensive analysis results
        """
        if self.verbose:
            logger.info(f"Auditor analyzing directory: {directory}")
        
        python_files = list_python_files(directory)
        
        if not python_files:
            return {
                "success": True,
                "message": "No Python files found",
                "analyses": [],
                "total_files": 0
            }
        
        analyses = []
        total_score = 0.0
        
        for file_path in python_files:
            result = self.analyze_file(file_path, directory)
            analyses.append(result)
            
            if result["success"]:
                total_score += result["analysis"].get("original_pylint_score", 0.0)
        
        successful = [a for a in analyses if a["success"]]
        average_score = total_score / len(successful) if successful else 0.0
        
        # Create prioritized refactoring plan
        refactoring_plan = self._create_aggregate_plan(analyses)
        
        return {
            "success": True,
            "total_files": len(python_files),
            "analyzed_files": len(successful),
            "average_score": round(average_score, 2),
            "analyses": analyses,
            "aggregate_refactoring_plan": refactoring_plan
        }
    
    def _create_aggregate_plan(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create an aggregate refactoring plan from multiple file analyses.
        
        Args:
            analyses: List of individual file analyses
            
        Returns:
            List[dict]: Prioritized refactoring steps
        """
        plan = []
        step_num = 1
        
        # Priority order: high -> medium -> low
        for priority in ["high", "medium", "low"]:
            for analysis in analyses:
                if not analysis.get("success"):
                    continue
                
                file_analysis = analysis.get("analysis", {})
                file_path = file_analysis.get("file_path", "unknown")
                
                for issue in file_analysis.get("issues", []):
                    if issue.get("priority") == priority:
                        plan.append({
                            "step": step_num,
                            "file": file_path,
                            "priority": priority,
                            "action": issue.get("fix", issue.get("description", "Fix issue")),
                            "type": issue.get("type", "unknown"),
                            "line": issue.get("line")
                        })
                        step_num += 1
        
        return plan
    
    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self._cache.clear()
        if self.verbose:
            logger.info("Auditor cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_files": len(self._cache)
        }
