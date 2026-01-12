"""
Auditor Agent - Analyzes code and produces refactoring plans
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from prompts.auditor_prompt import AUDITOR_SYSTEM_PROMPT, AUDITOR_ANALYSIS_PROMPT
from tools.file_tools import read_file, list_python_files
from tools.analysis_tools import run_pylint, format_pylint_report


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
            model_name: Gemini model to use
            temperature: LLM temperature (lower = more deterministic)
            verbose: Enable verbose output
        """
        self.model_name = model_name or os.getenv("MODEL_NAME", "gemini-2.5-flash")
        self.temperature = temperature
        self.verbose = verbose
        
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=self.temperature
        )
        
        self.system_prompt = AUDITOR_SYSTEM_PROMPT
    
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
            print(f"  🔍 Auditor analyzing: {file_path}")
        
        try:
            # Read file content
            code_content = read_file(file_path, sandbox_dir)
            
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
            
            # Call LLM
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse response
            analysis = self._parse_response(response.content)
            
            # Add metadata
            analysis["file_path"] = file_path
            analysis["original_pylint_score"] = pylint_score
            analysis["pylint_messages"] = pylint_result.get("messages", [])
            
            if self.verbose:
                print(f"    ✅ Analysis complete. Score: {pylint_score}/10")
                print(f"    📋 Issues found: {len(analysis.get('issues', []))}")
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Analysis failed: {str(e)}")
            
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
            print(f"🔍 Auditor analyzing directory: {directory}")
        
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
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into a structured format.
        
        Args:
            response: Raw LLM response
            
        Returns:
            dict: Parsed analysis
        """
        # Try to extract JSON from response
        try:
            # Look for JSON block
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                # Try to find JSON object directly
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            
            return json.loads(json_str)
            
        except json.JSONDecodeError:
            # Return structured fallback
            return {
                "summary": "Analysis completed but response parsing failed",
                "issues": [],
                "refactoring_plan": [],
                "raw_response": response
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
        
        # First, collect all high-priority issues
        for analysis in analyses:
            if not analysis.get("success"):
                continue
            
            file_analysis = analysis.get("analysis", {})
            file_path = file_analysis.get("file_path", "unknown")
            
            for issue in file_analysis.get("issues", []):
                if issue.get("priority") == "high":
                    plan.append({
                        "step": step_num,
                        "file": file_path,
                        "priority": "high",
                        "action": issue.get("fix", issue.get("description", "Fix issue")),
                        "type": issue.get("type", "unknown")
                    })
                    step_num += 1
        
        # Then medium priority
        for analysis in analyses:
            if not analysis.get("success"):
                continue
            
            file_analysis = analysis.get("analysis", {})
            file_path = file_analysis.get("file_path", "unknown")
            
            for issue in file_analysis.get("issues", []):
                if issue.get("priority") == "medium":
                    plan.append({
                        "step": step_num,
                        "file": file_path,
                        "priority": "medium",
                        "action": issue.get("fix", issue.get("description", "Fix issue")),
                        "type": issue.get("type", "unknown")
                    })
                    step_num += 1
        
        return plan
