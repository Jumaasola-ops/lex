"""
Utility functions for Android Security Scanner.
"""

import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, Any
from datetime import datetime

from config import LOG_FILE, LOG_LEVEL


def setup_logger() -> logging.Logger:
    """
    Configure and return logger instance.
    
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger("AndroidSecurityScanner")
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logger()


def log_info(message: str) -> None:
    """Log info message."""
    logger.info(message)


def log_error(message: str) -> None:
    """Log error message."""
    logger.error(message)


def log_warning(message: str) -> None:
    """Log warning message."""
    logger.warning(message)


def log_debug(message: str) -> None:
    """Log debug message."""
    logger.debug(message)


def format_timestamp() -> str:
    """
    Get current timestamp in standard format.
    
    Returns:
        str: Formatted timestamp
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def validate_file_path(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if file path exists and is accessible.
    
    Args:
        file_path: Path to file
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, f"File does not exist: {file_path}"
    
    if not path.is_file():
        return False, f"Path is not a file: {file_path}"
    
    if not os.access(file_path, os.R_OK):
        return False, f"File is not readable: {file_path}"
    
    return True, None


def sanitize_package_name(package_name: str) -> str:
    """
    Sanitize package name for safe display.
    
    Args:
        package_name: Package name to sanitize
        
    Returns:
        str: Sanitized package name
    """
    return package_name.strip().lower()


def is_valid_package_name(package_name: str) -> bool:
    """
    Validate package name format.
    
    Args:
        package_name: Package name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    # Android package name format: com.example.app or similar
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z0-9_]+)*$'
    return bool(re.match(pattern, package_name))


def format_size(size_bytes: int) -> str:
    """
    Format bytes to human-readable size.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def print_section_header(title: str) -> None:
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_success(message: str) -> None:
    """Print success message with formatting."""
    print(f"✓ {message}")


def print_error(message: str) -> None:
    """Print error message with formatting."""
    print(f"✗ {message}")


def print_warning(message: str) -> None:
    """Print warning message with formatting."""
    print(f"⚠ {message}")


def print_info(message: str) -> None:
    """Print info message with formatting."""
    print(f"ℹ {message}")


def display_banner() -> None:
    """Display LEX_BY ASOLA banner with ASCII art and colors."""
    # ANSI color codes
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BRIGHT_WHITE = "\033[97m"
    
    banner = f"""{RED}
    ██╗     ███████╗██╗  ██╗{RESET}{GREEN}    ██████╗ ██╗   ██╗{RESET}{YELLOW}    █████╗ ███████╗ ██████╗ ██╗      █████╗ {RESET}
    {RED}██║     ██╔════╝╚██╗██╔╝{RESET}{GREEN}    ██╔══██╗╚██╗ ██╔╝{RESET}{YELLOW}   ██╔══██╗██╔════╝██╔═══██╗██║     ██╔══██╗{RESET}
    {RED}██║     █████╗   ╚███╔╝ {RESET}{GREEN}    ██████╔╝ ╚████╔╝ {RESET}{YELLOW}   ███████║███████╗██║   ██║██║     ███████║{RESET}
    {RED}██║     ██╔══╝   ██╔██╗ {RESET}{GREEN}    ██╔══██╗  ╚██╔╝  {RESET}{YELLOW}   ██╔══██║╚════██║██║   ██║██║     ██╔══██║{RESET}
    {RED}███████╗███████╗██╔╝ ██╗{RESET}{GREEN}    ██████╔╝   ██║   {RESET}{YELLOW}   ██║  ██║███████║╚██████╔╝███████╗██║  ██║{RESET}
    {RED}╚══════╝╚══════╝╚═╝  ╚═╝{RESET}{GREEN}    ╚═════╝    ╚═╝   {RESET}{YELLOW}   ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝{RESET}
    
    """
    print(banner)
    print(f"    {CYAN}Android Security Intelligence System{RESET}")
    print(f"    {MAGENTA}{format_timestamp()}{RESET}")
    print("\n" + f"{BLUE}{'='*60}{RESET}\n")


import os
