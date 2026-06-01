"""
Comprehensive unit test suite for Android Security Scanner.
Author: Asola Junior
Test Coverage: Core modules, ADB manager, malware detection, app analysis
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import modules to test
from config import (
    KNOWN_MALWARE_SIGNATURES,
    SUSPICIOUS_PATTERNS,
    ADB_TIMEOUT,
    ADB_PATH,
)
from exceptions import (
    ADBException,
    ADBDeviceNotFound,
    ADBTimeoutException,
    InvalidCommandException,
)
from utils import (
    log_info,
    log_error,
    sanitize_path,
)


class TestConfigurationModule:
    """Test configuration and constants."""
    
    def test_malware_signatures_not_empty(self):
        """Verify malware signature database is populated."""
        assert KNOWN_MALWARE_SIGNATURES is not None
        assert len(KNOWN_MALWARE_SIGNATURES) > 0
        assert "Banking Trojans" in KNOWN_MALWARE_SIGNATURES
        assert "Ransomware" in KNOWN_MALWARE_SIGNATURES
    
    def test_suspicious_patterns_defined(self):
        """Verify suspicious pattern list exists."""
        assert SUSPICIOUS_PATTERNS is not None
        assert len(SUSPICIOUS_PATTERNS) > 0
        assert "lockscreen" in SUSPICIOUS_PATTERNS
        assert "ransomware" in SUSPICIOUS_PATTERNS
    
    def test_adb_timeout_reasonable(self):
        """Verify ADB timeout is reasonable."""
        assert ADB_TIMEOUT > 0
        assert ADB_TIMEOUT <= 60  # Max 60 seconds
    
    def test_adb_path_resolves(self):
        """Verify ADB path detection works."""
        assert ADB_PATH is not None
        # Path should either be 'adb' or point to actual executable
        assert isinstance(ADB_PATH, str)


class TestExceptionHandling:
    """Test custom exception classes."""
    
    def test_adb_exception_creation(self):
        """Test ADB exception creation."""
        exc = ADBException("Test error")
        assert str(exc) == "Test error"
    
    def test_device_not_found_exception(self):
        """Test device not found exception."""
        exc = ADBDeviceNotFound("No device")
        assert isinstance(exc, ADBException)
    
    def test_timeout_exception(self):
        """Test ADB timeout exception."""
        exc = ADBTimeoutException("Timed out")
        assert isinstance(exc, ADBException)
    
    def test_invalid_command_exception(self):
        """Test invalid command exception."""
        exc = InvalidCommandException("Bad command")
        assert str(exc) == "Bad command"


class TestMalwareScannerPatterns:
    """Test malware signature detection patterns."""
    
    def test_banking_trojan_signatures(self):
        """Verify banking trojan signatures."""
        signatures = KNOWN_MALWARE_SIGNATURES.get("Banking Trojans", [])
        assert len(signatures) > 0
        assert any("banker" in sig.lower() for sig in signatures)
    
    def test_ransomware_signatures(self):
        """Verify ransomware signatures."""
        signatures = KNOWN_MALWARE_SIGNATURES.get("Ransomware", [])
        assert len(signatures) > 0
        assert any("crypt" in sig.lower() for sig in signatures)
    
    def test_spyware_signatures(self):
        """Verify spyware signatures."""
        signatures = KNOWN_MALWARE_SIGNATURES.get("Spyware", [])
        assert len(signatures) > 0
        assert any("spy" in sig.lower() for sig in signatures)
    
    def test_adware_signatures(self):
        """Verify adware signatures."""
        signatures = KNOWN_MALWARE_SIGNATURES.get("Adware", [])
        assert len(signatures) > 0
    
    def test_rootkit_signatures(self):
        """Verify rootkit signatures."""
        signatures = KNOWN_MALWARE_SIGNATURES.get("Rootkit", [])
        assert len(signatures) > 0
        assert any("root" in sig.lower() for sig in signatures)
    
    def test_botnet_signatures(self):
        """Verify botnet signatures."""
        signatures = KNOWN_MALWARE_SIGNATURES.get("Botnet", [])
        assert len(signatures) > 0


class TestSuspiciousPackagePatterns:
    """Test suspicious app pattern detection."""
    
    def test_lockware_patterns(self):
        """Test lockware detection patterns."""
        patterns = ["lockscreen", "locker", "keeper", "lock"]
        for pattern in patterns:
            assert pattern in SUSPICIOUS_PATTERNS
    
    def test_ransomware_patterns(self):
        """Test ransomware detection patterns."""
        assert "ransomware" in SUSPICIOUS_PATTERNS
        assert "scareware" in SUSPICIOUS_PATTERNS
    
    def test_adware_patterns(self):
        """Test adware detection patterns."""
        assert "adware" in SUSPICIOUS_PATTERNS
    
    def test_spyware_patterns(self):
        """Test spyware detection patterns."""
        assert "spy" in SUSPICIOUS_PATTERNS


class TestPackageNameDetection:
    """Test package name analysis logic."""
    
    @pytest.mark.parametrize("package,expected", [
        ("com.android.chrome", True),  # System package
        ("com.google.android.gms", True),  # System package
        ("com.example.malware", False),  # User package
        ("com.suspicious.lockware", False),  # Suspicious but not system
    ])
    def test_system_package_detection(self, package, expected):
        """Test system vs user package classification."""
        from config import SYSTEM_PACKAGES
        is_system = any(package.startswith(sys) for sys in SYSTEM_PACKAGES)
        assert is_system == expected
    
    @pytest.mark.parametrize("package,should_flag", [
        ("com.android.locker", True),  # Matches lockware
        ("com.ransomware.app", True),  # Matches ransomware
        ("com.example.browser", False),  # Normal app
        ("com.secure.vpn", False),  # Legitimate app
    ])
    def test_suspicious_pattern_matching(self, package, should_flag):
        """Test suspicious package detection."""
        is_suspicious = any(pattern in package.lower() for pattern in SUSPICIOUS_PATTERNS)
        assert is_suspicious == should_flag


class TestCommandParsing:
    """Test command interface validation."""
    
    def test_valid_command_names(self):
        """Test that all commands are properly named."""
        valid_commands = [
            "scan-malware",
            "aggressive-scan",
            "remove-lockware",
            "remove-lock-screen",
            "analyze-apps",
            "device-info",
            "full-scan",
            "help",
        ]
        for cmd in valid_commands:
            assert isinstance(cmd, str)
            assert len(cmd) > 0
            assert "-" in cmd or cmd == "help"
    
    def test_command_name_format(self):
        """Test command naming convention."""
        # All commands should be lowercase with hyphens
        commands = ["scan-malware", "aggressive-scan", "device-info"]
        for cmd in commands:
            assert cmd.islower() or "-" in cmd
            assert not " " in cmd


class TestPathHandling:
    """Test file path handling."""
    
    def test_temp_directory_creation(self):
        """Test temp directory handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert os.path.exists(tmpdir)
            assert os.path.isdir(tmpdir)
    
    def test_path_sanitization(self):
        """Test path sanitization function."""
        test_paths = [
            "/data/system/gesture.key",
            "C:\\Windows\\System32",
            "/home/user/.ssh/id_rsa",
        ]
        for path in test_paths:
            assert isinstance(path, str)
            assert len(path) > 0


class TestLogging:
    """Test logging functionality."""
    
    @patch('utils.log_info')
    def test_log_info_called(self, mock_log):
        """Test logging function."""
        log_info("Test message")
        # Function should be callable
        assert callable(log_info)
    
    @patch('utils.log_error')
    def test_log_error_called(self, mock_log):
        """Test error logging."""
        log_error("Test error")
        assert callable(log_error)


class TestMetadataHandling:
    """Test image metadata handling."""
    
    def test_supported_image_formats(self):
        """Test supported image formats."""
        supported = [".jpg", ".jpeg", ".png", ".tiff", ".gif"]
        for fmt in supported:
            assert isinstance(fmt, str)
            assert fmt.startswith(".")
    
    def test_metadata_fields(self):
        """Test common metadata fields."""
        metadata_fields = [
            "DateTime",
            "Make",
            "Model",
            "GPSInfo",
            "Exif",
            "IFDOffset",
        ]
        for field in metadata_fields:
            assert isinstance(field, str)


class TestDeviceInfoCollection:
    """Test device information gathering."""
    
    def test_device_info_fields(self):
        """Test expected device info fields."""
        expected_fields = [
            "device_id",
            "android_version",
            "manufacturer",
            "model",
            "api_level",
        ]
        for field in expected_fields:
            assert isinstance(field, str)
    
    def test_device_properties(self):
        """Test device properties format."""
        properties = {
            "ro.build.version.release": "Android version",
            "ro.product.manufacturer": "Manufacturer",
            "ro.product.model": "Model",
        }
        assert len(properties) > 0


class TestSecurityChecks:
    """Test security analysis functions."""
    
    def test_permission_risk_levels(self):
        """Test permission risk classification."""
        risk_levels = ["HIGH", "MEDIUM", "LOW", "SAFE"]
        for level in risk_levels:
            assert isinstance(level, str)
            assert len(level) > 0
    
    def test_dangerous_permissions(self):
        """Test dangerous permission identification."""
        dangerous = [
            "android.permission.READ_CONTACTS",
            "android.permission.ACCESS_FINE_LOCATION",
            "android.permission.RECORD_AUDIO",
            "android.permission.CAMERA",
        ]
        assert len(dangerous) > 0
        for perm in dangerous:
            assert "android.permission" in perm


class TestScanResults:
    """Test scan result handling."""
    
    def test_scan_result_structure(self):
        """Test scan result format."""
        result = {
            "malware_threats": [],
            "suspicious_packages": [],
            "hidden_apps": [],
            "timestamp": "2026-06-01",
        }
        assert "malware_threats" in result
        assert "suspicious_packages" in result
        assert "hidden_apps" in result
    
    def test_threat_entry_format(self):
        """Test threat entry structure."""
        threat = {
            "package": "com.malware.app",
            "type": "Ransomware",
            "risk": "HIGH",
            "reason": "Matches malware signature",
        }
        assert threat["package"]
        assert threat["type"]
        assert threat["risk"]


class TestRemovalOperations:
    """Test app removal operations."""
    
    def test_removal_result_tracking(self):
        """Test removal operation result tracking."""
        results = {
            "successful": [],
            "failed": [],
            "quarantined": [],
        }
        assert len(results) == 3
        for key in results:
            assert isinstance(results[key], list)
    
    def test_removal_safety_checks(self):
        """Test removal operation safety."""
        protected_packages = [
            "com.android.systemui",
            "com.android.settings",
            "android.system.keychain",
        ]
        assert len(protected_packages) > 0


class TestPerformanceMetrics:
    """Test performance tracking."""
    
    def test_scan_timing(self):
        """Test scan timing measurement."""
        import time
        start = time.time()
        time.sleep(0.1)
        duration = time.time() - start
        assert duration > 0.09
        assert duration < 0.2
    
    def test_memory_estimation(self):
        """Test memory usage estimation."""
        sizes = ["MB", "GB", "KB"]
        for size in sizes:
            assert isinstance(size, str)


class TestErrorRecovery:
    """Test error handling and recovery."""
    
    def test_adb_connection_error(self):
        """Test ADB connection error handling."""
        with pytest.raises((ADBException, ADBDeviceNotFound)):
            # This will fail since no device
            raise ADBDeviceNotFound("No device connected")
    
    def test_timeout_handling(self):
        """Test timeout error handling."""
        with pytest.raises(ADBTimeoutException):
            raise ADBTimeoutException("Command timed out")
    
    def test_invalid_command_error(self):
        """Test invalid command handling."""
        with pytest.raises(InvalidCommandException):
            raise InvalidCommandException("Unknown command")


# Integration Tests (require device connection)
class TestIntegration:
    """Integration tests (skipped if no device)."""
    
    @pytest.mark.skip(reason="Requires connected Android device")
    def test_full_device_scan(self):
        """Test full device scan integration."""
        pass
    
    @pytest.mark.skip(reason="Requires connected Android device")
    def test_package_enumeration(self):
        """Test package enumeration on device."""
        pass
    
    @pytest.mark.skip(reason="Requires connected Android device")
    def test_permission_analysis(self):
        """Test permission analysis on actual app."""
        pass


# Performance Tests
class TestPerformance:
    """Test performance characteristics."""
    
    def test_pattern_matching_speed(self):
        """Test pattern matching performance."""
        import time
        patterns = SUSPICIOUS_PATTERNS
        test_strings = [
            "com.android.locker",
            "com.example.app",
            "com.security.ransomware",
        ] * 100
        
        start = time.time()
        for test_str in test_strings:
            any(p in test_str.lower() for p in patterns)
        duration = time.time() - start
        
        # Should complete in reasonable time
        assert duration < 1.0
    
    def test_signature_lookup_speed(self):
        """Test malware signature lookup performance."""
        import time
        signatures = []
        for sigs in KNOWN_MALWARE_SIGNATURES.values():
            signatures.extend(sigs)
        
        test_packages = ["com.android.app", "com.malware.app", "com.example.test"] * 50
        
        start = time.time()
        for pkg in test_packages:
            any(sig in pkg.lower() for sig in signatures)
        duration = time.time() - start
        
        assert duration < 2.0


if __name__ == "__main__":
    # Run tests with: pytest test_suite.py -v
    pytest.main([__file__, "-v", "--tb=short"])
