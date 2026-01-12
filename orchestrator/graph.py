"""
Refactoring Graph - LangGraph workflow for agent orchestration
"""

from typing import Dict, Any, Literal, Optional
from pathlib import Path

from langgraph.graph import StateGraph, END

from agents import AuditorAgent, FixerAgent, JudgeAgent
from tools.file_tools import list_python_files
from logging_system.telemetry import TelemetryLogger
from .state import SwarmState, FileState, FileStatus, WorkflowStatus


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
        # Define the state graph
        workflow = StateGraph(dict)
        
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
    
    def _initialize_node(self, state: dict) -> dict:
        """Initialize the workflow state"""
        if self.verbose:
            print("\n🚀 Initializing refactoring workflow...")
        
        # Discover Python files
        python_files = list_python_files(str(self.target_dir))
        
        if self.verbose:
            print(f"   Found {len(python_files)} Python files")
        
        # Initialize file states
        files = {}
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
    
    def _analyze_node(self, state: dict) -> dict:
        """Run the Auditor on the current file"""
        current_file = state.get("current_file")
        
        if not current_file:
            return {**state, "status": "no_files"}
        
        if self.verbose:
            print(f"\n📊 Analyzing: {current_file}")
        
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
            state["files"][current_file]["error_logs"].append(result.get("error", "Unknown error"))
        
        return state
    
    def _fix_node(self, state: dict) -> dict:
        """Run the Fixer on the current file"""
        current_file = state.get("current_file")
        
        if not current_file:
            return state
        
        file_state = state["files"][current_file]
        
        if self.verbose:
            iteration = file_state.get("fix_iterations", 0) + 1
            print(f"\n🔧 Fixing (iteration {iteration}): {current_file}")
        
        # Check if this is a retry
        if file_state.get("fix_iterations", 0) > 0:
            # Use feedback-based fixing
            result = self.fixer.fix_with_feedback(
                file_path=current_file,
                sandbox_dir=str(self.target_dir),
                error_logs="\n".join(file_state.get("error_logs", [])),
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
            file_state["changes_made"].extend(result.get("changes_made", []))
            
            if self.telemetry:
                self.telemetry.log_event("file_fixed", {
                    "file": current_file,
                    "iteration": file_state["fix_iterations"],
                    "changes": result.get("changes_made", [])
                })
        else:
            file_state["error_logs"].append(result.get("error", "Fix failed"))
            file_state["fix_iterations"] += 1
        
        state["files"][current_file] = file_state
        return state
    
    def _evaluate_node(self, state: dict) -> dict:
        """Run the Judge to evaluate the fixes"""
        current_file = state.get("current_file")
        
        if not current_file:
            return state
        
        file_state = state["files"][current_file]
        
        if self.verbose:
            print(f"\n⚖️  Evaluating: {current_file}")
        
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
                    file_state["error_logs"].append(feedback)
            
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
            file_state["error_logs"].append(result.get("error", "Evaluation failed"))
        
        state["files"][current_file] = file_state
        state["iteration"] = state.get("iteration", 0) + 1
        
        return state
    
    def _should_continue(self, state: dict) -> Literal["continue", "next_file", "end"]:
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
    
    def _finalize_node(self, state: dict) -> dict:
        """Finalize the workflow and calculate metrics"""
        if self.verbose:
            print("\n📊 Finalizing refactoring workflow...")
        
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
        
        if file_count > 0:
            state["initial_pylint_score"] = round(total_original / file_count, 2)
            state["final_pylint_score"] = round(total_final / file_count, 2)
        
        state["tests_passed"] = success_count == file_count
        state["status"] = "success" if state["tests_passed"] else "partial"
        
        if self.telemetry:
            self.telemetry.log_event("workflow_complete", {
                "status": state["status"],
                "files_processed": file_count,
                "files_successful": success_count,
                "initial_score": state.get("initial_pylint_score", 0),
                "final_score": state.get("final_pylint_score", 0)
            })
        
        if self.verbose:
            print(f"   Status: {state['status']}")
            print(f"   Files: {success_count}/{file_count} successful")
            print(f"   Score: {state.get('initial_pylint_score', 0)} -> {state.get('final_pylint_score', 0)}")
        
        return state
    
    def run(self, initial_state: SwarmState) -> SwarmState:
        """
        Run the refactoring workflow.
        
        Args:
            initial_state: Initial SwarmState
            
        Returns:
            SwarmState: Final state after workflow completion
        """
        # Convert SwarmState to dict for graph processing
        state_dict = {
            "target_dir": initial_state.target_dir,
            "max_iterations": initial_state.max_iterations,
            "iteration": 0,
            "status": "running",
            "files": {},
            "pending_files": [],
            "current_file": None
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
