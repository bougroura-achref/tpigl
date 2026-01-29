"""
Telemetry Logger - Centralized logging for The Refactoring Swarm.
Captures all events and outputs experiment_data.json as required.
Improvements:
- Auto-save to prevent data loss
- Consistent model naming
- Better error tracking
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class AgentLog:
    """Log entry for a single agent action"""
    timestamp: str
    agent: str
    action: str
    iteration: int
    file: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentData:
    """
    Structure for experiment_data.json output.
    This is the required output format per the lab specification.
    """
    # Metadata
    experiment_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    target_directory: str = ""
    max_iterations: int = 10
    
    # Configuration - use environment variable for model
    llm_model: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "claude-sonnet-4-20250514"))
    tools_used: List[str] = field(default_factory=list)
    
    # Results
    status: str = ""
    total_iterations: int = 0
    files_processed: int = 0
    files_successful: int = 0
    files_failed: int = 0
    
    # Scores
    initial_pylint_score: float = 0.0
    final_pylint_score: float = 0.0
    score_improvement: float = 0.0
    
    # Test results
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    
    # File details
    file_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Agent logs
    agent_logs: List[Dict[str, Any]] = field(default_factory=list)
    
    # Errors encountered
    errors: List[Dict[str, Any]] = field(default_factory=list)


class TelemetryLogger:
    """
    Centralized telemetry logger for The Refactoring Swarm.
    Captures all events and generates the required experiment_data.json.
    """
    
    def __init__(
        self,
        target_dir: str,
        log_dir: Optional[str] = None,
        experiment_id: Optional[str] = None
    ):
        """
        Initialize the telemetry logger.
        
        Args:
            target_dir: The target directory being refactored
            log_dir: Directory to store logs (default: ./logs)
            experiment_id: Unique experiment identifier
        """
        self.target_dir = target_dir
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "logs"
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate experiment ID if not provided
        self.experiment_id = experiment_id or self._generate_experiment_id()
        
        # Initialize experiment data
        self.data = ExperimentData(
            experiment_id=self.experiment_id,
            started_at=datetime.now().isoformat(),
            target_directory=target_dir,
            tools_used=["pylint", "pytest", "file_tools"]
        )
        
        # Internal tracking
        self._event_count = 0
        self._start_time = datetime.now()
        self._auto_save_interval = 10  # Save every 10 events
    
    def _generate_experiment_id(self) -> str:
        """Generate a unique experiment ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"swarm_experiment_{timestamp}"
    
    def log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log an event to the telemetry system.
        
        Args:
            event_type: Type of event (e.g., "file_analyzed", "fix_applied")
            details: Event details
        """
        self._event_count += 1
        
        log_entry = {
            "event_id": self._event_count,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        self.data.agent_logs.append(log_entry)
        
        # Auto-save every N events to prevent data loss
        if self._event_count % self._auto_save_interval == 0:
            self._quick_save()
        
        # Also log to console in verbose mode
        if details.get("verbose"):
            print(f"  [LOG] {event_type}: {details}")
    
    def _quick_save(self) -> None:
        """Quick save to temporary file to prevent data loss."""
        try:
            temp_path = self.log_dir / "experiment_data_temp.json"
            data_dict = asdict(self.data)
            data_dict["duration_seconds"] = (datetime.now() - self._start_time).total_seconds()
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # Silently fail on quick save
    
    def log_agent_action(
        self,
        agent: str,
        action: str,
        iteration: int,
        file: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an agent action.
        
        Args:
            agent: Agent name (auditor, fixer, judge)
            action: Action performed
            iteration: Current iteration number
            file: File being processed
            details: Additional details
        """
        entry = AgentLog(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            action=action,
            iteration=iteration,
            file=file,
            details=details or {}
        )
        
        self.data.agent_logs.append(asdict(entry))
    
    def log_error(
        self,
        error_type: str,
        message: str,
        file: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an error.
        
        Args:
            error_type: Type of error
            message: Error message
            file: Related file (if any)
            details: Additional details
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "message": message,
            "file": file,
            "details": details or {}
        }
        
        self.data.errors.append(error_entry)
    
    def log_file_result(
        self,
        file_path: str,
        status: str,
        original_score: float,
        final_score: float,
        iterations: int,
        changes: List[str],
        tests_passed: bool = False
    ) -> None:
        """
        Log the result for a processed file.
        
        Args:
            file_path: Path to the file
            status: Final status (success, failed)
            original_score: Initial pylint score
            final_score: Final pylint score
            iterations: Number of fix iterations
            changes: List of changes made
            tests_passed: Whether tests pass
        """
        result = {
            "file": file_path,
            "status": status,
            "original_score": original_score,
            "final_score": final_score,
            "score_improvement": final_score - original_score,
            "iterations": iterations,
            "changes_count": len(changes),
            "changes": changes[:10],  # Limit to 10 changes for readability
            "tests_passed": tests_passed
        }
        
        self.data.file_results.append(result)
    
    def set_final_metrics(
        self,
        status: str,
        total_iterations: int,
        initial_score: float,
        final_score: float,
        files_processed: int,
        files_successful: int,
        tests_run: int = 0,
        tests_passed: int = 0
    ) -> None:
        """
        Set the final experiment metrics.
        
        Args:
            status: Final workflow status
            total_iterations: Total iterations performed
            initial_score: Average initial pylint score
            final_score: Average final pylint score
            files_processed: Number of files processed
            files_successful: Number of files successfully refactored
            tests_run: Total tests run
            tests_passed: Tests that passed
        """
        self.data.status = status
        self.data.total_iterations = total_iterations
        self.data.initial_pylint_score = initial_score
        self.data.final_pylint_score = final_score
        self.data.score_improvement = round(final_score - initial_score, 2)
        self.data.files_processed = files_processed
        self.data.files_successful = files_successful
        self.data.files_failed = files_processed - files_successful
        self.data.tests_run = tests_run
        self.data.tests_passed = tests_passed
        self.data.tests_failed = tests_run - tests_passed
        self.data.completed_at = datetime.now().isoformat()
    
    def save(self, filename: Optional[str] = None) -> Path:
        """
        Save the experiment data to experiment_data.json.
        
        Args:
            filename: Custom filename (default: experiment_data.json)
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            filename = "experiment_data.json"
        
        output_path = self.log_dir / filename
        
        # Convert dataclass to dict
        data_dict = asdict(self.data)
        
        # Calculate duration
        duration = datetime.now() - self._start_time
        data_dict["duration_seconds"] = duration.total_seconds()
        
        # Write JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the experiment.
        
        Returns:
            Dict with experiment summary
        """
        return {
            "experiment_id": self.data.experiment_id,
            "status": self.data.status,
            "duration": (datetime.now() - self._start_time).total_seconds(),
            "files_processed": self.data.files_processed,
            "files_successful": self.data.files_successful,
            "score_improvement": self.data.score_improvement,
            "events_logged": self._event_count,
            "errors_count": len(self.data.errors)
        }
    
    def print_summary(self) -> None:
        """Print a formatted summary to console"""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("📊 EXPERIMENT SUMMARY")
        print("="*60)
        print(f"  Experiment ID: {summary['experiment_id']}")
        print(f"  Status: {summary['status']}")
        print(f"  Duration: {summary['duration']:.2f} seconds")
        print(f"  Files Processed: {summary['files_processed']}")
        print(f"  Files Successful: {summary['files_successful']}")
        print(f"  Score Improvement: {summary['score_improvement']:+.2f}")
        print(f"  Events Logged: {summary['events_logged']}")
        print(f"  Errors: {summary['errors_count']}")
        print("="*60)


def create_telemetry_logger(
    target_dir: str,
    log_dir: Optional[str] = None
) -> TelemetryLogger:
    """
    Factory function to create a TelemetryLogger.
    
    Args:
        target_dir: Target directory being refactored
        log_dir: Optional log directory
        
    Returns:
        TelemetryLogger instance
    """
    return TelemetryLogger(target_dir=target_dir, log_dir=log_dir)
