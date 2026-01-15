#!/usr/bin/env python3
"""
The Refactoring Swarm - Main Entry Point
A multi-agent system for autonomous software maintenance.

Usage:
    python main.py --target_dir ./sandbox
    python main.py --target_dir ./sandbox --max_iterations 5 --verbose
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from orchestrator.graph import RefactoringGraph
from orchestrator.state import SwarmState
from logging_system.telemetry import TelemetryLogger

# Load environment variables
load_dotenv()

console = Console()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="The Refactoring Swarm - Autonomous Code Refactoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py --target_dir ./sandbox
    python main.py --target_dir ./sandbox --max_iterations 5
    python main.py --target_dir ./sandbox --verbose
        """
    )
    
    parser.add_argument(
        "--target_dir",
        type=str,
        required=True,
        help="Directory containing the code to refactor"
    )
    
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=10,
        help="Maximum number of self-healing loop iterations (default: 10)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output"
    )
    
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Analyze code without making changes"
    )
    
    return parser.parse_args()


def validate_target_dir(target_dir: str) -> Path:
    """Validate the target directory exists and is accessible."""
    path = Path(target_dir).resolve()
    
    if not path.exists():
        console.print(f"[red]❌ Error: Target directory does not exist: {path}[/red]")
        sys.exit(1)
    
    if not path.is_dir():
        console.print(f"[red]❌ Error: Target path is not a directory: {path}[/red]")
        sys.exit(1)
    
    # Check for Python files
    python_files = list(path.glob("**/*.py"))
    if not python_files:
        console.print(f"[yellow]⚠️  Warning: No Python files found in {path}[/yellow]")
    
    return path


def validate_api_key():
    """Validate that Anthropic API key is configured."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key or api_key == "your_anthropic_api_key_here":
        console.print("[red]❌ Error: ANTHROPIC_API_KEY not configured[/red]")
        console.print("[yellow]   Please set your API key in the .env file[/yellow]")
        sys.exit(1)
    
    return api_key


def display_banner():
    """Display the application banner."""
    banner = """
🎓 The Refactoring Swarm
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Autonomous Code Refactoring System
IGL Lab - 2025/2026
    """
    console.print(Panel(banner, style="bold blue"))


def display_config(args, target_path: Path):
    """Display the current configuration."""
    console.print("\n[bold]📋 Configuration:[/bold]")
    console.print(f"   Target Directory: {target_path}")
    console.print(f"   Max Iterations: {args.max_iterations}")
    console.print(f"   Verbose Mode: {'Enabled' if args.verbose else 'Disabled'}")
    console.print(f"   Dry Run: {'Yes' if args.dry_run else 'No'}")
    
    # Count Python files
    python_files = list(target_path.glob("**/*.py"))
    console.print(f"   Python Files Found: {len(python_files)}")
    console.print()


def main():
    """Main entry point for The Refactoring Swarm."""
    # Parse arguments
    args = parse_arguments()
    
    # Display banner
    display_banner()
    
    # Validate inputs
    console.print("[bold]🔍 Validating configuration...[/bold]")
    target_path = validate_target_dir(args.target_dir)
    api_key = validate_api_key()
    console.print("[green]   ✅ Configuration valid[/green]")
    
    # Display configuration
    display_config(args, target_path)
    
    # Initialize telemetry logger
    telemetry = TelemetryLogger(
        experiment_id=f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        target_dir=str(target_path)
    )
    
    try:
        # Initialize the refactoring graph
        console.print("[bold]🚀 Starting The Refactoring Swarm...[/bold]\n")
        
        graph = RefactoringGraph(
            target_dir=target_path,
            max_iterations=args.max_iterations,
            verbose=args.verbose,
            telemetry=telemetry,
            dry_run=args.dry_run
        )
        
        # Initialize state
        initial_state = SwarmState(
            target_dir=str(target_path),
            iteration=0,
            max_iterations=args.max_iterations,
            status="initialized"
        )
        
        # Run the refactoring process
        telemetry.log_event("swarm_started", {
            "target_dir": str(target_path),
            "max_iterations": args.max_iterations
        })
        
        final_state = graph.run(initial_state)
        
        # Display results
        console.print("\n" + "=" * 60)
        console.print("[bold]📊 Refactoring Complete![/bold]")
        console.print("=" * 60)
        
        console.print(f"\n   Status: {final_state.status}")
        console.print(f"   Iterations: {final_state.iteration}")
        console.print(f"   Initial Pylint Score: {final_state.initial_pylint_score:.2f}")
        console.print(f"   Final Pylint Score: {final_state.final_pylint_score:.2f}")
        console.print(f"   Tests Passed: {final_state.tests_passed}")
        
        # Log completion
        telemetry.log_event("swarm_completed", {
            "status": final_state.status,
            "iterations": final_state.iteration,
            "initial_score": final_state.initial_pylint_score,
            "final_score": final_state.final_pylint_score,
            "tests_passed": final_state.tests_passed
        })
        
        # Save telemetry
        telemetry.save()
        console.print(f"\n   📁 Experiment data saved to: logs/experiment_data.json")
        
        # Exit with appropriate code
        if final_state.status == "success":
            console.print("\n[bold green]🎉 Refactoring completed successfully![/bold green]")
            return 0
        else:
            console.print(f"\n[bold yellow]⚠️  Refactoring completed with status: {final_state.status}[/bold yellow]")
            return 1
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
        telemetry.log_event("swarm_cancelled", {"reason": "user_interrupt"})
        telemetry.save()
        return 130
        
    except Exception as e:
        console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        telemetry.log_event("swarm_error", {"error": str(e)})
        telemetry.save()
        if args.verbose:
            import traceback
            console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
