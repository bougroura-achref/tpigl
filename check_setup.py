"""
Check Setup Script - Validates the environment for The Refactoring Swarm
Run this script to ensure all dependencies and configurations are correct.
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.10+"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Need 3.10+")
        return False


def check_dependencies():
    """Check if all required packages are installed"""
    print("\n🔍 Checking dependencies...")
    required_packages = [
        ("langchain", "langchain"),
        ("langgraph", "langgraph"),
        ("langchain_google_genai", "langchain-google-genai"),
        ("google.generativeai", "google-generativeai"),
        ("pylint", "pylint"),
        ("pytest", "pytest"),
        ("dotenv", "python-dotenv"),
        ("pydantic", "pydantic"),
        ("rich", "rich"),
    ]
    
    all_ok = True
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"   ✅ {package_name} - OK")
        except ImportError:
            print(f"   ❌ {package_name} - NOT INSTALLED")
            all_ok = False
    
    return all_ok


def check_env_file():
    """Check if .env file exists and has API key"""
    print("\n🔍 Checking environment configuration...")
    env_path = Path(".env")
    
    if not env_path.exists():
        print("   ⚠️  .env file not found - Copy .env.example to .env")
        return False
    
    # Check for API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key and api_key != "your_google_api_key_here":
        print("   ✅ GOOGLE_API_KEY configured")
        return True
    else:
        print("   ⚠️  GOOGLE_API_KEY not set or using default value")
        return False


def check_directory_structure():
    """Check if all required directories exist"""
    print("\n🔍 Checking directory structure...")
    required_dirs = [
        "agents",
        "tools",
        "prompts",
        "orchestrator",
        "logging_system",
        "logs",
        "sandbox",
        "tests",
    ]
    
    all_ok = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            print(f"   ✅ {dir_name}/ - OK")
        else:
            print(f"   ❌ {dir_name}/ - MISSING")
            all_ok = False
    
    return all_ok


def check_main_files():
    """Check if main module files exist"""
    print("\n🔍 Checking main files...")
    required_files = [
        "main.py",
        "requirements.txt",
        "agents/__init__.py",
        "agents/auditor.py",
        "agents/fixer.py",
        "agents/judge.py",
        "tools/__init__.py",
        "tools/file_tools.py",
        "tools/analysis_tools.py",
        "tools/test_tools.py",
        "prompts/__init__.py",
        "orchestrator/__init__.py",
        "orchestrator/graph.py",
        "orchestrator/state.py",
        "logging_system/__init__.py",
        "logging_system/telemetry.py",
    ]
    
    all_ok = True
    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists() and file_path.is_file():
            print(f"   ✅ {file_name} - OK")
        else:
            print(f"   ❌ {file_name} - MISSING")
            all_ok = False
    
    return all_ok


def check_pylint():
    """Check if pylint works correctly"""
    print("\n🔍 Checking pylint integration...")
    try:
        from pylint import lint
        from pylint.reporters.text import TextReporter
        from io import StringIO
        
        # Create a simple test
        test_code = '''
def hello():
    """A simple function."""
    print("Hello, World!")
'''
        # Write temporary file
        test_file = Path("_temp_check.py")
        test_file.write_text(test_code)
        
        # Run pylint
        output = StringIO()
        reporter = TextReporter(output)
        
        try:
            lint.Run([str(test_file), "--disable=all", "--enable=E"], reporter=reporter, exit=False)
            print("   ✅ pylint - OK")
            result = True
        except Exception as e:
            print(f"   ❌ pylint error: {e}")
            result = False
        finally:
            test_file.unlink()
        
        return result
        
    except Exception as e:
        print(f"   ❌ pylint import error: {e}")
        return False


def check_pytest():
    """Check if pytest works correctly"""
    print("\n🔍 Checking pytest integration...")
    try:
        import pytest
        print(f"   ✅ pytest version {pytest.__version__} - OK")
        return True
    except Exception as e:
        print(f"   ❌ pytest error: {e}")
        return False


def main():
    """Run all checks"""
    print("=" * 60)
    print("🎓 The Refactoring Swarm - Setup Validation")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directory Structure", check_directory_structure),
        ("Main Files", check_main_files),
        ("Pylint Integration", check_pylint),
        ("Pytest Integration", check_pytest),
        ("Environment Config", check_env_file),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            results.append((name, check_func()))
        except Exception as e:
            print(f"   ❌ Error during {name} check: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"   {name}: {status}")
    
    print(f"\n   Total: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Your environment is ready.")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
