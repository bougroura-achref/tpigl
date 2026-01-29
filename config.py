"""
Configuration Module - Centralized configuration for The Refactoring Swarm.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path


@dataclass
class LLMConfig:
    """Configuration for LLM settings."""
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "claude-sonnet-4-20250514"))
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class AgentConfig:
    """Configuration for agent behavior."""
    # Auditor settings
    auditor_cache_enabled: bool = True
    
    # Fixer settings
    fixer_create_backups: bool = True
    fixer_validate_syntax: bool = True
    
    # Judge settings
    judge_success_score_threshold: float = 8.0
    judge_regression_threshold: float = 2.0
    judge_require_tests_pass: bool = True


@dataclass
class WorkflowConfig:
    """Configuration for workflow behavior."""
    max_iterations: int = 10
    max_error_logs: int = 50
    checkpoint_interval: int = 5
    enable_parallel_analysis: bool = False
    max_parallel_workers: int = 4
    timeout_seconds: int = 3600


@dataclass
class TelemetryConfig:
    """Configuration for telemetry and logging."""
    log_dir: Path = field(default_factory=lambda: Path.cwd() / "logs")
    auto_save_interval: int = 10
    verbose: bool = False
    log_level: str = "INFO"


@dataclass
class SecurityConfig:
    """Configuration for security settings."""
    enable_sandbox: bool = True
    allowed_file_extensions: List[str] = field(default_factory=lambda: [".py"])
    max_file_size_bytes: int = 1_000_000  # 1MB


@dataclass
class SwarmConfig:
    """Master configuration for The Refactoring Swarm."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    agents: AgentConfig = field(default_factory=AgentConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    @classmethod
    def from_env(cls) -> "SwarmConfig":
        """Create configuration from environment variables."""
        config = cls()
        
        # Override from environment
        if os.getenv("MODEL_NAME"):
            config.llm.model_name = os.getenv("MODEL_NAME")
        if os.getenv("LLM_TEMPERATURE"):
            config.llm.temperature = float(os.getenv("LLM_TEMPERATURE"))
        if os.getenv("MAX_ITERATIONS"):
            config.workflow.max_iterations = int(os.getenv("MAX_ITERATIONS"))
        if os.getenv("VERBOSE"):
            config.telemetry.verbose = os.getenv("VERBOSE").lower() == "true"
        if os.getenv("LOG_DIR"):
            config.telemetry.log_dir = Path(os.getenv("LOG_DIR"))
            
        return config


# Global default configuration
_default_config: Optional[SwarmConfig] = None


def get_config() -> SwarmConfig:
    """Get the global configuration instance."""
    global _default_config
    if _default_config is None:
        _default_config = SwarmConfig.from_env()
    return _default_config


def set_config(config: SwarmConfig) -> None:
    """Set the global configuration instance."""
    global _default_config
    _default_config = config
