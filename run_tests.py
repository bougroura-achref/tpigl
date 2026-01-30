#!/usr/bin/env python3
"""
Test Runner Script - Quality & Data Manager
Runs all tests with coverage and generates reports.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


def run_tests(
    coverage: bool = False,
    verbose: bool = False,
    markers: str = None,
    specific_test: str = None,
    html_report: bool = False
) -> int:
    """
    Run the test suite with optional coverage.
    
    Args:
        coverage: Enable coverage reporting
        verbose: Verbose output
        markers: Run only tests with specific markers
        specific_test: Run a specific test file or test
        html_report: Generate HTML coverage report
        
    Returns:
        Exit code from pytest
    """
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=agents",
            "--cov=orchestrator", 
            "--cov=tools",
            "--cov=logging_system",
            "--cov-report=term-missing"
        ])
        if html_report:
            cmd.append("--cov-report=html:coverage_report")
    
    # Add marker filter
    if markers:
        cmd.extend(["-m", markers])
    
    # Add specific test
    if specific_test:
        cmd.append(specific_test)
    else:
        cmd.append("tests/")
    
    # Print command
    print(f"\n{'='*60}")
    print(f"🧪 Running Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}\n")
    
    # Run tests
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    # Print summary
    print(f"\n{'='*60}")
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed with exit code: {result.returncode}")
    print(f"{'='*60}\n")
    
    if coverage and html_report and result.returncode == 0:
        print(f"📊 Coverage report generated: coverage_report/index.html")
    
    return result.returncode


def run_quick_tests() -> int:
    """Run quick tests (no API calls)."""
    print("\n🚀 Running quick tests (skipping API tests)...")
    return run_tests(markers="not requires_api and not slow")


def run_all_tests() -> int:
    """Run all tests including integration."""
    print("\n🔄 Running all tests...")
    return run_tests(coverage=True, verbose=True)


def run_coverage_report() -> int:
    """Run tests with full coverage report."""
    print("\n📈 Running tests with coverage...")
    return run_tests(coverage=True, html_report=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Runner for The Refactoring Swarm"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Run quick tests only (no API, no slow)"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Enable coverage reporting"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--markers", "-m",
        type=str,
        help="Run tests with specific markers (e.g., 'not slow')"
    )
    parser.add_argument(
        "--test", "-t",
        type=str,
        help="Run specific test file or test"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all tests with coverage"
    )
    
    args = parser.parse_args()
    
    # Determine which tests to run
    if args.quick:
        exit_code = run_quick_tests()
    elif args.all:
        exit_code = run_all_tests()
    else:
        exit_code = run_tests(
            coverage=args.coverage,
            verbose=args.verbose,
            markers=args.markers,
            specific_test=args.test,
            html_report=args.html
        )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
