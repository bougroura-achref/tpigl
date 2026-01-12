"""
Prompts Module - System prompts for agents
Contains versioned prompts for Auditor, Fixer, and Judge agents.
"""

from .auditor_prompt import AUDITOR_SYSTEM_PROMPT, AUDITOR_ANALYSIS_PROMPT
from .fixer_prompt import FIXER_SYSTEM_PROMPT, FIXER_REPAIR_PROMPT
from .judge_prompt import JUDGE_SYSTEM_PROMPT, JUDGE_EVALUATION_PROMPT

__all__ = [
    "AUDITOR_SYSTEM_PROMPT",
    "AUDITOR_ANALYSIS_PROMPT",
    "FIXER_SYSTEM_PROMPT",
    "FIXER_REPAIR_PROMPT",
    "JUDGE_SYSTEM_PROMPT",
    "JUDGE_EVALUATION_PROMPT",
]

# Prompt version for tracking
PROMPT_VERSION = "1.0.0"
