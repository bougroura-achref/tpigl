"""
Test Logger - Unit tests for the src/utils/logger module
Quality & Data Manager

Tests the mandatory logging functionality as specified in the IGL Lab documentation.
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import (
    ActionType,
    log_experiment,
    get_logger,
    save_experiment_data,
    ExperimentLogger,
    ExperimentData
)


class TestActionType:
    """Tests for ActionType enum."""
    
    def test_action_type_values(self):
        """Test that all required action types exist."""
        assert ActionType.ANALYSIS.value == "ANALYSIS"
        assert ActionType.GENERATION.value == "GENERATION"
        assert ActionType.DEBUG.value == "DEBUG"
        assert ActionType.FIX.value == "FIX"
    
    def test_action_type_count(self):
        """Test that we have exactly 4 action types."""
        assert len(ActionType) == 4


class TestExperimentLogger:
    """Tests for ExperimentLogger class."""
    
    def setup_method(self):
        """Reset logger before each test."""
        ExperimentLogger._instance = None
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up after tests."""
        import shutil
        ExperimentLogger._instance = None
        for dir_path in [self.temp_dir, self.log_dir]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
    
    def test_logger_initialization(self):
        """Test logger initializes correctly."""
        logger = ExperimentLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        assert logger.target_dir == self.temp_dir
        assert logger.experiment_id is not None
        assert logger.data.started_at is not None
    
    def test_logger_singleton(self):
        """Test that logger is a singleton."""
        logger1 = ExperimentLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        logger2 = ExperimentLogger()
        
        assert logger1 is logger2
    
    def test_log_with_required_fields(self):
        """Test logging with all required fields."""
        logger = ExperimentLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        logger.log(
            agent_name="Auditor_Agent",
            model_used="gemini-2.0-flash",
            action=ActionType.ANALYSIS,
            details={
                "file_analyzed": "test.py",
                "input_prompt": "Analyze this code...",
                "output_response": "I found 3 issues...",
                "issues_found": 3
            },
            status="SUCCESS"
        )
        
        assert len(logger.data.experiment_logs) == 1
        log_entry = logger.data.experiment_logs[0]
        assert log_entry["agent_name"] == "Auditor_Agent"
        assert log_entry["action"] == "ANALYSIS"
        assert "input_prompt" in log_entry["details"]
        assert "output_response" in log_entry["details"]
    
    def test_log_missing_input_prompt_raises_error(self):
        """Test that missing input_prompt raises ValueError."""
        logger = ExperimentLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        with pytest.raises(ValueError, match="input_prompt"):
            logger.log(
                agent_name="Auditor_Agent",
                model_used="gemini-2.0-flash",
                action=ActionType.ANALYSIS,
                details={
                    "output_response": "Some response..."
                },
                status="SUCCESS"
            )
    
    def test_log_missing_output_response_raises_error(self):
        """Test that missing output_response raises ValueError."""
        logger = ExperimentLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        with pytest.raises(ValueError, match="output_response"):
            logger.log(
                agent_name="Fixer_Agent",
                model_used="gemini-2.0-flash",
                action=ActionType.FIX,
                details={
                    "input_prompt": "Fix this code..."
                },
                status="SUCCESS"
            )
    
    def test_save_creates_json_file(self):
        """Test that save creates experiment_data.json."""
        logger = ExperimentLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        logger.log(
            agent_name="Test_Agent",
            model_used="gemini-2.0-flash",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": "Test prompt",
                "output_response": "Test response"
            }
        )
        
        output_path = logger.save()
        
        assert output_path.exists()
        assert output_path.name == "experiment_data.json"
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "experiment_logs" in data
        assert len(data["experiment_logs"]) == 1
    
    def test_set_final_metrics(self):
        """Test setting final metrics."""
        logger = ExperimentLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        logger.set_final_metrics(
            status="SUCCESS",
            total_iterations=5,
            initial_score=5.0,
            final_score=9.0,
            files_processed=3,
            files_successful=2,
            tests_run=10,
            tests_passed=8
        )
        
        assert logger.data.status == "SUCCESS"
        assert logger.data.score_improvement == 4.0
        assert logger.data.files_failed == 1
        assert logger.data.tests_failed == 2


class TestLogExperimentFunction:
    """Tests for the log_experiment convenience function."""
    
    def setup_method(self):
        """Reset logger before each test."""
        ExperimentLogger._instance = None
    
    def teardown_method(self):
        """Reset logger after tests."""
        ExperimentLogger._instance = None
    
    def test_log_experiment_function(self):
        """Test the log_experiment function works correctly."""
        # This should create a logger and log the event
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
        
        logger = get_logger()
        assert len(logger.data.experiment_logs) == 1


class TestExperimentData:
    """Tests for ExperimentData dataclass."""
    
    def test_default_values(self):
        """Test default values match PDF specification."""
        data = ExperimentData()
        
        assert data.max_iterations == 10
        assert "gemini" in data.llm_model.lower() or data.llm_model != ""
        assert "pylint" in data.tools_used
        assert "pytest" in data.tools_used
    
    def test_custom_values(self):
        """Test custom values."""
        data = ExperimentData(
            experiment_id="test_exp_001",
            max_iterations=5,
            llm_model="gemini-2.0-flash"
        )
        
        assert data.experiment_id == "test_exp_001"
        assert data.max_iterations == 5
        assert data.llm_model == "gemini-2.0-flash"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
