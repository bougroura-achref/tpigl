"""
Test Orchestrator - Unit tests for the orchestrator module
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.state import SwarmState, FileState, FileStatus, WorkflowStatus


class TestSwarmState:
    """Tests for SwarmState"""
    
    def test_state_initialization(self):
        """Test SwarmState initializes correctly"""
        state = SwarmState(target_dir="/tmp/test", max_iterations=5)
        
        assert state.target_dir == "/tmp/test"
        assert state.max_iterations == 5
        assert state.iteration == 0
        assert state.status == "initialized"
        assert state.started_at is not None
    
    def test_add_file(self):
        """Test adding files to track"""
        state = SwarmState(target_dir="/tmp/test")
        
        file_state = state.add_file("/tmp/test/example.py")
        
        assert isinstance(file_state, FileState)
        assert file_state.path == "/tmp/test/example.py"
        assert file_state.status == FileStatus.PENDING
    
    def test_get_file(self):
        """Test retrieving file state"""
        state = SwarmState(target_dir="/tmp/test")
        state.add_file("/tmp/test/example.py")
        
        file_state = state.get_file("/tmp/test/example.py")
        
        assert file_state is not None
        assert file_state.path == "/tmp/test/example.py"
    
    def test_get_nonexistent_file(self):
        """Test retrieving non-existent file returns None"""
        state = SwarmState(target_dir="/tmp/test")
        
        file_state = state.get_file("/tmp/test/nonexistent.py")
        
        assert file_state is None
    
    def test_record_action(self):
        """Test recording actions in history"""
        state = SwarmState(target_dir="/tmp/test")
        
        state.record_action(
            agent="auditor",
            action="analyze",
            details={"file": "test.py"}
        )
        
        assert len(state.history) == 1
        assert state.history[0]["agent"] == "auditor"
        assert state.history[0]["action"] == "analyze"
    
    def test_get_pending_files(self):
        """Test getting pending files"""
        state = SwarmState(target_dir="/tmp/test")
        state.add_file("/tmp/test/a.py")
        state.add_file("/tmp/test/b.py")
        state.files["/tmp/test/a.py"].status = FileStatus.SUCCESS
        
        pending = state.get_pending_files()
        
        assert len(pending) == 1
        assert "/tmp/test/b.py" in pending
    
    def test_to_dict(self):
        """Test serialization to dictionary"""
        state = SwarmState(target_dir="/tmp/test", max_iterations=10)
        state.add_file("/tmp/test/test.py")
        
        result = state.to_dict()
        
        assert result["target_dir"] == "/tmp/test"
        assert result["max_iterations"] == 10
        assert "files" in result
        assert "started_at" in result
    
    def test_complete(self):
        """Test completing the workflow"""
        state = SwarmState(target_dir="/tmp/test")
        state.add_file("/tmp/test/test.py")
        state.files["/tmp/test/test.py"].original_score = 5.0
        state.files["/tmp/test/test.py"].current_score = 8.0
        state.files["/tmp/test/test.py"].verdict = "SUCCESS"
        
        state.complete("success")
        
        assert state.status == "success"
        assert state.completed_at is not None
        assert state.initial_pylint_score == 5.0
        assert state.final_pylint_score == 8.0


class TestFileState:
    """Tests for FileState"""
    
    def test_file_state_initialization(self):
        """Test FileState initializes correctly"""
        state = FileState(path="/tmp/test.py")
        
        assert state.path == "/tmp/test.py"
        assert state.status == FileStatus.PENDING
        assert state.original_score == 0.0
        assert state.issues == []
    
    def test_to_dict(self):
        """Test serialization"""
        state = FileState(path="/tmp/test.py")
        state.original_score = 6.5
        state.current_score = 8.0
        state.verdict = "SUCCESS"
        
        result = state.to_dict()
        
        assert result["path"] == "/tmp/test.py"
        assert result["original_score"] == 6.5
        assert result["current_score"] == 8.0
        assert result["verdict"] == "SUCCESS"


class TestWorkflowStatus:
    """Tests for WorkflowStatus enum"""
    
    def test_status_values(self):
        """Test status enum values"""
        assert WorkflowStatus.INITIALIZED.value == "initialized"
        assert WorkflowStatus.ANALYZING.value == "analyzing"
        assert WorkflowStatus.SUCCESS.value == "success"
        assert WorkflowStatus.FAILED.value == "failed"


class TestFileStatus:
    """Tests for FileStatus enum"""
    
    def test_file_status_values(self):
        """Test file status enum values"""
        assert FileStatus.PENDING.value == "pending"
        assert FileStatus.ANALYZING.value == "analyzing"
        assert FileStatus.SUCCESS.value == "success"
        assert FileStatus.FAILED.value == "failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
