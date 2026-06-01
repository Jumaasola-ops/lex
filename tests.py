"""
Production Integration Tests for Android Security Scanner.

These tests require a live Android device connected via ADB.
"""

import unittest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from adb_manager import ADBManager
from app_analyzer import AppAnalyzer
from malware_scanner import MalwareScanner
from system_analyzer import SystemAnalyzer
from command_interface import CommandInterface
from exceptions import AndroidSecurityException, ADBException


class ProductionTestBase(unittest.TestCase):
    """Base class for production tests requiring live device."""
    
    @classmethod
    def setUpClass(cls):
        """Initialize ADB manager for all tests."""
        cls.adb_manager = ADBManager()
        # Verify device is connected
        if not cls.adb_manager.is_device_connected():
            raise ADBException("No Android device connected. Live tests require a connected device.")
    
    def tearDown(self):
        """Cleanup after each test."""
        pass


class ProductionDeviceTests(ProductionTestBase):
    """Production tests for device connectivity and basic operations."""
    
    def test_device_connected(self):
        """Test that device is connected."""
        self.assertTrue(self.adb_manager.is_device_connected())
    
    def test_get_device_info(self):
        """Test retrieving device information."""
        device_info = self.adb_manager.get_device_info()
        self.assertIsNotNone(device_info)
        self.assertIn("model", device_info)


class ProductionMalwareScannerTests(ProductionTestBase):
    """Production tests for malware scanning with live device."""
    
    def setUp(self):
        """Initialize scanner for each test."""
        self.scanner = MalwareScanner(self.adb_manager)
    
    def test_scan_installed_apps(self):
        """Test scanning installed applications on device."""
        results = self.scanner.scan_device()
        self.assertIsNotNone(results)


class ProductionSystemAnalysisTests(ProductionTestBase):
    """Production tests for system analysis with live device."""
    
    def setUp(self):
        """Initialize analyzer for each test."""
        self.analyzer = SystemAnalyzer(self.adb_manager)
    
    def test_analyze_system(self):
        """Test system analysis on device."""
        analysis = self.analyzer.analyze_system()
        self.assertIsNotNone(analysis)


def run_tests():
    """Run all production tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
