"""
Test Tools - Pytest integration for running unit tests
"""

import subprocess
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


def run_pytest(
    target: str,
    additional_args: Optional[List[str]] = None,
    timeout: int = 120
) -> Dict[str, Any]:
    """
    Run pytest on a file or directory.
    
    Args:
        target: Path to test file or directory
        additional_args: Optional additional pytest arguments
        timeout: Maximum execution time in seconds
        
    Returns:
        dict: Test results including pass/fail counts
    """
    path = Path(target)
    
    if not path.exists():
        return {
            "success": False,
            "error": f"Path not found: {target}",
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "total": 0,
            "output": ""
        }
    
    # Build pytest command
    cmd = [
        "python", "-m", "pytest",
        str(path),
        "-v",
        "--tb=short",
        "-q"
    ]
    
    if additional_args:
        cmd.extend(additional_args)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Parse test results
        stats = parse_pytest_output(result.stdout + result.stderr)
        
        return {
            "success": result.returncode == 0,
            "passed": stats["passed"],
            "failed": stats["failed"],
            "errors": stats["errors"],
            "skipped": stats["skipped"],
            "total": stats["total"],
            "output": result.stdout,
            "error_output": result.stderr,
            "return_code": result.returncode,
            "failures_detail": stats.get("failures_detail", [])
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Pytest timed out after {timeout} seconds",
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "total": 0,
            "output": ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "total": 0,
            "output": ""
        }


def parse_pytest_output(output: str) -> Dict[str, Any]:
    """
    Parse pytest output to extract test statistics.
    
    Args:
        output: Combined stdout/stderr from pytest
        
    Returns:
        dict: Parsed test statistics
    """
    stats = {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "total": 0,
        "failures_detail": []
    }
    
    # Pattern for summary line like "5 passed, 2 failed in 0.12s"
    summary_pattern = r"(\d+)\s+(passed|failed|error|skipped|warnings?)"
    matches = re.findall(summary_pattern, output, re.IGNORECASE)
    
    for count, status in matches:
        count = int(count)
        status = status.lower()
        
        if "pass" in status:
            stats["passed"] = count
        elif "fail" in status:
            stats["failed"] = count
        elif "error" in status:
            stats["errors"] = count
        elif "skip" in status:
            stats["skipped"] = count
    
    stats["total"] = stats["passed"] + stats["failed"] + stats["errors"] + stats["skipped"]
    
    # Extract failure details
    failure_pattern = r"FAILED\s+(\S+)::\S+\s+-\s+(.+)"
    failures = re.findall(failure_pattern, output)
    stats["failures_detail"] = [{"file": f, "reason": r} for f, r in failures]
    
    return stats


def discover_tests(directory: str) -> List[str]:
    """
    Discover test files in a directory.
    
    Args:
        directory: Directory to search for tests
        
    Returns:
        List[str]: List of test file paths
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return []
    
    test_files = []
    
    # Look for test_*.py and *_test.py files
    for pattern in ["**/test_*.py", "**/*_test.py"]:
        for f in dir_path.glob(pattern):
            if "__pycache__" not in str(f):
                test_files.append(str(f))
    
    return sorted(set(test_files))


def get_test_results(directory: str) -> Dict[str, Any]:
    """
    Run all tests in a directory and get comprehensive results.
    
    Args:
        directory: Directory containing tests
        
    Returns:
        dict: Comprehensive test results
    """
    test_files = discover_tests(directory)
    
    if not test_files:
        return {
            "success": True,
            "message": "No test files found",
            "test_files": 0,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "files": []
        }
    
    # Run tests on the entire directory
    result = run_pytest(directory)
    
    return {
        "success": result["success"],
        "test_files": len(test_files),
        "total_tests": result["total"],
        "passed": result["passed"],
        "failed": result["failed"],
        "errors": result["errors"],
        "skipped": result.get("skipped", 0),
        "output": result["output"],
        "failures_detail": result.get("failures_detail", []),
        "files": test_files
    }


def create_test_file(
    file_path: str,
    module_path: str,
    function_names: List[str]
) -> str:
    """
    Generate a basic test file template for a module.
    
    Args:
        file_path: Path for the test file
        module_path: Import path for the module to test
        function_names: List of function names to create tests for
        
    Returns:
        str: Generated test file content
    """
    lines = [
        '"""',
        f'Unit tests for {module_path}',
        '"""',
        '',
        'import pytest',
        f'from {module_path} import *',
        '',
        ''
    ]
    
    for func_name in function_names:
        lines.extend([
            f'class Test{func_name.title().replace("_", "")}:',
            f'    """Tests for {func_name} function."""',
            '',
            f'    def test_{func_name}_basic(self):',
            f'        """Test basic functionality of {func_name}."""',
            '        # TODO: Implement test',
            '        pass',
            '',
            f'    def test_{func_name}_edge_cases(self):',
            f'        """Test edge cases for {func_name}."""',
            '        # TODO: Implement test',
            '        pass',
            '',
            ''
        ])
    
    return '\n'.join(lines)


def format_test_report(results: Dict[str, Any]) -> str:
    """
    Format test results into a readable report.
    
    Args:
        results: Test results dictionary
        
    Returns:
        str: Formatted report string
    """
    lines = [
        "Test Execution Report",
        "=" * 50,
        f"Test Files: {results.get('test_files', 0)}",
        f"Total Tests: {results.get('total_tests', 0)}",
        "",
        "Results:",
        f"  ✅ Passed: {results.get('passed', 0)}",
        f"  ❌ Failed: {results.get('failed', 0)}",
        f"  ⚠️  Errors: {results.get('errors', 0)}",
        f"  ⏭️  Skipped: {results.get('skipped', 0)}",
    ]
    
    if results.get("failures_detail"):
        lines.append("\nFailure Details:")
        lines.append("-" * 30)
        for failure in results["failures_detail"]:
            lines.append(f"  {failure['file']}: {failure['reason']}")
    
    status = "PASSED" if results.get("success") else "FAILED"
    lines.append(f"\nOverall Status: {status}")
    
    return "\n".join(lines)
