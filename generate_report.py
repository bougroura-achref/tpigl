#!/usr/bin/env python3
"""
Telemetry Report Generator - Quality & Data Manager
Generates human-readable reports from experiment_data.json.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class TelemetryReportGenerator:
    """Generate reports from experiment data."""
    
    def __init__(self, data_path: str):
        """
        Initialize the report generator.
        
        Args:
            data_path: Path to experiment_data.json
        """
        self.data_path = Path(data_path)
        self.data: Dict[str, Any] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """Load experiment data from JSON file."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
    
    def generate_summary_report(self) -> str:
        """Generate a summary report."""
        lines = []
        lines.append("=" * 70)
        lines.append("📊 EXPERIMENT SUMMARY REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        # Metadata
        lines.append("📋 METADATA")
        lines.append("-" * 40)
        lines.append(f"  Experiment ID: {self.data.get('experiment_id', 'N/A')}")
        lines.append(f"  Started:       {self.data.get('started_at', 'N/A')}")
        lines.append(f"  Completed:     {self.data.get('completed_at', 'N/A')}")
        lines.append(f"  Duration:      {self.data.get('duration_seconds', 0):.2f} seconds")
        lines.append(f"  Target Dir:    {self.data.get('target_directory', 'N/A')}")
        lines.append(f"  LLM Model:     {self.data.get('llm_model', 'N/A')}")
        lines.append("")
        
        # Results
        status = self.data.get('status', 'N/A')
        status_emoji = "✅" if status == "success" else "❌" if status == "failed" else "⏳"
        
        lines.append("📈 RESULTS")
        lines.append("-" * 40)
        lines.append(f"  Status:           {status_emoji} {status.upper()}")
        lines.append(f"  Total Iterations: {self.data.get('total_iterations', 0)}")
        lines.append(f"  Files Processed:  {self.data.get('files_processed', 0)}")
        lines.append(f"  Files Successful: {self.data.get('files_successful', 0)}")
        lines.append(f"  Files Failed:     {self.data.get('files_failed', 0)}")
        lines.append("")
        
        # Scores
        initial = self.data.get('initial_pylint_score', 0)
        final = self.data.get('final_pylint_score', 0)
        improvement = self.data.get('score_improvement', 0)
        
        lines.append("🎯 PYLINT SCORES")
        lines.append("-" * 40)
        lines.append(f"  Initial Score:    {initial:.2f}/10")
        lines.append(f"  Final Score:      {final:.2f}/10")
        lines.append(f"  Improvement:      {improvement:+.2f}")
        
        # Score bar visualization
        initial_bar = "█" * int(initial) + "░" * (10 - int(initial))
        final_bar = "█" * int(final) + "░" * (10 - int(final))
        lines.append(f"  Before: [{initial_bar}] {initial:.1f}")
        lines.append(f"  After:  [{final_bar}] {final:.1f}")
        lines.append("")
        
        # Tests
        tests_run = self.data.get('tests_run', 0)
        tests_passed = self.data.get('tests_passed', 0)
        tests_failed = self.data.get('tests_failed', 0)
        
        if tests_run > 0:
            lines.append("🧪 TESTS")
            lines.append("-" * 40)
            lines.append(f"  Tests Run:    {tests_run}")
            lines.append(f"  Tests Passed: {tests_passed} ✅")
            lines.append(f"  Tests Failed: {tests_failed} {'❌' if tests_failed > 0 else ''}")
            lines.append("")
        
        # Errors
        errors = self.data.get('errors', [])
        if errors:
            lines.append("⚠️ ERRORS")
            lines.append("-" * 40)
            for i, error in enumerate(errors[:5], 1):  # Show max 5 errors
                lines.append(f"  {i}. [{error.get('error_type', 'Unknown')}] {error.get('message', 'No message')[:50]}")
            if len(errors) > 5:
                lines.append(f"  ... and {len(errors) - 5} more errors")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def generate_file_report(self) -> str:
        """Generate detailed report for each file."""
        lines = []
        lines.append("=" * 70)
        lines.append("📁 FILE RESULTS REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        file_results = self.data.get('file_results', [])
        
        if not file_results:
            lines.append("  No file results available.")
            return "\n".join(lines)
        
        for i, result in enumerate(file_results, 1):
            status = result.get('status', 'unknown')
            status_emoji = "✅" if status == "success" else "❌"
            
            lines.append(f"📄 File {i}: {result.get('file', 'Unknown')}")
            lines.append("-" * 50)
            lines.append(f"  Status:      {status_emoji} {status.upper()}")
            lines.append(f"  Original:    {result.get('original_score', 0):.2f}/10")
            lines.append(f"  Final:       {result.get('final_score', 0):.2f}/10")
            lines.append(f"  Improvement: {result.get('score_improvement', 0):+.2f}")
            lines.append(f"  Iterations:  {result.get('iterations', 0)}")
            lines.append(f"  Tests Pass:  {'✅' if result.get('tests_passed') else '❌'}")
            
            changes = result.get('changes', [])
            if changes:
                lines.append(f"  Changes ({result.get('changes_count', len(changes))}):")
                for change in changes[:5]:
                    lines.append(f"    • {change[:60]}{'...' if len(change) > 60 else ''}")
                if len(changes) > 5:
                    lines.append(f"    ... and {len(changes) - 5} more changes")
            
            lines.append("")
        
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def generate_agent_activity_report(self) -> str:
        """Generate report of agent activity timeline."""
        lines = []
        lines.append("=" * 70)
        lines.append("🤖 AGENT ACTIVITY TIMELINE")
        lines.append("=" * 70)
        lines.append("")
        
        agent_logs = self.data.get('agent_logs', [])
        
        if not agent_logs:
            lines.append("  No agent activity recorded.")
            return "\n".join(lines)
        
        # Group by agent
        agent_actions = {"auditor": 0, "fixer": 0, "judge": 0, "other": 0}
        
        for log in agent_logs:
            agent = log.get('agent', 'other').lower()
            if agent in agent_actions:
                agent_actions[agent] += 1
            else:
                agent_actions['other'] += 1
        
        lines.append("📊 Agent Action Counts:")
        lines.append(f"  🔍 Auditor: {agent_actions['auditor']} actions")
        lines.append(f"  🔧 Fixer:   {agent_actions['fixer']} actions")
        lines.append(f"  ⚖️ Judge:   {agent_actions['judge']} actions")
        if agent_actions['other'] > 0:
            lines.append(f"  📋 Other:   {agent_actions['other']} events")
        lines.append("")
        
        lines.append("📜 Activity Timeline (last 10):")
        lines.append("-" * 50)
        
        for log in agent_logs[-10:]:
            timestamp = log.get('timestamp', '')[:19]  # Trim to seconds
            event_type = log.get('event_type', log.get('action', 'unknown'))
            agent = log.get('agent', '')
            
            emoji = {"auditor": "🔍", "fixer": "🔧", "judge": "⚖️"}.get(agent, "📋")
            lines.append(f"  {timestamp} {emoji} {event_type}")
        
        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def generate_full_report(self) -> str:
        """Generate complete report with all sections."""
        sections = [
            self.generate_summary_report(),
            "",
            self.generate_file_report(),
            "",
            self.generate_agent_activity_report()
        ]
        return "\n".join(sections)
    
    def save_report(self, output_path: Optional[str] = None, format: str = "txt") -> Path:
        """
        Save report to file.
        
        Args:
            output_path: Output file path
            format: Output format (txt, md, json)
            
        Returns:
            Path to saved report
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.data_path.parent / f"report_{timestamp}.{format}"
        else:
            output_path = Path(output_path)
        
        if format == "json":
            content = json.dumps(self.data, indent=2)
        elif format == "md":
            content = self._to_markdown(self.generate_full_report())
        else:
            content = self.generate_full_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path
    
    def _to_markdown(self, text: str) -> str:
        """Convert plain text report to Markdown format."""
        # Simple conversion - wrap code-like sections
        lines = text.split("\n")
        md_lines = []
        
        for line in lines:
            if line.startswith("="):
                md_lines.append("---")
            elif line.startswith("-" * 10):
                md_lines.append("")
            elif line.startswith("📊") or line.startswith("📁") or line.startswith("🤖"):
                md_lines.append(f"## {line}")
            elif line.startswith("📋") or line.startswith("📈") or line.startswith("🎯"):
                md_lines.append(f"### {line}")
            else:
                md_lines.append(line)
        
        return "\n".join(md_lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate reports from experiment data"
    )
    parser.add_argument(
        "data_file",
        nargs="?",
        default="logs/experiment_data.json",
        help="Path to experiment_data.json"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["txt", "md", "json"],
        default="txt",
        help="Output format"
    )
    parser.add_argument(
        "--save", "-s",
        action="store_true",
        help="Save report to file"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show only summary"
    )
    parser.add_argument(
        "--files",
        action="store_true",
        help="Show only file results"
    )
    parser.add_argument(
        "--activity",
        action="store_true",
        help="Show only agent activity"
    )
    
    args = parser.parse_args()
    
    try:
        generator = TelemetryReportGenerator(args.data_file)
        
        # Determine which report to generate
        if args.summary:
            report = generator.generate_summary_report()
        elif args.files:
            report = generator.generate_file_report()
        elif args.activity:
            report = generator.generate_agent_activity_report()
        else:
            report = generator.generate_full_report()
        
        # Output
        if args.save or args.output:
            output_path = generator.save_report(args.output, args.format)
            print(f"📄 Report saved to: {output_path}")
        else:
            print(report)
            
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
