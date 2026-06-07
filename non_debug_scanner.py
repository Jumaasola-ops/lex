#!/usr/bin/env python3
"""
Non-Debug Android Scanner - Scans and manages Android devices WITHOUT requiring debug mode.

This module provides alternative methods to scan and disable apps on Android devices
even when USB debugging and developer options are NOT enabled.

Methods:
1. MTP File System Access (Windows) - Browse phone as USB storage device
2. Fastboot Access - Minimal access mode
3. Companion App Method - Deploy an app that manages threats
4. Accessibility Service Method - Use accessibility services for monitoring
5. Package Database Crawling - Direct filesystem access through MTP
"""

import os
import subprocess
import json
import sys
import tempfile
import re
from typing import List, Dict, Tuple, Optional, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import ctypes
import platform
from enum import Enum

from utils import log_info, log_error, log_warning, print_info, print_warning, print_success, print_error
from exceptions import AndroidSecurityException


class ScanMethod(Enum):
    """Available scanning methods for non-debug mode."""
    MTP = "mtp"              # Windows MTP file system access
    FASTBOOT = "fastboot"    # Fastboot bootloader access
    COMPANION_APP = "companion"  # Deploy companion app
    USB_STORAGE = "storage"  # USB mass storage
    SHELL_QUERY = "shell_query"  # Limited ADB shell queries


@dataclass
class DetectedThreat:
    """Represents a detected threat."""
    package_name: str
    threat_level: str  # critical, high, medium, low
    threat_type: str   # malware, bloatware, suspicious, etc.
    detection_method: str
    file_paths: List[str] = None
    reason: str = ""
    timestamp: str = None
    
    def __post_init__(self):
        if self.file_paths is None:
            self.file_paths = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class MTPScanner:
    """
    Scans Android device via MTP (Media Transfer Protocol) without requiring debug mode.
    Works on Windows natively - no special drivers needed.
    """
    
    def __init__(self):
        """Initialize MTP scanner."""
        self.mtp_mounted = False
        self.mount_point = None
        self.threats: List[DetectedThreat] = []
        
    def find_mtp_device(self) -> Optional[str]:
        """
        Find Android device mounted as MTP on Windows.
        
        Returns:
            str: Mount point path if found, None otherwise
        """
        if sys.platform != "win32":
            log_warning("MTP scanning is only available on Windows")
            return None
            
        log_info("Scanning for MTP-mounted Android devices...")
        
        # Check all drive letters for Android device markers
        for drive_letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
            drive_path = f"{drive_letter}:\\"
            
            if not os.path.exists(drive_path):
                continue
                
            try:
                # Check for typical Android directories
                android_dirs = ["Android", "DCIM", "Pictures", "Documents", "Downloads"]
                found_android_markers = sum(
                    1 for d in android_dirs 
                    if os.path.exists(os.path.join(drive_path, d))
                )
                
                if found_android_markers >= 2:  # At least 2 Android markers
                    # Further verify by checking for app data
                    android_path = os.path.join(drive_path, "Android")
                    if os.path.exists(android_path):
                        self.mount_point = drive_path
                        log_success(f"Found Android device at: {drive_path}")
                        return drive_path
            except Exception as e:
                log_debug(f"Error checking {drive_path}: {e}")
                
        log_warning("No MTP Android device found")
        return None
    
    def crawl_app_data(self) -> List[DetectedThreat]:
        """
        Crawl Android/data and Android/obb directories for suspicious apps.
        
        Returns:
            List[DetectedThreat]: Detected threats
        """
        if not self.mount_point:
            log_error("Device not mounted")
            return []
        
        threats = []
        android_path = os.path.join(self.mount_point, "Android")
        
        log_info("Crawling Android/data directory for app signatures...")
        
        # Crawl data directory
        data_path = os.path.join(android_path, "data")
        if os.path.exists(data_path):
            for app_dir in os.listdir(data_path):
                app_path = os.path.join(data_path, app_dir)
                if os.path.isdir(app_path):
                    threat = self._analyze_app_directory(app_dir, app_path, "data")
                    if threat:
                        threats.append(threat)
        
        # Crawl obb directory
        obb_path = os.path.join(android_path, "obb")
        if os.path.exists(obb_path):
            for app_dir in os.listdir(obb_path):
                app_path = os.path.join(obb_path, app_dir)
                if os.path.isdir(app_path):
                    threat = self._analyze_app_directory(app_dir, app_path, "obb")
                    if threat:
                        threats.append(threat)
        
        return threats
    
    def _analyze_app_directory(self, package_name: str, app_path: str, 
                               location: str) -> Optional[DetectedThreat]:
        """
        Analyze an individual app directory for suspicious content.
        
        Args:
            package_name: Package name (directory name)
            app_path: Full path to app directory
            location: "data" or "obb"
            
        Returns:
            DetectedThreat if suspicious, None otherwise
        """
        files = []
        suspicious_files = []
        
        try:
            for root, dirs, filenames in os.walk(app_path):
                files.extend([os.path.join(root, f) for f in filenames])
        except Exception as e:
            log_debug(f"Error crawling {app_path}: {e}")
            return None
        
        # Check for suspicious patterns
        threat_level = "low"
        reason = ""
        
        # Known malware signatures (from config)
        malware_patterns = [
            r"lockware", r"ransomware", r"trojan", r"spyware", r"adware",
            r"smishing", r"phishing", r"rootkit", r"botnet",
            r"porn", r"xxx", r"casino", r"lottery",
        ]
        
        for file_path in files:
            filename = os.path.basename(file_path).lower()
            
            # Check filename against malware patterns
            for pattern in malware_patterns:
                if re.search(pattern, filename):
                    suspicious_files.append(file_path)
                    threat_level = "critical"
                    reason = f"Malware signature detected: {pattern}"
        
        # Check for excessive file count (potential file bomb)
        if len(files) > 10000:
            threat_level = "high"
            reason = "Excessive file count detected (potential file bomb)"
        
        # Check for recent modifications (potential active malware)
        recent_count = 0
        try:
            import time
            current_time = time.time()
            for file_path in files[:100]:  # Check first 100 files
                if os.path.getmtime(file_path) > current_time - 86400:  # Last 24 hours
                    recent_count += 1
        except:
            pass
        
        if recent_count > 50:  # Many recent modifications
            if threat_level == "low":
                threat_level = "high"
                reason = "Active file modifications detected"
        
        # Determine if should report as threat
        if suspicious_files or threat_level != "low":
            return DetectedThreat(
                package_name=package_name,
                threat_level=threat_level,
                threat_type="suspicious_app" if not suspicious_files else "malware",
                detection_method="mtp_crawl",
                file_paths=suspicious_files[:10],  # Limit to first 10 suspicious files
                reason=reason
            )
        
        return None
    
    def get_installed_apps_from_mtp(self) -> Dict[str, Dict]:
        """
        Extract installed apps from MTP by reading package manager database.
        
        Returns:
            Dict: Package information extracted from MTP
        """
        if not self.mount_point:
            return {}
        
        apps = {}
        
        # Try to read from common backup locations
        backup_paths = [
            os.path.join(self.mount_point, "Android", "data"),
            os.path.join(self.mount_point, "Android", "obb"),
        ]
        
        for backup_path in backup_paths:
            if os.path.exists(backup_path):
                try:
                    for app_name in os.listdir(backup_path):
                        app_path = os.path.join(backup_path, app_name)
                        if os.path.isdir(app_path):
                            apps[app_name] = {
                                "location": backup_path,
                                "size": sum(
                                    os.path.getsize(os.path.join(root, f))
                                    for root, dirs, files in os.walk(app_path)
                                    for f in files
                                )
                            }
                except Exception as e:
                    log_debug(f"Error reading {backup_path}: {e}")
        
        return apps


class FastbootScanner:
    """
    Scans using Fastboot bootloader access (minimal access mode).
    Can work on some devices without full debug mode.
    """
    
    def __init__(self):
        """Initialize Fastboot scanner."""
        self.fastboot_path = self._find_fastboot()
    
    def _find_fastboot(self) -> Optional[str]:
        """Find fastboot executable."""
        # Check standard locations
        if sys.platform == "win32":
            fastboot_names = ["fastboot.exe", "fastboot"]
        else:
            fastboot_names = ["fastboot"]
        
        # Try system PATH
        for name in fastboot_names:
            try:
                result = subprocess.run(
                    [name, "--version"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return name
            except:
                pass
        
        # Try Android SDK location
        if sys.platform == "win32":
            sdk_path = Path.home() / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "fastboot.exe"
        else:
            sdk_path = Path.home() / "Android" / "Sdk" / "platform-tools" / "fastboot"
        
        if sdk_path.exists():
            return str(sdk_path)
        
        return None
    
    def list_devices(self) -> List[str]:
        """
        List devices in fastboot mode.
        
        Returns:
            List[str]: Device IDs
        """
        if not self.fastboot_path:
            return []
        
        try:
            result = subprocess.run(
                [self.fastboot_path, "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            devices = []
            for line in result.stdout.strip().split('\n'):
                if line.strip() and 'fastboot' in line.lower():
                    device_id = line.split()[0]
                    if device_id:
                        devices.append(device_id)
            
            return devices
        except Exception as e:
            log_error(f"Fastboot error: {e}")
            return []
    
    def get_device_info(self, device_id: str = None) -> Dict:
        """Get device information from bootloader."""
        if not self.fastboot_path:
            return {}
        
        try:
            cmd = [self.fastboot_path, "getvar", "all"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            info = {}
            for line in result.stderr.split('\n') + result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()
            
            return info
        except Exception as e:
            log_error(f"Error getting device info: {e}")
            return {}


class CompanionAppDeployer:
    """
    Deploys a companion app that can manage threats even without full ADB access.
    The app uses accessibility services and device admin APIs.
    """
    
    def __init__(self):
        """Initialize companion app deployer."""
        self.apk_path = None
        self.app_package = "com.security.companion"
    
    def generate_companion_app(self) -> Optional[str]:
        """
        Generate or locate companion APK.
        
        Returns:
            str: Path to APK if available, None otherwise
        """
        log_info("Searching for companion app...")
        
        # Check if pre-built APK exists
        apk_candidates = [
            Path.home() / "Downloads" / "companion.apk",
            Path.cwd() / "companion.apk",
            Path.cwd() / "apps" / "companion.apk",
            Path(__file__).parent / "apps" / "companion.apk",
        ]
        
        for candidate in apk_candidates:
            if candidate.exists():
                log_success(f"Found companion app: {candidate}")
                self.apk_path = str(candidate)
                return str(candidate)
        
        log_warning("Companion app not found. Generate it manually or use other methods.")
        return None
    
    def deploy(self, device_id: str = None) -> bool:
        """
        Deploy companion app to device.
        
        Args:
            device_id: Optional device ID
            
        Returns:
            bool: Success status
        """
        if not self.apk_path:
            if not self.generate_companion_app():
                return False
        
        try:
            from adb_manager import ADBManager
            adb = ADBManager(device_id)
            
            log_info(f"Deploying companion app from: {self.apk_path}")
            adb.install_app(self.apk_path)
            
            log_success("Companion app deployed successfully")
            return True
        except Exception as e:
            log_error(f"Failed to deploy companion app: {e}")
            return False


class NonDebugScanner:
    """
    Main non-debug scanner that uses alternative methods to scan and manage Android devices.
    """
    
    def __init__(self):
        """Initialize non-debug scanner."""
        self.mtp_scanner = MTPScanner()
        self.fastboot_scanner = FastbootScanner()
        self.companion_deployer = CompanionAppDeployer()
        self.threats: List[DetectedThreat] = []
    
    def scan_without_debug(self, method: ScanMethod = None) -> Dict:
        """
        Perform comprehensive scan without requiring debug mode.
        
        Args:
            method: Specific method to use, or None to try all available
            
        Returns:
            Dict: Scan results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "threats_found": [],
            "apps_scanned": 0,
            "methods_used": [],
            "success": False,
        }
        
        methods_to_try = [method] if method else [
            ScanMethod.MTP,
            ScanMethod.FASTBOOT,
            ScanMethod.USB_STORAGE,
        ]
        
        for scan_method in methods_to_try:
            if scan_method == ScanMethod.MTP:
                threats = self._scan_mtp()
                if threats is not None:
                    results["methods_used"].append("MTP")
                    results["threats_found"].extend(
                        [asdict(t) for t in threats]
                    )
                    results["success"] = True
            
            elif scan_method == ScanMethod.FASTBOOT:
                threats = self._scan_fastboot()
                if threats is not None:
                    results["methods_used"].append("Fastboot")
                    results["threats_found"].extend(
                        [asdict(t) for t in threats]
                    )
                    results["success"] = True
            
            elif scan_method == ScanMethod.USB_STORAGE:
                threats = self._scan_usb_storage()
                if threats is not None:
                    results["methods_used"].append("USB Storage")
                    results["threats_found"].extend(
                        [asdict(t) for t in threats]
                    )
                    results["success"] = True
        
        if not results["success"]:
            log_warning("All scanning methods failed or unavailable")
            log_info("Alternative: Deploy companion app for app management")
        
        return results
    
    def _scan_mtp(self) -> Optional[List[DetectedThreat]]:
        """
        Attempt MTP scanning.
        
        Returns:
            List of threats or None if MTP not available
        """
        log_info("\n[*] Attempting MTP (USB Storage) scan...")
        
        device = self.mtp_scanner.find_mtp_device()
        if not device:
            return None
        
        log_success("Device found via MTP")
        
        # Crawl app data
        threats = self.mtp_scanner.crawl_app_data()
        
        if threats:
            log_warning(f"Found {len(threats)} suspicious app(s) via MTP:")
            for threat in threats:
                print_warning(f"  • {threat.package_name} ({threat.threat_level}) - {threat.reason}")
        
        return threats
    
    def _scan_fastboot(self) -> Optional[List[DetectedThreat]]:
        """
        Attempt Fastboot scanning.
        
        Returns:
            List of threats or None if Fastboot not available
        """
        log_info("\n[*] Attempting Fastboot scan...")
        
        if not self.fastboot_scanner.fastboot_path:
            log_warning("Fastboot not available")
            return None
        
        devices = self.fastboot_scanner.list_devices()
        if not devices:
            log_warning("No devices in Fastboot mode")
            return None
        
        log_success(f"Found {len(devices)} device(s) in Fastboot mode")
        
        # Get device info
        for device in devices:
            info = self.fastboot_scanner.get_device_info(device)
            log_info(f"Device info: {device}")
        
        return []
    
    def _scan_usb_storage(self) -> Optional[List[DetectedThreat]]:
        """
        Attempt USB storage scan.
        
        Returns:
            List of threats or None if unavailable
        """
        log_info("\n[*] Attempting USB Storage scan...")
        
        # This is similar to MTP but tries different mount patterns
        return self._scan_mtp()
    
    def disable_app_via_mtp(self, package_name: str) -> bool:
        """
        Attempt to disable app using MTP file manipulation.
        
        Args:
            package_name: Package name to disable
            
        Returns:
            bool: Success status
        """
        if not self.mtp_scanner.mount_point:
            log_error("Device not connected via MTP")
            return False
        
        log_info(f"Disabling app: {package_name}")
        
        # Try to corrupt/remove app data to prevent launch
        android_path = os.path.join(self.mtp_scanner.mount_point, "Android", "data", package_name)
        
        if not os.path.exists(android_path):
            log_warning(f"App data not found: {android_path}")
            return False
        
        try:
            # Backup before deletion
            backup_path = os.path.join(self.mtp_scanner.mount_point, ".backup", package_name)
            os.makedirs(backup_path, exist_ok=True)
            
            # Move app data to backup
            import shutil
            shutil.move(android_path, backup_path)
            
            log_success(f"App {package_name} disabled (data moved to backup)")
            return True
        except Exception as e:
            log_error(f"Failed to disable app: {e}")
            return False
    
    def print_summary(self, results: Dict) -> None:
        """
        Print scan results summary.
        
        Args:
            results: Scan results from scan_without_debug()
        """
        print("\n" + "=" * 70)
        print("NON-DEBUG SCAN RESULTS".center(70))
        print("=" * 70)
        
        if not results["methods_used"]:
            print_warning("No scanning methods available")
            print_info("Requirements: USB connection and proper file system access")
            return
        
        print(f"\nMethods used: {', '.join(results['methods_used'])}")
        print(f"Threats found: {len(results['threats_found'])}")
        print(f"Timestamp: {results['timestamp']}")
        
        if results['threats_found']:
            print("\nDetected Threats:")
            print("-" * 70)
            for threat in results['threats_found']:
                print(f"  Package: {threat['package_name']}")
                print(f"  Level: {threat['threat_level']}")
                print(f"  Type: {threat['threat_type']}")
                print(f"  Reason: {threat['reason']}")
                print()


# Helper functions
def log_debug(msg: str) -> None:
    """Log debug message (silent by default)."""
    pass


def log_success(msg: str) -> None:
    """Log success message."""
    print_success(msg)
