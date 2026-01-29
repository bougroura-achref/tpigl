"""
Judge Agent - Validates refactored code through testing.
Improvements:
- Shared JSON parsing utility
- LLM retry logic with exponential backoff
- Configurable thresholds
- Proper logging
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage

from prompts.judge_prompt import (
    JUDGE_SYSTEM_PROMPT,
    JUDGE_EVALUATION_PROMPT,
    JUDGE_ERROR_ANALYSIS_PROMPT
)
from tools.file_tools import read_file
from tools.analysis_tools import run_pylint, get_pylint_score
from tools.test_tools import run_pytest, get_test_results, format_test_report
from utils.response_parser import parse_llm_json_response
from utils.retry_handler import retry_llm_call
from utils.llm_factory import get_llm
from config import get_config

logger = logging.getLogger(__name__)


class JudgeAgent:
    """
    The Judge Agent executes tests and validates the refactored code.
    """
    
    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.1,
        verbose: bool = False,
        success_score_threshold: float = None,
        regression_threshold: float = None
    ):
        """
        Initialize the Judge Agent.
        
        Args:
            model_name: LLM model to use
            temperature: LLM temperature
            verbose: Enable verbose output
            success_score_threshold: Minimum score for success (default: 8.0)
            regression_threshold: Score drop that triggers failure (default: 2.0)
        """
        config = get_config()
        self.model_name = model_name or config.llm.model_name
        self.temperature = temperature
        self.verbose = verbose
        
        # Configurable thresholds
        self.success_score_threshold = success_score_threshold or config.agents.judge_success_score_threshold
        self.regression_threshold = regression_threshold or config.agents.judge_regression_threshold
        self.require_tests_pass = config.agents.judge_require_tests_pass
        
        self.llm = get_llm(
            model_name=self.model_name,
            temperature=self.temperature,
            timeout=config.llm.timeout
        )
        
        self.system_prompt = JUDGE_SYSTEM_PROMPT
    
    @retry_llm_call(max_attempts=3, initial_delay=2.0)
    def _call_llm(self, messages: List) -> str:
        """Call LLM with retry logic."""
        response = self.llm.invoke(messages)
        return response.content
    
    def evaluate_file(
        self,
        file_path: str,
        sandbox_dir: str,
        original_score: float,
        changes_summary: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate a refactored file.
        
        Args:
            file_path: Path to the file to evaluate
            sandbox_dir: Sandbox directory
            original_score: Original pylint score
            changes_summary: Summary of changes made
            
        Returns:
            dict: Evaluation result with verdict
        """
        if self.verbose:
            logger.info(f"Judge evaluating: {file_path}")
        
        try:
            # Get new pylint score
            new_pylint = run_pylint(file_path)
            new_score = new_pylint.get("score", 0.0)
            
            # Run tests on the file's directory
            test_dir = Path(file_path).parent
            test_results = get_test_results(str(test_dir))
            
            # Prepare evaluation prompt
            eval_prompt = JUDGE_EVALUATION_PROMPT.format(
                file_path=file_path,
                original_score=original_score,
                original_test_status="Unknown",
                new_score=new_score,
                test_results=format_test_report(test_results),
                changes_summary=json.dumps(changes_summary, indent=2),
                score_diff=round(new_score - original_score, 2)
            )
            
            # Call LLM for evaluation with retry
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=eval_prompt)
            ]
            
            response_content = self._call_llm(messages)
            
            # Parse evaluation using shared utility
            evaluation = parse_llm_json_response(
                response_content,
                fallback={
                    "verdict": "RETRY",
                    "feedback_for_fixer": "Unable to parse evaluation"
                }
            )
            
            # Determine verdict based on rules
            verdict = self._determine_verdict(
                new_score=new_score,
                original_score=original_score,
                test_results=test_results,
                llm_verdict=evaluation.get("verdict", "RETRY")
            )
            
            if self.verbose:
                logger.info(f"Score: {original_score} -> {new_score}, Tests: {test_results.get('passed', 0)}/{test_results.get('total_tests', 0)}, Verdict: {verdict}")
            
            return {
                "success": True,
                "file_path": file_path,
                "verdict": verdict,
                "original_score": original_score,
                "new_score": new_score,
                "score_improvement": round(new_score - original_score, 2),
                "tests_passed": test_results.get("success", False),
                "test_summary": {
                    "passed": test_results.get("passed", 0),
                    "failed": test_results.get("failed", 0),
                    "total": test_results.get("total_tests", 0)
                },
                "evaluation": evaluation,
                "feedback_for_fixer": evaluation.get("feedback_for_fixer", "")
            }
            
        except Exception as e:
            logger.error(f"Evaluation failed for {file_path}: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "verdict": "RETRY"
            }
    
    def analyze_errors(
        self,
        file_path: str,
        sandbox_dir: str,
        test_failures: str,
        error_logs: str
    ) -> Dict[str, Any]:
        """
        Analyze test failures and provide feedback for the Fixer.
        
        Args:
            file_path: Path to the file with issues
            sandbox_dir: Sandbox directory
            test_failures: Description of test failures
            error_logs: Error log output
            
        Returns:
            dict: Error analysis with fix suggestions
        """
        if self.verbose:
            logger.info(f"Judge analyzing errors for: {file_path}")
        
        try:
            # Read current code
            current_code = read_file(file_path, sandbox_dir)
            
            # Prepare analysis prompt
            analysis_prompt = JUDGE_ERROR_ANALYSIS_PROMPT.format(
                test_failures=test_failures,
                error_logs=error_logs,
                current_code=current_code
            )
            
            # Call LLM with retry
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=analysis_prompt)
            ]
            
            response_content = self._call_llm(messages)
            
            # Parse analysis using shared utility
            analysis = parse_llm_json_response(
                response_content,
                fallback={
                    "root_causes": [],
                    "priority_order": [],
                    "estimated_difficulty": "medium"
                }
            )
            
            return {
                "success": True,
                "file_path": file_path,
                "analysis": analysis,
                "root_causes": analysis.get("root_causes", []),
                "priority_order": analysis.get("priority_order", []),
                "estimated_difficulty": analysis.get("estimated_difficulty", "medium")
            }
            
        except Exception as e:
            logger.error(f"Error analysis failed for {file_path}: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def _determine_verdict(
        self,
        new_score: float,
        original_score: float,
        test_results: Dict[str, Any],
        llm_verdict: str
    ) -> str:
        """
        Determine the final verdict based on objective criteria.
        Uses configurable thresholds for flexibility.
        
        Args:
            new_score: New pylint score
            original_score: Original pylint score
            test_results: Test execution results
            llm_verdict: LLM's suggested verdict
            
        Returns:
            str: Final verdict (SUCCESS, RETRY, or FAILURE)
        """
        tests_pass = test_results.get("success", False)
        score_improved = new_score > original_score
        score_good = new_score >= self.success_score_threshold
        
        # SUCCESS conditions
        if tests_pass and (score_improved or score_good):
            return "SUCCESS"
        
        # If no tests exist, rely on score - require actual improvement or good score
        if test_results.get("total_tests", 0) == 0:
            if score_good:
                return "SUCCESS"
            if score_improved:
                return "SUCCESS"
            return "RETRY"
        
        # FAILURE if score got much worse (configurable threshold)
        if new_score < original_score - self.regression_threshold:
            return "FAILURE"
        
        # Default to RETRY for fixable issues
        return "RETRY"
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into a structured format.
        
        Args:
            response: Raw LLM response
            
        Returns:
            dict: Parsed evaluation
        """
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
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
            return {
                "verdict": "RETRY",
                "evaluation": {"raw_response": response},
                "feedback_for_fixer": "Unable to parse evaluation, please review manually"
            }
