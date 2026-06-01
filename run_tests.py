#!/usr/bin/env python
"""
Test runner with coverage reporting.
Author: Asola Junior
"""

import subprocess
import sys

def run_tests(coverage=True, verbose=True):
    """Run test suite with optional coverage."""
    cmd = ["pytest"]
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "test_suite.py",
        "-x",  # Stop on first failure
        "--tb=short",
    ])
    
    print("Running tests...")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode

if __name__ == "__main__":
    exit_code = run_tests(coverage=True, verbose=True)
    sys.exit(exit_code)
