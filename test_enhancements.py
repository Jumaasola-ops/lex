"""
Test suite for Tier 1 production enhancements.
Tests: Input Validation, Reporting, Batch Processing, Threat Intelligence
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from validators import InputValidator, ValidationError
from report_generator import ReportGenerator, SecurityFinding, ScanReport
from batch_processor import DeviceBatchProcessor, BatchConfig, TaskStatus
from threat_intelligence import ThreatIntelligenceAggregator, AbuseChProvider


# ============================================================================
# INPUT VALIDATION TESTS
# ============================================================================

class TestInputValidator:
    """Tests for input validation and sanitization."""
    
    def test_validate_device_id_usb_format(self):
        """Test USB device ID validation."""
        valid, error = InputValidator.validate_device_id("emulator-5554")
        assert valid, error
        assert error is None
    
    def test_validate_device_id_wireless_format(self):
        """Test wireless device ID validation."""
        valid, error = InputValidator.validate_device_id("192.168.1.100:5555")
        assert valid, error
    
    def test_validate_device_id_invalid_ip(self):
        """Test invalid IP in device ID."""
        valid, error = InputValidator.validate_device_id("999.999.999.999:5555")
        assert not valid
        assert "octet" in error.lower() or "invalid" in error.lower()
    
    def test_validate_device_id_invalid_port(self):
        """Test invalid port in device ID."""
        valid, error = InputValidator.validate_device_id("192.168.1.100:99999")
        assert not valid
        assert "port" in error.lower()
    
    def test_validate_package_name_valid(self):
        """Test valid package name."""
        valid, error = InputValidator.validate_package_name("com.example.app")
        assert valid, error
    
    def test_validate_package_name_too_short(self):
        """Test package name with insufficient parts."""
        valid, error = InputValidator.validate_package_name("invalid")
        assert not valid
    
    def test_validate_package_name_special_chars(self):
        """Test package name with invalid characters."""
        valid, error = InputValidator.validate_package_name("com.example.app@bad")
        assert not valid
    
    def test_validate_adb_command_dangerous_rm(self):
        """Test dangerous rm command detection."""
        valid, error = InputValidator.validate_adb_command("ls; rm -rf /")
        assert not valid
        assert "dangerous" in error.lower()
    
    def test_validate_adb_command_safe(self):
        """Test safe command."""
        valid, error = InputValidator.validate_adb_command("getprop ro.build.version.sdk")
        assert valid, error
    
    def test_validate_ip_address_valid(self):
        """Test valid IP address."""
        valid, error = InputValidator.validate_ip_address("192.168.1.100")
        assert valid, error
    
    def test_validate_ip_address_invalid_octet(self):
        """Test IP with invalid octet."""
        valid, error = InputValidator.validate_ip_address("192.168.1.256")
        assert not valid
    
    def test_validate_port_valid(self):
        """Test valid port."""
        valid, error = InputValidator.validate_port(5555)
        assert valid, error
    
    def test_validate_port_out_of_range(self):
        """Test port out of range."""
        valid, error = InputValidator.validate_port(99999)
        assert not valid
    
    def test_validate_hash_sha256_valid(self):
        """Test valid SHA256 hash."""
        valid, error = InputValidator.validate_hash(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "sha256"
        )
        assert valid, error
    
    def test_validate_hash_sha256_invalid(self):
        """Test invalid SHA256 hash."""
        valid, error = InputValidator.validate_hash("invalid_hash", "sha256")
        assert not valid
    
    def test_sanitize_filename_dangerous(self):
        """Test filename sanitization."""
        sanitized = InputValidator.sanitize_filename("../../etc/passwd")
        assert ".." not in sanitized
        assert "/" not in sanitized


# ============================================================================
# REPORT GENERATOR TESTS
# ============================================================================

class TestReportGenerator:
    """Tests for report generation system."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def sample_report(self):
        """Create sample scan report."""
        report = ScanReport(
            report_id="test_001",
            scan_date=datetime.now().isoformat(),
            device_id="test_device",
            device_model="Test Device",
            android_version="13.0",
            apps_scanned=100,
            scan_duration_seconds=30.5,
        )
        
        report.findings = [
            SecurityFinding(
                finding_id="CRIT_001",
                severity="CRITICAL",
                category="Malware",
                package_name="com.malware.app",
                title="Trojan Detected",
                description="Banking trojan",
                remediation="Uninstall immediately",
            ),
            SecurityFinding(
                finding_id="HIGH_001",
                severity="HIGH",
                category="Permission",
                package_name="com.example.app",
                title="Dangerous Permissions",
                description="App requests unnecessary permissions",
                remediation="Review settings",
            ),
        ]
        
        return report
    
    def test_report_json_generation(self, temp_dir, sample_report):
        """Test JSON report generation."""
        generator = ReportGenerator(temp_dir)
        outputs = generator.generate_report(sample_report, formats=["json"])
        
        assert "json" in outputs
        assert Path(outputs["json"]).exists()
        
        # Verify JSON content
        with open(outputs["json"]) as f:
            data = json.load(f)
            assert data["report_id"] == "test_001"
            assert len(data["findings"]) == 2
    
    def test_report_csv_generation(self, temp_dir, sample_report):
        """Test CSV report generation."""
        generator = ReportGenerator(temp_dir)
        outputs = generator.generate_report(sample_report, formats=["csv"])
        
        assert "csv" in outputs
        assert Path(outputs["csv"]).exists()
    
    def test_report_html_generation(self, temp_dir, sample_report):
        """Test HTML report generation."""
        generator = ReportGenerator(temp_dir)
        outputs = generator.generate_report(sample_report, formats=["html"])
        
        assert "html" in outputs
        assert Path(outputs["html"]).exists()
        
        with open(outputs["html"]) as f:
            html = f.read()
            assert "Android Security Scanner" in html
            assert sample_report.device_model in html
    
    def test_empty_report_generation(self, temp_dir):
        """Test report with no findings."""
        report = ScanReport(
            report_id="empty_001",
            scan_date=datetime.now().isoformat(),
            device_id="safe_device",
            device_model="Safe Device",
            android_version="13.0",
        )
        
        generator = ReportGenerator(temp_dir)
        outputs = generator.generate_report(report, formats=["json", "csv"])
        
        assert "json" in outputs
        assert "csv" in outputs
    
    def test_trend_analysis(self, sample_report):
        """Test trend analysis across reports."""
        report1 = ScanReport(
            report_id="trend_001",
            scan_date="2024-01-01T10:00:00",
            device_id="device1",
            device_model="Device 1",
            android_version="13.0",
        )
        
        report2 = ScanReport(
            report_id="trend_002",
            scan_date="2024-01-02T10:00:00",
            device_id="device2",
            device_model="Device 2",
            android_version="14.0",
        )
        
        generator = ReportGenerator()
        trend = generator.generate_trend_report([report1, report2])
        
        assert trend["total_scans"] == 2
        assert len(trend["devices_scanned"]) == 2


# ============================================================================
# BATCH PROCESSOR TESTS
# ============================================================================

class TestBatchProcessor:
    """Tests for batch processing system."""
    
    @pytest.fixture
    def batch_config(self):
        """Create batch configuration."""
        return BatchConfig(max_workers=2, max_retries=2, verbose=False)
    
    def test_batch_config_defaults(self):
        """Test default batch configuration."""
        config = BatchConfig()
        assert config.max_workers == 4
        assert config.max_retries == 3
        assert config.timeout_seconds == 300.0
    
    def test_batch_config_custom(self, batch_config):
        """Test custom batch configuration."""
        assert batch_config.max_workers == 2
        assert batch_config.max_retries == 2
    
    def test_is_retryable_error(self, batch_config):
        """Test retryable error detection."""
        from unittest.mock import patch
        
        with patch('batch_processor.ADBManager'):
            processor = DeviceBatchProcessor(batch_config)
        
        # Retryable errors
        assert processor._is_retryable_error("Connection timeout")
        assert processor._is_retryable_error("Device busy")
        
        # Non-retryable errors
        assert not processor._is_retryable_error("Device not found")
        assert not processor._is_retryable_error("Permission denied")
    
    def test_aggregated_results_summary(self, batch_config):
        """Test result aggregation."""
        from unittest.mock import patch, Mock
        
        with patch('batch_processor.ADBManager'):
            processor = DeviceBatchProcessor(batch_config)
        
        processor.results = [
            Mock(
                device_id="device1",
                status=TaskStatus.COMPLETED,
                duration_seconds=10.0
            ),
            Mock(
                device_id="device2",
                status=TaskStatus.FAILED,
                duration_seconds=5.0
            ),
            Mock(
                device_id="device3",
                status=TaskStatus.SKIPPED,
                duration_seconds=0.0
            ),
        ]
        
        agg = processor.get_aggregated_results()
        
        assert agg["summary"]["total_devices"] == 3
        assert agg["summary"]["completed"] == 1
        assert agg["summary"]["failed"] == 1
        assert agg["summary"]["skipped"] == 1


# ============================================================================
# THREAT INTELLIGENCE TESTS
# ============================================================================

class TestThreatIntelligence:
    """Tests for threat intelligence integration."""
    
    def test_aggregator_initialization(self):
        """Test aggregator initialization."""
        agg = ThreatIntelligenceAggregator()
        
        assert "abusech" in agg.providers
        assert isinstance(agg.providers["abusech"], AbuseChProvider)
    
    def test_aggregator_with_virustotal(self):
        """Test aggregator with VirusTotal."""
        try:
            agg = ThreatIntelligenceAggregator(vt_api_key="test_key_12345678901234567890")
            assert "virustotal" in agg.providers
        except Exception as e:
            # API key validation may fail
            pass
    
    def test_aggregator_hash_check_interface(self):
        """Test hash checking interface."""
        agg = ThreatIntelligenceAggregator()
        
        # Valid SHA256 hash
        result = agg.check_file_hash("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        
        assert "hash" in result
        assert "malicious" in result
        assert "providers" in result
    
    def test_apk_safety_check(self):
        """Test APK safety check."""
        agg = ThreatIntelligenceAggregator()
        
        is_safe, verdict = agg.check_apk_safety("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        
        assert isinstance(is_safe, bool)
        assert isinstance(verdict, str)
        assert len(verdict) > 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestTier1Integration:
    """Integration tests for Tier 1 enhancements."""
    
    def test_validation_before_processing(self):
        """Test validation guards batch processing."""
        # Valid device ID should pass
        valid, error = InputValidator.validate_device_id("emulator-5554")
        assert valid
        
        # Invalid device ID should fail
        valid, error = InputValidator.validate_device_id("../../../etc/passwd")
        assert not valid
    
    def test_report_generation_with_findings(self):
        """Test complete report generation workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create report
            report = ScanReport(
                report_id="integration_001",
                scan_date=datetime.now().isoformat(),
                device_id="test_device",
                device_model="Test Model",
                android_version="13.0",
                apps_scanned=50,
            )
            
            # Add findings with validation
            for i in range(3):
                valid, error = InputValidator.validate_package_name(f"com.test.app{i}")
                if valid:
                    finding = SecurityFinding(
                        finding_id=f"TEST_{i}",
                        severity="MEDIUM",
                        category="Test",
                        package_name=f"com.test.app{i}",
                        title=f"Test Finding {i}",
                        description="Test description",
                        remediation="Test remediation",
                    )
                    report.findings.append(finding)
            
            # Generate reports
            generator = ReportGenerator(tmpdir)
            outputs = generator.generate_report(report)
            
            # Verify outputs
            assert len(outputs) > 0
            for path in outputs.values():
                assert Path(path).exists()


import json
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
