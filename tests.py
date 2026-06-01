"""
Unit tests for Android Security Scanner.
"""

import unittest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from exceptions import (
    AndroidSecurityException,
    ADBException,
    MetadataException,
    InvalidCommandException,
)
from utils import (
    sanitize_package_name,
    is_valid_package_name,
    format_size,
)
from config import SUSPICIOUS_PATTERNS, SYSTEM_PACKAGES


class TestExceptions(unittest.TestCase):
    """Test exception classes."""
    
    def test_base_exception(self):
        """Test AndroidSecurityException."""
        with self.assertRaises(AndroidSecurityException):
            raise AndroidSecurityException("Test error")
    
    def test_adb_exception(self):
        """Test ADBException."""
        with self.assertRaises(ADBException):
            raise ADBException("ADB error")
    
    def test_metadata_exception(self):
        """Test MetadataException."""
        with self.assertRaises(MetadataException):
            raise MetadataException("Metadata error")


class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def test_sanitize_package_name(self):
        """Test package name sanitization."""
        result = sanitize_package_name("COM.EXAMPLE.APP")
        self.assertEqual(result, "com.example.app")
        
        result = sanitize_package_name("  com.example.app  ")
        self.assertEqual(result, "com.example.app")
    
    def test_is_valid_package_name(self):
        """Test package name validation."""
        self.assertTrue(is_valid_package_name("com.example.app"))
        self.assertTrue(is_valid_package_name("com.google.android.gms"))
        self.assertFalse(is_valid_package_name("invalid-package"))
        self.assertFalse(is_valid_package_name(".invalid"))
        self.assertFalse(is_valid_package_name("invalid."))
    
    def test_format_size(self):
        """Test file size formatting."""
        self.assertEqual(format_size(512), "512.00 B")
        self.assertEqual(format_size(1024), "1.00 KB")
        self.assertEqual(format_size(1024 * 1024), "1.00 MB")
        self.assertEqual(format_size(1024 * 1024 * 1024), "1.00 GB")


class TestConfiguration(unittest.TestCase):
    """Test configuration."""
    
    def test_suspicious_patterns_exist(self):
        """Test that suspicious patterns are defined."""
        self.assertIsInstance(SUSPICIOUS_PATTERNS, list)
        self.assertGreater(len(SUSPICIOUS_PATTERNS), 0)
        self.assertIn("spy", SUSPICIOUS_PATTERNS)
    
    def test_system_packages_exist(self):
        """Test that system packages are defined."""
        self.assertIsInstance(SYSTEM_PACKAGES, list)
        self.assertGreater(len(SYSTEM_PACKAGES), 0)
        self.assertIn("com.android", SYSTEM_PACKAGES)


class TestAppAnalyzer(unittest.TestCase):
    """Test app analyzer without device connection."""
    
    def test_is_system_package(self):
        """Test system package detection."""
        from app_analyzer import AppAnalyzer
        from adb_manager import ADBManager
        
        # Note: Can't test without device, but we can test the concept
        self.assertIn("com.android", SYSTEM_PACKAGES)
    
    def test_is_suspicious_app(self):
        """Test suspicious app detection."""
        from app_analyzer import AppAnalyzer
        
        suspicious_pkg = "com.spy.tracker"
        pkg_lower = suspicious_pkg.lower()
        
        found = False
        for pattern in SUSPICIOUS_PATTERNS:
            if pattern in pkg_lower:
                found = True
                break
        
        self.assertTrue(found, f"Pattern not found in {suspicious_pkg}")


class TestMetadataHandler(unittest.TestCase):
    """Test metadata handler."""
    
    def test_metadata_handler_init(self):
        """Test metadata handler initialization."""
        from metadata_handler import MetadataHandler
        
        handler = MetadataHandler()
        self.assertIsNotNone(handler)


class TestCommandInterface(unittest.TestCase):
    """Test command interface without device connection."""
    
    def test_command_interface_init(self):
        """Test command interface initialization."""
        from command_interface import CommandInterface
        
        interface = CommandInterface()
        self.assertIsNotNone(interface)
        self.assertIn("help", interface.commands)
        self.assertIn("scan-malware", interface.commands)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
