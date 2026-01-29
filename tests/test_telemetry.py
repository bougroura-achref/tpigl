"""
Test Telemetry - Unit tests for the logging system
"""

import os
import sys
import pytest
import tempfile
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_system.telemetry import TelemetryLogger, ExperimentData


class TestTelemetryLogger:
    """Tests for TelemetryLogger"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up"""
        import shutil
        for dir_path in [self.temp_dir, self.log_dir]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
    
    def test_initialization(self):
        """Test TelemetryLogger initializes correctly"""
        logger = TelemetryLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        assert logger.target_dir == self.temp_dir
        assert logger.experiment_id is not None
        assert logger.data.started_at is not None
    
    def test_log_event(self):
        """Test logging events"""
        logger = TelemetryLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        logger.log_event("test_event", {"key": "value"})
        
        assert len(logger.data.agent_logs) == 1
        assert logger.data.agent_logs[0]["event_type"] == "test_event"
    
    def test_log_agent_action(self):
        """Test logging agent actions"""
        logger = TelemetryLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        logger.log_agent_action(
            agent="auditor",
            action="analyze",
            iteration=1,
            file="test.py",
            details={"score": 8.0}
        )
        
        assert len(logger.data.agent_logs) == 1
        log = logger.data.agent_logs[0]
        assert log["agent"] == "auditor"
        assert log["action"] == "analyze"
    
    def test_log_error(self):
        """Test logging errors"""
        logger = TelemetryLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        logger.log_error(
            error_type="SyntaxError",
            message="Invalid syntax",
            file="test.py"
        )
        
        assert len(logger.data.errors) == 1
        assert logger.data.errors[0]["error_type"] == "SyntaxError"
    
    def test_log_file_result(self):
        """Test logging file results"""
        logger = TelemetryLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        logger.log_file_result(
            file_path="test.py",
            status="success",
            original_score=5.0,
            final_score=8.5,
            iterations=2,
            changes=["Added docstring", "Fixed imports"],
            tests_passed=True
        )
        
        assert len(logger.data.file_results) == 1
        result = logger.data.file_results[0]
        assert result["file"] == "test.py"
        assert result["score_improvement"] == 3.5
    
    def test_set_final_metrics(self):
        """Test setting final metrics"""
        logger = TelemetryLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        logger.set_final_metrics(
            status="success",
            total_iterations=5,
            initial_score=5.0,
            final_score=8.5,
            files_processed=3,
            files_successful=2,
            tests_run=10,
            tests_passed=8
        )
        
        assert logger.data.status == "success"
        assert logger.data.total_iterations == 5
        assert logger.data.score_improvement == 3.5
        assert logger.data.files_failed == 1
        assert logger.data.tests_failed == 2
    
    def test_save(self):
        """Test saving experiment data"""
        logger = TelemetryLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        logger.log_event("test", {"data": "value"})
        logger.set_final_metrics(
            status="success",
            total_iterations=1,
            initial_score=5.0,
            final_score=8.0,
            files_processed=1,
            files_successful=1
        )
        
        output_path = logger.save()
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "success"
        assert "duration_seconds" in data
    
    def test_get_summary(self):
        """Test getting summary"""
        logger = TelemetryLogger(
            target_dir=self.temp_dir,
            log_dir=self.log_dir
        )
        
        logger.set_final_metrics(
            status="success",
            total_iterations=3,
            initial_score=5.0,
            final_score=8.0,
            files_processed=2,
            files_successful=2
        )
        
        summary = logger.get_summary()
        
        assert summary["status"] == "success"
        assert summary["files_processed"] == 2
        assert summary["score_improvement"] == 3.0


class TestExperimentData:
    """Tests for ExperimentData dataclass"""
    
    def test_default_values(self):
        """Test default values"""
        data = ExperimentData()
        
        assert data.experiment_id == ""
        assert data.max_iterations == 10
        assert data.llm_model == "gpt-4"
        assert data.file_results == []
        assert data.errors == []
    
    def test_custom_values(self):
        """Test custom values"""
        data = ExperimentData(
            experiment_id="test123",
            max_iterations=5,
            llm_model="gpt-4-turbo"
        )
        
        assert data.experiment_id == "test123"
        assert data.max_iterations == 5
        assert data.llm_model == "gpt-4-turbo"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
