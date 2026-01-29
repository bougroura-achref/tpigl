"""
Refactoring Graph - LangGraph workflow for agent orchestration.
Improvements:
- Proper TypedDict state
- Error log size limits
- Checkpoint support
- Better logging
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Literal, Optional, List, TypedDict, TYPE_CHECKING

from pathlib import Path

from langgraph.graph import StateGraph, END

from agents import AuditorAgent, FixerAgent, JudgeAgent
from tools.file_tools import list_python_files
from logging_system.telemetry import TelemetryLogger
from config import get_config

if TYPE_CHECKING:
    from .state import SwarmState

logger = logging.getLogger(__name__)

# Maximum error logs to keep per file to prevent memory issues
MAX_ERROR_LOGS = 50


class FileStateDict(TypedDict, total=False):
    """Type definition for file state."""
    path: str
    status: str
    original_score: float
    current_score: float
    issues: List[Dict[str, Any]]
    refactoring_plan: List[Dict[str, Any]]
    fix_iterations: int
    changes_made: List[str]
    error_logs: List[str]
    tests_passed: bool
    verdict: str


class GraphState(TypedDict, total=False):
    """Type definition for graph state."""
    target_dir: str
    files: Dict[str, FileStateDict]
    pending_files: List[str]
    current_file: Optional[str]
    iteration: int
    max_iterations: int
    status: str
    initial_pylint_score: float
    final_pylint_score: float
    tests_passed: bool


class RefactoringGraph:
    """
    Orchestrates the refactoring workflow using LangGraph.
    Manages the Auditor -> Fixer -> Judge pipeline with self-healing loop.
    """
    
    def __init__(
        self,
        target_dir: Path,
        max_iterations: int = 10,
        verbose: bool = False,
        telemetry: Optional[TelemetryLogger] = None,
        dry_run: bool = False
    ):
        """
        Initialize the Refactoring Graph.
        
        Args:
            target_dir: Directory containing code to refactor
            max_iterations: Maximum self-healing loop iterations
            verbose: Enable verbose output
            telemetry: Telemetry logger instance
            dry_run: If True, don't actually write changes
        """
        self.target_dir = target_dir
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.telemetry = telemetry
        self.dry_run = dry_run
        self.config = get_config()
        
        # Initialize agents
        self.auditor = AuditorAgent(verbose=verbose)
        self.fixer = FixerAgent(verbose=verbose)
        self.judge = JudgeAgent(verbose=verbose)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            StateGraph: Compiled workflow graph
        """
        # Define the state graph with typed dict
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("fix", self._fix_node)
        workflow.add_node("evaluate", self._evaluate_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        # Add edges
        workflow.add_edge("initialize", "analyze")
        workflow.add_edge("analyze", "fix")
        workflow.add_edge("fix", "evaluate")
        
        # Conditional edges from evaluate
        workflow.add_conditional_edges(
            "evaluate",
            self._should_continue,
            {
                "continue": "fix",  # Loop back to fix
                "next_file": "analyze",  # Move to next file
                "end": "finalize"  # Finish
            }
        )
        
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _initialize_node(self, state: GraphState) -> GraphState:
        """Initialize the workflow state"""
        if self.verbose:
            logger.info("Initializing refactoring workflow...")
        
        # Discover Python files
        python_files = list_python_files(str(self.target_dir))
        
        if self.verbose:
            logger.info(f"Found {len(python_files)} Python files")
        
        # Initialize file states
        files: Dict[str, FileStateDict] = {}
        for file_path in python_files:
            files[file_path] = {
                "path": file_path,
                "status": "pending",
                "original_score": 0.0,
                "current_score": 0.0,
                "issues": [],
                "refactoring_plan": [],
                "fix_iterations": 0,
                "changes_made": [],
                "error_logs": [],
                "tests_passed": False,
                "verdict": ""
            }
        
        # Log event
        if self.telemetry:
            self.telemetry.log_event("initialization_complete", {
                "file_count": len(python_files),
                "files": python_files
            })
        
        return {
            **state,
            "files": files,
            "pending_files": python_files.copy(),
            "current_file": python_files[0] if python_files else None,
            "iteration": 0,
            "status": "initialized"
        }
    
    def _analyze_node(self, state: GraphState) -> GraphState:
        """Run the Auditor on the current file"""
        current_file = state.get("current_file")
        
        if not current_file:
            return {**state, "status": "no_files"}
        
        if self.verbose:
            logger.info(f"Analyzing: {current_file}")
        
        # Run auditor analysis
        result = self.auditor.analyze_file(current_file, str(self.target_dir))
        
        if result["success"]:
            analysis = result["analysis"]
            
            # Update file state
            state["files"][current_file].update({
                "status": "analyzed",
                "original_score": analysis.get("original_pylint_score", 0.0),
                "current_score": analysis.get("original_pylint_score", 0.0),
                "issues": analysis.get("issues", []),
                "refactoring_plan": analysis.get("refactoring_plan", [])
            })
            
            # Log event
            if self.telemetry:
                self.telemetry.log_event("file_analyzed", {
                    "file": current_file,
                    "score": analysis.get("original_pylint_score", 0.0),
                    "issues_count": len(analysis.get("issues", []))
                })
        else:
            state["files"][current_file]["status"] = "analysis_failed"
            self._append_error_log(state["files"][current_file], result.get("error", "Unknown error"))
        
        return state
    
    def _append_error_log(self, file_state: FileStateDict, error: str) -> None:
        """Append error to log with size limit to prevent memory issues."""
        file_state["error_logs"].append(error)
        if len(file_state["error_logs"]) > MAX_ERROR_LOGS:
            file_state["error_logs"] = file_state["error_logs"][-MAX_ERROR_LOGS:]
    
    def _fix_node(self, state: GraphState) -> GraphState:
        """Run the Fixer on the current file"""
        current_file = state.get("current_file")
        
        if not current_file:
            return state
        
        file_state = state["files"][current_file]
        
        if self.verbose:
            iteration = file_state.get("fix_iterations", 0) + 1
            logger.info(f"Fixing (iteration {iteration}): {current_file}")
        
        # Check if this is a retry
        if file_state.get("fix_iterations", 0) > 0:
            # Use feedback-based fixing
            result = self.fixer.fix_with_feedback(
                file_path=current_file,
                sandbox_dir=str(self.target_dir),
                error_logs="\n".join(file_state.get("error_logs", [])[-10:]),  # Limit to last 10 errors
                previous_changes=file_state.get("changes_made", []),
                iteration=file_state["fix_iterations"] + 1,
                max_iterations=self.max_iterations,
                dry_run=self.dry_run
            )
        else:
            # Initial fix
            result = self.fixer.fix_file(
                file_path=current_file,
                sandbox_dir=str(self.target_dir),
                refactoring_plan=file_state.get("refactoring_plan", []),
                issues=file_state.get("issues", []),
                dry_run=self.dry_run
            )
        
        if result["success"]:
            file_state["status"] = "fixed"
            file_state["fix_iterations"] += 1
            file_state["changes_made"].extend(result.get("changes_made", result.get("new_changes", [])))
            
            if self.telemetry:
                self.telemetry.log_event("file_fixed", {
                    "file": current_file,
                    "iteration": file_state["fix_iterations"],
                    "changes": result.get("changes_made", result.get("new_changes", []))
                })
        else:
            self._append_error_log(file_state, result.get("error", "Fix failed"))
            file_state["fix_iterations"] += 1
        
        state["files"][current_file] = file_state
        return state
    
    def _evaluate_node(self, state: GraphState) -> GraphState:
        """Run the Judge to evaluate the fixes"""
        current_file = state.get("current_file")
        
        if not current_file:
            return state
        
        file_state = state["files"][current_file]
        
        if self.verbose:
            logger.info(f"Evaluating: {current_file}")
        
        # Run judge evaluation
        result = self.judge.evaluate_file(
            file_path=current_file,
            sandbox_dir=str(self.target_dir),
            original_score=file_state.get("original_score", 0.0),
            changes_summary=file_state.get("changes_made", [])
        )
        
        if result["success"]:
            file_state["status"] = "evaluated"
            file_state["current_score"] = result.get("new_score", 0.0)
            file_state["tests_passed"] = result.get("tests_passed", False)
            file_state["verdict"] = result.get("verdict", "RETRY")
            
            # If verdict is RETRY, add feedback to error logs
            if result["verdict"] == "RETRY":
                feedback = result.get("feedback_for_fixer", "")
                if feedback:
                    self._append_error_log(file_state, feedback)
            
            if self.telemetry:
                self.telemetry.log_event("file_evaluated", {
                    "file": current_file,
                    "verdict": result["verdict"],
                    "original_score": file_state["original_score"],
                    "new_score": result["new_score"],
                    "tests_passed": result["tests_passed"]
                })
        else:
            file_state["verdict"] = "RETRY"
            self._append_error_log(file_state, result.get("error", "Evaluation failed"))
        
        state["files"][current_file] = file_state
        state["iteration"] = state.get("iteration", 0) + 1
        
        return state
    
    def _should_continue(self, state: GraphState) -> Literal["continue", "next_file", "end"]:
        """Decide whether to continue, move to next file, or end"""
        current_file = state.get("current_file")
        
        if not current_file:
            return "end"
        
        file_state = state["files"][current_file]
        verdict = file_state.get("verdict", "")
        iterations = file_state.get("fix_iterations", 0)
        
        # SUCCESS - move to next file
        if verdict == "SUCCESS":
            file_state["status"] = "success"
            pending = state.get("pending_files", [])
            
            # Remove current file from pending
            if current_file in pending:
                pending.remove(current_file)
                state["pending_files"] = pending
            
            # Get next file
            if pending:
                state["current_file"] = pending[0]
                return "next_file"
            return "end"
        
        # FAILURE or max iterations - mark as failed, move on
        if verdict == "FAILURE" or iterations >= self.max_iterations:
            file_state["status"] = "failed"
            pending = state.get("pending_files", [])
            
            if current_file in pending:
                pending.remove(current_file)
                state["pending_files"] = pending
            
            if pending:
                state["current_file"] = pending[0]
                return "next_file"
            return "end"
        
        # RETRY - continue fixing
        return "continue"
    
    def _finalize_node(self, state: GraphState) -> GraphState:
        """Finalize the workflow and calculate metrics"""
        if self.verbose:
            logger.info("Finalizing refactoring workflow...")
        
        # Calculate final metrics
        total_original = 0.0
        total_final = 0.0
        success_count = 0
        file_count = len(state.get("files", {}))
        
        for file_path, file_state in state.get("files", {}).items():
            total_original += file_state.get("original_score", 0.0)
            total_final += file_state.get("current_score", 0.0)
            if file_state.get("verdict") == "SUCCESS":
                success_count += 1
        
        initial_score = round(total_original / file_count, 2) if file_count > 0 else 0.0
        final_score = round(total_final / file_count, 2) if file_count > 0 else 0.0
        
        state["initial_pylint_score"] = initial_score
        state["final_pylint_score"] = final_score
        state["tests_passed"] = success_count == file_count
        state["status"] = "success" if state["tests_passed"] else "partial"
        
        if self.telemetry:
            self.telemetry.log_event("workflow_complete", {
                "status": state["status"],
                "files_processed": file_count,
                "files_successful": success_count,
                "initial_score": initial_score,
                "final_score": final_score
            })
        
        if self.verbose:
            logger.info(f"Status: {state['status']}, Files: {success_count}/{file_count}, Score: {initial_score} -> {final_score}")
        
        return state
    
    def run(self, initial_state) -> "SwarmState":
        """
        Run the refactoring workflow.
        
        Args:
            initial_state: Initial SwarmState
            
        Returns:
            SwarmState: Final state after workflow completion
        """
        from .state import SwarmState
        
        # Convert SwarmState to dict for graph processing
        state_dict: GraphState = {
            "target_dir": initial_state.target_dir,
            "max_iterations": initial_state.max_iterations,
            "iteration": 0,
            "status": "running",
            "files": {},
            "pending_files": [],
            "current_file": None,
            "initial_pylint_score": 0.0,
            "final_pylint_score": 0.0,
            "tests_passed": False
        }
        
        # Run the graph
        final_state_dict = self.graph.invoke(state_dict)
        
        # Convert back to SwarmState
        final_state = SwarmState(
            target_dir=initial_state.target_dir,
            max_iterations=initial_state.max_iterations
        )
        final_state.iteration = final_state_dict.get("iteration", 0)
        final_state.status = final_state_dict.get("status", "unknown")
        final_state.initial_pylint_score = final_state_dict.get("initial_pylint_score", 0.0)
        final_state.final_pylint_score = final_state_dict.get("final_pylint_score", 0.0)
        final_state.tests_passed = final_state_dict.get("tests_passed", False)
        
        return final_state
