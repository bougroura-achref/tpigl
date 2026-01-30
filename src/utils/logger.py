"""
Experiment Logger - Quality & Data Manager
Required logging module as specified in the IGL Lab documentation.

This module provides:
- ActionType enum for categorizing agent actions
- log_experiment function for mandatory logging
- Automatic saving to logs/experiment_data.json

IMPORTANT: Every significant LLM interaction must be logged with:
- input_prompt: The exact text sent to the LLM
- output_response: The raw response received from the LLM
"""

import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict


class ActionType(Enum):
    """
    Standardized action types for agent logging.
    You MUST use these values - do not invent action names.
    """
    ANALYSIS = "ANALYSIS"       # Agent reads code to understand, check standards, or find bugs. No modifications.
    GENERATION = "GENERATION"   # Agent creates new content (tests, documentation).
    DEBUG = "DEBUG"             # Agent analyzes execution error or stack trace to diagnose.
    FIX = "FIX"                 # Agent rewrites code to fix bugs or improve quality (Refactoring).


@dataclass
class ExperimentLog:
    """Single experiment log entry."""
    timestamp: str
    agent_name: str
    model_used: str
    action: str
    details: Dict[str, Any]
    status: str
    
    def validate(self) -> bool:
        """Validate that required fields are present."""
        required_fields = ["input_prompt", "output_response"]
        for field_name in required_fields:
            if field_name not in self.details:
                raise ValueError(
                    f"Missing required field '{field_name}' in details. "
                    f"Both 'input_prompt' and 'output_response' are MANDATORY."
                )
        return True


@dataclass
class ExperimentData:
    """
    Structure for experiment_data.json output.
    This is the required output format per the lab specification.
    """
    experiment_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    target_directory: str = ""
    max_iterations: int = 10
    llm_model: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "gemini-2.0-flash"))
    tools_used: List[str] = field(default_factory=lambda: ["pylint", "pytest", "file_tools"])
    
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
    
    # Logs
    experiment_logs: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)


class ExperimentLogger:
    """
    Centralized experiment logger for The Refactoring Swarm.
    Generates logs/experiment_data.json as required by the lab specification.
    """
    
    _instance: Optional['ExperimentLogger'] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure single logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        target_dir: Optional[str] = None,
        log_dir: Optional[str] = None,
        experiment_id: Optional[str] = None
    ):
        if self._initialized:
            return
            
        self.target_dir = target_dir or ""
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.experiment_id = experiment_id or self._generate_experiment_id()
        
        self.data = ExperimentData(
            experiment_id=self.experiment_id,
            started_at=datetime.now().isoformat(),
            target_directory=self.target_dir
        )
        
        self._event_count = 0
        self._start_time = datetime.now()
        self._initialized = True
    
    def _generate_experiment_id(self) -> str:
        """Generate unique experiment ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"exp_{timestamp}"
    
    def log(
        self,
        agent_name: str,
        model_used: str,
        action: ActionType,
        details: Dict[str, Any],
        status: str = "SUCCESS"
    ) -> None:
        """
        Log an experiment interaction.
        
        Args:
            agent_name: Name of the agent (e.g., "Auditor_Agent")
            model_used: LLM model used (e.g., "gemini-2.0-flash")
            action: ActionType enum value
            details: Must contain 'input_prompt' and 'output_response'
            status: SUCCESS or FAILURE
            
        Raises:
            ValueError: If required fields are missing
        """
        # Create log entry
        log_entry = ExperimentLog(
            timestamp=datetime.now().isoformat(),
            agent_name=agent_name,
            model_used=model_used,
            action=action.value if isinstance(action, ActionType) else str(action),
            details=details,
            status=status
        )
        
        # Validate required fields
        log_entry.validate()
        
        # Add to experiment data
        self.data.experiment_logs.append(asdict(log_entry))
        self._event_count += 1
        
        # Auto-save every 5 events
        if self._event_count % 5 == 0:
            self.save()
    
    def log_error(
        self,
        error_type: str,
        message: str,
        file: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an error."""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "message": message,
            "file": file,
            "details": details or {}
        }
        self.data.errors.append(error_entry)
    
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
        """Set final experiment metrics."""
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
    
    def save(self, filename: str = "experiment_data.json") -> Path:
        """Save experiment data to JSON file."""
        output_path = self.log_dir / filename
        
        data_dict = asdict(self.data)
        data_dict["duration_seconds"] = (datetime.now() - self._start_time).total_seconds()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def reset(self) -> None:
        """Reset the logger for a new experiment."""
        self._initialized = False
        ExperimentLogger._instance = None


# Global logger instance
_logger: Optional[ExperimentLogger] = None


def get_logger(
    target_dir: Optional[str] = None,
    log_dir: Optional[str] = None
) -> ExperimentLogger:
    """Get or create the global experiment logger."""
    global _logger
    if _logger is None:
        _logger = ExperimentLogger(target_dir=target_dir, log_dir=log_dir)
    return _logger


def log_experiment(
    agent_name: str,
    model_used: str,
    action: ActionType,
    details: Dict[str, Any],
    status: str = "SUCCESS"
) -> None:
    """
    Log an experiment interaction.
    
    This is the main logging function as specified in the lab documentation.
    
    Args:
        agent_name: Name of the agent (e.g., "Auditor_Agent")
        model_used: LLM model used (e.g., "gemini-2.0-flash")
        action: ActionType enum value (ANALYSIS, GENERATION, DEBUG, FIX)
        details: Dictionary with at least:
            - input_prompt: The exact text sent to the LLM (MANDATORY)
            - output_response: The raw response from the LLM (MANDATORY)
            - Additional fields as needed
        status: "SUCCESS" or "FAILURE"
        
    Raises:
        ValueError: If input_prompt or output_response is missing
        
    Example:
        log_experiment(
            agent_name="Auditor_Agent",
            model_used="gemini-2.0-flash",
            action=ActionType.ANALYSIS,
            details={
                "file_analyzed": "messy_code.py",
                "input_prompt": "You're a Python expert. Analyze this code...",
                "output_response": "I detected a missing docstring...",
                "issues_found": 3
            },
            status="SUCCESS"
        )
    """
    logger = get_logger()
    logger.log(
        agent_name=agent_name,
        model_used=model_used,
        action=action,
        details=details,
        status=status
    )


def save_experiment_data(filename: str = "experiment_data.json") -> Path:
    """Save the experiment data to file."""
    logger = get_logger()
    return logger.save(filename)


# Re-export for convenience
__all__ = [
    "ActionType",
    "log_experiment",
    "get_logger",
    "save_experiment_data",
    "ExperimentLogger",
    "ExperimentData"
]
