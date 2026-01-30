"""
Pytest Configuration and Shared Fixtures
Quality & Data Manager - Test Infrastructure
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# ENVIRONMENT FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def has_api_key() -> bool:
    """Check if any API key is available."""
    return bool(
        os.environ.get("ANTHROPIC_API_KEY") or 
        os.environ.get("GOOGLE_API_KEY")
    )


@pytest.fixture
def skip_without_api_key(has_api_key: bool):
    """Skip test if no API key is available."""
    if not has_api_key:
        pytest.skip("No API key available (ANTHROPIC_API_KEY or GOOGLE_API_KEY)")


# ============================================================================
# TEMPORARY DIRECTORY FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for tests."""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


@pytest.fixture
def temp_log_dir() -> Generator[str, None, None]:
    """Create a temporary log directory."""
    dir_path = tempfile.mkdtemp(prefix="logs_")
    yield dir_path
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


# ============================================================================
# SAMPLE CODE FIXTURES
# ============================================================================

@pytest.fixture
def sample_buggy_code() -> str:
    """Return sample buggy Python code for testing."""
    return '''import os
import sys
x=1
y=2
def foo():
    pass
def bar( a,b ):
    return a+b
class MyClass:
    def method(self):
        print( "hello" )
'''


@pytest.fixture
def sample_clean_code() -> str:
    """Return sample clean Python code for testing."""
    return '''"""Sample module with clean code."""


def add(a: int, b: int) -> int:
    """Add two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    return a + b


def main() -> None:
    """Main entry point."""
    result = add(1, 2)
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
'''


@pytest.fixture
def sample_buggy_file(temp_dir: str, sample_buggy_code: str) -> str:
    """Create a buggy Python file in temp directory."""
    file_path = os.path.join(temp_dir, "buggy.py")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(sample_buggy_code)
    return file_path


@pytest.fixture
def sample_clean_file(temp_dir: str, sample_clean_code: str) -> str:
    """Create a clean Python file in temp directory."""
    file_path = os.path.join(temp_dir, "clean.py")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(sample_clean_code)
    return file_path


@pytest.fixture
def sample_test_file(temp_dir: str) -> str:
    """Create a sample pytest file in temp directory."""
    file_path = os.path.join(temp_dir, "test_sample.py")
    content = '''"""Sample test file."""

def test_addition():
    """Test basic addition."""
    assert 1 + 1 == 2


def test_subtraction():
    """Test basic subtraction."""
    assert 5 - 3 == 2


def test_multiplication():
    """Test basic multiplication."""
    assert 2 * 3 == 6
'''
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


# ============================================================================
# MOCK DATA FIXTURES
# ============================================================================

@pytest.fixture
def mock_pylint_result() -> Dict[str, Any]:
    """Return a mock pylint result."""
    return {
        "score": 7.5,
        "messages": [
            {
                "type": "convention",
                "module": "test",
                "line": 1,
                "message": "Missing module docstring"
            },
            {
                "type": "warning",
                "module": "test",
                "line": 5,
                "message": "Unused import os"
            }
        ],
        "stats": {
            "error": 0,
            "warning": 1,
            "convention": 1,
            "refactor": 0
        }
    }


@pytest.fixture
def mock_analysis_plan() -> Dict[str, Any]:
    """Return a mock analysis plan from the Auditor."""
    return {
        "file_path": "test.py",
        "pylint_score": 5.0,
        "issues": [
            {
                "type": "missing_docstring",
                "location": "module",
                "severity": "convention",
                "suggestion": "Add module docstring"
            },
            {
                "type": "unused_import",
                "location": "line 1",
                "severity": "warning",
                "suggestion": "Remove unused import"
            }
        ],
        "refactoring_plan": [
            "Add module docstring",
            "Remove unused imports",
            "Add function docstrings",
            "Fix PEP8 formatting"
        ]
    }


@pytest.fixture
def mock_fix_result() -> Dict[str, Any]:
    """Return a mock fix result from the Fixer."""
    return {
        "success": True,
        "file_path": "test.py",
        "changes_made": [
            "Added module docstring",
            "Removed unused import os",
            "Added type hints"
        ],
        "new_code": '"""Module docstring."""\n\ndef main():\n    print("hello")\n'
    }


@pytest.fixture
def mock_judge_verdict() -> Dict[str, Any]:
    """Return a mock verdict from the Judge."""
    return {
        "verdict": "SUCCESS",
        "original_score": 5.0,
        "new_score": 9.5,
        "score_improved": True,
        "tests_passed": True,
        "reasoning": "Code quality improved significantly. All tests pass."
    }


# ============================================================================
# TELEMETRY FIXTURES
# ============================================================================

@pytest.fixture
def telemetry_logger(temp_dir: str, temp_log_dir: str):
    """Create a TelemetryLogger instance for testing."""
    from logging_system.telemetry import TelemetryLogger
    return TelemetryLogger(
        target_dir=temp_dir,
        log_dir=temp_log_dir,
        experiment_id="test_experiment_001"
    )


@pytest.fixture
def sample_experiment_data() -> Dict[str, Any]:
    """Return sample experiment data structure."""
    return {
        "experiment_id": "test_exp_001",
        "started_at": "2026-01-30T10:00:00",
        "completed_at": "2026-01-30T10:05:00",
        "target_directory": "/tmp/test",
        "max_iterations": 10,
        "llm_model": "claude-sonnet-4-20250514",
        "status": "success",
        "total_iterations": 3,
        "files_processed": 2,
        "files_successful": 2,
        "files_failed": 0,
        "initial_pylint_score": 5.0,
        "final_pylint_score": 9.0,
        "score_improvement": 4.0,
        "tests_run": 10,
        "tests_passed": 10,
        "tests_failed": 0
    }


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_api: marks tests that require an API key"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add slow marker to tests with 'integration' in name
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
        
        # Add requires_api marker to agent tests
        if "test_agent" in item.nodeid.lower():
            item.add_marker(pytest.mark.requires_api)
