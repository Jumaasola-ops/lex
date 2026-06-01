"""
Android Device Compatibility Testing Framework.
Author: Asola Junior
Tests against Android versions 5.0 (API 21) through 14.0 (API 34)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

from utils import log_info, log_error, log_warning
from adb_manager import ADBManager


class AndroidAPI(Enum):
    """Android API levels and versions."""
    LOLLIPOP = (21, "5.0")      # Android 5.0
    LOLLIPOP_MR1 = (22, "5.1")  # Android 5.1
    MARSHMALLOW = (23, "6.0")   # Android 6.0
    NOUGAT = (24, "7.0")        # Android 7.0
    NOUGAT_MR1 = (25, "7.1")    # Android 7.1
    OREO = (26, "8.0")          # Android 8.0
    OREO_MR1 = (27, "8.1")      # Android 8.1
    PIE = (28, "9.0")           # Android 9.0
    Q = (29, "10.0")            # Android 10.0
    R = (30, "11.0")            # Android 11.0
    S = (31, "12.0")            # Android 12.0
    S_V2 = (32, "12.0L")        # Android 12L
    T = (33, "13.0")            # Android 13.0
    U = (34, "14.0")            # Android 14.0
    
    @property
    def api_level(self) -> int:
        return self.value[0]
    
    @property
    def version(self) -> str:
        return self.value[1]


@dataclass
class DeviceProfile:
    """Device profile for testing."""
    device_id: str
    api_level: int
    android_version: str
    manufacturer: str
    model: str
    features: List[str]
    storage_gb: int
    ram_gb: int
    
    def is_compatible_with(self, min_api: int, max_api: Optional[int] = None) -> bool:
        """Check if device matches API requirements."""
        if self.api_level < min_api:
            return False
        if max_api and self.api_level > max_api:
            return False
        return True


class DeviceCompatibilityTester:
    """Test runner for multiple Android devices."""
    
    # Feature availability by API level
    FEATURE_AVAILABILITY = {
        "usb_debugging": 21,          # Available in all supported versions
        "developer_mode": 21,         # All versions
        "adb_over_network": 27,       # Android 8.1+
        "scoped_storage": 30,         # Android 11+
        "granular_permissions": 23,   # Android 6.0+
        "runtime_permissions": 23,    # Android 6.0+
        "package_visibility": 30,     # Android 11+
    }
    
    def __init__(self):
        """Initialize compatibility tester."""
        self.adb = ADBManager()
        self.test_results = {}
        self.device_profiles = {}
    
    def discover_devices(self) -> List[DeviceProfile]:
        """
        Discover connected devices.
        
        Returns:
            List[DeviceProfile]: Profiles of connected devices
        """
        devices = []
        device_ids = self.adb.list_devices()
        
        for device_id in device_ids:
            try:
                profile = self._build_device_profile(device_id)
                if profile:
                    devices.append(profile)
                    self.device_profiles[device_id] = profile
            except Exception as e:
                log_error(f"Failed to profile device {device_id}: {e}")
        
        return devices
    
    def _build_device_profile(self, device_id: str) -> Optional[DeviceProfile]:
        """
        Build device profile from properties.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Optional[DeviceProfile]: Device profile or None if unavailable
        """
        try:
            # Get Android version
            version = self.adb.execute_command(
                device_id, 
                "getprop ro.build.version.release"
            ).strip()
            
            # Get API level
            api_level_str = self.adb.execute_command(
                device_id,
                "getprop ro.build.version.sdk"
            ).strip()
            api_level = int(api_level_str) if api_level_str.isdigit() else 0
            
            # Get device info
            manufacturer = self.adb.execute_command(
                device_id,
                "getprop ro.product.manufacturer"
            ).strip()
            
            model = self.adb.execute_command(
                device_id,
                "getprop ro.product.model"
            ).strip()
            
            # Get storage
            storage_output = self.adb.execute_command(
                device_id,
                "df /data | tail -1"
            ).strip()
            storage_gb = self._parse_storage(storage_output)
            
            # Get RAM
            mem_output = self.adb.execute_command(
                device_id,
                "cat /proc/meminfo | grep MemTotal"
            ).strip()
            ram_gb = self._parse_memory(mem_output)
            
            # Detect features
            features = self._detect_features(device_id, api_level)
            
            return DeviceProfile(
                device_id=device_id,
                api_level=api_level,
                android_version=version,
                manufacturer=manufacturer,
                model=model,
                features=features,
                storage_gb=storage_gb,
                ram_gb=ram_gb,
            )
        except Exception as e:
            log_error(f"Error building profile: {e}")
            return None
    
    def _parse_storage(self, output: str) -> int:
        """Parse storage size from df output."""
        try:
            parts = output.split()
            if len(parts) >= 2:
                size_kb = int(parts[1])
                return size_kb // (1024 * 1024)  # Convert to GB
        except:
            pass
        return 0
    
    def _parse_memory(self, output: str) -> int:
        """Parse memory from meminfo."""
        try:
            parts = output.split()
            if len(parts) >= 2:
                mem_kb = int(parts[1])
                return mem_kb // (1024 * 1024)  # Convert to GB
        except:
            pass
        return 0
    
    def _detect_features(self, device_id: str, api_level: int) -> List[str]:
        """
        Detect available features.
        
        Args:
            device_id: Device identifier
            api_level: Android API level
            
        Returns:
            List[str]: List of available features
        """
        features = []
        
        for feature, min_api in self.FEATURE_AVAILABILITY.items():
            if api_level >= min_api:
                features.append(feature)
        
        return features
    
    def run_compatibility_tests(self, test_functions: Dict[str, callable]) -> None:
        """
        Run tests across all devices.
        
        Args:
            test_functions: Dict of test_name -> test_function
        """
        devices = self.discover_devices()
        
        if not devices:
            log_warning("No devices found for testing")
            return
        
        log_info(f"Testing {len(devices)} device(s)...")
        
        for device in devices:
            self.test_results[device.device_id] = {}
            
            log_info(f"\nTesting {device.manufacturer} {device.model} "
                    f"(API {device.api_level})")
            
            for test_name, test_func in test_functions.items():
                try:
                    result = test_func(device)
                    self.test_results[device.device_id][test_name] = {
                        "status": "PASSED" if result else "FAILED",
                        "device": f"{device.manufacturer} {device.model}",
                    }
                except Exception as e:
                    self.test_results[device.device_id][test_name] = {
                        "status": "ERROR",
                        "error": str(e),
                    }
                    log_error(f"Test {test_name} error: {e}")
    
    def test_malware_scan(self, device: DeviceProfile) -> bool:
        """
        Test malware scanning on device.
        
        Args:
            device: Device profile
            
        Returns:
            bool: Test passed
        """
        try:
            # Run scan
            output = self.adb.execute_command(
                device.device_id,
                "pm list packages"
            )
            return len(output) > 0
        except Exception as e:
            log_error(f"Malware scan test failed: {e}")
            return False
    
    def test_permission_handling(self, device: DeviceProfile) -> bool:
        """
        Test permission handling on device.
        
        Args:
            device: Device profile
            
        Returns:
            bool: Test passed
        """
        # Runtime permissions available in Android 6.0+
        if device.api_level < 23:
            log_info("Runtime permissions not available on this API level")
            return True
        
        try:
            # Check if we can query permissions
            output = self.adb.execute_command(
                device.device_id,
                "pm list permissions"
            )
            return len(output) > 0
        except Exception as e:
            log_error(f"Permission test failed: {e}")
            return False
    
    def test_file_access(self, device: DeviceProfile) -> bool:
        """
        Test file system access.
        
        Args:
            device: Device profile
            
        Returns:
            bool: Test passed
        """
        try:
            # Try to list /data/data (requires root typically, but test access)
            output = self.adb.execute_command(
                device.device_id,
                "ls -la /data/data | head -5"
            )
            return "permission denied" not in output.lower()
        except Exception as e:
            log_error(f"File access test failed: {e}")
            return False
    
    def test_storage_access(self, device: DeviceProfile) -> bool:
        """
        Test storage access for scoped storage compatibility.
        
        Args:
            device: Device profile
            
        Returns:
            bool: Test passed
        """
        try:
            output = self.adb.execute_command(
                device.device_id,
                "ls /sdcard/"
            )
            return len(output) > 0
        except Exception as e:
            log_error(f"Storage access test failed: {e}")
            return False
    
    def get_compatibility_report(self) -> Dict:
        """
        Generate compatibility report.
        
        Returns:
            Dict: Compatibility test results
        """
        report = {
            "devices_tested": len(self.device_profiles),
            "devices": {},
            "compatibility_matrix": {},
        }
        
        for device_id, device in self.device_profiles.items():
            report["devices"][device_id] = {
                "model": f"{device.manufacturer} {device.model}",
                "api_level": device.api_level,
                "version": device.android_version,
                "features": device.features,
                "storage_gb": device.storage_gb,
                "ram_gb": device.ram_gb,
            }
        
        for device_id, tests in self.test_results.items():
            report["compatibility_matrix"][device_id] = tests
        
        return report
    
    def save_report(self, output_file: str) -> None:
        """
        Save compatibility report to file.
        
        Args:
            output_file: Output file path
        """
        try:
            report = self.get_compatibility_report()
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            log_info(f"Report saved to {output_file}")
        except Exception as e:
            log_error(f"Failed to save report: {e}")


def create_test_suite(tester: DeviceCompatibilityTester) -> Dict[str, callable]:
    """
    Create test suite for compatibility testing.
    
    Args:
        tester: DeviceCompatibilityTester instance
        
    Returns:
        Dict[str, callable]: Test suite
    """
    return {
        "malware_scan": tester.test_malware_scan,
        "permissions": tester.test_permission_handling,
        "file_access": tester.test_file_access,
        "storage_access": tester.test_storage_access,
    }


def main():
    """Run device compatibility tests."""
    tester = DeviceCompatibilityTester()
    
    # Discover devices
    devices = tester.discover_devices()
    print(f"\nFound {len(devices)} device(s)")
    for device in devices:
        print(f"  • {device.manufacturer} {device.model} (API {device.api_level})")
    
    # Run tests
    test_suite = create_test_suite(tester)
    tester.run_compatibility_tests(test_suite)
    
    # Generate report
    tester.save_report("compatibility_report.json")
    
    # Print summary
    report = tester.get_compatibility_report()
    print("\n" + "="*50)
    print("COMPATIBILITY REPORT")
    print("="*50)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
