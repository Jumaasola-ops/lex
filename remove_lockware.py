#!/usr/bin/env python3
"""
Direct launcher for aggressive malware removal.
No menu, just direct execution of the removal tool.
Simply run: python remove_lockware.py
"""

import subprocess
import sys
import os

def main():
    """Direct execution without menu."""
    result = subprocess.run(
        [sys.executable, "aggressive_malware_remover.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
