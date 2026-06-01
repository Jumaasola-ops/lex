#!/usr/bin/env python3
"""
Android Security Scanner - Main entry point.

A comprehensive security and privacy tool for Android devices via USB connection.
"""

import sys
import argparse
from command_interface import CommandInterface
from utils import log_info, print_section_header, print_info
from exceptions import AndroidSecurityException


def main() -> int:
    """
    Main entry point for Android Security Scanner.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        prog="android-security",
        description="Android Security Scanner - Malware detection, app analysis, and metadata removal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  android-security scan-malware              - Scan device for malware
  android-security analyze-apps              - Analyze installed apps
  android-security extract-metadata photo.jpg - Extract photo metadata
  android-security remove-metadata photo.jpg  - Remove photo metadata
  android-security full-scan                 - Comprehensive security scan
  android-security help                      - Show all available commands
        """,
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        help="Command to execute",
    )
    parser.add_argument(
        "args",
        nargs="*",
        help="Command arguments",
    )
    parser.add_argument(
        "-d", "--device",
        help="Device ID (if multiple devices connected)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    
    
    parsed = parser.parse_args()
    
    try:
        # Create and initialize command interface
        interface = CommandInterface()
        
        # Display banner
        if parsed.command != "help" or parsed.args:
            print_section_header("Android Security Scanner v1.0 - PRODUCTION READY")
        
        log_info(f"Executing command: {parsed.command}")
        
        # Execute command
        success = interface.execute(parsed.command, parsed.args)
        
        return 0 if success else 1
        
    except AndroidSecurityException as e:
        print(f"Error: {str(e)}")
        return 1
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
