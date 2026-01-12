"""
Fixer Agent - Implements code fixes based on refactoring plans
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from prompts.fixer_prompt import (
    FIXER_SYSTEM_PROMPT,
    FIXER_REPAIR_PROMPT,
    FIXER_ITERATIVE_PROMPT
)
from tools.file_tools import read_file, write_file, backup_file


class FixerAgent:
    """
    The Fixer Agent reads refactoring plans and modifies code to fix issues.
    """
    
    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.1,
        verbose: bool = False
    ):
        """
        Initialize the Fixer Agent.
        
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
        
        self.system_prompt = FIXER_SYSTEM_PROMPT
    
    def fix_file(
        self,
        file_path: str,
        sandbox_dir: str,
        refactoring_plan: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Fix a single file based on the refactoring plan.
        
        Args:
            file_path: Path to the file to fix
            sandbox_dir: Sandbox directory for security
            refactoring_plan: The refactoring plan from Auditor
            issues: List of issues to fix
            dry_run: If True, don't actually write changes
            
        Returns:
            dict: Fix results
        """
        if self.verbose:
            print(f"  🔧 Fixer working on: {file_path}")
        
        try:
            # Read original code
            original_code = read_file(file_path, sandbox_dir)
            
            # Backup before modifying
            if not dry_run:
                backup_path = backup_file(file_path, sandbox_dir)
                if self.verbose and backup_path:
                    print(f"    📦 Backup created: {backup_path}")
            
            # Prepare prompt
            repair_prompt = FIXER_REPAIR_PROMPT.format(
                file_path=file_path,
                original_code=original_code,
                refactoring_plan=json.dumps(refactoring_plan, indent=2),
                issues=json.dumps(issues, indent=2)
            )
            
            # Call LLM
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=repair_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse response
            fix_result = self._parse_response(response.content)
            
            # Extract fixed code
            fixed_code = fix_result.get("fixed_code", "")
            
            if not fixed_code:
                return {
                    "success": False,
                    "error": "No fixed code generated",
                    "file_path": file_path
                }
            
            # Validate the fixed code is syntactically correct
            validation = self._validate_python_syntax(fixed_code)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": f"Generated code has syntax errors: {validation['error']}",
                    "file_path": file_path,
                    "fixed_code": fixed_code
                }
            
            # Write the fixed code (unless dry run)
            if not dry_run:
                write_file(file_path, fixed_code, sandbox_dir)
                if self.verbose:
                    print(f"    ✅ File updated")
            else:
                if self.verbose:
                    print(f"    ⏸️  Dry run - no changes written")
            
            return {
                "success": True,
                "file_path": file_path,
                "original_code": original_code,
                "fixed_code": fixed_code,
                "changes_made": fix_result.get("changes_made", []),
                "dry_run": dry_run
            }
            
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Fix failed: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def fix_with_feedback(
        self,
        file_path: str,
        sandbox_dir: str,
        error_logs: str,
        previous_changes: List[str],
        iteration: int,
        max_iterations: int,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Fix a file based on error feedback (self-healing loop).
        
        Args:
            file_path: Path to the file to fix
            sandbox_dir: Sandbox directory for security
            error_logs: Error logs from failed tests
            previous_changes: List of previous changes made
            iteration: Current iteration number
            max_iterations: Maximum iterations allowed
            dry_run: If True, don't write changes
            
        Returns:
            dict: Fix results
        """
        if self.verbose:
            print(f"  🔧 Fixer (iteration {iteration}/{max_iterations}): {file_path}")
        
        try:
            # Read current code
            current_code = read_file(file_path, sandbox_dir)
            
            # Prepare iterative prompt
            prompt = FIXER_ITERATIVE_PROMPT.format(
                file_path=file_path,
                current_code=current_code,
                error_logs=error_logs,
                previous_changes=json.dumps(previous_changes, indent=2),
                iteration=iteration,
                max_iterations=max_iterations
            )
            
            # Call LLM
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse response
            fix_result = self._parse_response(response.content)
            
            # Extract fixed code
            fixed_code = fix_result.get("fixed_code", "")
            
            if not fixed_code:
                return {
                    "success": False,
                    "error": "No fixed code generated",
                    "file_path": file_path,
                    "iteration": iteration
                }
            
            # Validate syntax
            validation = self._validate_python_syntax(fixed_code)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": f"Generated code has syntax errors: {validation['error']}",
                    "file_path": file_path,
                    "iteration": iteration
                }
            
            # Write the fixed code
            if not dry_run:
                write_file(file_path, fixed_code, sandbox_dir)
                if self.verbose:
                    print(f"    ✅ File updated (iteration {iteration})")
            
            return {
                "success": True,
                "file_path": file_path,
                "fixed_code": fixed_code,
                "error_analysis": fix_result.get("error_analysis", ""),
                "new_changes": fix_result.get("new_changes", []),
                "confidence": fix_result.get("confidence", 0.5),
                "iteration": iteration,
                "dry_run": dry_run
            }
            
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Fix failed: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "iteration": iteration
            }
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into a structured format.
        
        Args:
            response: Raw LLM response
            
        Returns:
            dict: Parsed fix result
        """
        try:
            # Look for JSON block
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```python" in response:
                # Sometimes LLM puts code directly
                code_start = response.find("```python") + 9
                code_end = response.find("```", code_start)
                code = response[code_start:code_end].strip()
                return {"fixed_code": code, "changes_made": ["Code refactored"]}
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            
            return json.loads(json_str)
            
        except json.JSONDecodeError:
            # Try to extract code if JSON parsing fails
            if "def " in response or "class " in response:
                return {
                    "fixed_code": response,
                    "changes_made": ["Code extracted from response"]
                }
            return {
                "fixed_code": "",
                "error": "Failed to parse response",
                "raw_response": response
            }
    
    def _validate_python_syntax(self, code: str) -> Dict[str, Any]:
        """
        Validate that the code is syntactically correct Python.
        
        Args:
            code: Python code to validate
            
        Returns:
            dict: Validation result
        """
        try:
            compile(code, "<string>", "exec")
            return {"valid": True}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Line {e.lineno}: {e.msg}"
            }
