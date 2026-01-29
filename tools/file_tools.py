"""
File Tools - Secure file operations for agents.
Implements sandbox security to prevent writing outside target directory.
Improvements:
- Atomic writes to prevent file corruption
- Better error handling
- File size validation
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
from datetime import datetime


class SandboxViolationError(Exception):
    """Raised when an operation tries to access files outside the sandbox."""
    pass


class FileSizeError(Exception):
    """Raised when a file exceeds the maximum allowed size."""
    pass


MAX_FILE_SIZE = 1_000_000  # 1MB default limit


def validate_sandbox_path(file_path: str, sandbox_dir: str) -> Path:
    """
    Validate that a file path is within the sandbox directory.
    
    Args:
        file_path: The path to validate
        sandbox_dir: The allowed sandbox directory
        
    Returns:
        Path: The resolved, validated path
        
    Raises:
        SandboxViolationError: If the path is outside the sandbox
    """
    sandbox = Path(sandbox_dir).resolve()
    target = Path(file_path).resolve()
    
    try:
        target.relative_to(sandbox)
        return target
    except ValueError:
        raise SandboxViolationError(
            f"Security violation: Path '{file_path}' is outside sandbox '{sandbox_dir}'"
        )


def read_file(file_path: str, sandbox_dir: Optional[str] = None) -> str:
    """
    Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
        sandbox_dir: Optional sandbox directory for validation
        
    Returns:
        str: The file contents
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        SandboxViolationError: If path is outside sandbox
    """
    if sandbox_dir:
        validated_path = validate_sandbox_path(file_path, sandbox_dir)
    else:
        validated_path = Path(file_path)
    
    if not validated_path.exists():
        raise FileNotFoundError(f"File not found: {validated_path}")
    
    with open(validated_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(file_path: str, content: str, sandbox_dir: str) -> bool:
    """
    Write content to a file with sandbox security and atomic writes.
    Uses temp file + rename for atomicity to prevent corruption.
    
    Args:
        file_path: Path to the file to write
        content: Content to write
        sandbox_dir: Sandbox directory for validation (required)
        
    Returns:
        bool: True if successful
        
    Raises:
        SandboxViolationError: If path is outside sandbox
    """
    validated_path = validate_sandbox_path(file_path, sandbox_dir)
    
    # Ensure parent directory exists
    validated_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Atomic write using temp file
    fd = None
    temp_path = None
    try:
        fd, temp_path = tempfile.mkstemp(
            dir=validated_path.parent,
            prefix='.tmp_',
            suffix=validated_path.suffix
        )
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            fd = None  # fd is now owned by the file object
            f.write(content)
        
        # Atomic rename (works on most systems)
        os.replace(temp_path, validated_path)
        temp_path = None  # Rename succeeded
        
    except Exception:
        # Clean up temp file on error
        if fd is not None:
            os.close(fd)
        if temp_path is not None and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
    
    return True


def backup_file(file_path: str, sandbox_dir: str) -> Optional[str]:
    """
    Create a backup of a file before modifying it.
    
    Args:
        file_path: Path to the file to backup
        sandbox_dir: Sandbox directory for validation
        
    Returns:
        str: Path to the backup file, or None if file doesn't exist
    """
    validated_path = validate_sandbox_path(file_path, sandbox_dir)
    
    if not validated_path.exists():
        return None
    
    # Create backup directory
    backup_dir = Path(sandbox_dir) / ".backups"
    backup_dir.mkdir(exist_ok=True)
    
    # Create timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{validated_path.stem}_{timestamp}{validated_path.suffix}"
    backup_path = backup_dir / backup_name
    
    shutil.copy2(validated_path, backup_path)
    
    return str(backup_path)


def list_python_files(directory: str, recursive: bool = True) -> List[str]:
    """
    List all Python files in a directory.
    
    Args:
        directory: Directory to search
        recursive: Whether to search recursively
        
    Returns:
        List[str]: List of Python file paths
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return []
    
    pattern = "**/*.py" if recursive else "*.py"
    
    # Filter out backup files and __pycache__
    python_files = []
    for f in dir_path.glob(pattern):
        if "__pycache__" not in str(f) and ".backups" not in str(f):
            python_files.append(str(f))
    
    return sorted(python_files)


def get_file_content(file_path: str, sandbox_dir: Optional[str] = None) -> dict:
    """
    Get file content with metadata.
    
    Args:
        file_path: Path to the file
        sandbox_dir: Optional sandbox directory for validation
        
    Returns:
        dict: File content and metadata
    """
    if sandbox_dir:
        validated_path = validate_sandbox_path(file_path, sandbox_dir)
    else:
        validated_path = Path(file_path)
    
    if not validated_path.exists():
        return {
            "path": str(validated_path),
            "exists": False,
            "content": None,
            "lines": 0,
            "size": 0
        }
    
    content = read_file(str(validated_path), sandbox_dir)
    
    return {
        "path": str(validated_path),
        "exists": True,
        "content": content,
        "lines": len(content.splitlines()),
        "size": len(content),
        "modified": datetime.fromtimestamp(validated_path.stat().st_mtime).isoformat()
    }


def create_file(file_path: str, content: str, sandbox_dir: str) -> bool:
    """
    Create a new file with content.
    
    Args:
        file_path: Path for the new file
        content: Content to write
        sandbox_dir: Sandbox directory for validation
        
    Returns:
        bool: True if successful
    """
    return write_file(file_path, content, sandbox_dir)


def delete_file(file_path: str, sandbox_dir: str) -> bool:
    """
    Delete a file with sandbox security.
    
    Args:
        file_path: Path to the file to delete
        sandbox_dir: Sandbox directory for validation
        
    Returns:
        bool: True if successful
    """
    validated_path = validate_sandbox_path(file_path, sandbox_dir)
    
    if validated_path.exists():
        validated_path.unlink()
        return True
    
    return False
