"""
Judge Agent - Validates refactored code through testing
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from prompts.judge_prompt import (
    JUDGE_SYSTEM_PROMPT,
    JUDGE_EVALUATION_PROMPT,
    JUDGE_ERROR_ANALYSIS_PROMPT
)
from tools.file_tools import read_file
from tools.analysis_tools import run_pylint, get_pylint_score
from tools.test_tools import run_pytest, get_test_results, format_test_report


class JudgeAgent:
    """
    The Judge Agent executes tests and validates the refactored code.
    """
    
    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.1,
        verbose: bool = False
    ):
        """
        Initialize the Judge Agent.
        
        Args:
            model_name: Gemini model to use
            temperature: LLM temperature
            verbose: Enable verbose output
        """
        self.model_name = model_name or os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")
        self.temperature = temperature
        self.verbose = verbose
        
        self.llm = ChatAnthropic(
            model=self.model_name,
            temperature=self.temperature
        )
        
        self.system_prompt = JUDGE_SYSTEM_PROMPT
    
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
            print(f"  ⚖️  Judge evaluating: {file_path}")
        
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
            
            # Call LLM for evaluation
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=eval_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse evaluation
            evaluation = self._parse_response(response.content)
            
            # Determine verdict based on rules
            verdict = self._determine_verdict(
                new_score=new_score,
                original_score=original_score,
                test_results=test_results,
                llm_verdict=evaluation.get("verdict", "RETRY")
            )
            
            if self.verbose:
                print(f"    Score: {original_score} -> {new_score}")
                print(f"    Tests: {test_results.get('passed', 0)}/{test_results.get('total_tests', 0)} passed")
                print(f"    Verdict: {verdict}")
            
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
            if self.verbose:
                print(f"    ❌ Evaluation failed: {str(e)}")
            
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
            print(f"  🔍 Judge analyzing errors for: {file_path}")
        
        try:
            # Read current code
            current_code = read_file(file_path, sandbox_dir)
            
            # Prepare analysis prompt
            analysis_prompt = JUDGE_ERROR_ANALYSIS_PROMPT.format(
                test_failures=test_failures,
                error_logs=error_logs,
                current_code=current_code
            )
            
            # Call LLM
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse analysis
            analysis = self._parse_response(response.content)
            
            return {
                "success": True,
                "file_path": file_path,
                "analysis": analysis,
                "root_causes": analysis.get("root_causes", []),
                "priority_order": analysis.get("priority_order", []),
                "estimated_difficulty": analysis.get("estimated_difficulty", "medium")
            }
            
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Error analysis failed: {str(e)}")
            
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
        score_good = new_score >= 8.0
        
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
        
        # FAILURE if score got much worse
        if new_score < original_score - 2.0:
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
