"""
Swarm State - Shared state management for the agent workflow
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """Status of the workflow"""
    INITIALIZED = "initialized"
    ANALYZING = "analyzing"
    FIXING = "fixing"
    TESTING = "testing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileStatus(str, Enum):
    """Status of individual file processing"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    FIXING = "fixing"
    FIXED = "fixed"
    TESTING = "testing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FileState:
    """State for an individual file being processed"""
    path: str
    status: FileStatus = FileStatus.PENDING
    
    # Analysis results
    original_score: float = 0.0
    current_score: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    refactoring_plan: List[Dict[str, Any]] = field(default_factory=list)
    
    # Fix tracking
    fix_iterations: int = 0
    changes_made: List[str] = field(default_factory=list)
    error_logs: List[str] = field(default_factory=list)
    
    # Test results
    tests_passed: bool = False
    test_output: str = ""
    
    # Verdict
    verdict: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "path": self.path,
            "status": self.status.value,
            "original_score": self.original_score,
            "current_score": self.current_score,
            "issues_count": len(self.issues),
            "fix_iterations": self.fix_iterations,
            "changes_made": self.changes_made,
            "tests_passed": self.tests_passed,
            "verdict": self.verdict
        }


@dataclass
class SwarmState:
    """
    Shared state for The Refactoring Swarm workflow.
    Passed between agents during execution.
    """
    # Configuration
    target_dir: str
    max_iterations: int = 10
    
    # Progress tracking
    iteration: int = 0
    status: str = "initialized"
    
    # File states
    files: Dict[str, FileState] = field(default_factory=dict)
    current_file: Optional[str] = None
    
    # Aggregate metrics
    initial_pylint_score: float = 0.0
    final_pylint_score: float = 0.0
    tests_passed: bool = False
    total_tests: int = 0
    passed_tests: int = 0
    
    # History
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timing
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.now().isoformat()
    
    def add_file(self, file_path: str) -> FileState:
        """Add a file to track"""
        if file_path not in self.files:
            self.files[file_path] = FileState(path=file_path)
        return self.files[file_path]
    
    def get_file(self, file_path: str) -> Optional[FileState]:
        """Get file state"""
        return self.files.get(file_path)
    
    def record_action(self, agent: str, action: str, details: Dict[str, Any]):
        """Record an action in the history"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "iteration": self.iteration,
            "agent": agent,
            "action": action,
            "details": details
        })
    
    def get_pending_files(self) -> List[str]:
        """Get files that haven't been processed yet"""
        return [
            path for path, state in self.files.items()
            if state.status in [FileStatus.PENDING, FileStatus.ANALYZED]
        ]
    
    def get_failed_files(self) -> List[str]:
        """Get files that failed and might need retry"""
        return [
            path for path, state in self.files.items()
            if state.status == FileStatus.FAILED and state.fix_iterations < self.max_iterations
        ]
    
    def calculate_metrics(self):
        """Calculate aggregate metrics from file states"""
        if not self.files:
            return
        
        total_original = 0.0
        total_current = 0.0
        success_count = 0
        
        for file_state in self.files.values():
            total_original += file_state.original_score
            total_current += file_state.current_score
            if file_state.verdict == "SUCCESS":
                success_count += 1
        
        file_count = len(self.files)
        self.initial_pylint_score = total_original / file_count
        self.final_pylint_score = total_current / file_count
        self.tests_passed = success_count == file_count
    
    def complete(self, status: str = "success"):
        """Mark the workflow as complete"""
        self.status = status
        self.completed_at = datetime.now().isoformat()
        self.calculate_metrics()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "target_dir": self.target_dir,
            "max_iterations": self.max_iterations,
            "iteration": self.iteration,
            "status": self.status,
            "files": {path: state.to_dict() for path, state in self.files.items()},
            "current_file": self.current_file,
            "initial_pylint_score": self.initial_pylint_score,
            "final_pylint_score": self.final_pylint_score,
            "tests_passed": self.tests_passed,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "history_count": len(self.history),
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SwarmState":
        """Create from dictionary"""
        state = cls(
            target_dir=data["target_dir"],
            max_iterations=data.get("max_iterations", 10)
        )
        state.iteration = data.get("iteration", 0)
        state.status = data.get("status", "initialized")
        state.initial_pylint_score = data.get("initial_pylint_score", 0.0)
        state.final_pylint_score = data.get("final_pylint_score", 0.0)
        state.tests_passed = data.get("tests_passed", False)
        state.started_at = data.get("started_at")
        state.completed_at = data.get("completed_at")
        
        return state
