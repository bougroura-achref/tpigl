# 🎓 The Refactoring Swarm

A multi-agent system for autonomous software maintenance, built as part of the IGL Lab (2025-2026).

## 📋 Project Description

This project implements an autonomous agent architecture capable of performing software maintenance without human intervention. The system takes a folder containing "badly made" Python code (buggy, undocumented, untested) and delivers a clean, functional version validated by tests.

## 🏗️ System Architecture

The system orchestrates collaboration between 3 specialized agents:

1. **The Auditor** 🔍: Reads the code, runs static analysis (pylint) and produces a refactoring plan.
2. **The Fixer** 🔧: Reads the plan, modifies the code file by file to correct errors.
3. **The Judge** ⚖️: Executes unit tests (pytest).
   - If unsuccessful: Sends the code back to the Fixer with error logs (Self-Healing Loop)
   - If successful: Confirms the end of the mission

## 📁 Project Structure

```
tpigl/
├── main.py                 # Entry point with CLI
├── check_setup.py          # Environment validation script
├── requirements.txt        # Project dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
│
├── agents/                 # Agent implementations
│   ├── __init__.py
│   ├── auditor.py         # The Auditor agent
│   ├── fixer.py           # The Fixer agent
│   └── judge.py           # The Judge agent
│
├── tools/                  # Tools called by agents
│   ├── __init__.py
│   ├── file_tools.py      # File reading/writing with sandbox security
│   ├── analysis_tools.py  # Pylint integration
│   └── test_tools.py      # Pytest integration
│
├── prompts/                # System prompts for agents
│   ├── __init__.py
│   ├── auditor_prompt.py
│   ├── fixer_prompt.py
│   └── judge_prompt.py
│
├── orchestrator/           # Execution graph and workflow
│   ├── __init__.py
│   ├── graph.py           # LangGraph workflow definition
│   └── state.py           # Shared state management
│
├── logging_system/         # Telemetry and logging
│   ├── __init__.py
│   └── telemetry.py       # Experiment data logging
│
├── logs/                   # Log output directory
│   ├── .gitkeep
│   └── experiment_data.json
│
├── sandbox/                # Target directory for refactoring (example)
│   └── .gitkeep
│
└── tests/                  # Internal test dataset
    ├── __init__.py
    ├── test_tools.py
    └── sample_buggy_code/  # Test input files
        └── .gitkeep
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Google Gemini API key
```

### 3. Validate Setup

```bash
python check_setup.py
```

### 4. Run the System

```bash
python main.py --target_dir ./sandbox
```

## 📊 CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--target_dir` | Directory containing code to refactor | Required |
| `--max_iterations` | Maximum self-healing loop iterations | 10 |
| `--verbose` | Enable verbose logging | False |

## 📈 Evaluation Criteria

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| Performance | 40% | Unit tests pass, Pylint score improved |
| Technical Robustness | 30% | No crashes, no infinite loops, CLI compliance |
| Data Quality | 30% | Valid experiment_data.json with complete history |

## 👥 Team Roles

1. **Orchestrator (Lead Dev)** 🧠 - Designs execution graph, manages workflow
2. **Toolsmith** 🛠️ - Develops agent tools, implements security
3. **Prompt Engineer** 💬 - Writes and optimizes prompts
4. **Quality & Data Manager** 📊 - Manages telemetry and logging

## 📜 License

This project is for educational purposes as part of the IGL Module at the National School of Computer Science.
