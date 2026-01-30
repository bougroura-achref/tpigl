"""
Test Tools - Unit tests for the tools module
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.file_tools import (
    validate_sandbox_path,
    read_file,
    write_file,
    backup_file,
    list_python_files,
    SandboxViolationError
)
from tools.analysis_tools import run_pylint, get_pylint_score, format_pylint_report
from tools.test_tools import discover_tests


class TestFileTools:
    """Tests for file_tools module"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.py")
        
        # Create a test file
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("# Test file\nprint('hello')\n")
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_validate_sandbox_path_valid(self):
        """Test that valid paths pass validation"""
        result = validate_sandbox_path(self.test_file, self.temp_dir)
        # validate_sandbox_path returns a Path object
        assert str(result) == str(Path(self.test_file).resolve())
    
    def test_validate_sandbox_path_invalid(self):
        """Test that paths outside sandbox raise exception"""
        with pytest.raises(SandboxViolationError):
            validate_sandbox_path("/etc/passwd", self.temp_dir)
    
    def test_read_file(self):
        """Test reading a file"""
        content = read_file(self.test_file, self.temp_dir)
        assert "# Test file" in content
        assert "print('hello')" in content
    
    def test_read_file_not_found(self):
        """Test reading non-existent file"""
        with pytest.raises(FileNotFoundError):
            read_file(os.path.join(self.temp_dir, "nonexistent.py"), self.temp_dir)
    
    def test_write_file(self):
        """Test writing a file"""
        new_file = os.path.join(self.temp_dir, "new.py")
        content = "# New file\nprint('new')\n"
        
        result = write_file(new_file, content, self.temp_dir)
        
        # write_file returns bool directly
        assert result is True
        assert os.path.exists(new_file)
        
        with open(new_file, 'r', encoding='utf-8') as f:
            assert f.read() == content
    
    def test_backup_file(self):
        """Test creating a backup"""
        backup_path = backup_file(self.test_file, self.temp_dir)
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        # Backups go to .backups folder with timestamp
        assert ".backups" in backup_path or "_20" in backup_path
    
    def test_list_python_files(self):
        """Test listing Python files"""
        # Create additional Python files
        for name in ["a.py", "b.py"]:
            with open(os.path.join(self.temp_dir, name), 'w') as f:
                f.write("# File\n")
        
        files = list_python_files(self.temp_dir)
        
        assert len(files) >= 2
        assert all(f.endswith('.py') for f in files)
    
    def test_list_python_files_excludes_pycache(self):
        """Test that __pycache__ and .backups are excluded"""
        # Create a pycache directory with files
        pycache_dir = os.path.join(self.temp_dir, "__pycache__")
        os.makedirs(pycache_dir, exist_ok=True)
        pycache_file = os.path.join(pycache_dir, "cached.py")
        with open(pycache_file, 'w') as f:
            f.write("# Cached file\n")
        
        files = list_python_files(self.temp_dir)
        
        # __pycache__ files should be excluded
        assert pycache_file not in files


class TestAnalysisTools:
    """Tests for analysis_tools module"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a file with known issues
        self.bad_file = os.path.join(self.temp_dir, "bad.py")
        with open(self.bad_file, 'w', encoding='utf-8') as f:
            f.write("import os\nimport sys\n\nx=1\n")  # Unused imports, missing spaces
        
        # Create a clean file
        self.good_file = os.path.join(self.temp_dir, "good.py")
        with open(self.good_file, 'w', encoding='utf-8') as f:
            f.write('"""Module docstring."""\n\n\ndef main():\n    """Main function."""\n    print("Hello")\n\n\nif __name__ == "__main__":\n    main()\n')
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_run_pylint_returns_result(self):
        """Test that pylint runs and returns a result"""
        result = run_pylint(self.bad_file)
        
        assert result is not None
        assert "score" in result
        assert "messages" in result
    
    def test_get_pylint_score(self):
        """Test getting pylint score"""
        score = get_pylint_score(self.good_file)
        
        assert isinstance(score, float)
        assert 0 <= score <= 10
    
    def test_format_pylint_report(self):
        """Test formatting pylint report"""
        result = run_pylint(self.bad_file)
        # format_pylint_report expects a list of messages, not the full result
        messages = result.get("messages", [])
        report = format_pylint_report(messages)
        
        assert isinstance(report, str)
        # Report should have header or content
        assert len(report) > 0


class TestTestTools:
    """Tests for test_tools module"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test_example.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('''
def test_addition():
    assert 1 + 1 == 2

def test_subtraction():
    assert 5 - 3 == 2
''')
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_discover_tests(self):
        """Test discovering test files"""
        test_files = discover_tests(self.temp_dir)
        
        assert len(test_files) >= 1
        assert any("test_example.py" in f for f in test_files)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
