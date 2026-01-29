"""
Fixer Agent - Implements code fixes based on refactoring plans.
Improvements:
- Shared JSON parsing utility
- LLM retry logic with exponential backoff
- Diff generation for tracking changes
- Proper logging
"""

import difflib
import logging
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage

from prompts.fixer_prompt import (
    FIXER_SYSTEM_PROMPT,
    FIXER_REPAIR_PROMPT,
    FIXER_ITERATIVE_PROMPT
)
from tools.file_tools import read_file, write_file, backup_file
from utils.response_parser import parse_llm_json_response, extract_code_from_response
from utils.retry_handler import retry_llm_call
from utils.llm_factory import get_llm
from config import get_config

logger = logging.getLogger(__name__)


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
            model_name: LLM model to use
            temperature: LLM temperature (lower = more deterministic)
            verbose: Enable verbose output
        """
        config = get_config()
        self.model_name = model_name or config.llm.model_name
        self.temperature = temperature
        self.verbose = verbose
        self.create_backups = config.agents.fixer_create_backups
        self.validate_syntax = config.agents.fixer_validate_syntax
        
        self.llm = get_llm(
            model_name=self.model_name,
            temperature=self.temperature,
            timeout=config.llm.timeout
        )
        
        self.system_prompt = FIXER_SYSTEM_PROMPT
    
    @retry_llm_call(max_attempts=3, initial_delay=2.0)
    def _call_llm(self, messages: List) -> str:
        """Call LLM with retry logic."""
        response = self.llm.invoke(messages)
        return response.content
    
    def _generate_diff(self, original: str, fixed: str, file_path: str = "") -> str:
        """
        Generate unified diff for tracking changes.
        
        Args:
            original: Original code
            fixed: Fixed code
            file_path: File path for diff header
            
        Returns:
            Unified diff string
        """
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=f"a/{file_path}" if file_path else "original",
            tofile=f"b/{file_path}" if file_path else "fixed"
        )
        return ''.join(diff)
    
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
            logger.info(f"Fixer working on: {file_path}")
        
        try:
            # Read original code
            original_code = read_file(file_path, sandbox_dir)
            
            # Backup before modifying
            backup_path = None
            if not dry_run and self.create_backups:
                backup_path = backup_file(file_path, sandbox_dir)
                if self.verbose and backup_path:
                    logger.info(f"Backup created: {backup_path}")
            
            # Prepare prompt
            import json
            repair_prompt = FIXER_REPAIR_PROMPT.format(
                file_path=file_path,
                original_code=original_code,
                refactoring_plan=json.dumps(refactoring_plan, indent=2),
                issues=json.dumps(issues, indent=2)
            )
            
            # Call LLM with retry
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=repair_prompt)
            ]
            
            response_content = self._call_llm(messages)
            
            # Parse response using shared utility
            fix_result = parse_llm_json_response(response_content)
            
            # Extract fixed code (try multiple sources)
            fixed_code = fix_result.get("fixed_code", "")
            if not fixed_code:
                fixed_code = extract_code_from_response(response_content)
            
            if not fixed_code:
                return {
                    "success": False,
                    "error": "No fixed code generated",
                    "file_path": file_path
                }
            
            # Validate the fixed code is syntactically correct
            if self.validate_syntax:
                validation = self._validate_python_syntax(fixed_code)
                if not validation["valid"]:
                    return {
                        "success": False,
                        "error": f"Generated code has syntax errors: {validation['error']}",
                        "file_path": file_path,
                        "fixed_code": fixed_code
                    }
            
            # Generate diff for tracking
            diff = self._generate_diff(original_code, fixed_code, file_path)
            
            # Write the fixed code (unless dry run)
            if not dry_run:
                write_file(file_path, fixed_code, sandbox_dir)
                if self.verbose:
                    logger.info(f"File updated: {file_path}")
            else:
                if self.verbose:
                    logger.info(f"Dry run - no changes written")
            
            return {
                "success": True,
                "file_path": file_path,
                "original_code": original_code,
                "fixed_code": fixed_code,
                "diff": diff,
                "changes_made": fix_result.get("changes_made", []),
                "backup_path": backup_path,
                "dry_run": dry_run
            }
            
        except Exception as e:
            logger.error(f"Fix failed for {file_path}: {str(e)}")
            
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
            logger.info(f"Fixer (iteration {iteration}/{max_iterations}): {file_path}")
        
        try:
            # Read current code
            current_code = read_file(file_path, sandbox_dir)
            
            # Prepare iterative prompt
            import json
            prompt = FIXER_ITERATIVE_PROMPT.format(
                file_path=file_path,
                current_code=current_code,
                error_logs=error_logs,
                previous_changes=json.dumps(previous_changes, indent=2),
                iteration=iteration,
                max_iterations=max_iterations
            )
            
            # Call LLM with retry
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response_content = self._call_llm(messages)
            
            # Parse response using shared utility
            fix_result = parse_llm_json_response(response_content)
            
            # Extract fixed code (try multiple sources)
            fixed_code = fix_result.get("fixed_code", "")
            if not fixed_code:
                fixed_code = extract_code_from_response(response_content)
            
            if not fixed_code:
                return {
                    "success": False,
                    "error": "No fixed code generated",
                    "file_path": file_path,
                    "iteration": iteration
                }
            
            # Validate syntax
            if self.validate_syntax:
                validation = self._validate_python_syntax(fixed_code)
                if not validation["valid"]:
                    return {
                        "success": False,
                        "error": f"Generated code has syntax errors: {validation['error']}",
                        "file_path": file_path,
                        "iteration": iteration
                    }
            
            # Generate diff
            diff = self._generate_diff(current_code, fixed_code, file_path)
            
            # Write the fixed code
            if not dry_run:
                write_file(file_path, fixed_code, sandbox_dir)
                if self.verbose:
                    logger.info(f"File updated (iteration {iteration})")
            
            return {
                "success": True,
                "file_path": file_path,
                "fixed_code": fixed_code,
                "diff": diff,
                "error_analysis": fix_result.get("error_analysis", ""),
                "new_changes": fix_result.get("new_changes", []),
                "confidence": fix_result.get("confidence", 0.5),
                "iteration": iteration,
                "dry_run": dry_run
            }
            
        except Exception as e:
            logger.error(f"Fix with feedback failed for {file_path}: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "iteration": iteration
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
