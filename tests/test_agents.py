"""
Test Agents - Unit tests for the agents module
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAuditorAgent:
    """Tests for AuditorAgent"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test file with issues
        self.test_file = os.path.join(self.temp_dir, "sample.py")
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("import os\nx=1\nprint( x )\n")
    
    def teardown_method(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_auditor_initialization(self):
        """Test AuditorAgent can be initialized"""
        # Skip if no API key (supports both Anthropic and Google)
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
            pytest.skip("No API key set (ANTHROPIC_API_KEY or GOOGLE_API_KEY)")
        
        from agents import AuditorAgent
        agent = AuditorAgent(verbose=False)
        assert agent is not None
    
    def test_auditor_analyze_file_structure(self):
        """Test that analyze_file returns expected structure"""
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
            pytest.skip("No API key set (ANTHROPIC_API_KEY or GOOGLE_API_KEY)")
        
        from agents import AuditorAgent
        agent = AuditorAgent(verbose=False)
        
        result = agent.analyze_file(self.test_file, self.temp_dir)
        
        assert "success" in result
        if result["success"]:
            assert "analysis" in result
            analysis = result["analysis"]
            assert "file_path" in analysis


class TestFixerAgent:
    """Tests for FixerAgent"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        self.test_file = os.path.join(self.temp_dir, "to_fix.py")
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("x=1\ny=2\nz=x+y\n")
    
    def teardown_method(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_fixer_initialization(self):
        """Test FixerAgent can be initialized"""
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
            pytest.skip("No API key set (ANTHROPIC_API_KEY or GOOGLE_API_KEY)")
        
        from agents import FixerAgent
        agent = FixerAgent(verbose=False)
        assert agent is not None


class TestJudgeAgent:
    """Tests for JudgeAgent"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        self.test_file = os.path.join(self.temp_dir, "evaluated.py")
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write('"""Module."""\n\n\ndef main():\n    """Main."""\n    print("hello")\n')
    
    def teardown_method(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_judge_initialization(self):
        """Test JudgeAgent can be initialized"""
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
            pytest.skip("No API key set (ANTHROPIC_API_KEY or GOOGLE_API_KEY)")
        
        from agents import JudgeAgent
        agent = JudgeAgent(verbose=False)
        assert agent is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
